"""KiranaFlow AI - Order and Inventory Tools

Server-validated tools for creating orders and managing inventory.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional
from ..models import Order, OrderItem, Product, Customer, InventoryTransaction, AgentEvent, DeliveryPerson
from ..config import settings


def create_order(
    db: Session,
    customer_id: int,
    items: List[dict],
    subtotal: float,
    delivery_fee: float,
    total: float,
    delivery_address: str = "",
    delivery_requested: bool = False,
    original_request: str = "",
    channel: str = "whatsapp",
) -> dict:
    """
    Create a validated order in the database.
    items: list of {product_id, quantity, unit_price, total_price}
    """
    # Validate customer
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return {"error": "Customer not found", "success": False}

    # Validate all items
    validated_items = []
    recalculated_subtotal = 0

    for item in items:
        product = db.query(Product).filter(Product.id == item["product_id"]).first()
        if not product:
            return {"error": f"Product ID {item['product_id']} not found", "success": False}

        if product.stock < item["quantity"]:
            return {
                "error": f"Insufficient stock for {product.name}: {product.stock} available, {item['quantity']} requested",
                "success": False,
            }

        # Server-side price validation
        unit_price = product.price
        cost_price = product.cost_price or 0
        total_price = round(unit_price * item["quantity"], 2)
        recalculated_subtotal += total_price

        validated_items.append({
            "product_id": product.id,
            "quantity": item["quantity"],
            "unit_price": unit_price,
            "cost_price": cost_price,
            "total_price": total_price,
            "product_name": product.name,
        })

    # Recalculate total server-side
    actual_delivery = delivery_fee if delivery_requested else 0
    recalculated_total = round(recalculated_subtotal + actual_delivery, 2)

    # Create order
    order = Order(
        customer_id=customer_id,
        status="confirmed",
        subtotal=round(recalculated_subtotal, 2),
        delivery_fee=round(actual_delivery, 2),
        total=recalculated_total,
        delivery_address=delivery_address or customer.address,
        delivery_requested=delivery_requested,
        original_request=original_request,
        channel=channel,
    )
    db.add(order)
    db.flush()  # Get the order ID

    # Create order items
    for vi in validated_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=vi["product_id"],
            quantity=vi["quantity"],
            unit_price=vi["unit_price"],
            cost_price=vi.get("cost_price") or 0,
            total_price=vi["total_price"],
        )
        db.add(order_item)

    db.commit()
    db.refresh(order)

    return {
        "success": True,
        "order_id": order.id,
        "order_display_id": f"KF-{1000 + order.id}",
        "customer_name": customer.name,
        "total": recalculated_total,
        "items": validated_items,
    }


def update_inventory(db: Session, product_id: int, quantity_sold: int, order_id: Optional[int] = None) -> dict:
    """
    Reduce inventory after a sale. Creates an inventory transaction record.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"error": "Product not found", "success": False}

    previous_stock = product.stock
    new_stock = previous_stock - quantity_sold

    if new_stock < 0:
        return {"error": f"Cannot reduce stock below 0. Current: {previous_stock}, Requested: {quantity_sold}", "success": False}

    # Update stock
    product.stock = new_stock
    db.flush()

    # Create inventory transaction
    transaction = InventoryTransaction(
        product_id=product.id,
        type="sale",
        quantity=quantity_sold,
        previous_stock=previous_stock,
        new_stock=new_stock,
        order_id=order_id,
    )
    db.add(transaction)
    db.commit()

    return {
        "success": True,
        "product_id": product.id,
        "product_name": product.name,
        "previous_stock": previous_stock,
        "quantity_sold": quantity_sold,
        "new_stock": new_stock,
        "is_low_stock": new_stock <= product.low_stock_threshold,
    }


def get_customer(db: Session, phone: str) -> Optional[dict]:
    """Get customer by phone number."""
    customer = db.query(Customer).filter(Customer.phone == phone).first()
    if not customer:
        return None
    return {
        "id": customer.id,
        "name": customer.name,
        "phone": customer.phone,
        "address": customer.address,
    }


def create_customer(db: Session, name: str, phone: str, address: str = "") -> dict:
    """Create a new customer."""
    existing = db.query(Customer).filter(Customer.phone == phone).first()
    if existing:
        return {
            "id": existing.id,
            "name": existing.name,
            "phone": existing.phone,
            "address": existing.address,
            "already_existed": True,
        }

    customer = Customer(name=name, phone=phone, address=address)
    db.add(customer)
    db.commit()
    db.refresh(customer)

    return {
        "id": customer.id,
        "name": customer.name,
        "phone": customer.phone,
        "address": customer.address,
        "already_existed": False,
    }


def record_agent_event(
    db: Session,
    event_type: str,
    description: str,
    status: str = "completed",
    order_id: Optional[int] = None,
    session_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    tool_input: Optional[dict] = None,
    tool_output: Optional[dict] = None,
    confidence: Optional[float] = None,
) -> AgentEvent:
    """Record an agent activity event."""
    event = AgentEvent(
        order_id=order_id,
        session_id=session_id,
        event_type=event_type,
        description=description,
        status=status,
        tool_name=tool_name,
        tool_input=tool_input,
        tool_output=tool_output,
        confidence=confidence,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def send_confirmation(order_data: dict, items: list, delivery: bool = False) -> dict:
    """
    Generate English + Hindi order confirmation.
    In production this would send via WhatsApp/SMS.
    """
    items_en = "\n".join(
        f"  {item['quantity']} × {item['product_name']}"
        for item in items
    )
    items_hi = "\n".join(
        f"  {item['quantity']} × {item['product_name']}"
        for item in items
    )
    display = order_data.get("order_display_id", "")
    total = order_data.get("total", 0)
    delivery_en = "\n\nYour order will be delivered to your home shortly." if delivery else ""
    delivery_hi = "\n\nAapka order ghar pe deliver ho jayega." if delivery else ""

    message_en = (
        f"✓ Order Confirmed\n\n"
        f"Your order #{display} has been confirmed.\n\n"
        f"{items_en}\n\n"
        f"Total: ₹{total}"
        f"{delivery_en}"
    )
    message_hi = (
        f"✓ Order Confirm ho gaya\n\n"
        f"Aapka order #{display} confirm ho chuka hai.\n\n"
        f"{items_hi}\n\n"
        f"Kul: ₹{total}"
        f"{delivery_hi}"
    )

    return {
        "success": True,
        "message": message_en,
        "message_hi": message_hi,
        "order_id": order_data.get("order_id"),
        "channel": "whatsapp",
    }


def _build_bill_text(order: Order, item_details: list) -> str:
    lines = [
        "────────────────────────────────",
        "     🏪 KIRANAFLOW AI — BILL",
        f"     Order: KF-{1000 + order.id}",
        "────────────────────────────────",
    ]
    for it in item_details:
        lines.append(f"  {it['product_name']} ({it['unit']})")
        lines.append(f"    {it['quantity']} × ₹{it['unit_price']} = ₹{it['total_price']}")
    lines.append("────────────────────────────────")
    lines.append(f"  Subtotal:     ₹{order.subtotal}")
    if order.delivery_fee > 0:
        lines.append(f"  Delivery Fee: ₹{order.delivery_fee}")
    lines.append(f"  TOTAL:        ₹{order.total}")
    lines.append("────────────────────────────────")
    return "\n".join(lines)


def dispatch_order(db: Session, order_id: int) -> dict:
    """
    Assign a delivery person (if needed) and build the two WhatsApp-style messages:
    - customer: rider name/phone/vehicle + bill
    - rider: customer name/phone/address + items + bill
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"success": False, "error": "Order not found"}

    customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
    if not customer:
        return {"success": False, "error": "Customer not found"}

    delivery_person = None
    if order.delivery_person_id:
        delivery_person = db.query(DeliveryPerson).filter(
            DeliveryPerson.id == order.delivery_person_id
        ).first()

    if not delivery_person:
        delivery_person = (
            db.query(DeliveryPerson)
            .filter(DeliveryPerson.is_available == True)
            .first()
        )
        if not delivery_person:
            return {"success": False, "error": "No delivery person available"}
        order.delivery_person_id = delivery_person.id
        order.status = "out_for_delivery"
        delivery_person.is_available = False
        db.commit()
    elif order.status in ("confirmed", "pending"):
        order.status = "out_for_delivery"
        db.commit()

    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    item_details = []
    for item in items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        item_details.append({
            "product_name": product.name if product else "Unknown",
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "total_price": item.total_price,
            "unit": product.unit if product else "",
        })

    bill_text = _build_bill_text(order, item_details)
    address = order.delivery_address or customer.address or ""

    return {
        "success": True,
        "customer_message": {
            "order_id": f"KF-{1000 + order.id}",
            "status": "Out for Delivery",
            "text": (
                f"Order KF-{1000 + order.id} confirmed.\n"
                f"{delivery_person.name} is on the way "
                f"({delivery_person.vehicle_type}).\n"
                f"Call: {delivery_person.phone}\n"
                f"ETA: 15–25 minutes\n\n"
                f"{bill_text}"
            ),
            "delivery_person": {
                "name": delivery_person.name,
                "phone": delivery_person.phone,
                "vehicle": delivery_person.vehicle_type,
            },
            "estimated_time": "15-25 minutes",
            "bill_summary": bill_text,
            "total": order.total,
        },
        "delivery_person_message": {
            "order_id": f"KF-{1000 + order.id}",
            "text": (
                f"New delivery KF-{1000 + order.id}\n"
                f"Customer: {customer.name}\n"
                f"Phone: {customer.phone}\n"
                f"Address: {address}\n"
                f"COD: ₹{order.total}\n\n"
                f"{bill_text}"
            ),
            "customer": {
                "name": customer.name,
                "phone": customer.phone,
                "address": address,
            },
            "items": item_details,
            "total": order.total,
            "payment_mode": "Cash on Delivery",
            "bill_summary": bill_text,
        },
        "delivery_person_id": delivery_person.id,
        "delivery_person_name": delivery_person.name,
        "delivery_person_phone": delivery_person.phone,
    }
