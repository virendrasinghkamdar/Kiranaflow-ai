"""KiranaFlow AI - Pydantic Request/Response Schemas"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ── Product Schemas ──

class ProductOut(BaseModel):
    id: int
    name: str
    category: str
    brand: str
    unit: str
    price: float
    cost_price: float = 0
    stock: int
    low_stock_threshold: int
    description: str
    aliases: list
    is_active: bool

    class Config:
        from_attributes = True


class ProductBrief(BaseModel):
    id: int
    name: str
    brand: str
    unit: str
    price: float
    stock: int
    low_stock_threshold: int
    category: str

    class Config:
        from_attributes = True


# ── Customer Schemas ──

class CustomerOut(BaseModel):
    id: int
    name: str
    phone: str
    address: str
    email: str = ""
    preferred_time: str = ""
    created_at: datetime

    class Config:
        from_attributes = True


class CustomerCreate(BaseModel):
    name: str
    phone: str
    address: str = ""
    email: str = ""
    preferred_time: str = ""


class CustomerWithStats(CustomerOut):
    order_count: int = 0
    total_spent: float = 0
    last_order_at: Optional[datetime] = None


# ── Delivery Person Schemas ──

class DeliveryPersonOut(BaseModel):
    id: int
    name: str
    phone: str
    vehicle_type: str
    area: str
    is_available: bool

    class Config:
        from_attributes = True


# ── Order Schemas ──

class OrderItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str = ""
    quantity: int
    unit_price: float
    total_price: float

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    customer_id: int
    customer_name: str = ""
    status: str
    subtotal: float
    delivery_fee: float
    total: float
    delivery_address: str
    delivery_requested: bool
    original_request: str
    channel: str
    created_at: datetime
    items: List[OrderItemOut] = []

    class Config:
        from_attributes = True


class OrderBrief(BaseModel):
    id: int
    customer_name: str = ""
    item_count: int = 0
    total: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Inventory Schemas ──

class InventoryTransactionOut(BaseModel):
    id: int
    product_id: int
    product_name: str = ""
    type: str
    quantity: int
    previous_stock: int
    new_stock: int
    order_id: Optional[int] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# ── Agent Event Schemas ──

class AgentEventOut(BaseModel):
    id: int
    order_id: Optional[int] = None
    session_id: Optional[str] = None
    event_type: str
    description: str
    status: str
    tool_name: Optional[str] = None
    tool_input: Optional[dict] = None
    tool_output: Optional[dict] = None
    confidence: Optional[float] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# ── AI Agent Schemas ──

class ProductSelection(BaseModel):
    product_query: str
    product_id: int
    quantity: int = 1


class CustomerRequest(BaseModel):
    """The customer's natural-language request."""
    message: str = Field(..., min_length=1, max_length=2000)
    customer_phone: str = Field(default="9876543210")
    channel: str = Field(default="whatsapp")
    selections: List[ProductSelection] = []


class ParsedItem(BaseModel):
    """An item parsed from the customer request."""
    product_query: str
    quantity: int = 1


class ParsedRequest(BaseModel):
    """The AI-parsed structure from natural language."""
    intent: str = "create_order"
    items: List[ParsedItem] = []
    delivery: bool = False
    customer_name: Optional[str] = None
    raw_message: str = ""


class ResolvedItem(BaseModel):
    """A product resolved against the database."""
    product_id: int
    product_name: str
    brand: str
    unit: str
    quantity: int
    unit_price: float
    total_price: float
    stock_available: int
    confidence: float = 1.0
    match_explanation: str = ""
    cost_price: float = 0


class AlternativeSuggestion(BaseModel):
    """An alternative product suggestion."""
    original_query: str
    product: ProductBrief
    reason: str


class PendingChoice(BaseModel):
    original_query: str
    quantity: int = 1
    unit: str = ""
    options: List[ProductBrief] = []


class OrderResult(BaseModel):
    """The final result of the agent pipeline."""
    success: bool
    order_id: Optional[int] = None
    order_display_id: str = ""
    customer_name: str = ""
    customer_phone: str = ""
    items: List[ResolvedItem] = []
    subtotal: float = 0
    delivery_fee: float = 0
    total: float = 0
    delivery_requested: bool = False
    delivery_address: str = ""
    confirmation_message: str = ""
    confirmation_message_hi: str = ""
    low_stock_alerts: List[dict] = []
    agent_events: List[AgentEventOut] = []
    alternatives: List[AlternativeSuggestion] = []
    error: Optional[str] = None
    operator_confidence: Optional[dict] = None
    delivery_person: Optional[dict] = None
    bill_summary: Optional[str] = None
    dispatch: Optional[dict] = None
    needs_selection: bool = False
    pending_choices: List[PendingChoice] = []
    understood_as: Optional[str] = None


# ── Dashboard Schemas ──

class DashboardStats(BaseModel):
    today_orders: int = 0
    today_revenue: float = 0
    today_profit: float = 0
    week_orders: int = 0
    week_revenue: float = 0
    week_profit: float = 0
    month_orders: int = 0
    month_revenue: float = 0
    month_profit: float = 0
    today_margin_pct: float = 0
    week_margin_pct: float = 0
    month_margin_pct: float = 0
    low_stock_count: int = 0
    pending_deliveries: int = 0
    total_products: int = 0
    total_customers: int = 0
    inventory_value: float = 0
    potential_profit: float = 0
