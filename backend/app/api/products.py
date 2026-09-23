"""KiranaFlow AI - Products API Routes"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import Product
from ..schemas import ProductOut, ProductBrief
from ..tools.product_tools import search_products as search_fn, check_low_stock

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("", response_model=List[ProductOut])
def list_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all products, optionally filtered by category or search."""
    query = db.query(Product).filter(Product.is_active == True)

    if category:
        query = query.filter(Product.category == category)

    if search:
        results = search_fn(db, search, limit=20)
        product_ids = [r["product"].id for r in results]
        return db.query(Product).filter(Product.id.in_(product_ids)).all()

    return query.order_by(Product.category, Product.name).all()


@router.get("/categories", response_model=List[str])
def list_categories(db: Session = Depends(get_db)):
    """List all product categories."""
    rows = (
        db.query(Product.category)
        .filter(Product.is_active == True)
        .distinct()
        .order_by(Product.category)
        .all()
    )
    return [r[0] for r in rows]


@router.get("/low-stock")
def get_low_stock(db: Session = Depends(get_db)):
    """Get all products at or below their low-stock threshold."""
    return check_low_stock(db)


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a single product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Product not found")
    return product
