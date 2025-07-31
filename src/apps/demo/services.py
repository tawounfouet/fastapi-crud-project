"""
Demo App Services - Business logic layer
Contains the core business rules and operations
"""

import uuid

from fastapi import HTTPException
from sqlmodel import Session, desc, func, select

from src.apps.demo.models import Order, OrderItem, Product
from src.apps.demo.schemas import (
    DashboardStats,
    OrderCreate,
    OrderStats,
    OrderUpdate,
    ProductCreate,
    ProductStats,
    ProductUpdate,
)


class ProductService:
    """Service for product-related business logic"""

    @staticmethod
    def create_product(
        *, session: Session, product_in: ProductCreate, created_by_id: uuid.UUID
    ) -> Product:
        """Create a new product"""
        # Check if product name already exists
        existing = session.exec(
            select(Product).where(
                Product.name == product_in.name, Product.is_active is True
            )
        ).first()

        if existing:
            raise HTTPException(
                status_code=400, detail="Product with this name already exists"
            )

        db_product = Product.model_validate(
            product_in, update={"created_by_id": created_by_id}
        )
        session.add(db_product)
        session.commit()
        session.refresh(db_product)
        return db_product

    @staticmethod
    def get_product(*, session: Session, product_id: uuid.UUID) -> Product | None:
        """Get a product by ID"""
        return session.get(Product, product_id)

    @staticmethod
    def get_products(
        *,
        session: Session,
        skip: int = 0,
        limit: int = 100,
        category: str | None = None,
        is_active: bool | None = None,
    ) -> list[Product]:
        """Get products with optional filtering"""
        statement = select(Product)

        if category:
            statement = statement.where(Product.category == category)
        if is_active is not None:
            statement = statement.where(Product.is_active == is_active)

        statement = statement.offset(skip).limit(limit)
        return list(session.exec(statement).all())

    @staticmethod
    def update_product(
        *, session: Session, db_product: Product, product_in: ProductUpdate
    ) -> Product:
        """Update a product"""
        product_data = product_in.model_dump(exclude_unset=True)
        db_product.sqlmodel_update(product_data)
        session.add(db_product)
        session.commit()
        session.refresh(db_product)
        return db_product

    @staticmethod
    def delete_product(*, session: Session, product_id: uuid.UUID) -> bool:
        """Soft delete a product"""
        product = session.get(Product, product_id)
        if not product:
            return False

        product.is_active = False
        session.add(product)
        session.commit()
        return True

    @staticmethod
    def get_product_stats(*, session: Session) -> ProductStats:
        """Get product statistics"""
        total_products = (
            session.exec(select(func.count()).select_from(Product)).first() or 0
        )
        active_products = (
            session.exec(
                select(func.count())
                .select_from(Product)
                .where(Product.is_active is True)
            ).first()
            or 0
        )
        total_categories = (
            session.exec(select(func.count(func.distinct(Product.category)))).first()
            or 0
        )
        low_stock_products = (
            session.exec(
                select(func.count())
                .select_from(Product)
                .where(Product.stock_quantity < 10, Product.is_active is True)
            ).first()
            or 0
        )

        return ProductStats(
            total_products=total_products,
            active_products=active_products,
            total_categories=total_categories,
            low_stock_products=low_stock_products,
        )


class OrderService:
    """Service for order-related business logic"""

    @staticmethod
    def create_order(
        *, session: Session, order_in: OrderCreate, customer_id: uuid.UUID
    ) -> Order:
        """Create a new order with items"""
        # Validate products exist and calculate total
        total_amount = 0.0
        order_items_data = []

        for item in order_in.order_items:
            product = session.get(Product, item.product_id)
            if not product or not product.is_active:
                raise HTTPException(
                    status_code=400,
                    detail=f"Product {item.product_id} not found or inactive",
                )

            if product.stock_quantity < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for product {product.name}",
                )

            item_total = product.price * item.quantity
            total_amount += item_total

            order_items_data.append(
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_price": product.price,
                }
            )

        # Create order (exclude order_items since they're handled separately)
        order_data = order_in.model_dump(exclude={"order_items"})
        order_data.update({"customer_id": customer_id, "total_amount": total_amount})

        db_order = Order(**order_data)
        session.add(db_order)
        session.flush()  # Get the order ID

        # Create order items
        for item_data in order_items_data:
            order_item = OrderItem(order_id=db_order.id, **item_data)
            session.add(order_item)

        # Update product stock
        for item in order_in.order_items:
            product = session.get(Product, item.product_id)
            if product is not None:
                product.stock_quantity -= item.quantity
                session.add(product)

        session.commit()
        session.refresh(db_order)
        return db_order

    @staticmethod
    def get_order(*, session: Session, order_id: uuid.UUID) -> Order | None:
        """Get an order by ID"""
        return session.get(Order, order_id)

    @staticmethod
    def get_orders(
        *,
        session: Session,
        skip: int = 0,
        limit: int = 100,
        customer_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> list[Order]:
        """Get orders with optional filtering"""
        statement = select(Order)

        if customer_id:
            statement = statement.where(Order.customer_id == customer_id)
        if status:
            statement = statement.where(Order.status == status)

        statement = statement.offset(skip).limit(limit).order_by(desc(Order.created_at))
        return list(session.exec(statement).all())

    @staticmethod
    def update_order(
        *, session: Session, db_order: Order, order_in: OrderUpdate
    ) -> Order:
        """Update an order"""
        order_data = order_in.model_dump(exclude_unset=True)
        db_order.sqlmodel_update(order_data)
        session.add(db_order)
        session.commit()
        session.refresh(db_order)
        return db_order

    @staticmethod
    def get_order_stats(*, session: Session) -> OrderStats:
        """Get order statistics"""
        total_orders = (
            session.exec(select(func.count()).select_from(Order)).first() or 0
        )
        pending_orders = (
            session.exec(
                select(func.count()).select_from(Order).where(Order.status == "pending")
            ).first()
            or 0
        )
        completed_orders = (
            session.exec(
                select(func.count())
                .select_from(Order)
                .where(Order.status == "completed")
            ).first()
            or 0
        )
        total_revenue = (
            session.exec(
                select(func.sum(Order.total_amount)).where(Order.status == "completed")
            ).first()
            or 0.0
        )

        return OrderStats(
            total_orders=total_orders,
            pending_orders=pending_orders,
            completed_orders=completed_orders,
            total_revenue=total_revenue,
        )


class DashboardService:
    """Service for dashboard-related operations"""

    @staticmethod
    def get_dashboard_stats(*, session: Session) -> DashboardStats:
        """Get comprehensive dashboard statistics"""
        product_stats = ProductService.get_product_stats(session=session)
        order_stats = OrderService.get_order_stats(session=session)
        recent_orders = OrderService.get_orders(session=session, limit=5)

        return DashboardStats(
            products=product_stats, orders=order_stats, recent_orders=recent_orders
        )
