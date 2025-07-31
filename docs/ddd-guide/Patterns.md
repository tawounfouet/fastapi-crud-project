# Common Patterns Guide

This guide covers reusable design patterns and architectural solutions commonly used in Domain-Driven Development with FastAPI applications.

## 📚 Table of Contents

- [Architectural Patterns](#architectural-patterns)
- [Domain Patterns](#domain-patterns)
- [Data Access Patterns](#data-access-patterns)
- [Service Layer Patterns](#service-layer-patterns)
- [API Patterns](#api-patterns)
- [Error Handling Patterns](#error-handling-patterns)
- [Security Patterns](#security-patterns)
- [Performance Patterns](#performance-patterns)
- [Testing Patterns](#testing-patterns)
- [Integration Patterns](#integration-patterns)

## 🏗️ Architectural Patterns

### 1. Layered Architecture Pattern

```
┌─────────────────────┐
│   API Layer        │ ← FastAPI routes, request/response handling
├─────────────────────┤
│   Service Layer    │ ← Business logic, validation, orchestration
├─────────────────────┤
│   Repository Layer │ ← Data access abstraction
├─────────────────────┤
│   Model Layer      │ ← Domain models, database entities
└─────────────────────┘
```

```python
# Implementation structure
src/
├── apps/
│   └── users/
│       ├── views.py        # API Layer - Routes and endpoints
│       ├── services.py     # Service Layer - Business logic
│       ├── repository.py   # Repository Layer - Data access
│       ├── models.py       # Model Layer - Database entities
│       └── schemas.py      # Data transfer objects
```

### 2. Dependency Injection Pattern

```python
# src/core/dependencies.py
from typing import Generator
from sqlalchemy.orm import Session
from src.core.database import SessionLocal

def get_db() -> Generator[Session, None, None]:
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """User service dependency"""
    return UserService(db)

def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service)
) -> User:
    """Current user dependency"""
    return user_service.get_user_by_token(token)

# Usage in routes
@router.get("/profile/")
async def get_profile(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    return user_service.get_profile(current_user.id)
```

### 3. Factory Pattern

```python
# src/core/factories.py
from abc import ABC, abstractmethod
from typing import Protocol

class ServiceFactory(Protocol):
    def create_user_service(self, db: Session) -> UserService: ...
    def create_post_service(self, db: Session) -> PostService: ...
    def create_email_service(self) -> EmailService: ...

class ProductionServiceFactory:
    def create_user_service(self, db: Session) -> UserService:
        return UserService(
            repository=UserRepository(db),
            email_service=self.create_email_service(),
            cache_service=RedisCache()
        )
    
    def create_post_service(self, db: Session) -> PostService:
        return PostService(
            repository=PostRepository(db),
            user_service=self.create_user_service(db)
        )
    
    def create_email_service(self) -> EmailService:
        return SMTPEmailService(
            host=settings.smtp_host,
            port=settings.smtp_port
        )

class TestServiceFactory:
    def create_user_service(self, db: Session) -> UserService:
        return UserService(
            repository=UserRepository(db),
            email_service=MockEmailService(),
            cache_service=InMemoryCache()
        )
    
    def create_email_service(self) -> EmailService:
        return MockEmailService()

# Usage
def get_service_factory() -> ServiceFactory:
    if settings.environment == "test":
        return TestServiceFactory()
    return ProductionServiceFactory()
```

## 🎯 Domain Patterns

### 1. Value Object Pattern

```python
# src/core/value_objects.py
from dataclasses import dataclass
from typing import Self

@dataclass(frozen=True)
class Email:
    value: str
    
    def __post_init__(self):
        if not self._is_valid(self.value):
            raise ValueError(f"Invalid email: {self.value}")
    
    @staticmethod
    def _is_valid(email: str) -> bool:
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def domain(self) -> str:
        return self.value.split('@')[1]
    
    def __str__(self) -> str:
        return self.value

@dataclass(frozen=True)
class Money:
    amount: int  # Store as cents
    currency: str = "USD"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")
        if not self.currency:
            raise ValueError("Currency cannot be empty")
    
    def add(self, other: Self) -> Self:
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
    
    def to_decimal(self) -> float:
        return self.amount / 100

# Usage in models
class User(BaseModel):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    _email = Column("email", String(255), unique=True)
    
    @property
    def email(self) -> Email:
        return Email(self._email)
    
    @email.setter
    def email(self, value: Email):
        self._email = value.value
```

### 2. Domain Event Pattern

```python
# src/core/events.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Type
import uuid

class DomainEvent(ABC):
    def __init__(self):
        self.event_id = str(uuid.uuid4())
        self.occurred_at = datetime.utcnow()

@dataclass
class UserRegisteredEvent(DomainEvent):
    user_id: int
    email: str
    full_name: str

@dataclass
class UserEmailChangedEvent(DomainEvent):
    user_id: int
    old_email: str
    new_email: str

# Event handling
class EventHandler(ABC):
    @abstractmethod
    async def handle(self, event: DomainEvent):
        pass

class UserRegisteredHandler(EventHandler):
    def __init__(self, email_service: EmailService):
        self.email_service = email_service
    
    async def handle(self, event: UserRegisteredEvent):
        await self.email_service.send_welcome_email(
            email=event.email,
            name=event.full_name
        )

# Event dispatcher
class EventDispatcher:
    def __init__(self):
        self._handlers: dict[Type[DomainEvent], List[EventHandler]] = {}
    
    def register(self, event_type: Type[DomainEvent], handler: EventHandler):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    async def dispatch(self, event: DomainEvent):
        event_type = type(event)
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                await handler.handle(event)

# Usage in domain models
class User(BaseModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._events: List[DomainEvent] = []
    
    def register_event(self, event: DomainEvent):
        self._events.append(event)
    
    def clear_events(self):
        self._events.clear()
    
    @property
    def events(self) -> List[DomainEvent]:
        return self._events.copy()
    
    def change_email(self, new_email: Email):
        old_email = self.email.value
        self.email = new_email
        
        self.register_event(UserEmailChangedEvent(
            user_id=self.id,
            old_email=old_email,
            new_email=new_email.value
        ))
```

### 3. Aggregate Pattern

```python
# src/apps/blog/aggregates.py
from typing import List, Optional
from src.core.models import BaseModel

class BlogPost(BaseModel):
    """Aggregate root for blog posts"""
    __tablename__ = "blog_posts"
    
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"))
    is_published = Column(Boolean, default=False)
    
    # Aggregate members
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="post_tags", back_populates="posts")
    
    def __init__(self, title: str, content: str, author_id: int):
        super().__init__()
        self.title = title
        self.content = content
        self.author_id = author_id
        self._validate_invariants()
    
    def _validate_invariants(self):
        """Ensure aggregate invariants are maintained"""
        if not self.title or len(self.title.strip()) == 0:
            raise ValueError("Post title cannot be empty")
        if not self.content or len(self.content.strip()) < 10:
            raise ValueError("Post content must be at least 10 characters")
    
    def publish(self):
        """Business operation: publish the post"""
        if self.is_published:
            raise ValueError("Post is already published")
        
        self.is_published = True
        self.register_event(PostPublishedEvent(
            post_id=self.id,
            title=self.title,
            author_id=self.author_id
        ))
    
    def add_comment(self, content: str, author_id: int) -> 'Comment':
        """Business operation: add comment to post"""
        if not self.is_published:
            raise ValueError("Cannot comment on unpublished post")
        
        comment = Comment(
            content=content,
            author_id=author_id,
            post_id=self.id
        )
        self.comments.append(comment)
        return comment
    
    def add_tag(self, tag: 'Tag'):
        """Business operation: add tag to post"""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: 'Tag'):
        """Business operation: remove tag from post"""
        if tag in self.tags:
            self.tags.remove(tag)

class Comment(BaseModel):
    """Aggregate member - managed by BlogPost"""
    __tablename__ = "comments"
    
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("blog_posts.id"))
    is_approved = Column(Boolean, default=False)
    
    post = relationship("BlogPost", back_populates="comments")
    author = relationship("User")
    
    def approve(self):
        """Business operation: approve comment"""
        if self.is_approved:
            raise ValueError("Comment is already approved")
        
        self.is_approved = True
```

## 💾 Data Access Patterns

### 1. Repository Pattern

```python
# src/core/repository.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional
from sqlalchemy.orm import Session

T = TypeVar('T')

class Repository(Generic[T], ABC):
    def __init__(self, db: Session, model_class: type):
        self.db = db
        self.model_class = model_class
    
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        pass
    
    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        pass
    
    @abstractmethod
    def create(self, entity: T) -> T:
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        pass
    
    @abstractmethod
    def delete(self, entity: T) -> None:
        pass

class SQLAlchemyRepository(Repository[T]):
    def get_by_id(self, id: int) -> Optional[T]:
        return self.db.query(self.model_class).filter(self.model_class.id == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        return self.db.query(self.model_class).offset(skip).limit(limit).all()
    
    def create(self, entity: T) -> T:
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def update(self, entity: T) -> T:
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def delete(self, entity: T) -> None:
        self.db.delete(entity)
        self.db.commit()

# Specific repository implementations
class UserRepository(SQLAlchemyRepository[User]):
    def __init__(self, db: Session):
        super().__init__(db, User)
    
    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def get_active_users(self) -> List[User]:
        return self.db.query(User).filter(User.is_active == True).all()
    
    def search_by_name(self, name: str) -> List[User]:
        return self.db.query(User).filter(
            User.full_name.ilike(f"%{name}%")
        ).all()
```

### 2. Unit of Work Pattern

```python
# src/core/unit_of_work.py
from abc import ABC, abstractmethod
from typing import Dict, Type
from sqlalchemy.orm import Session
from src.core.repository import Repository

class UnitOfWork(ABC):
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
    
    @abstractmethod
    def commit(self):
        pass
    
    @abstractmethod
    def rollback(self):
        pass

class SQLAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, db: Session):
        self.db = db
        self._repositories: Dict[Type, Repository] = {}
    
    def get_repository(self, model_class: Type[T]) -> Repository[T]:
        if model_class not in self._repositories:
            # Factory pattern for repositories
            if model_class == User:
                self._repositories[model_class] = UserRepository(self.db)
            elif model_class == BlogPost:
                self._repositories[model_class] = BlogPostRepository(self.db)
            else:
                self._repositories[model_class] = SQLAlchemyRepository(self.db, model_class)
        
        return self._repositories[model_class]
    
    def commit(self):
        self.db.commit()
    
    def rollback(self):
        self.db.rollback()

# Usage in services
class UserService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
    
    def create_user_with_profile(self, user_data: UserCreate, profile_data: ProfileCreate):
        with self.uow:
            user_repo = self.uow.get_repository(User)
            profile_repo = self.uow.get_repository(Profile)
            
            # Create user
            user = User(**user_data.dict())
            user = user_repo.create(user)
            
            # Create profile
            profile = Profile(user_id=user.id, **profile_data.dict())
            profile = profile_repo.create(profile)
            
            # Both operations are committed together
            return user, profile
```

### 3. Specification Pattern

```python
# src/core/specifications.py
from abc import ABC, abstractmethod
from typing import TypeVar
from sqlalchemy.orm import Query

T = TypeVar('T')

class Specification(ABC):
    @abstractmethod
    def is_satisfied_by(self, entity: T) -> bool:
        pass
    
    @abstractmethod
    def to_expression(self, query: Query) -> Query:
        pass
    
    def and_(self, other: 'Specification') -> 'Specification':
        return AndSpecification(self, other)
    
    def or_(self, other: 'Specification') -> 'Specification':
        return OrSpecification(self, other)
    
    def not_(self) -> 'Specification':
        return NotSpecification(self)

class AndSpecification(Specification):
    def __init__(self, left: Specification, right: Specification):
        self.left = left
        self.right = right
    
    def is_satisfied_by(self, entity: T) -> bool:
        return self.left.is_satisfied_by(entity) and self.right.is_satisfied_by(entity)
    
    def to_expression(self, query: Query) -> Query:
        return self.right.to_expression(self.left.to_expression(query))

# User specifications
class ActiveUserSpecification(Specification):
    def is_satisfied_by(self, user: User) -> bool:
        return user.is_active
    
    def to_expression(self, query: Query) -> Query:
        return query.filter(User.is_active == True)

class UserEmailDomainSpecification(Specification):
    def __init__(self, domain: str):
        self.domain = domain
    
    def is_satisfied_by(self, user: User) -> bool:
        return user.email.endswith(f"@{self.domain}")
    
    def to_expression(self, query: Query) -> Query:
        return query.filter(User.email.like(f"%@{self.domain}"))

class UserCreatedAfterSpecification(Specification):
    def __init__(self, date):
        self.date = date
    
    def is_satisfied_by(self, user: User) -> bool:
        return user.created_at > self.date
    
    def to_expression(self, query: Query) -> Query:
        return query.filter(User.created_at > self.date)

# Usage
class UserRepository(SQLAlchemyRepository[User]):
    def find_by_specification(self, spec: Specification) -> List[User]:
        query = self.db.query(User)
        query = spec.to_expression(query)
        return query.all()

# Example usage
user_repo = UserRepository(db)

# Find active users from gmail
spec = ActiveUserSpecification().and_(UserEmailDomainSpecification("gmail.com"))
gmail_users = user_repo.find_by_specification(spec)

# Find active users created after a date
from datetime import datetime, timedelta
recent_date = datetime.utcnow() - timedelta(days=30)
recent_active_spec = ActiveUserSpecification().and_(UserCreatedAfterSpecification(recent_date))
recent_users = user_repo.find_by_specification(recent_active_spec)
```

## 🔧 Service Layer Patterns

### 1. Command Pattern

```python
# src/core/commands.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

class Command(ABC):
    @abstractmethod
    def execute(self) -> Any:
        pass

class CommandHandler(ABC):
    @abstractmethod
    def handle(self, command: Command) -> Any:
        pass

@dataclass
class CreateUserCommand(Command):
    email: str
    full_name: str
    password: str
    
    def execute(self) -> Any:
        # Command execution logic here
        pass

@dataclass
class UpdateUserCommand(Command):
    user_id: int
    email: Optional[str] = None
    full_name: Optional[str] = None
    
    def execute(self) -> Any:
        pass

class CreateUserCommandHandler(CommandHandler):
    def __init__(self, user_service: UserService):
        self.user_service = user_service
    
    def handle(self, command: CreateUserCommand) -> User:
        # Validation
        if self.user_service.email_exists(command.email):
            raise ValueError("Email already exists")
        
        # Execute business logic
        user = self.user_service.create_user(
            email=command.email,
            full_name=command.full_name,
            password=command.password
        )
        
        return user

# Command bus/dispatcher
class CommandBus:
    def __init__(self):
        self._handlers = {}
    
    def register(self, command_type: type, handler: CommandHandler):
        self._handlers[command_type] = handler
    
    def execute(self, command: Command) -> Any:
        command_type = type(command)
        if command_type not in self._handlers:
            raise ValueError(f"No handler registered for {command_type}")
        
        handler = self._handlers[command_type]
        return handler.handle(command)

# Usage
command_bus = CommandBus()
command_bus.register(CreateUserCommand, CreateUserCommandHandler(user_service))

# In your route
@router.post("/users/")
async def create_user(user_data: UserCreate):
    command = CreateUserCommand(
        email=user_data.email,
        full_name=user_data.full_name,
        password=user_data.password
    )
    return command_bus.execute(command)
```

### 2. Query Pattern (CQRS)

```python
# src/core/queries.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Any

class Query(ABC):
    pass

class QueryHandler(ABC):
    @abstractmethod
    def handle(self, query: Query) -> Any:
        pass

@dataclass
class GetUserQuery(Query):
    user_id: int

@dataclass
class ListUsersQuery(Query):
    skip: int = 0
    limit: int = 100
    is_active: Optional[bool] = None
    search: Optional[str] = None

@dataclass
class GetUserPostsQuery(Query):
    user_id: int
    published_only: bool = True

class GetUserQueryHandler(QueryHandler):
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    def handle(self, query: GetUserQuery) -> Optional[User]:
        return self.user_repository.get_by_id(query.user_id)

class ListUsersQueryHandler(QueryHandler):
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    def handle(self, query: ListUsersQuery) -> List[User]:
        # Build specification based on query
        spec = None
        
        if query.is_active is not None:
            active_spec = ActiveUserSpecification() if query.is_active else NotSpecification(ActiveUserSpecification())
            spec = active_spec if spec is None else spec.and_(active_spec)
        
        if query.search:
            search_spec = UserNameContainsSpecification(query.search)
            spec = search_spec if spec is None else spec.and_(search_spec)
        
        if spec:
            return self.user_repository.find_by_specification(spec)
        else:
            return self.user_repository.get_all(skip=query.skip, limit=query.limit)

# Query bus
class QueryBus:
    def __init__(self):
        self._handlers = {}
    
    def register(self, query_type: type, handler: QueryHandler):
        self._handlers[query_type] = handler
    
    def execute(self, query: Query) -> Any:
        query_type = type(query)
        if query_type not in self._handlers:
            raise ValueError(f"No handler registered for {query_type}")
        
        handler = self._handlers[query_type]
        return handler.handle(query)

# Usage in routes
@router.get("/users/{user_id}/")
async def get_user(user_id: int):
    query = GetUserQuery(user_id=user_id)
    user = query_bus.execute(query)
    if not user:
        raise HTTPException(404, "User not found")
    return user

@router.get("/users/")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    search: Optional[str] = None
):
    query = ListUsersQuery(
        skip=skip,
        limit=limit,
        is_active=is_active,
        search=search
    )
    return query_bus.execute(query)
```

### 3. Strategy Pattern

```python
# src/core/strategies.py
from abc import ABC, abstractmethod
from typing import Protocol

class NotificationStrategy(ABC):
    @abstractmethod
    async def send(self, recipient: str, message: str, subject: str = None):
        pass

class EmailNotificationStrategy(NotificationStrategy):
    def __init__(self, email_service: EmailService):
        self.email_service = email_service
    
    async def send(self, recipient: str, message: str, subject: str = None):
        await self.email_service.send_email(
            to=recipient,
            subject=subject or "Notification",
            body=message
        )

class SMSNotificationStrategy(NotificationStrategy):
    def __init__(self, sms_service: SMSService):
        self.sms_service = sms_service
    
    async def send(self, recipient: str, message: str, subject: str = None):
        await self.sms_service.send_sms(
            phone=recipient,
            message=message
        )

class PushNotificationStrategy(NotificationStrategy):
    def __init__(self, push_service: PushService):
        self.push_service = push_service
    
    async def send(self, recipient: str, message: str, subject: str = None):
        await self.push_service.send_push(
            device_token=recipient,
            title=subject or "Notification",
            body=message
        )

# Context class
class NotificationService:
    def __init__(self):
        self._strategies = {
            "email": EmailNotificationStrategy,
            "sms": SMSNotificationStrategy,
            "push": PushNotificationStrategy
        }
    
    async def send_notification(
        self,
        method: str,
        recipient: str,
        message: str,
        subject: str = None
    ):
        if method not in self._strategies:
            raise ValueError(f"Unsupported notification method: {method}")
        
        strategy = self._strategies[method]()
        await strategy.send(recipient, message, subject)
    
    async def send_multi_channel(
        self,
        methods: List[str],
        recipient_map: Dict[str, str],
        message: str,
        subject: str = None
    ):
        for method in methods:
            if method in recipient_map:
                await self.send_notification(
                    method=method,
                    recipient=recipient_map[method],
                    message=message,
                    subject=subject
                )
```

## 🌐 API Patterns

### 1. Response Wrapper Pattern

```python
# src/core/responses.py
from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None
    errors: Optional[List[str]] = None

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int

def success_response(data: T, message: str = None) -> ApiResponse[T]:
    return ApiResponse(success=True, data=data, message=message)

def error_response(message: str, errors: List[str] = None) -> ApiResponse[None]:
    return ApiResponse(success=False, message=message, errors=errors)

# Usage in routes
@router.get("/users/{user_id}/", response_model=ApiResponse[UserResponse])
async def get_user(user_id: int):
    user = user_service.get_user(user_id)
    if not user:
        return error_response("User not found")
    return success_response(user, "User retrieved successfully")
```

### 2. Middleware Pattern

```python
# src/core/middleware.py
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
import time
import logging

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} ({process_time:.3f}s)")
        
        response.headers["X-Process-Time"] = str(process_time)
        return response

class CORSMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, allowed_origins: List[str] = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["*"]
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        origin = request.headers.get("Origin")
        if origin in self.allowed_origins or "*" in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        return response

# Register middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(CORSMiddleware, allowed_origins=["http://localhost:3000"])
```

## 🛡️ Error Handling Patterns

### 1. Result Pattern

```python
# src/core/result.py
from typing import Generic, TypeVar, Union, Callable, Optional
from dataclasses import dataclass

T = TypeVar('T')
E = TypeVar('E')

@dataclass
class Success(Generic[T]):
    value: T
    
    def is_success(self) -> bool:
        return True
    
    def is_failure(self) -> bool:
        return False

@dataclass
class Failure(Generic[E]):
    error: E
    
    def is_success(self) -> bool:
        return False
    
    def is_failure(self) -> bool:
        return True

Result = Union[Success[T], Failure[E]]

class ResultMonad(Generic[T]):
    def __init__(self, result: Result[T, E]):
        self._result = result
    
    def map(self, func: Callable[[T], U]) -> 'ResultMonad[U]':
        if self._result.is_success():
            try:
                return ResultMonad(Success(func(self._result.value)))
            except Exception as e:
                return ResultMonad(Failure(e))
        return ResultMonad(self._result)
    
    def flat_map(self, func: Callable[[T], 'ResultMonad[U]']) -> 'ResultMonad[U]':
        if self._result.is_success():
            return func(self._result.value)
        return ResultMonad(self._result)
    
    def unwrap(self) -> T:
        if self._result.is_success():
            return self._result.value
        raise self._result.error

# Usage in services
class UserService:
    def create_user(self, user_data: UserCreate) -> Result[User, str]:
        try:
            if self.email_exists(user_data.email):
                return Failure("Email already exists")
            
            user = User(**user_data.dict())
            user = self.repository.create(user)
            return Success(user)
        
        except Exception as e:
            return Failure(f"Failed to create user: {str(e)}")
    
    def get_user(self, user_id: int) -> Result[User, str]:
        user = self.repository.get_by_id(user_id)
        if user:
            return Success(user)
        return Failure("User not found")

# Usage in routes
@router.post("/users/")
async def create_user(user_data: UserCreate):
    result = user_service.create_user(user_data)
    
    if result.is_success():
        return success_response(result.value, "User created successfully")
    else:
        raise HTTPException(400, result.error)
```

### 2. Exception Chain Pattern

```python
# src/core/exceptions.py
class DomainException(Exception):
    """Base domain exception"""
    pass

class ValidationException(DomainException):
    """Validation error in domain logic"""
    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(f"Validation error in {field}: {message}")

class BusinessRuleException(DomainException):
    """Business rule violation"""
    pass

class ResourceNotFoundException(DomainException):
    """Resource not found"""
    def __init__(self, resource_type: str, identifier: str):
        self.resource_type = resource_type
        self.identifier = identifier
        super().__init__(f"{resource_type} with identifier {identifier} not found")

class InfrastructureException(Exception):
    """Infrastructure layer exception"""
    pass

class DatabaseException(InfrastructureException):
    """Database operation exception"""
    pass

# Exception mapping
EXCEPTION_STATUS_MAP = {
    ValidationException: 400,
    BusinessRuleException: 400,
    ResourceNotFoundException: 404,
    DatabaseException: 500,
}

# Global exception handler
async def domain_exception_handler(request: Request, exc: DomainException):
    status_code = EXCEPTION_STATUS_MAP.get(type(exc), 500)
    
    return JSONResponse(
        status_code=status_code,
        content={
            "message": str(exc),
            "error_type": exc.__class__.__name__,
            "details": getattr(exc, '__dict__', {})
        }
    )
```

## 🔒 Security Patterns

### 1. Authorization Decorator Pattern

```python
# src/core/authorization.py
from functools import wraps
from typing import List, Callable
from fastapi import HTTPException, Depends

def authorize(permissions: List[str]):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(401, "Authentication required")
            
            user_permissions = get_user_permissions(current_user)
            if not all(perm in user_permissions for perm in permissions):
                raise HTTPException(403, "Insufficient permissions")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_ownership(resource_param: str):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            resource_id = kwargs.get(resource_param)
            
            if not current_user:
                raise HTTPException(401, "Authentication required")
            
            # Check if user owns the resource
            if not user_owns_resource(current_user.id, resource_id):
                raise HTTPException(403, "Access denied")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
@router.delete("/posts/{post_id}/")
@authorize(["delete_post"])
@require_ownership("post_id")
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user)
):
    pass
```

### 2. Input Sanitization Pattern

```python
# src/core/sanitization.py
import html
import re
from typing import Any, Dict

class InputSanitizer:
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Remove HTML tags and escape special characters"""
        # Remove HTML tags
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', text)
        # Escape HTML characters
        return html.escape(text)
    
    @staticmethod
    def sanitize_sql(text: str) -> str:
        """Basic SQL injection prevention"""
        dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_']
        for char in dangerous_chars:
            text = text.replace(char, '')
        return text
    
    @staticmethod
    def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary values"""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = InputSanitizer.sanitize_html(value)
            elif isinstance(value, dict):
                sanitized[key] = InputSanitizer.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    InputSanitizer.sanitize_html(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized

# Middleware for automatic sanitization
class SanitizationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "PATCH"]:
            # Read and sanitize request body
            body = await request.body()
            if body:
                try:
                    data = json.loads(body)
                    sanitized_data = InputSanitizer.sanitize_dict(data)
                    # Replace request body with sanitized data
                    request._body = json.dumps(sanitized_data).encode()
                except json.JSONDecodeError:
                    pass
        
        return await call_next(request)
```

## ⚡ Performance Patterns

### 1. Caching Pattern

```python
# src/core/caching.py
from abc import ABC, abstractmethod
from typing import Any, Optional, Callable
import json
import hashlib
from functools import wraps

class CacheBackend(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 300):
        pass
    
    @abstractmethod
    async def delete(self, key: str):
        pass

class RedisCache(CacheBackend):
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        value = await self.redis.get(key)
        return json.loads(value) if value else None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        await self.redis.setex(key, ttl, json.dumps(value, default=str))
    
    async def delete(self, key: str):
        await self.redis.delete(key)

class InMemoryCache(CacheBackend):
    def __init__(self):
        self._cache = {}
    
    async def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        self._cache[key] = value
        # Note: TTL not implemented for simplicity
    
    async def delete(self, key: str):
        self._cache.pop(key, None)

def cache_key_generator(*args, **kwargs) -> str:
    """Generate cache key from function arguments"""
    key_data = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_data.encode()).hexdigest()

def cached(ttl: int = 300, key_func: Callable = cache_key_generator):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = kwargs.pop('cache', None)
            if not cache:
                return await func(*args, **kwargs)
            
            # Generate cache key
            cache_key = f"{func.__name__}:{key_func(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator

# Usage
class UserService:
    def __init__(self, repository: UserRepository, cache: CacheBackend):
        self.repository = repository
        self.cache = cache
    
    @cached(ttl=600)  # Cache for 10 minutes
    async def get_user_profile(self, user_id: int, cache: CacheBackend = None):
        return self.repository.get_user_with_profile(user_id)
    
    async def update_user(self, user_id: int, user_data: UserUpdate):
        user = self.repository.update(user_id, user_data)
        # Invalidate cache
        await self.cache.delete(f"get_user_profile:{user_id}")
        return user
```

### 2. Lazy Loading Pattern

```python
# src/core/lazy_loading.py
from typing import Callable, Any, Optional

class LazyProperty:
    def __init__(self, func: Callable):
        self.func = func
        self.name = func.__name__
    
    def __get__(self, obj: Any, owner: type) -> Any:
        if obj is None:
            return self
        
        value = self.func(obj)
        setattr(obj, self.name, value)
        return value

class LazyLoader:
    def __init__(self, loader_func: Callable, *args, **kwargs):
        self._loader_func = loader_func
        self._args = args
        self._kwargs = kwargs
        self._loaded = False
        self._value = None
    
    def load(self):
        if not self._loaded:
            self._value = self._loader_func(*self._args, **self._kwargs)
            self._loaded = True
        return self._value
    
    @property
    def value(self):
        return self.load()

# Usage in models
class User(BaseModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._posts_loader = None
    
    @LazyProperty
    def posts_count(self):
        """Lazy load posts count"""
        return len(self.posts)
    
    @property
    def posts(self):
        if not self._posts_loader:
            self._posts_loader = LazyLoader(
                self._load_posts
            )
        return self._posts_loader.value
    
    def _load_posts(self):
        # This would be injected via dependency injection
        from src.apps.blog.repository import PostRepository
        post_repo = PostRepository(db)
        return post_repo.get_by_user_id(self.id)
```

## 🧪 Testing Patterns

### 1. Test Factory Pattern

```python
# tests/factories.py
import factory
from factory.alchemy import SQLAlchemyModelFactory
from src.apps.users.models import User
from src.apps.blog.models import Post

class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"
    
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    full_name = factory.Faker("name")
    is_active = True
    hashed_password = factory.Faker("password")

class PostFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Post
        sqlalchemy_session_persistence = "commit"
    
    title = factory.Faker("sentence", nb_words=4)
    content = factory.Faker("text", max_nb_chars=1000)
    author = factory.SubFactory(UserFactory)
    is_published = True

# Usage in tests
def test_user_creation():
    user = UserFactory()
    assert user.email is not None
    assert user.full_name is not None

def test_post_with_author():
    post = PostFactory()
    assert post.author is not None
    assert post.author.email is not None
```

### 2. Mock Pattern

```python
# tests/mocks.py
from unittest.mock import Mock, AsyncMock
from src.apps.users.models import User

class MockUserRepository:
    def __init__(self):
        self.users = {}
        self.next_id = 1
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.users.get(user_id)
    
    def get_by_email(self, email: str) -> Optional[User]:
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    def create(self, user: User) -> User:
        user.id = self.next_id
        self.next_id += 1
        self.users[user.id] = user
        return user

class MockEmailService:
    def __init__(self):
        self.sent_emails = []
    
    async def send_email(self, to: str, subject: str, body: str):
        self.sent_emails.append({
            "to": to,
            "subject": subject,
            "body": body
        })

# Usage in tests
def test_user_service_with_mocks():
    mock_repo = MockUserRepository()
    mock_email = MockEmailService()
    
    user_service = UserService(
        repository=mock_repo,
        email_service=mock_email
    )
    
    user = user_service.create_user(UserCreate(
        email="test@example.com",
        full_name="Test User",
        password="password123"
    ))
    
    assert user.id is not None
    assert len(mock_email.sent_emails) == 1
    assert mock_email.sent_emails[0]["to"] == "test@example.com"
```

This comprehensive patterns guide provides reusable solutions for common problems in Domain-Driven Development with FastAPI. These patterns help maintain clean architecture, improve code organization, and ensure scalable and maintainable applications.
