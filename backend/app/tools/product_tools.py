"""KiranaFlow AI - Product Tools

Server-side validated tools for product search and resolution.
The AI agent calls these tools; they execute against the real database.
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from ..models import Product
from ..schemas import ProductBrief
from difflib import SequenceMatcher
from ..services.language_rules import canonicalize_text


def _normalize(text: str) -> str:
    """Normalize + map Hinglish (aata→atta, doodh→milk) for matching."""
    return canonicalize_text(text)


def _similarity(a: str, b: str) -> float:
    """Calculate string similarity ratio."""
    return SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()


def _match_score(query: str, product: Product) -> Tuple[float, str]:
    """
    Calculate how well a query matches a product.
    Returns (score, explanation).
    """
    q = _normalize(query)
    best_score = 0.0
    explanation = ""

    # Exact name match
    if q == _normalize(product.name):
        return 1.0, f"Exact match: '{product.name}'"

    # Name contains query
    if q in _normalize(product.name):
        score = 0.9
        if score > best_score:
            best_score = score
            explanation = f"Name contains '{query}'"

    # Query contains product name word
    name_words = _normalize(product.name).split()
    for word in name_words:
        if len(word) > 2 and word in q:
            score = 0.85
            if score > best_score:
                best_score = score
                explanation = f"Query contains keyword '{word}' from '{product.name}'"

    # Brand match
    if q == _normalize(product.brand) or q in _normalize(product.brand):
        score = 0.8
        if score > best_score:
            best_score = score
            explanation = f"Brand match: '{product.brand}'"

    # Alias match - most important for Indian language support
    for alias in (product.aliases or []):
        alias_norm = _normalize(alias)
        if q == alias_norm:
            return 0.98, f"Matched alias '{alias}' → '{product.name}'"
        if q in alias_norm or alias_norm in q:
            score = 0.9
            if score > best_score:
                best_score = score
                explanation = f"Matched alias '{alias}' → '{product.name}'"
        sim = _similarity(q, alias_norm)
        if sim > 0.7 and sim > best_score:
            best_score = sim
            explanation = f"Fuzzy match '{query}' ≈ alias '{alias}' → '{product.name}'"

    # Fuzzy name match
    sim = _similarity(q, _normalize(product.name))
    if sim > 0.6 and sim > best_score:
        best_score = sim
        explanation = f"Fuzzy match '{query}' ≈ '{product.name}'"

    return best_score, explanation


def search_products(db: Session, query: str, limit: int = 8) -> List[dict]:
    """
    Search products by name, brand, aliases, or fuzzy match.
    Returns products sorted by relevance score.
    """
    products = db.query(Product).filter(Product.is_active == True).all()
    scored = []

    for product in products:
        score, explanation = _match_score(query, product)
        if score > 0.3:
            scored.append({
                "product": product,
                "score": score,
                "explanation": explanation
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]


def get_product(db: Session, product_id: int) -> Optional[Product]:
    """Get a product by ID."""
    return db.query(Product).filter(Product.id == product_id).first()


def check_inventory(db: Session, product_id: int, requested_qty: int) -> dict:
    """Check if requested quantity is available."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"available": False, "error": "Product not found", "stock": 0}

    return {
        "available": product.stock >= requested_qty,
        "stock": product.stock,
        "requested": requested_qty,
        "product_name": product.name,
        "product_id": product.id,
    }


def get_price(db: Session, product_id: int) -> dict:
    """Get current price for a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"error": "Product not found"}

    return {
        "product_id": product.id,
        "product_name": product.name,
        "price": product.price,
        "unit": product.unit,
    }


def find_alternatives(
    db: Session,
    query: str,
    category: Optional[str] = None,
    exclude_product_id: Optional[int] = None,
) -> List[dict]:
    """
    Find alternative products when the requested one is unavailable.
    Looks for products in the same category with available stock.
    """
    results = search_products(db, query, limit=10)
    alternatives = []
    original_category = category

    if not original_category and results:
        top = results[0]["product"]
        original_category = top.category if hasattr(top, "category") else top.get("category")

    if original_category:
        category_products = (
            db.query(Product)
            .filter(
                Product.is_active == True,
                Product.category == original_category,
                Product.stock > 0,
            )
            .all()
        )
    else:
        category_products = []

    for product in category_products:
        if exclude_product_id is not None and product.id == exclude_product_id:
            continue
        score, _ = _match_score(query, product)
        reason = (
            f"Same category ({product.category}), {product.stock} units available"
            if score < 0.5
            else f"Similar to '{query}' — {product.name} (₹{product.price})"
        )
        alternatives.append({
            "product": ProductBrief.model_validate(product),
            "reason": reason,
            "score": score,
        })

    alternatives.sort(key=lambda x: x["score"], reverse=True)
    return alternatives[:5]


def calculate_order_total(items: List[dict], delivery_fee: float = 30.0, delivery: bool = False) -> dict:
    """Calculate order subtotal, delivery fee, and total."""
    subtotal = sum(item["unit_price"] * item["quantity"] for item in items)
    actual_delivery = delivery_fee if delivery else 0
    total = subtotal + actual_delivery

    return {
        "subtotal": round(subtotal, 2),
        "delivery_fee": round(actual_delivery, 2),
        "total": round(total, 2),
        "item_count": len(items),
    }


def check_low_stock(db: Session) -> List[dict]:
    """Check for products that are at or below their low-stock threshold."""
    products = (
        db.query(Product)
        .filter(
            Product.is_active == True,
            Product.stock <= Product.low_stock_threshold,
        )
        .all()
    )

    alerts = []
    for p in products:
        status = "critical" if p.stock <= 2 else "low"
        # Suggest restocking to 3x threshold
        suggested_restock = max(p.low_stock_threshold * 3, 24)
        alerts.append({
            "product_id": p.id,
            "product_name": p.name,
            "current_stock": p.stock,
            "threshold": p.low_stock_threshold,
            "status": status,
            "suggested_restock": suggested_restock,
        })

    return alerts
