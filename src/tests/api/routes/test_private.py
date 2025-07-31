from fastapi.testclient import TestClient
from sqlmodel import Session, select
import uuid

from src.core.config import settings
from src.apps.users.models import User


def test_create_user(client: TestClient, db: Session) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/private/users/",
        json={
            "email": "pollo@listo.com",
            "password": "password123",
            "first_name": "Pollo",
            "last_name": "Listo",
        },
    )

    assert r.status_code == 200

    data = r.json()

    # Convert string UUID to UUID object for database query
    user_id = uuid.UUID(data["id"]) if isinstance(data["id"], str) else data["id"]
    user = db.exec(select(User).where(User.id == user_id)).first()

    assert user
    assert user.email == "pollo@listo.com"
    assert user.first_name == "Pollo"
    assert user.last_name == "Listo"
    assert user.full_name == "Pollo Listo"  # Test the computed property
