"""KiranaFlow AI - Delivery API Routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import DeliveryPerson, Order
from ..tools.order_tools import dispatch_order

router = APIRouter(prefix="/api/delivery", tags=["Delivery"])


@router.get("/persons")
def list_delivery_persons(db: Session = Depends(get_db)):
    """List all delivery persons."""
    persons = db.query(DeliveryPerson).order_by(DeliveryPerson.name).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "phone": p.phone,
            "vehicle_type": p.vehicle_type,
            "area": p.area,
            "is_available": p.is_available,
        }
        for p in persons
    ]


@router.post("/dispatch/{order_id}")
def dispatch_delivery(order_id: int, db: Session = Depends(get_db)):
    """Assign a delivery person and return customer + rider messages with bill."""
    result = dispatch_order(db, order_id)
    if not result.get("success"):
        status = 503 if "available" in (result.get("error") or "") else 404
        raise HTTPException(status_code=status, detail=result.get("error", "Dispatch failed"))
    return result


@router.post("/complete/{order_id}")
def complete_delivery(order_id: int, db: Session = Depends(get_db)):
    """Mark an order as delivered."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = "delivered"

    if order.delivery_person_id:
        dp = db.query(DeliveryPerson).filter(DeliveryPerson.id == order.delivery_person_id).first()
        if dp:
            dp.is_available = True

    db.commit()
    return {"status": "delivered", "order_id": f"KF-{1000 + order.id}"}
