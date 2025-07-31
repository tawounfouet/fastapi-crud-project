"""
Tests for demo app products functionality
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.apps.demo.models import Product
from src.core.config import settings


def test_create_product(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating a product"""
    data = {
        "name": "Test Product",
        "description": "A test product",
        "price": 29.99,
        "category": "Electronics",
        "stock_quantity": 100,
    }

    response = client.post(
        f"{settings.API_V1_STR}/demo/products/",
        headers=superuser_token_headers,
        json=data,
    )

    assert response.status_code == 200
    content = response.json()
    assert content["name"] == data["name"]
    assert content["price"] == data["price"]
    assert "id" in content
    assert "created_at" in content


def test_read_products(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test reading products"""
    # Create a test product first
    product_data = {
        "name": "Test Product 2",
        "description": "Another test product",
        "price": 19.99,
        "category": "Books",
        "stock_quantity": 50,
    }

    client.post(
        f"{settings.API_V1_STR}/demo/products/",
        headers=superuser_token_headers,
        json=product_data,
    )

    # Read products
    response = client.get(
        f"{settings.API_V1_STR}/demo/products/",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    content = response.json()
    assert "data" in content
    assert "count" in content
    assert len(content["data"]) >= 1


def test_read_product_by_id(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test reading a specific product"""
    # Create a test product
    product_data = {
        "name": "Test Product 3",
        "description": "Yet another test product",
        "price": 39.99,
        "category": "Clothing",
        "stock_quantity": 25,
    }

    create_response = client.post(
        f"{settings.API_V1_STR}/demo/products/",
        headers=superuser_token_headers,
        json=product_data,
    )

    product_id = create_response.json()["id"]

    # Read the specific product
    response = client.get(
        f"{settings.API_V1_STR}/demo/products/{product_id}",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    content = response.json()
    assert content["id"] == product_id
    assert content["name"] == product_data["name"]


def test_update_product(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test updating a product"""
    # Create a test product
    product_data = {
        "name": "Test Product 4",
        "description": "Product to update",
        "price": 49.99,
        "category": "Sports",
        "stock_quantity": 30,
    }

    create_response = client.post(
        f"{settings.API_V1_STR}/demo/products/",
        headers=superuser_token_headers,
        json=product_data,
    )

    product_id = create_response.json()["id"]

    # Update the product
    update_data = {"name": "Updated Product", "price": 59.99}

    response = client.put(
        f"{settings.API_V1_STR}/demo/products/{product_id}",
        headers=superuser_token_headers,
        json=update_data,
    )

    assert response.status_code == 200
    content = response.json()
    assert content["name"] == update_data["name"]
    assert content["price"] == update_data["price"]


def test_delete_product(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test deleting a product"""
    # Create a test product
    product_data = {
        "name": "Test Product 5",
        "description": "Product to delete",
        "price": 69.99,
        "category": "Home",
        "stock_quantity": 40,
    }

    create_response = client.post(
        f"{settings.API_V1_STR}/demo/products/",
        headers=superuser_token_headers,
        json=product_data,
    )

    product_id = create_response.json()["id"]

    # Delete the product
    response = client.delete(
        f"{settings.API_V1_STR}/demo/products/{product_id}",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Product deleted successfully"

    # Verify product is soft deleted
    get_response = client.get(
        f"{settings.API_V1_STR}/demo/products/{product_id}",
        headers=superuser_token_headers,
    )
    assert get_response.status_code == 200
    product = get_response.json()
    assert product["is_active"] == False


def test_create_product_duplicate_name(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating a product with duplicate name"""
    product_data = {
        "name": "Duplicate Product",
        "description": "First product",
        "price": 29.99,
        "category": "Test",
        "stock_quantity": 10,
    }

    # Create first product
    response1 = client.post(
        f"{settings.API_V1_STR}/demo/products/",
        headers=superuser_token_headers,
        json=product_data,
    )
    assert response1.status_code == 200

    # Try to create second product with same name
    response2 = client.post(
        f"{settings.API_V1_STR}/demo/products/",
        headers=superuser_token_headers,
        json=product_data,
    )
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"]


def test_filter_products_by_category(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test filtering products by category"""
    # Create products in different categories
    electronics_product = {
        "name": "Laptop",
        "price": 999.99,
        "category": "Electronics",
        "stock_quantity": 5,
    }

    books_product = {
        "name": "Python Book",
        "price": 39.99,
        "category": "Books",
        "stock_quantity": 20,
    }

    client.post(
        f"{settings.API_V1_STR}/demo/products/",
        headers=superuser_token_headers,
        json=electronics_product,
    )

    client.post(
        f"{settings.API_V1_STR}/demo/products/",
        headers=superuser_token_headers,
        json=books_product,
    )

    # Filter by Electronics category
    response = client.get(
        f"{settings.API_V1_STR}/demo/products/?category=Electronics",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    content = response.json()
    electronics_products = [
        p for p in content["data"] if p["category"] == "Electronics"
    ]
    assert len(electronics_products) >= 1
