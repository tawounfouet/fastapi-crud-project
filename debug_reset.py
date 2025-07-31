#!/usr/bin/env python3

"""Debug script to check reset password endpoint"""

from fastapi.testclient import TestClient
from sqlmodel import Session

from src.core.config import settings
from src.apps.users.services import UserService
from src.apps.users.schemas import UserCreate
from src.tests.utils.user import user_authentication_headers
from src.tests.utils.utils import random_email, random_password
from src.utils import generate_password_reset_token
from src.main import app


def main():
    client = TestClient(app)

    # Get a database session (using the test database setup)
    from src.core.database import SessionLocal

    db = SessionLocal()

    try:
        email = random_email()
        password = random_password()
        new_password = random_password()

        user_create = UserCreate(
            email=email,
            full_name="Test User",
            password=password,
            is_active=True,
        )
        user_service = UserService(db)
        user = user_service.create_user(user_create)
        token = generate_password_reset_token(email=email)
        headers = user_authentication_headers(
            client=client, email=email, password=password
        )
        data = {"new_password": new_password, "token": token}

        print(f"User created: {user.email}")
        print(f"Token generated: {token[:50]}...")
        print(f"Headers: {headers}")
        print(f"Data: {data}")

        r = client.post(
            f"{settings.API_V1_STR}/auth/reset-password",
            headers=headers,
            json=data,
        )

        print(f"Status code: {r.status_code}")
        print(f"Response: {r.json()}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
