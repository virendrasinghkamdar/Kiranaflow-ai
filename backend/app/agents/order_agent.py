"""KiranaFlow AI - Autonomous Order Agent Pipeline

This is the core autonomous agent that orchestrates the complete order workflow:
  REQUEST → UNDERSTAND → RETRIEVE → DECIDE → ACT → UPDATE → CONFIRM

The agent uses validated backend tools and never directly modifies the database.
"""

import uuid
import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from ..services.ai_provider import get_ai_provider
from ..tools.product_tools import (
    search_products, get_product, check_inventory, get_price,
    find_alternatives, calculate_order_total, check_low_stock,
)
from ..tools.order_tools import (
    create_order, update_inventory, get_customer, create_customer,
    record_agent_event, send_confirmation, dispatch_order,
)
from ..schemas import (
    OrderResult, ResolvedItem, AlternativeSuggestion,
    AgentEventOut, ProductBrief, PendingChoice,
)
from ..config import settings
from ..services.language_rules import canonicalize_text, matches_are_ambiguous

logger = logging.getLogger(__name__)


class OrderAgent:
    """
    Autonomous order processing agent.
    Executes the full pipeline from natural language to confirmed order.
    """

    def __init__(self, db: Session):
        self.db = db
        self.session_id = str(uuid.uuid4())[:12]
        self.ai = get_ai_provider()
        self.events: List[dict] = []

    def _record_event(
        self,
        event_type: str,
        description: str,
        status: str = "completed",
        order_id: Optional[int] = None,
        tool_name: Optional[str] = None,
        tool_input: Optional[dict] = None,
        tool_output: Optional[dict] = None,
        confidence: Optional[float] = None,
    ):
        """Record an agent event and add to local list."""
        event = record_agent_event(
            db=self.db,
            event_type=event_type,
            description=description,
            status=status,
            order_id=order_id,
            session_id=self.session_id,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            confidence=confidence,
        )
        self.events.append({
            "id": event.id,
            "event_type": event.event_type,
            "description": event.description,
            "status": event.status,
            "tool_name": event.tool_name,
            "tool_input": event.tool_input,
            "tool_output": event.tool_output,
            "confidence": event.confidence,
            "timestamp": event.timestamp.isoformat(),
        })

    async def process_request(
        self,
        message: str,
        customer_phone: str = "9876543210",
        channel: str = "whatsapp",
        selections: Optional[List[dict]] = None,
    ) -> OrderResult:
        """
        Main entry point: process a natural-language customer request
        through the complete autonomous pipeline.
        """
        selections = selections or []
        try:
            # ── STEP 1: Request Received ──
            self._record_event(
                "REQUEST_RECEIVED",
                f"Customer request received via {channel}: \"{message}\"",
                tool_name="receive_request",
                tool_input={"message": message, "channel": channel},
            )

            # ── STEP 2: Parse Intent ──
            parsed = await self.ai.parse_customer_request(message)
            self._record_event(
                "INTENT_DETECTED",
                f"Intent: {parsed.get('intent', 'unknown')}, "
                f"Items: {len(parsed.get('items', []))}, "
                f"Delivery: {parsed.get('delivery', False)}",
                tool_name="parse_request",
                tool_input={"message": message},
                tool_output={
                    "intent": parsed.get("intent"),
                    "item_count": len(parsed.get("items", [])),
                    "delivery": parsed.get("delivery"),
                    "items": parsed.get("items", []),
                },
                confidence=0.95,
            )

            # ── STEP 3: Resolve Customer ──
            customer_data = get_customer(self.db, customer_phone)
            if not customer_data:
                customer_data = create_customer(self.db, name="Walk-in Customer", phone=customer_phone)
                self._record_event("CUSTOMER_CREATED", f"New customer created: {customer_phone}")
            else:
                self._record_event("CUSTOMER_FOUND", f"Customer found: {customer_data['name']}")

            if parsed.get("intent") == "repeat_last_order":
                last_items = self._last_order_items(customer_data["id"])
                if not last_items:
                    return OrderResult(
                        success=False,
                        error="No previous order found for this customer.",
                        customer_name=customer_data["name"],
                        agent_events=[AgentEventOut(**e) for e in self.events],
                    )
                parsed["items"] = last_items
                parsed["intent"] = "create_order"
                self._record_event(
                    "REPEAT_LAST_ORDER",
                    f"Repeating last order: {len(last_items)} items",
                    tool_name="repeat_last_order",
                    tool_output={"items": last_items},
                )

            if parsed.get("intent") != "create_order" or not parsed.get("items"):
                return OrderResult(
                    success=False,
                    error="Samajh nahi aaya / Could not understand. Product naam aur quantity batayiye — jaise '2 kilo aata'.",
                    agent_events=[AgentEventOut(**e) for e in self.events],
                )

            understood_bits = []
            for it in parsed["items"]:
                unit = it.get("unit") or ""
                understood_bits.append(f"{it['quantity']}{(' ' + unit) if unit else ''} {it['product_query']}".strip())
            understood_as = ", ".join(understood_bits)

            sel_map = {
                canonicalize_text(s.get("product_query", "")): s
                for s in selections if s.get("product_query")
            }

            # ── STEP 4-7: Resolve Products, Check Inventory, Get Prices ──
            resolved_items: List[ResolvedItem] = []
            alternatives: List[AlternativeSuggestion] = []
            pending_choices: List[PendingChoice] = []
            all_items_resolved = True

            for parsed_item in parsed["items"]:
                query = parsed_item["product_query"]
                qty = parsed_item["quantity"]
                unit = parsed_item.get("unit") or ""
                forced_id = parsed_item.get("product_id") or (
                    sel_map.get(canonicalize_text(query)) or {}
                ).get("product_id")

                search_results = search_products(self.db, query, limit=8)
                self._record_event(
                    "PRODUCT_SEARCHED",
                    f"Searched for '{query}'"
                    + (f" ({qty} {unit})".strip() if unit else f" ×{qty}")
                    + f": {len(search_results)} results",
                    tool_name="search_products",
                    tool_input={"query": query, "quantity": qty, "unit": unit},
                    tool_output={
                        "results": len(search_results),
                        "top_match": search_results[0]["product"].name if search_results else None,
                    },
                    confidence=search_results[0]["score"] if search_results else 0,
                )

                if forced_id:
                    product = get_product(self.db, int(forced_id))
                    if not product:
                        all_items_resolved = False
                        continue
                    match_confidence = 1.0
                    match_explanation = "Customer selected this brand"
                    self._record_event(
                        "PRODUCT_RESOLVED",
                        f"Customer picked {product.name} for '{query}'",
                        tool_name="resolve_product",
                        tool_output={"product_id": product.id, "product_name": product.name},
                        confidence=1.0,
                    )
                else:
                    if not search_results:
                        self._record_event(
                            "PRODUCT_NOT_FOUND",
                            f"No products found matching '{query}'",
                            status="failed",
                        )
                        all_items_resolved = False
                        continue

                    if matches_are_ambiguous(query, search_results):
                        options = [
                            ProductBrief.model_validate(r["product"])
                            for r in search_results[:6]
                        ]
                        pending_choices.append(PendingChoice(
                            original_query=query,
                            quantity=qty,
                            unit=unit,
                            options=options,
                        ))
                        names = ", ".join(o.name for o in options[:4])
                        self._record_event(
                            "BRAND_CHOICE_REQUIRED",
                            f"'{query}' matches multiple brands. Please choose: {names}",
                            status="warning",
                            tool_name="disambiguate_products",
                            tool_output={"options": [o.name for o in options]},
                        )
                        continue

                    best = search_results[0]
                    product = best["product"]
                    match_confidence = best["score"]
                    match_explanation = best["explanation"]
                    self._record_event(
                        "PRODUCT_RESOLVED",
                        f"Resolved '{query}' → {product.name} ({match_explanation})",
                        tool_name="resolve_product",
                        tool_input={"query": query},
                        tool_output={
                            "product_id": product.id,
                            "product_name": product.name,
                            "confidence": round(match_confidence, 2),
                        },
                        confidence=round(match_confidence, 2),
                    )

                # STEP 6: Check inventory
                inv_check = check_inventory(self.db, product.id, qty)
                self._record_event(
                    "INVENTORY_CHECKED",
                    f"{product.name}: Requested {qty}, Available {inv_check['stock']}",
                    tool_name="check_inventory",
                    tool_input={"product_id": product.id, "quantity": qty},
                    tool_output=inv_check,
                    confidence=1.0,
                )

                if not inv_check["available"]:
                    # STEP 8: Find alternatives
                    self._record_event(
                        "PRODUCT_UNAVAILABLE",
                        f"{product.name} unavailable (stock: {inv_check['stock']}). Searching alternatives...",
                        status="warning",
                    )

                    alts = find_alternatives(
                        self.db, query, product.category, exclude_product_id=product.id
                    )
                    substitute_product = None
                    for alt in alts:
                        alt_brief = alt["product"]
                        alternatives.append(AlternativeSuggestion(
                            original_query=query,
                            product=alt_brief,
                            reason=alt["reason"],
                        ))
                        self._record_event(
                            "ALTERNATIVE_FOUND",
                            f"Alternative for '{query}': {alt_brief.name} "
                            f"(₹{alt_brief.price}, {alt_brief.stock} in stock)",
                            tool_name="find_alternatives",
                            tool_output={
                                "alternative": alt_brief.name,
                                "price": alt_brief.price,
                            },
                        )
                        if substitute_product is None:
                            candidate = get_product(self.db, alt_brief.id)
                            if candidate and candidate.stock >= qty:
                                substitute_product = candidate

                    if substitute_product:
                        product = substitute_product
                        match_confidence = 0.85
                        match_explanation = (
                            f"Substituted unavailable item with {substitute_product.name}"
                        )
                        self._record_event(
                            "PRODUCT_SUBSTITUTED",
                            f"Auto-substituted '{query}' with {substitute_product.name}",
                            confidence=0.85,
                        )
                    else:
                        all_items_resolved = False
                        continue

                # STEP 7: Get price
                price_data = get_price(self.db, product.id)
                self._record_event(
                    "PRICE_RETRIEVED",
                    f"{product.name}: ₹{price_data['price']} per {price_data['unit']}",
                    tool_name="get_price",
                    tool_input={"product_id": product.id},
                    tool_output=price_data,
                    confidence=1.0,
                )

                resolved_items.append(ResolvedItem(
                    product_id=product.id,
                    product_name=product.name,
                    brand=product.brand,
                    unit=product.unit,
                    quantity=qty,
                    unit_price=price_data["price"],
                    total_price=round(price_data["price"] * qty, 2),
                    stock_available=product.stock,
                    confidence=round(match_confidence, 2),
                    match_explanation=match_explanation,
                    cost_price=product.cost_price or 0,
                ))

            if pending_choices:
                return OrderResult(
                    success=False,
                    needs_selection=True,
                    pending_choices=pending_choices,
                    understood_as=understood_as,
                    customer_name=customer_data["name"],
                    error="Kaunsa brand chahiye? Multiple products match — pick one to continue.",
                    alternatives=alternatives,
                    agent_events=[AgentEventOut(**e) for e in self.events],
                )

            if not resolved_items:
                return OrderResult(
                    success=False,
                    error="Could not resolve any products from your request.",
                    alternatives=alternatives,
                    agent_events=[AgentEventOut(**e) for e in self.events],
                )

            # ── STEP 9-10: Calculate Total ──
            delivery_requested = parsed.get("delivery", False)
            order_calc = calculate_order_total(
                items=[{"unit_price": item.unit_price, "quantity": item.quantity} for item in resolved_items],
                delivery_fee=settings.default_delivery_fee,
                delivery=delivery_requested,
            )

            self._record_event(
                "ORDER_CALCULATED",
                f"Subtotal: ₹{order_calc['subtotal']}, Delivery: ₹{order_calc['delivery_fee']}, Total: ₹{order_calc['total']}",
                tool_name="calculate_order_total",
                tool_input={"item_count": len(resolved_items), "delivery": delivery_requested},
                tool_output=order_calc,
                confidence=1.0,
            )

            # ── STEP 11: Create Order ──
            order_result = create_order(
                db=self.db,
                customer_id=customer_data["id"],
                items=[
                    {
                        "product_id": item.product_id,
                        "quantity": item.quantity,
                        "unit_price": item.unit_price,
                        "total_price": item.total_price,
                    }
                    for item in resolved_items
                ],
                subtotal=order_calc["subtotal"],
                delivery_fee=order_calc["delivery_fee"],
                total=order_calc["total"],
                delivery_address=customer_data.get("address", ""),
                delivery_requested=delivery_requested,
                original_request=message,
                channel=channel,
            )

            if not order_result.get("success"):
                self._record_event(
                    "ORDER_FAILED",
                    f"Order creation failed: {order_result.get('error')}",
                    status="failed",
                )
                return OrderResult(
                    success=False,
                    error=order_result.get("error", "Order creation failed"),
                    agent_events=[AgentEventOut(**e) for e in self.events],
                )

            order_id = order_result["order_id"]
            order_display_id = order_result["order_display_id"]

            self._record_event(
                "ORDER_CREATED",
                f"Order {order_display_id} created successfully. Total: ₹{order_calc['total']}",
                order_id=order_id,
                tool_name="create_order",
                tool_output={"order_id": order_id, "display_id": order_display_id, "total": order_calc["total"]},
                confidence=1.0,
            )

            # ── STEP 12-13: Update Inventory ──
            low_stock_alerts = []
            for item in resolved_items:
                inv_update = update_inventory(self.db, item.product_id, item.quantity, order_id)
                self._record_event(
                    "INVENTORY_UPDATED",
                    f"{item.product_name}: {inv_update.get('previous_stock')} → {inv_update.get('new_stock')}",
                    order_id=order_id,
                    tool_name="update_inventory",
                    tool_input={"product_id": item.product_id, "quantity": item.quantity},
                    tool_output=inv_update,
                    confidence=1.0,
                )

                if inv_update.get("is_low_stock"):
                    product_obj = get_product(self.db, item.product_id)
                    alert = {
                        "product_name": item.product_name,
                        "current_stock": inv_update["new_stock"],
                        "threshold": product_obj.low_stock_threshold if product_obj else 5,
                        "suggested_restock": max((product_obj.low_stock_threshold if product_obj else 5) * 3, 24),
                    }
                    low_stock_alerts.append(alert)

            # ── STEP 14: Check Low Stock ──
            all_low_stock = check_low_stock(self.db)
            self._record_event(
                "LOW_STOCK_CHECKED",
                f"{len(all_low_stock)} products at or below threshold",
                order_id=order_id,
                tool_name="check_low_stock",
                tool_output={"low_stock_count": len(all_low_stock), "alerts": [a["product_name"] for a in all_low_stock]},
            )

            # ── STEP 15: Send Confirmation ──
            confirmation = send_confirmation(
                order_data=order_result,
                items=[{"quantity": i.quantity, "product_name": i.product_name} for i in resolved_items],
                delivery=delivery_requested,
            )

            self._record_event(
                "CONFIRMATION_SENT",
                f"Order confirmation sent to customer via {channel}",
                order_id=order_id,
                tool_name="send_confirmation",
                tool_output={"success": True, "channel": channel},
                confidence=1.0,
            )

            # Update all previous events with the order_id
            from ..models import AgentEvent as AgentEventModel
            self.db.query(AgentEventModel).filter(
                AgentEventModel.session_id == self.session_id,
                AgentEventModel.order_id == None,
            ).update({"order_id": order_id})
            self.db.commit()

            # Update local events list
            for evt in self.events:
                if evt.get("order_id") is None:
                    evt["order_id"] = order_id

            product_match = (
                round(sum(i.confidence for i in resolved_items) / len(resolved_items), 2)
                if resolved_items
                else 0.0
            )
            operator_confidence = {
                "product_matching": product_match,
                "inventory_verification": 1.0,
                "order_confidence": round(min(0.99, (product_match + 1.0) / 2), 2),
            }

            delivery_person_info = None
            bill_summary = None
            dispatch_payload = None
            if delivery_requested:
                dispatch_payload = dispatch_order(self.db, order_id)
                if dispatch_payload.get("success"):
                    dp = dispatch_payload.get("customer_message", {}).get("delivery_person", {})
                    delivery_person_info = dp or None
                    bill_summary = dispatch_payload.get("customer_message", {}).get("bill_summary")
                    self._record_event(
                        "DELIVERY_DISPATCHED",
                        f"Assigned {dispatch_payload.get('delivery_person_name')} — "
                        f"customer & rider notified with bill",
                        order_id=order_id,
                        tool_name="dispatch_order",
                        tool_output={
                            "rider": dispatch_payload.get("delivery_person_name"),
                            "customer": customer_data["name"],
                        },
                        confidence=1.0,
                    )

            return OrderResult(
                success=True,
                order_id=order_id,
                order_display_id=order_display_id,
                customer_name=customer_data["name"],
                customer_phone=customer_phone,
                items=resolved_items,
                subtotal=order_calc["subtotal"],
                delivery_fee=order_calc["delivery_fee"],
                total=order_calc["total"],
                delivery_requested=delivery_requested,
                delivery_address=customer_data.get("address", ""),
                confirmation_message=confirmation["message"],
                confirmation_message_hi=confirmation.get("message_hi", ""),
                understood_as=understood_as,
                low_stock_alerts=low_stock_alerts,
                alternatives=alternatives,
                operator_confidence=operator_confidence,
                delivery_person=delivery_person_info,
                bill_summary=bill_summary,
                dispatch=dispatch_payload if dispatch_payload and dispatch_payload.get("success") else None,
                agent_events=[AgentEventOut(**e) for e in self.events],
            )

        except Exception as e:
            logger.exception("Agent pipeline error")
            self._record_event(
                "PIPELINE_ERROR",
                f"Error: {str(e)}",
                status="failed",
            )
            return OrderResult(
                success=False,
                error=f"An error occurred processing your request: {str(e)}",
                agent_events=[AgentEventOut(**e) for e in self.events],
            )

    def _last_order_items(self, customer_id: int) -> List[dict]:
        from ..models import Order, OrderItem

        last = (
            self.db.query(Order)
            .filter(Order.customer_id == customer_id)
            .order_by(Order.created_at.desc())
            .first()
        )
        if not last:
            return []
        rows = self.db.query(OrderItem).filter(OrderItem.order_id == last.id).all()
        items = []
        for row in rows:
            product = get_product(self.db, row.product_id)
            items.append({
                "product_query": product.name if product else str(row.product_id),
                "quantity": row.quantity,
                "product_id": row.product_id,
                "unit": product.unit if product else "",
            })
        return items
