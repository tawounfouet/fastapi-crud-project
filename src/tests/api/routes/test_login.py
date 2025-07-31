from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from src.apps.users.schemas import UserCreate
from src.apps.users.services import UserService
from src.core.config import settings
from src.core.security import verify_password
from src.tests.utils.utils import random_email, random_password
from src.utils import generate_password_reset_token


def test_get_access_token(client: TestClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)
    tokens = r.json()
    assert r.status_code == 200
    assert "access_token" in tokens
    assert tokens["access_token"]


def test_get_access_token_incorrect_password(client: TestClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": "incorrect",
    }
    r = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)
    assert r.status_code == 400


def test_use_access_token(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/auth/test-token",
        headers=superuser_token_headers,
    )
    result = r.json()
    assert r.status_code == 200
    assert "email" in result


def test_recovery_password(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    with (
        patch("src.core.config.settings.SMTP_HOST", "smtp.example.com"),
        patch("src.core.config.settings.SMTP_USER", "admin@example.com"),
    ):
        email = "test@example.com"
        r = client.post(
            f"{settings.API_V1_STR}/auth/password-recovery",
            headers=normal_user_token_headers,
            json={"email": email},
        )
        assert r.status_code == 200
        assert "message" in r.json()


def test_recovery_password_user_not_exits(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    email = "jVgQr@example.com"
    r = client.post(
        f"{settings.API_V1_STR}/auth/password-recovery",
        headers=normal_user_token_headers,
        json={"email": email},
    )
    # Auth app returns 200 for security (doesn't reveal if email exists)
    assert r.status_code == 200


def test_reset_password(client: TestClient, db: Session) -> None:
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

    # Request a password reset which creates the database token entry
    with patch("src.core.config.settings.SMTP_HOST", "smtp.example.com"):
        reset_request = client.post(
            f"{settings.API_V1_STR}/auth/password-recovery",
            json={"email": email},
        )
        assert reset_request.status_code == 200

    # For testing, we need to extract the token that was generated during the request
    # Since we can't access the email, we'll query the database for the token
    from sqlmodel import select

    from src.apps.auth.models import PasswordResetToken

    # Get the most recent password reset token for this email
    db_token = db.exec(
        select(PasswordResetToken)
        .where(PasswordResetToken.email == email)
        .order_by(PasswordResetToken.created_at.desc())
    ).first()

    assert db_token is not None, "Password reset token should have been created"

    # We need to generate a matching JWT token since we can't access the original
    # The issue is that the token_hash is a hash of the JWT token
    # For testing, let's use the auth service to properly request and get the token
    from src.apps.auth.services import AuthService

    auth_service = AuthService(db)

    # Generate a new token and update the existing DB entry
    token = generate_password_reset_token(email=email)
    token_hash = auth_service._hash_token(token)
    db_token.token_hash = token_hash
    db.add(db_token)
    db.commit()

    data = {"new_password": new_password, "token": token}

    r = client.post(
        f"{settings.API_V1_STR}/auth/reset-password",
        json=data,
    )

    print(f"Reset password response: {r.status_code}, {r.text}")
    assert r.status_code == 200
    assert r.json() == {"message": "Password updated successfully", "success": True}

    db.refresh(user)
    assert verify_password(new_password, user.hashed_password)


def test_reset_password_invalid_token(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"new_password": random_password(), "token": "invalid"}
    r = client.post(
        f"{settings.API_V1_STR}/auth/reset-password",
        headers=superuser_token_headers,
        json=data,
    )
    response = r.json()

    assert "detail" in response
    assert r.status_code == 400
    assert response["detail"] == "Invalid or expired reset token"
