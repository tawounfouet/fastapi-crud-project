# Database Integration Guide

This guide covers database patterns, migrations, and integration strategies for Domain-Driven Development in FastAPI applications.

## 📚 Table of Contents

- [Database Architecture](#database-architecture)
- [Model Design Patterns](#model-design-patterns)
- [Migration Strategies](#migration-strategies)
- [Connection Management](#connection-management)
- [Query Patterns](#query-patterns)
- [Testing with Databases](#testing-with-databases)
- [Performance Optimization](#performance-optimization)
- [Best Practices](#best-practices)

## 🏗️ Database Architecture

### Database Layer Structure

```
src/
├── core/
│   ├── database.py          # Database configuration and session management
│   └── config.py           # Database connection settings
├── apps/
│   └── {app_name}/
│       ├── models.py       # SQLAlchemy models for the domain
│       ├── schemas.py      # Pydantic schemas for API
│       └── services.py     # Business logic with database operations
└── alembic/                # Database migrations
    ├── versions/           # Migration files
    └── env.py             # Alembic configuration
```

### Database Session Management

The application uses SQLAlchemy with proper session management:

```python
# src/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

@contextmanager
def get_db_context():
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_db():
    """Dependency injection for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## 🎨 Model Design Patterns

### 1. Base Model Pattern

Create a base model with common fields:

```python
# src/core/models.py
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def to_dict(self):
        """Convert model instance to dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
```

### 2. Domain Model Pattern

Each app defines its own models:

```python
# src/apps/users/models.py
from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import relationship
from src.core.models import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    bio = Column(Text, nullable=True)
    
    # Relationships
    posts = relationship("Post", back_populates="author", lazy="dynamic")
    
    def __repr__(self):
        return f"<User(email='{self.email}', full_name='{self.full_name}')>"
    
    @property
    def is_authenticated(self):
        return self.is_active
```

### 3. Relationship Patterns

#### One-to-Many Relationships

```python
# src/apps/blog/models.py
from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from src.core.models import BaseModel

class Post(BaseModel):
    __tablename__ = "posts"
    
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")

class Comment(BaseModel):
    __tablename__ = "comments"
    
    content = Column(Text, nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    post = relationship("Post", back_populates="comments")
    author = relationship("User")
```

#### Many-to-Many Relationships

```python
# Association table
from sqlalchemy import Table, Column, Integer, ForeignKey

post_tags = Table(
    'post_tags',
    BaseModel.metadata,
    Column('post_id', Integer, ForeignKey('posts.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class Post(BaseModel):
    # ... other fields ...
    tags = relationship("Tag", secondary=post_tags, back_populates="posts")

class Tag(BaseModel):
    __tablename__ = "tags"
    
    name = Column(String(100), unique=True, nullable=False)
    posts = relationship("Post", secondary=post_tags, back_populates="tags")
```

## 🚀 Migration Strategies

### Alembic Configuration

```python
# alembic/env.py
from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.database import Base
from src.core.config import settings

# Import all models to ensure they're registered
from src.apps.users.models import *
from src.apps.blog.models import *

target_metadata = Base.metadata

def run_migrations_online():
    """Run migrations in 'online' mode."""
    configuration = context.config
    configuration.set_main_option("sqlalchemy.url", settings.database_url)
    
    connectable = engine_from_config(
        configuration.get_section(configuration.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
```

### Migration Commands

```bash
# Create a new migration
alembic revision --autogenerate -m "Add user table"

# Apply migrations
alembic upgrade head

# Downgrade migrations
alembic downgrade -1

# Show migration history
alembic history

# Show current revision
alembic current
```

### Migration Best Practices

1. **Always Review Auto-Generated Migrations**
```python
# Review and edit migration files before applying
def upgrade():
    # Add validation for data migration
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add indexes explicitly
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
```

2. **Handle Data Migrations Carefully**
```python
def upgrade():
    # Schema change first
    op.add_column('users', sa.Column('full_name', sa.String(255), nullable=True))
    
    # Data migration
    connection = op.get_bind()
    connection.execute(
        "UPDATE users SET full_name = first_name || ' ' || last_name"
    )
    
    # Make field non-nullable after data migration
    op.alter_column('users', 'full_name', nullable=False)
    
    # Remove old columns
    op.drop_column('users', 'first_name')
    op.drop_column('users', 'last_name')
```

## 🔗 Connection Management

### Database Dependencies

```python
# src/core/dependencies.py
from fastapi import Depends
from sqlalchemy.orm import Session
from src.core.database import get_db

def get_db_session() -> Session:
    """Get database session for dependency injection"""
    return Depends(get_db)

# Usage in routes
@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: Session = Depends(get_db_session())
):
    return user_service.get_user(db, user_id)
```

### Connection Pooling

```python
# src/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # Set to True for SQL debugging
)
```

## 🔍 Query Patterns

### Repository Pattern

```python
# src/apps/users/repository.py
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from src.apps.users.models import User

class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def search(self, query: str) -> List[User]:
        return self.db.query(User).filter(
            or_(
                User.full_name.contains(query),
                User.email.contains(query)
            )
        ).all()
    
    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update(self, user: User) -> User:
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.commit()
```

### Service Layer with Repository

```python
# src/apps/users/services.py
from typing import Optional, List
from sqlalchemy.orm import Session
from src.apps.users.repository import UserRepository
from src.apps.users.models import User
from src.apps.users.schemas import UserCreate, UserUpdate

class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)
    
    def get_user(self, user_id: int) -> Optional[User]:
        return self.repository.get_by_id(user_id)
    
    def create_user(self, user_data: UserCreate) -> User:
        # Business logic here
        if self.repository.get_by_email(user_data.email):
            raise ValueError("Email already registered")
        
        user = User(**user_data.dict())
        return self.repository.create(user)
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        user = self.repository.get_by_id(user_id)
        if not user:
            return None
        
        for field, value in user_data.dict(exclude_unset=True).items():
            setattr(user, field, value)
        
        return self.repository.update(user)
```

### Complex Queries

```python
# src/apps/blog/repository.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func
from src.apps.blog.models import Post, Comment

class PostRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_posts_with_comments(self, skip: int = 0, limit: int = 10):
        """Get posts with their comments loaded"""
        return (
            self.db.query(Post)
            .options(joinedload(Post.comments))
            .order_by(desc(Post.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_popular_posts(self, limit: int = 10):
        """Get posts ordered by comment count"""
        return (
            self.db.query(Post)
            .join(Comment)
            .group_by(Post.id)
            .order_by(desc(func.count(Comment.id)))
            .limit(limit)
            .all()
        )
    
    def get_posts_by_tag(self, tag_name: str):
        """Get posts filtered by tag"""
        return (
            self.db.query(Post)
            .join(Post.tags)
            .filter(Tag.name == tag_name)
            .all()
        )
```

## 🧪 Testing with Databases

### Test Database Setup

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.core.database import Base
from src.core.database import get_db
from main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

### Database Test Patterns

```python
# tests/test_users.py
import pytest
from src.apps.users.models import User
from src.apps.users.services import UserService

def test_create_user(db_session):
    service = UserService(db_session)
    user_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpass123"
    }
    
    user = service.create_user(user_data)
    
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.full_name == "Test User"

def test_get_user_by_email(db_session):
    # Create test user
    user = User(email="test@example.com", full_name="Test User")
    db_session.add(user)
    db_session.commit()
    
    service = UserService(db_session)
    found_user = service.get_user_by_email("test@example.com")
    
    assert found_user is not None
    assert found_user.email == "test@example.com"
```

## ⚡ Performance Optimization

### Query Optimization

```python
# Use select_related equivalent (joinedload)
users_with_posts = (
    db.query(User)
    .options(joinedload(User.posts))
    .all()
)

# Use selectinload for collections
users_with_posts = (
    db.query(User)
    .options(selectinload(User.posts))
    .all()
)

# Limit fields selection
from sqlalchemy.orm import load_only

users = db.query(User).options(load_only("id", "email")).all()
```

### Indexing Strategy

```python
# In your models
class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), index=True, nullable=False)  # For search
    created_at = Column(DateTime, default=func.now(), index=True)  # For sorting
    
    # Composite index
    __table_args__ = (
        Index('ix_user_name_email', 'full_name', 'email'),
    )
```

### Connection Pool Tuning

```python
# For high-traffic applications
engine = create_engine(
    DATABASE_URL,
    pool_size=50,           # Number of connections to maintain
    max_overflow=100,       # Additional connections beyond pool_size
    pool_timeout=30,        # Timeout for getting connection
    pool_recycle=3600,      # Recycle connections every hour
    pool_pre_ping=True,     # Validate connections before use
)
```

## 📋 Best Practices

### 1. Model Design
- Use descriptive table and column names
- Always include created_at and updated_at timestamps
- Use appropriate data types and constraints
- Define relationships clearly with proper foreign keys

### 2. Migration Management
- Review all auto-generated migrations
- Test migrations on staging before production
- Keep migrations small and focused
- Always provide rollback capability

### 3. Query Performance
- Use appropriate indexes
- Avoid N+1 queries with proper eager loading
- Implement pagination for large datasets
- Use database-level aggregations when possible

### 4. Testing
- Use separate test database
- Clean up test data between tests
- Test both success and failure scenarios
- Mock external database calls in unit tests

### 5. Security
- Always use parameterized queries
- Validate all input data
- Implement proper authentication and authorization
- Use connection pooling and timeouts

### 6. Monitoring
- Log slow queries
- Monitor connection pool usage
- Track database performance metrics
- Set up alerts for connection failures

## 🔧 Troubleshooting

### Common Issues

1. **Migration Conflicts**
```bash
# Reset migration head
alembic stamp head

# Create new migration from current state
alembic revision --autogenerate -m "Resolve conflicts"
```

2. **Connection Pool Exhaustion**
```python
# Monitor pool status
from sqlalchemy import event

@event.listens_for(engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    print(f"New connection: {id(dbapi_connection)}")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    print(f"Connection checked out: {id(dbapi_connection)}")
```

3. **Slow Queries**
```python
# Enable SQL logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Or set echo=True in create_engine
engine = create_engine(DATABASE_URL, echo=True)
```

This database integration guide provides comprehensive patterns and best practices for working with databases in a DDD FastAPI application. The patterns ensure maintainable, performant, and testable database operations while maintaining clean architecture principles.
