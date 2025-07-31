from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from src.apps.auth.models import LoginAttempt, PasswordResetToken, RefreshToken
from src.apps.users.models import User
from src.core.config import settings
from src.core.database import engine, init_db
from src.main import app
from src.tests.utils.user import authentication_token_from_email
from src.tests.utils.utils import get_superuser_token_headers


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)

        # Clear auth tables to reset rate limiting
        session.execute(delete(LoginAttempt))
        session.execute(delete(RefreshToken))
        session.execute(delete(PasswordResetToken))
        session.commit()

        # Ensure the session is properly committed before yielding
        session.commit()

        yield session

        # Clean up test data
        try:
            session.execute(delete(LoginAttempt))
            session.execute(delete(RefreshToken))
            session.execute(delete(PasswordResetToken))
            session.execute(delete(User))
            session.commit()
        except Exception:
            # If cleanup fails, rollback to ensure clean state
            session.rollback()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
