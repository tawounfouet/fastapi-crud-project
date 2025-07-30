from sqlmodel import Session, SQLModel, create_engine, select

from app import crud
from app.core.config import settings
from app.models import User, UserCreate

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

# Create tables automatically for SQLite (since it doesn't support migrations well)
if str(settings.SQLALCHEMY_DATABASE_URI).startswith("sqlite"):
    SQLModel.metadata.create_all(engine)


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations for PostgreSQL
    # But for SQLite, tables are already created above
    # If you don't want to use migrations at all, uncomment the next lines
    # from sqlmodel import SQLModel
    # SQLModel.metadata.create_all(engine)

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)
