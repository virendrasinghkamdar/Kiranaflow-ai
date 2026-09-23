"""KiranaFlow AI - Dashboard & Events API Routes"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timezone, timedelta

from ..database import get_db
from ..models import Order, Product, AgentEvent, Customer, OrderItem
from ..schemas import DashboardStats, AgentEventOut

router = APIRouter(prefix="/api", tags=["Dashboard"])


def _period_start(now: datetime, kind: str) -> datetime:
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if kind == "week":
        return today - timedelta(days=today.weekday())
    if kind == "month":
        return today.replace(day=1)
    return today


def _finance_between(db: Session, start: datetime):
    orders = (
        db.query(Order)
        .filter(Order.created_at >= start, Order.status != "cancelled")
        .all()
    )
    revenue = round(sum(o.total for o in orders), 2)
    profit = 0.0
    for order in orders:
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        for item in items:
            cp = item.cost_price or 0
            if not cp and item.product_id:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                cp = (product.cost_price if product else 0) or 0
            profit += (item.unit_price - cp) * item.quantity
        profit += order.delivery_fee or 0
    profit = round(profit, 2)
    margin = round((profit / revenue) * 100, 1) if revenue else 0
    return len(orders), revenue, profit, margin


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    now = datetime.now(timezone.utc)
    today_orders, today_revenue, today_profit, today_margin = _finance_between(db, _period_start(now, "today"))
    week_orders, week_revenue, week_profit, week_margin = _finance_between(db, _period_start(now, "week"))
    month_orders, month_revenue, month_profit, month_margin = _finance_between(db, _period_start(now, "month"))

    low_stock = (
        db.query(Product)
        .filter(Product.is_active == True, Product.stock <= Product.low_stock_threshold)
        .count()
    )

    pending = db.query(Order).filter(
        Order.delivery_requested == True,
        Order.status.in_(["confirmed", "pending", "out_for_delivery"]),
    ).count()

    products = db.query(Product).filter(Product.is_active == True).all()
    inventory_value = round(sum((p.cost_price or 0) * p.stock for p in products), 2)
    potential_profit = round(sum(((p.price or 0) - (p.cost_price or 0)) * p.stock for p in products), 2)

    return DashboardStats(
        today_orders=today_orders,
        today_revenue=today_revenue,
        today_profit=today_profit,
        today_margin_pct=today_margin,
        week_orders=week_orders,
        week_revenue=week_revenue,
        week_profit=week_profit,
        week_margin_pct=week_margin,
        month_orders=month_orders,
        month_revenue=month_revenue,
        month_profit=month_profit,
        month_margin_pct=month_margin,
        low_stock_count=low_stock,
        pending_deliveries=pending,
        total_products=len(products),
        total_customers=db.query(Customer).count(),
        inventory_value=inventory_value,
        potential_profit=potential_profit,
    )


@router.get("/events", response_model=List[AgentEventOut])
def list_agent_events(
    order_id: Optional[int] = None,
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List agent activity events with optional filters."""
    query = db.query(AgentEvent)

    if order_id:
        query = query.filter(AgentEvent.order_id == order_id)
    if event_type:
        query = query.filter(AgentEvent.event_type == event_type)
    if status:
        query = query.filter(AgentEvent.status == status)

    events = query.order_by(desc(AgentEvent.timestamp)).limit(limit).all()

    return [
        AgentEventOut(
            id=e.id,
            order_id=e.order_id,
            session_id=e.session_id,
            event_type=e.event_type,
            description=e.description,
            status=e.status,
            tool_name=e.tool_name,
            tool_input=e.tool_input,
            tool_output=e.tool_output,
            confidence=e.confidence,
            timestamp=e.timestamp,
        )
        for e in events
    ]


@router.get("/inventory-transactions")
def list_inventory_transactions(
    product_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List inventory transactions."""
    from ..models import InventoryTransaction
    query = db.query(InventoryTransaction)
    if product_id:
        query = query.filter(InventoryTransaction.product_id == product_id)
    txns = query.order_by(desc(InventoryTransaction.timestamp)).limit(limit).all()
    return [
        {
            "id": t.id,
            "product_id": t.product_id,
            "product_name": t.product.name if t.product else "Unknown",
            "type": t.type,
            "quantity": t.quantity,
            "previous_stock": t.previous_stock,
            "new_stock": t.new_stock,
            "order_id": t.order_id,
            "timestamp": t.timestamp.isoformat(),
        }
        for t in txns
    ]


@router.get("/dashboard/low-stock")
def get_low_stock_details(db: Session = Depends(get_db)):
    """Get detailed low stock product information for the dashboard drilldown."""
    products = (
        db.query(Product)
        .filter(Product.is_active == True, Product.stock <= Product.low_stock_threshold)
        .order_by(Product.stock)
        .all()
    )
    return [
        {
            "id": p.id,
            "name": p.name,
            "brand": p.brand,
            "category": p.category,
            "stock": p.stock,
            "threshold": p.low_stock_threshold,
            "price": p.price,
            "unit": p.unit,
            "status": "critical" if p.stock <= 2 else ("out" if p.stock == 0 else "low"),
            "suggested_restock": max(p.low_stock_threshold * 3, 24),
        }
        for p in products
    ]


@router.get("/dashboard/pending-deliveries")
def get_pending_deliveries(db: Session = Depends(get_db)):
    """Get pending delivery orders with customer details."""
    from sqlalchemy.orm import joinedload

    orders = (
        db.query(Order)
        .options(joinedload(Order.customer), joinedload(Order.items))
        .filter(
            Order.delivery_requested == True,
            Order.status.in_(["confirmed", "pending"]),
        )
        .order_by(desc(Order.created_at))
        .all()
    )
    return [
        {
            "order_id": o.id,
            "display_id": f"KF-{1000 + o.id}",
            "customer_name": o.customer.name if o.customer else "Unknown",
            "customer_phone": o.customer.phone if o.customer else "",
            "address": o.delivery_address or (o.customer.address if o.customer else ""),
            "total": o.total,
            "item_count": len(o.items),
            "status": o.status,
            "created_at": o.created_at.isoformat(),
        }
        for o in orders
    ]


@router.get("/dashboard/revenue-breakdown")
def get_revenue_breakdown(db: Session = Depends(get_db)):
    """Get per-order revenue breakdown for today."""
    from sqlalchemy.orm import joinedload

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    orders = (
        db.query(Order)
        .options(joinedload(Order.customer), joinedload(Order.items))
        .filter(Order.created_at >= today_start)
        .order_by(desc(Order.created_at))
        .all()
    )

    total_revenue = round(sum(o.total for o in orders), 2)

    return {
        "total_revenue": total_revenue,
        "order_count": len(orders),
        "orders": [
            {
                "order_id": o.id,
                "display_id": f"KF-{1000 + o.id}",
                "customer_name": o.customer.name if o.customer else "Unknown",
                "subtotal": o.subtotal,
                "delivery_fee": o.delivery_fee,
                "total": o.total,
                "item_count": len(o.items),
                "status": o.status,
                "created_at": o.created_at.isoformat(),
            }
            for o in orders
        ],
    }


@router.get("/dashboard/pulse")
def neighborhood_pulse(db: Session = Depends(get_db)):
    """Live neighborhood demand: what the mohalla is buying."""
    from ..models import OrderItem, Product

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_order_ids = [
        r[0] for r in db.query(Order.id).filter(Order.created_at >= today_start).all()
    ]

    movers = []
    if today_order_ids:
        rows = (
            db.query(
                OrderItem.product_id,
                func.sum(OrderItem.quantity),
                func.sum(OrderItem.total_price),
            )
            .filter(OrderItem.order_id.in_(today_order_ids))
            .group_by(OrderItem.product_id)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(6)
            .all()
        )
        for product_id, qty, revenue in rows:
            product = db.query(Product).filter(Product.id == product_id).first()
            if product:
                movers.append({
                    "name": product.name,
                    "qty": int(qty or 0),
                    "revenue": round(float(revenue or 0), 2),
                })

    if not movers:
        # Seeded history still tells a neighborhood story
        rows = (
            db.query(
                OrderItem.product_id,
                func.sum(OrderItem.quantity),
            )
            .group_by(OrderItem.product_id)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(6)
            .all()
        )
        for product_id, qty in rows:
            product = db.query(Product).filter(Product.id == product_id).first()
            if product:
                movers.append({
                    "name": product.name,
                    "qty": int(qty or 0),
                    "revenue": 0,
                })

    return {
        "headline": "Mohalla pulse",
        "movers": movers,
        "low_stock": db.query(Product).filter(
            Product.is_active == True, Product.stock <= Product.low_stock_threshold
        ).count(),
    }
