"""
Tests for demo app orders functionality
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.apps.demo.models import Order, Product
from src.core.config import settings


def test_create_order(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating an order"""
    # First create a product
    product_data = {
        "name": "Order Test Product",
        "description": "Product for order testing",
        "price": 25.00,
        "category": "Test",
        "stock_quantity": 100,
    }

    product_response = client.post(
        f"{settings.API_V1_STR}/demo/products/",
        headers=superuser_token_headers,
        json=product_data,
    )

    product_id = product_response.json()["id"]

    # Create order
    order_data = {
        "status": "pending",
        "notes": "Test order",
        "order_items": [{"product_id": product_id, "quantity": 2, "unit_price": 25.00}],
    }

    response = client.post(
        f"{settings.API_V1_STR}/demo/orders/",
        headers=superuser_token_headers,
        json=order_data,
    )

    assert response.status_code == 200
    content = response.json()
    assert content["status"] == "pending"
    assert content["total_amount"] == 50.00  # 2 * 25.00
    assert len(content["order_items"]) == 1
    assert "id" in content


def test_create_order_insufficient_stock(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating an order with insufficient stock"""
    # Create a product with limited stock
    product_data = {
        "name": "Limited Stock Product",
        "price": 30.00,
        "category": "Test",
        "stock_quantity": 5,
    }

    product_response = client.post(
        f"{settings.API_V1_STR}/demo/products/",
        headers=superuser_token_headers,
        json=product_data,
    )

    product_id = product_response.json()["id"]

    # Try to order more than available
    order_data = {
        "status": "pending",
        "order_items": [
            {
                "product_id": product_id,
                "quantity": 10,  # More than the 5 in stock
                "unit_price": 30.00,
            }
        ],
    }

    response = client.post(
        f"{settings.API_V1_STR}/demo/orders/",
        headers=superuser_token_headers,
        json=order_data,
    )

    assert response.status_code == 400
    assert "Insufficient stock" in response.json()["detail"]


def test_create_order_nonexistent_product(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating an order with non-existent product"""
    fake_product_id = str(uuid.uuid4())

    order_data = {
        "status": "pending",
        "order_items": [
            {"product_id": fake_product_id, "quantity": 1, "unit_price": 25.00}
        ],
    }

    response = client.post(
        f"{settings.API_V1_STR}/demo/orders/",
        headers=superuser_token_headers,
        json=order_data,
    )

    assert response.status_code == 400
    assert "not found" in response.json()["detail"]


def test_read_orders(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test reading orders"""
    # Create a product first
    product_data = {
        "name": "Read Orders Test Product",
        "price": 15.00,
        "category": "Test",
        "stock_quantity": 50,
    }

    product_response = client.post(
        f"{settings.API_V1_STR}/demo/products/",
        headers=superuser_token_headers,
        json=product_data,
    )

    product_id = product_response.json()["id"]

    # Create an order
    order_data = {
        "status": "pending",
        "order_items": [{"product_id": product_id, "quantity": 1, "unit_price": 15.00}],
    }

    client.post(
        f"{settings.API_V1_STR}/demo/orders/",
        headers=superuser_token_headers,
        json=order_data,
    )

    # Read orders
    response = client.get(
        f"{settings.API_V1_STR}/demo/orders/",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    content = response.json()
    assert "data" in content
    assert "count" in content
    assert len(content["data"]) >= 1


def test_read_order_by_id(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test reading a specific order"""
    # Create a product
    product_data = {
        "name": "Specific Order Test Product",
        "price": 35.00,
        "category": "Test",
        "stock_quantity": 20,
    }

    product_response = client.post(
        f"{settings.API_V1_STR}/demo/products/",
        headers=superuser_token_headers,
        json=product_data,
    )

    product_id = product_response.json()["id"]

    # Create an order
    order_data = {
        "status": "pending",
        "notes": "Specific order test",
        "order_items": [{"product_id": product_id, "quantity": 3, "unit_price": 35.00}],
    }

    create_response = client.post(
        f"{settings.API_V1_STR}/demo/orders/",
        headers=superuser_token_headers,
        json=order_data,
    )

    order_id = create_response.json()["id"]

    # Read the specific order
    response = client.get(
        f"{settings.API_V1_STR}/demo/orders/{order_id}",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    content = response.json()
    assert content["id"] == order_id
    assert content["notes"] == "Specific order test"
    assert content["total_amount"] == 105.00  # 3 * 35.00


def test_update_order_status(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test updating order status"""
    # Create a product
    product_data = {
        "name": "Update Status Test Product",
        "price": 45.00,
        "category": "Test",
        "stock_quantity": 30,
    }

    product_response = client.post(
        f"{settings.API_V1_STR}/demo/products/",
        headers=superuser_token_headers,
        json=product_data,
    )

    product_id = product_response.json()["id"]

    # Create an order
    order_data = {
        "status": "pending",
        "order_items": [{"product_id": product_id, "quantity": 1, "unit_price": 45.00}],
    }

    create_response = client.post(
        f"{settings.API_V1_STR}/demo/orders/",
        headers=superuser_token_headers,
        json=order_data,
    )

    order_id = create_response.json()["id"]

    # Update order status
    update_data = {"status": "completed", "notes": "Order fulfilled"}

    response = client.put(
        f"{settings.API_V1_STR}/demo/orders/{order_id}",
        headers=superuser_token_headers,
        json=update_data,
    )

    assert response.status_code == 200
    content = response.json()
    assert content["status"] == "completed"
    assert content["notes"] == "Order fulfilled"


def test_filter_orders_by_status(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test filtering orders by status"""
    # Create a product
    product_data = {
        "name": "Filter Orders Test Product",
        "price": 20.00,
        "category": "Test",
        "stock_quantity": 100,
    }

    product_response = client.post(
        f"{settings.API_V1_STR}/demo/products/",
        headers=superuser_token_headers,
        json=product_data,
    )

    product_id = product_response.json()["id"]

    # Create orders with different statuses
    pending_order = {
        "status": "pending",
        "order_items": [{"product_id": product_id, "quantity": 1, "unit_price": 20.00}],
    }

    completed_order = {
        "status": "completed",
        "order_items": [{"product_id": product_id, "quantity": 2, "unit_price": 20.00}],
    }

    client.post(
        f"{settings.API_V1_STR}/demo/orders/",
        headers=superuser_token_headers,
        json=pending_order,
    )
    client.post(
        f"{settings.API_V1_STR}/demo/orders/",
        headers=superuser_token_headers,
        json=completed_order,
    )

    # Filter by pending status
    response = client.get(
        f"{settings.API_V1_STR}/demo/orders/?status=pending",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    content = response.json()
    pending_orders = [o for o in content["data"] if o["status"] == "pending"]
    assert len(pending_orders) >= 1
