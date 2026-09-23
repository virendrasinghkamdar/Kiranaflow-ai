"""KiranaFlow AI - Customers API Routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from typing import List, Optional

from ..database import get_db
from ..models import Customer, Order, OrderItem, Product
from ..schemas import CustomerOut, CustomerWithStats, CustomerCreate

router = APIRouter(prefix="/api/customers", tags=["Customers"])


@router.get("", response_model=List[CustomerWithStats])
def list_customers(db: Session = Depends(get_db)):
    """List all customers with order stats."""
    customers = db.query(Customer).order_by(Customer.name).all()

    result = []
    for customer in customers:
        orders = db.query(Order).filter(Order.customer_id == customer.id).all()
        total_spent = sum(o.total for o in orders)
        last_order = max((o.created_at for o in orders), default=None) if orders else None

        result.append(CustomerWithStats(
            id=customer.id,
            name=customer.name,
            phone=customer.phone,
            address=customer.address,
            email=customer.email or "",
            preferred_time=customer.preferred_time or "",
            created_at=customer.created_at,
            order_count=len(orders),
            total_spent=round(total_spent, 2),
            last_order_at=last_order,
        ))

    return result


@router.get("/lookup")
def lookup_customer_by_phone(phone: str, db: Session = Depends(get_db)):
    """Look up a customer by phone number. Returns profile + purchase history.
    This is the key API for auto-filling customer details on the Dashboard."""
    customer = db.query(Customer).filter(Customer.phone == phone).first()
    if not customer:
        return {"found": False, "phone": phone}

    # Get full order history with item details
    orders = (
        db.query(Order)
        .filter(Order.customer_id == customer.id)
        .order_by(desc(Order.created_at))
        .all()
    )

    order_history = []
    frequently_bought = {}  # product_name -> count

    for o in orders:
        items = (
            db.query(OrderItem)
            .filter(OrderItem.order_id == o.id)
            .all()
        )

        items_detail = []
        for item in items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            product_name = product.name if product else "Unknown"
            items_detail.append({
                "product_name": product_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
            })
            # Track frequently bought items
            frequently_bought[product_name] = frequently_bought.get(product_name, 0) + item.quantity

        order_history.append({
            "order_id": o.id,
            "display_id": f"KF-{1000 + o.id}",
            "total": o.total,
            "status": o.status,
            "delivery_requested": o.delivery_requested,
            "item_count": len(items),
            "items": items_detail,
            "created_at": o.created_at.isoformat(),
        })

    # Sort frequently bought items by count
    top_items = sorted(frequently_bought.items(), key=lambda x: -x[1])[:5]

    return {
        "found": True,
        "id": customer.id,
        "name": customer.name,
        "phone": customer.phone,
        "address": customer.address,
        "email": customer.email or "",
        "preferred_time": customer.preferred_time or "",
        "created_at": customer.created_at.isoformat(),
        "total_orders": len(orders),
        "total_spent": round(sum(o.total for o in orders), 2),
        "order_history": order_history,
        "frequently_bought": [{"product": name, "total_qty": qty} for name, qty in top_items],
        "is_regular": len(orders) >= 3,
    }


@router.get("/{customer_id}")
def get_customer_detail(customer_id: int, db: Session = Depends(get_db)):
    """Get customer details with order history."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    orders = (
        db.query(Order)
        .filter(Order.customer_id == customer_id)
        .order_by(desc(Order.created_at))
        .all()
    )

    # Get items for each order
    order_list = []
    for o in orders:
        items = db.query(OrderItem).filter(OrderItem.order_id == o.id).all()
        items_detail = []
        for item in items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            items_detail.append({
                "product_name": product.name if product else "Unknown",
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
            })
        order_list.append({
            "id": o.id,
            "display_id": f"KF-{1000 + o.id}",
            "total": o.total,
            "status": o.status,
            "item_count": len(items),
            "items": items_detail,
            "created_at": o.created_at.isoformat(),
        })

    return {
        "id": customer.id,
        "name": customer.name,
        "phone": customer.phone,
        "address": customer.address,
        "email": customer.email or "",
        "preferred_time": customer.preferred_time or "",
        "created_at": customer.created_at.isoformat(),
        "orders": order_list,
        "total_spent": round(sum(o.total for o in orders), 2),
    }


@router.post("", response_model=CustomerOut)
def create_customer_endpoint(data: CustomerCreate, db: Session = Depends(get_db)):
    """Create a new customer."""
    existing = db.query(Customer).filter(Customer.phone == data.phone).first()
    if existing:
        raise HTTPException(status_code=409, detail="Customer with this phone already exists")

    customer = Customer(
        name=data.name,
        phone=data.phone,
        address=data.address,
        email=data.email or "",
        preferred_time=data.preferred_time or "",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer
