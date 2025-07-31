"""
Database Dependencies for FastAPI

Provides specialized database session dependencies and utilities
following best practices for connection management and error handling.
"""

from contextlib import contextmanager
from typing import Generator
from sqlmodel import Session
from src.core.database import engine


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Provides automatic transaction management:
    - Commits on success
    - Rolls back on exception
    - Always closes the session

    Usage:
        with get_db_context() as db:
            user = UserService.create_user(db, user_data)
    """
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db_readonly() -> Generator[Session, None, None]:
    """
    Database dependency for read-only operations.

    Optimized for queries that don't modify data.
    """
    with Session(engine) as session:
        # Disable autoflush for read-only operations
        session.autoflush = False
        yield session


def get_db_transactional() -> Generator[Session, None, None]:
    """
    Database dependency with explicit transaction management.

    Useful for operations that require guaranteed consistency.
    """
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
