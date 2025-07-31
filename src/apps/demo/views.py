"""
Demo App Views - Route handlers and controllers
Similar to Django views.py
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import func, select

from src.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from src.apps.demo.models import Order, Product
from src.apps.demo.schemas import (
    DashboardStats,
    OrderCreate,
    OrderPublic,
    OrdersPublic,
    OrderUpdate,
    ProductCreate,
    ProductPublic,
    ProductsPublic,
    ProductUpdate,
)
from src.apps.demo.services import DashboardService, OrderService, ProductService
from src.apps.shared import Message

router = APIRouter()


# Product Views
@router.post("/products/", response_model=ProductPublic)
def create_product(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    product_in: ProductCreate,
) -> Any:
    """Create new product"""
    return ProductService.create_product(
        session=session, product_in=product_in, created_by_id=current_user.id
    )


@router.get("/products/", response_model=ProductsPublic)
def read_products(
    session: SessionDep,
    skip: int = 0,
    limit: int = Query(default=100, le=100),
    category: str | None = None,
    is_active: bool | None = None,
) -> Any:
    """Retrieve products with optional filtering"""
    products = ProductService.get_products(
        session=session, skip=skip, limit=limit, category=category, is_active=is_active
    )

    # Get total count for pagination
    count_statement = select(func.count()).select_from(Product)
    if category:
        count_statement = count_statement.where(Product.category == category)
    if is_active is not None:
        count_statement = count_statement.where(Product.is_active == is_active)

    count = session.exec(count_statement).one()

    return ProductsPublic(data=products, count=count)


@router.get("/products/{product_id}", response_model=ProductPublic)
def read_product(product_id: uuid.UUID, session: SessionDep) -> Any:
    """Get product by ID"""
    product = ProductService.get_product(session=session, product_id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/products/{product_id}", response_model=ProductPublic)
def update_product(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    product_id: uuid.UUID,
    product_in: ProductUpdate,
) -> Any:
    """Update product"""
    product = ProductService.get_product(session=session, product_id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Only allow creator or superuser to update
    if not current_user.is_superuser and product.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return ProductService.update_product(
        session=session, db_product=product, product_in=product_in
    )


@router.delete("/products/{product_id}")
def delete_product(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    product_id: uuid.UUID,
) -> Message:
    """Delete product (soft delete)"""
    product = ProductService.get_product(session=session, product_id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Only allow creator or superuser to delete
    if not current_user.is_superuser and product.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    success = ProductService.delete_product(session=session, product_id=product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")

    return Message(message="Product deleted successfully")


# Order Views
@router.post("/orders/", response_model=OrderPublic)
def create_order(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    order_in: OrderCreate,
) -> Any:
    """Create new order"""
    return OrderService.create_order(
        session=session, order_in=order_in, customer_id=current_user.id
    )


@router.get("/orders/", response_model=OrdersPublic)
def read_orders(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = Query(default=100, le=100),
    status: str | None = None,
) -> Any:
    """Retrieve orders"""
    # Regular users can only see their own orders
    customer_id = None if current_user.is_superuser else current_user.id

    orders = OrderService.get_orders(
        session=session, skip=skip, limit=limit, customer_id=customer_id, status=status
    )

    # Get total count
    count_statement = select(func.count()).select_from(Order)
    if not current_user.is_superuser:
        count_statement = count_statement.where(Order.customer_id == current_user.id)
    if status:
        count_statement = count_statement.where(Order.status == status)

    count = session.exec(count_statement).one()

    return OrdersPublic(data=orders, count=count)


@router.get("/orders/{order_id}", response_model=OrderPublic)
def read_order(
    order_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Get order by ID"""
    order = OrderService.get_order(session=session, order_id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Users can only see their own orders unless they're superuser
    if not current_user.is_superuser and order.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return order


@router.put("/orders/{order_id}", response_model=OrderPublic)
def update_order(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    order_id: uuid.UUID,
    order_in: OrderUpdate,
) -> Any:
    """Update order (status, notes)"""
    order = OrderService.get_order(session=session, order_id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Users can only update their own orders unless they're superuser
    if not current_user.is_superuser and order.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return OrderService.update_order(session=session, db_order=order, order_in=order_in)


# Dashboard Views
@router.get(
    "/dashboard/stats/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=DashboardStats,
)
def get_dashboard_stats(session: SessionDep) -> Any:
    """Get dashboard statistics (admin only)"""
    return DashboardService.get_dashboard_stats(session=session)
