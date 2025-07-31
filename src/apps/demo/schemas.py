"""
Demo App Schemas - Input/Output data models
Similar to Django serializers or forms
"""

import uuid
from datetime import datetime

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from src.apps.demo.models import OrderBase, OrderItemBase, ProductBase


# Product Schemas
class ProductCreate(ProductBase):
    """Schema for creating a new product"""

    pass


class ProductUpdate(SQLModel):
    """Schema for updating a product - all fields optional"""

    name: str | None = None
    description: str | None = None
    price: float | None = None
    is_active: bool | None = None
    category: str | None = None
    stock_quantity: int | None = None

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: float | None) -> float | None:
        if v is not None and v <= 0:
            raise ValueError("Price must be greater than 0")
        return v


class ProductPublic(ProductBase):
    """Schema for public product data"""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    created_by_id: uuid.UUID


class ProductsPublic(SQLModel):
    """Schema for paginated products response"""

    data: list[ProductPublic]
    count: int


# Order Schemas
class OrderItemCreate(OrderItemBase):
    """Schema for creating order items"""

    product_id: uuid.UUID


class OrderItemPublic(OrderItemBase):
    """Schema for public order item data"""

    id: uuid.UUID
    product_id: uuid.UUID
    product: ProductPublic | None = None


class OrderCreate(SQLModel):
    """Schema for creating orders"""

    status: str = Field(default="pending", max_length=50)
    notes: str | None = Field(default=None, max_length=500)
    order_items: list[OrderItemCreate]

    @field_validator("order_items")
    @classmethod
    def validate_order_items(cls, v: list[OrderItemCreate]) -> list[OrderItemCreate]:
        if not v:
            raise ValueError("Order must have at least one item")
        return v


class OrderUpdate(SQLModel):
    """Schema for updating orders"""

    status: str | None = None
    notes: str | None = None


class OrderPublic(OrderBase):
    """Schema for public order data"""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    customer_id: uuid.UUID
    order_items: list[OrderItemPublic] = []


class OrdersPublic(SQLModel):
    """Schema for paginated orders response"""

    data: list[OrderPublic]
    count: int


# Dashboard/Analytics Schemas
class ProductStats(SQLModel):
    """Schema for product statistics"""

    total_products: int
    active_products: int
    total_categories: int
    low_stock_products: int


class OrderStats(SQLModel):
    """Schema for order statistics"""

    total_orders: int
    pending_orders: int
    completed_orders: int
    total_revenue: float


class DashboardStats(SQLModel):
    """Schema for dashboard overview"""

    products: ProductStats
    orders: OrderStats
    recent_orders: list[OrderPublic]
