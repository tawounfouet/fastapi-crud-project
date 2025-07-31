"""
Demo App Models - Domain entities and database models
Similar to Django models.py
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.apps.users.models import User


# Shared properties
class ProductBase(SQLModel):
    name: str = Field(min_length=1, max_length=255, index=True)
    description: str | None = Field(default=None, max_length=1000)
    price: float = Field(gt=0, description="Price must be greater than 0")
    is_active: bool = Field(default=True)
    category: str = Field(min_length=1, max_length=100)
    stock_quantity: int = Field(ge=0, description="Stock quantity must be non-negative")


# Database model
class Product(ProductBase, table=True):
    __tablename__ = "demo_product"  # Prefix with app name

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Foreign key to User
    created_by_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    created_by: "User" = Relationship()


# Order models
class OrderBase(SQLModel):
    total_amount: float = Field(gt=0)
    status: str = Field(default="pending", max_length=50)
    notes: str | None = Field(default=None, max_length=500)


class Order(OrderBase, table=True):
    __tablename__ = "demo_order"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Foreign keys
    customer_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    customer: "User" = Relationship()

    # Relationship with order items
    order_items: list["OrderItem"] = Relationship(back_populates="order")


class OrderItemBase(SQLModel):
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)


class OrderItem(OrderItemBase, table=True):
    __tablename__ = "demo_order_item"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Foreign keys
    order_id: uuid.UUID = Field(foreign_key="demo_order.id", nullable=False)
    product_id: uuid.UUID = Field(foreign_key="demo_product.id", nullable=False)

    # Relationships
    order: Order = Relationship(back_populates="order_items")
    product: Product = Relationship()
