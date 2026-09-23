"""KiranaFlow AI - Database Models (SQLAlchemy ORM)"""

from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean, JSON,
    create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime, timezone

Base = declarative_base()


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    brand = Column(String(100), nullable=False)
    unit = Column(String(50), nullable=False)  # e.g., "5kg", "1L", "200g"
    price = Column(Float, nullable=False)  # selling price (SP)
    cost_price = Column(Float, nullable=False, default=0)  # cost price (CP)
    stock = Column(Integer, nullable=False, default=0)
    low_stock_threshold = Column(Integer, nullable=False, default=5)
    description = Column(Text, default="")
    aliases = Column(JSON, default=list)  # List of alternate names/search terms
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    order_items = relationship("OrderItem", back_populates="product")
    inventory_transactions = relationship("InventoryTransaction", back_populates="product")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False, unique=True, index=True)
    address = Column(Text, default="")
    email = Column(String(200), default="")
    preferred_time = Column(String(50), default="")  # Morning, Afternoon, Evening
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    orders = relationship("Order", back_populates="customer")


class DeliveryPerson(Base):
    __tablename__ = "delivery_persons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False, unique=True)
    vehicle_type = Column(String(50), default="Bicycle")  # Bicycle, Scooter, E-Bike
    area = Column(Text, default="")
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    deliveries = relationship("Order", back_populates="delivery_person")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    delivery_person_id = Column(Integer, ForeignKey("delivery_persons.id"), nullable=True)
    status = Column(String(50), nullable=False, default="confirmed")  # pending, confirmed, delivered, cancelled
    subtotal = Column(Float, nullable=False, default=0)
    delivery_fee = Column(Float, nullable=False, default=0)
    total = Column(Float, nullable=False, default=0)
    delivery_address = Column(Text, default="")
    delivery_requested = Column(Boolean, default=False)
    original_request = Column(Text, default="")
    channel = Column(String(50), default="in-store")  # whatsapp, in-store, phone
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    customer = relationship("Customer", back_populates="orders")
    delivery_person = relationship("DeliveryPerson", back_populates="deliveries")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    agent_events = relationship("AgentEvent", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    cost_price = Column(Float, nullable=False, default=0)
    total_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    type = Column(String(50), nullable=False)  # sale, restock, adjustment
    quantity = Column(Integer, nullable=False)
    previous_stock = Column(Integer, nullable=False)
    new_stock = Column(Integer, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    product = relationship("Product", back_populates="inventory_transactions")


class AgentEvent(Base):
    __tablename__ = "agent_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    session_id = Column(String(100), nullable=True, index=True)
    event_type = Column(String(100), nullable=False)
    description = Column(Text, default="")
    status = Column(String(50), nullable=False, default="completed")  # completed, failed, pending
    tool_name = Column(String(100), nullable=True)
    tool_input = Column(JSON, nullable=True)
    tool_output = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    order = relationship("Order", back_populates="agent_events")
