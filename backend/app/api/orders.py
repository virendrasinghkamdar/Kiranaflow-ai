"""KiranaFlow AI - Orders API Routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timezone, timedelta

from ..database import get_db
from ..models import Order, OrderItem, Customer, AgentEvent
from ..schemas import OrderOut, OrderItemOut, OrderBrief, AgentEventOut

router = APIRouter(prefix="/api/orders", tags=["Orders"])


@router.get("", response_model=List[OrderBrief])
def list_orders(
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List orders, newest first."""
    query = db.query(Order).options(joinedload(Order.customer), joinedload(Order.items))

    if status:
        query = query.filter(Order.status == status)

    orders = query.order_by(desc(Order.created_at)).limit(limit).all()

    result = []
    for order in orders:
        result.append(OrderBrief(
            id=order.id,
            customer_name=order.customer.name if order.customer else "Unknown",
            item_count=len(order.items),
            total=order.total,
            status=order.status,
            created_at=order.created_at,
        ))
    return result


@router.get("/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    """Get detailed order information."""
    order = (
        db.query(Order)
        .options(
            joinedload(Order.customer),
            joinedload(Order.items).joinedload(OrderItem.product),
            joinedload(Order.agent_events),
        )
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    items = []
    for item in order.items:
        items.append(OrderItemOut(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product.name if item.product else "Unknown",
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.total_price,
        ))

    events = []
    for event in sorted(order.agent_events, key=lambda e: e.timestamp):
        events.append(AgentEventOut(
            id=event.id,
            order_id=event.order_id,
            session_id=event.session_id,
            event_type=event.event_type,
            description=event.description,
            status=event.status,
            tool_name=event.tool_name,
            tool_input=event.tool_input,
            tool_output=event.tool_output,
            confidence=event.confidence,
            timestamp=event.timestamp,
        ))

    return {
        "id": order.id,
        "display_id": f"KF-{1000 + order.id}",
        "customer_id": order.customer_id,
        "customer_name": order.customer.name if order.customer else "Unknown",
        "customer_phone": order.customer.phone if order.customer else "",
        "status": order.status,
        "subtotal": order.subtotal,
        "delivery_fee": order.delivery_fee,
        "total": order.total,
        "delivery_address": order.delivery_address,
        "delivery_requested": order.delivery_requested,
        "original_request": order.original_request,
        "channel": order.channel,
        "created_at": order.created_at.isoformat(),
        "items": items,
        "agent_events": events,
    }
