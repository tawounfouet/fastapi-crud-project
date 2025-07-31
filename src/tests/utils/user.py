from fastapi.testclient import TestClient
from sqlmodel import Session

from src.apps.users.models import User
from src.apps.users.schemas import UserCreate, UserUpdate
from src.apps.users.services import UserService
from src.core.config import settings
from src.tests.utils.utils import random_email, random_password


def user_authentication_headers(
    *, client: TestClient, email: str, password: str
) -> dict[str, str]:
    data = {"username": email, "password": password}

    r = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=data)
    response = r.json()
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers


def create_random_user(db: Session) -> User:
    email = random_email()
    password = random_password()
    user_in = UserCreate(
        email=email,
        password=password,
        first_name="Test",
        last_name="User",
        is_active=True,
        is_superuser=False,
    )
    user_service = UserService(db)
    user = user_service.create_user(user_in)
    return user


def authentication_token_from_email(
    *, client: TestClient, email: str, db: Session
) -> dict[str, str]:
    """
    Return a valid token for the user with given email.

    If the user doesn't exist it is created first.
    """
    password = random_password()
    user_service = UserService(db)
    user = user_service.get_user_by_email(email)
    if not user:
        user_in_create = UserCreate(
            email=email,
            password=password,
            first_name="Test",
            last_name="User",
            is_active=True,
            is_superuser=False,
        )
        user = user_service.create_user(user_in_create)
    else:
        # For existing users, update the password
        user_in_update = UserUpdate(
            email=email,
            password=password,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
        )
        if not user.id:
            raise Exception("User id not set")
        user_service.update_user(user.id, user_in_update)

    return user_authentication_headers(client=client, email=email, password=password)
