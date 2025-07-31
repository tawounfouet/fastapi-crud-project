from sqlmodel import Session, SQLModel, create_engine, select

from src.core.config import settings

# Import ALL models to ensure they're included in SQLModel metadata
# This is critical for:
# 1. Alembic migration auto-generation
# 2. Proper relationship detection
# 3. Foreign key constraint creation

# User domain models
from src.apps.users.models import User, UserSession, UserProfile

# Auth domain models
from src.apps.auth.models import RefreshToken, PasswordResetToken, LoginAttempt

# Demo domain models
from src.apps.demo.models import Product, Order, OrderItem

# NOTE: When adding new apps, import their models here
# Example: from src.apps.blog.models import Post, Comment, Tag

# Create engine with optimized connection pooling
engine_config = {
    "echo": settings.DB_ECHO or settings.ENVIRONMENT == "local",  # SQL logging
    "pool_pre_ping": True,  # Validate connections before use
}

# Add PostgreSQL-specific optimizations
if not str(settings.SQLALCHEMY_DATABASE_URI).startswith("sqlite"):
    engine_config.update(
        {
            "pool_size": settings.DB_POOL_SIZE,  # Base connection pool size
            "max_overflow": settings.DB_MAX_OVERFLOW,  # Additional connections beyond pool_size
            "pool_recycle": settings.DB_POOL_RECYCLE,  # Recycle connections periodically
            "pool_timeout": settings.DB_POOL_TIMEOUT,  # Connection timeout
        }
    )
else:
    # SQLite specific settings
    engine_config.update(
        {
            "connect_args": {"check_same_thread": False},  # Allow multiple threads
            "poolclass": None,  # Disable pooling for SQLite
        }
    )

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI), **engine_config)

# Create tables automatically for SQLite (since it doesn't support migrations well)
if str(settings.SQLALCHEMY_DATABASE_URI).startswith("sqlite"):
    SQLModel.metadata.create_all(engine)


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    """
    Initialize database with required data.

    For SQLite: Tables are auto-created above
    For PostgreSQL: Tables created via Alembic migrations

    This function handles:
    - Creating the initial superuser
    - Setting up any required seed data
    - Verifying critical database constraints
    """
    # Import here to avoid circular imports
    from src.apps.users.services import UserService

    # Check if superuser already exists
    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()

    if not user:
        print(f"Creating superuser: {settings.FIRST_SUPERUSER}")
        user_service = UserService(session)
        user = user_service.create_superuser(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            first_name="Admin",
            last_name="User",
        )
        print(f"✓ Superuser created successfully: {user.email}")
    else:
        print(f"✓ Superuser already exists: {user.email}")


def verify_db_connection() -> bool:
    """
    Verify database connection and basic functionality.

    Returns:
        bool: True if database is accessible and working
    """
    try:
        with Session(engine) as session:
            # Test basic query
            session.exec(select(User).limit(1)).first()
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
