from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from src.api.deps import SessionDep
from src.apps.users.models import User
from src.apps.users.schemas import UserPublic
from src.core.security import get_password_hash

router = APIRouter(tags=["private"], prefix="/private")


class PrivateUserCreate(BaseModel):
    email: str
    password: str
    first_name: str | None = None
    last_name: str | None = None
    is_verified: bool = False


@router.post("/users/", response_model=UserPublic)
def create_user(user_in: PrivateUserCreate, session: SessionDep) -> Any:
    """
    Create a new user.
    """

    user = User(
        email=user_in.email,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        hashed_password=get_password_hash(user_in.password),
    )

    session.add(user)
    session.commit()

    return user
