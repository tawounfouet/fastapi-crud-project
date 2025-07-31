# Implementation Guide

This guide provides step-by-step instructions for implementing the Domain-Driven Development (DDD) architecture in FastAPI applications.

## 🎯 Overview

The DDD implementation follows these core principles:
- **Domain Isolation**: Each app represents a bounded context
- **Layered Architecture**: Clear separation between models, services, and views
- **Business Logic Encapsulation**: Services contain all business rules
- **Clean API Design**: Schemas separate internal models from API contracts

## 📋 Prerequisites

Before implementing DDD patterns, ensure you have:
- FastAPI application with basic structure
- SQLModel for database models
- Alembic for database migrations
- Pytest for testing
- Understanding of dependency injection

## 🏗️ Step-by-Step Implementation

### Step 1: Create Apps Directory Structure

First, create the apps directory structure:

```bash
mkdir -p src/apps
touch src/apps/__init__.py
```

### Step 2: Create Your First App

Create a new domain app (example: `shop`):

```bash
mkdir -p src/apps/shop
touch src/apps/shop/__init__.py
touch src/apps/shop/models.py
touch src/apps/shop/schemas.py
touch src/apps/shop/services.py
touch src/apps/shop/views.py
touch src/apps/shop/urls.py
mkdir -p src/apps/shop/tests
touch src/apps/shop/tests/__init__.py
```

### Step 3: Implement Models

Define your domain models in `models.py`:

```python
"""
Shop App Models - Database entities
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class Product(SQLModel, table=True):
    """Product model representing items in the shop"""
    
    __tablename__ = "shop_products"
    
    # Primary key
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Core attributes
    name: str = Field(max_length=255, index=True)
    description: Optional[str] = Field(default=None, max_length=1000)
    price: float = Field(gt=0)
    stock_quantity: int = Field(default=0, ge=0)
    category: str = Field(max_length=100, index=True)
    
    # Status
    is_active: bool = Field(default=True, index=True)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    
    # Foreign keys
    created_by_id: uuid.UUID = Field(foreign_key="user.id")
    
    # Relationships
    created_by: Optional["User"] = Relationship(back_populates="products")
    order_items: list["OrderItem"] = Relationship(back_populates="product")


class Order(SQLModel, table=True):
    """Order model representing customer orders"""
    
    __tablename__ = "shop_orders"
    
    # Primary key
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Core attributes
    status: str = Field(default="pending", max_length=50, index=True)
    total_amount: float = Field(default=0.0, ge=0)
    notes: Optional[str] = Field(default=None, max_length=500)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    
    # Foreign keys
    customer_id: uuid.UUID = Field(foreign_key="user.id")
    
    # Relationships
    customer: Optional["User"] = Relationship(back_populates="orders")
    order_items: list["OrderItem"] = Relationship(back_populates="order")


class OrderItem(SQLModel, table=True):
    """Order item model representing products in an order"""
    
    __tablename__ = "shop_order_items"
    
    # Primary key
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Core attributes
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)
    
    # Foreign keys
    order_id: uuid.UUID = Field(foreign_key="shop_orders.id")
    product_id: uuid.UUID = Field(foreign_key="shop_products.id")
    
    # Relationships
    order: Optional[Order] = Relationship(back_populates="order_items")
    product: Optional[Product] = Relationship(back_populates="order_items")
```

### Step 4: Define Schemas

Create API schemas in `schemas.py`:

```python
"""
Shop App Schemas - API input/output models
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# Product Schemas
class ProductBase(BaseModel):
    """Base product schema"""
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    price: float = Field(gt=0)
    stock_quantity: int = Field(ge=0)
    category: str = Field(min_length=1, max_length=100)


class ProductCreate(ProductBase):
    """Schema for creating products"""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating products"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[float] = Field(None, gt=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None


class ProductOut(ProductBase):
    """Schema for product output"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by_id: uuid.UUID


# Order Schemas
class OrderItemCreate(BaseModel):
    """Schema for creating order items"""
    product_id: uuid.UUID
    quantity: int = Field(gt=0)


class OrderItemOut(BaseModel):
    """Schema for order item output"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    product_id: uuid.UUID
    quantity: int
    unit_price: float


class OrderCreate(BaseModel):
    """Schema for creating orders"""
    notes: Optional[str] = Field(None, max_length=500)
    order_items: list[OrderItemCreate] = Field(min_length=1)


class OrderUpdate(BaseModel):
    """Schema for updating orders"""
    status: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None, max_length=500)


class OrderOut(BaseModel):
    """Schema for order output"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    status: str
    total_amount: float
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    customer_id: uuid.UUID
    order_items: list[OrderItemOut] = []


# Statistics Schemas
class ProductStats(BaseModel):
    """Product statistics schema"""
    total_products: int
    active_products: int
    total_categories: int
    low_stock_products: int


class OrderStats(BaseModel):
    """Order statistics schema"""
    total_orders: int
    pending_orders: int
    completed_orders: int
    total_revenue: float
```

### Step 5: Implement Services

Create business logic in `services.py`:

```python
"""
Shop App Services - Business logic layer
"""
import uuid
from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.apps.shop.models import Order, OrderItem, Product
from app.apps.shop.schemas import (
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
        """Create a new product with business validation"""
        # Business rule: No duplicate product names
        existing = session.exec(
            select(Product).where(
                Product.name == product_in.name, Product.is_active == True
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
    def get_product(*, session: Session, product_id: uuid.UUID) -> Optional[Product]:
        """Get a product by ID"""
        return session.get(Product, product_id)

    @staticmethod
    def get_products(
        *,
        session: Session,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> list[Product]:
        """Get products with filtering"""
        statement = select(Product)

        if category:
            statement = statement.where(Product.category == category)
        if is_active is not None:
            statement = statement.where(Product.is_active == is_active)

        statement = statement.offset(skip).limit(limit)
        return session.exec(statement).all()

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
        total_products = session.exec(select(func.count(Product.id))).first() or 0
        active_products = (
            session.exec(
                select(func.count(Product.id)).where(Product.is_active == True)
            ).first()
            or 0
        )
        total_categories = (
            session.exec(select(func.count(func.distinct(Product.category)))).first()
            or 0
        )
        low_stock_products = (
            session.exec(
                select(func.count(Product.id)).where(
                    Product.stock_quantity < 10, Product.is_active == True
                )
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
        """Create a new order with complex business logic"""
        # Validate products and calculate total
        total_amount = 0.0
        order_items_data = []

        for item in order_in.order_items:
            product = session.get(Product, item.product_id)
            if not product or not product.is_active:
                raise HTTPException(
                    status_code=400,
                    detail=f"Product {item.product_id} not found or inactive",
                )

            # Business rule: Check stock availability
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

        # Create order
        order_data = order_in.model_dump(exclude={"order_items"})
        order_data.update({"customer_id": customer_id, "total_amount": total_amount})
        
        db_order = Order(**order_data)
        session.add(db_order)
        session.flush()  # Get the order ID

        # Create order items
        for item_data in order_items_data:
            order_item = OrderItem(order_id=db_order.id, **item_data)
            session.add(order_item)

        # Update product stock (business rule)
        for item in order_in.order_items:
            product = session.get(Product, item.product_id)
            product.stock_quantity -= item.quantity
            session.add(product)

        session.commit()
        session.refresh(db_order)
        return db_order

    # ... additional service methods
```

### Step 6: Create Views (Route Handlers)

Implement route handlers in `views.py`:

```python
"""
Shop App Views - Route handlers and controllers
"""
import uuid
from typing import Any

from fastapi import Depends, HTTPException, status
from sqlmodel import Session

from app.api.deps import CurrentUser, get_session
from app.apps.shop.models import Product
from app.apps.shop.schemas import ProductCreate, ProductOut, ProductUpdate
from app.apps.shop.services import ProductService


def create_product(
    *,
    session: Session = Depends(get_session),
    current_user: CurrentUser,
    product_in: ProductCreate,
) -> ProductOut:
    """Create a new product"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create products",
        )
    
    product = ProductService.create_product(
        session=session, product_in=product_in, created_by_id=current_user.id
    )
    return ProductOut.model_validate(product)


def get_products(
    *,
    session: Session = Depends(get_session),
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    category: str | None = None,
) -> list[ProductOut]:
    """Get products with optional filtering"""
    products = ProductService.get_products(
        session=session, skip=skip, limit=limit, category=category, is_active=True
    )
    return [ProductOut.model_validate(product) for product in products]


def get_product(
    *,
    session: Session = Depends(get_session),
    current_user: CurrentUser,
    product_id: uuid.UUID,
) -> ProductOut:
    """Get a specific product"""
    product = ProductService.get_product(session=session, product_id=product_id)
    if not product or not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return ProductOut.model_validate(product)


def update_product(
    *,
    session: Session = Depends(get_session),
    current_user: CurrentUser,
    product_id: uuid.UUID,
    product_in: ProductUpdate,
) -> ProductOut:
    """Update a product"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update products",
        )
    
    product = ProductService.get_product(session=session, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    
    updated_product = ProductService.update_product(
        session=session, db_product=product, product_in=product_in
    )
    return ProductOut.model_validate(updated_product)


def delete_product(
    *,
    session: Session = Depends(get_session),
    current_user: CurrentUser,
    product_id: uuid.UUID,
) -> dict[str, str]:
    """Delete a product (soft delete)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete products",
        )
    
    success = ProductService.delete_product(session=session, product_id=product_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    
    return {"message": "Product deleted successfully"}
```

### Step 7: Configure Routes

Set up route configuration in `urls.py`:

```python
"""
Shop App URLs - Route configuration
"""
from fastapi import APIRouter

from app.apps.shop import views

router = APIRouter()

# Product routes
router.add_api_route(
    "/products/", views.create_product, methods=["POST"], response_model=ProductOut
)
router.add_api_route(
    "/products/", views.get_products, methods=["GET"], response_model=list[ProductOut]
)
router.add_api_route(
    "/products/{product_id}",
    views.get_product,
    methods=["GET"],
    response_model=ProductOut,
)
router.add_api_route(
    "/products/{product_id}",
    views.update_product,
    methods=["PUT"],
    response_model=ProductOut,
)
router.add_api_route(
    "/products/{product_id}",
    views.delete_product,
    methods=["DELETE"],
    response_model=dict[str, str],
)

# Order routes
router.add_api_route(
    "/orders/", views.create_order, methods=["POST"], response_model=OrderOut
)
router.add_api_route(
    "/orders/", views.get_orders, methods=["GET"], response_model=list[OrderOut]
)
router.add_api_route(
    "/orders/{order_id}", views.get_order, methods=["GET"], response_model=OrderOut
)
```

### Step 8: Register Models

Add your models to the global model registry in `src/models.py`:

```python
# Add to src/models.py
from app.apps.shop.models import Order, OrderItem, Product  # noqa: F401
```

### Step 9: Integrate with Main API

Add your app router to the main API in `src/api/main.py`:

```python
from app.apps.shop.urls import router as shop_router

api_router.include_router(shop_router, prefix="/shop", tags=["shop"])
```

### Step 10: Create Database Migration

Generate and apply database migration:

```bash
# Generate migration
alembic revision --autogenerate -m "add shop app models"

# Apply migration
alembic upgrade head
```

## 🧪 Testing Implementation

Create comprehensive tests in `src/apps/shop/tests/`:

```python
"""
Test Shop App
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.apps.shop.models import Product
from app.apps.shop.services import ProductService


class TestProductService:
    """Test product service business logic"""

    def test_create_product(self, session: Session, normal_user):
        """Test product creation"""
        product_data = {
            "name": "Test Product",
            "description": "A test product",
            "price": 29.99,
            "stock_quantity": 100,
            "category": "electronics",
        }
        
        product = ProductService.create_product(
            session=session,
            product_in=ProductCreate(**product_data),
            created_by_id=normal_user.id,
        )
        
        assert product.name == "Test Product"
        assert product.price == 29.99
        assert product.is_active is True

    def test_duplicate_product_name(self, session: Session, normal_user):
        """Test duplicate product name validation"""
        # Create first product
        ProductService.create_product(
            session=session,
            product_in=ProductCreate(
                name="Duplicate Test",
                price=10.0,
                stock_quantity=5,
                category="test",
            ),
            created_by_id=normal_user.id,
        )
        
        # Try to create duplicate
        with pytest.raises(HTTPException) as exc_info:
            ProductService.create_product(
                session=session,
                product_in=ProductCreate(
                    name="Duplicate Test",
                    price=20.0,
                    stock_quantity=10,
                    category="test",
                ),
                created_by_id=normal_user.id,
            )
        
        assert exc_info.value.status_code == 400
        assert "already exists" in str(exc_info.value.detail)


class TestProductAPI:
    """Test product API endpoints"""

    def test_create_product_api(self, client: TestClient, superuser_token_headers):
        """Test product creation via API"""
        data = {
            "name": "API Test Product",
            "description": "Created via API",
            "price": 49.99,
            "stock_quantity": 50,
            "category": "api-test",
        }
        
        response = client.post(
            "/api/v1/shop/products/",
            headers=superuser_token_headers,
            json=data,
        )
        
        assert response.status_code == 200
        content = response.json()
        assert content["name"] == "API Test Product"
        assert content["price"] == 49.99

    def test_create_product_permission(self, client: TestClient, normal_user_token_headers):
        """Test product creation permission"""
        data = {
            "name": "Permission Test",
            "price": 10.0,
            "stock_quantity": 1,
            "category": "test",
        }
        
        response = client.post(
            "/api/v1/shop/products/",
            headers=normal_user_token_headers,
            json=data,
        )
        
        assert response.status_code == 403
```

## 🎯 Best Practices

### 1. **Service Layer Design**
- Keep business logic in services
- Use static methods for stateless operations
- Validate business rules before database operations
- Handle exceptions appropriately

### 2. **Schema Design**
- Separate input and output schemas
- Use validation for business rules
- Keep schemas focused and minimal
- Use type hints consistently

### 3. **Model Design**
- Use UUIDs for primary keys
- Add timestamps for audit trails
- Include soft delete capabilities
- Define clear relationships

### 4. **View Design**
- Keep views thin - delegate to services
- Use proper HTTP status codes
- Handle permissions at view level
- Validate input schemas

### 5. **Testing Strategy**
- Test business logic in services
- Test API endpoints separately
- Use fixtures for test data
- Mock external dependencies

## 🚀 Next Steps

After implementing your first app:

1. **Add More Features**: Implement additional business logic
2. **Create More Apps**: Follow the same pattern for other domains
3. **Optimize Performance**: Add caching and query optimization
4. **Add Monitoring**: Implement logging and metrics
5. **Deploy**: Prepare for production deployment

This implementation guide provides a solid foundation for building scalable FastAPI applications using Domain-Driven Development principles.
