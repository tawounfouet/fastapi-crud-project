# API Design Guide

This guide covers RESTful API design principles, patterns, and best practices for Domain-Driven Development in FastAPI applications.

## 📚 Table of Contents

- [API Design Principles](#api-design-principles)
- [URL Structure and Naming](#url-structure-and-naming)
- [HTTP Methods and Status Codes](#http-methods-and-status-codes)
- [Request and Response Patterns](#request-and-response-patterns)
- [Validation and Error Handling](#validation-and-error-handling)
- [Authentication and Authorization](#authentication-and-authorization)
- [Versioning Strategies](#versioning-strategies)
- [Documentation Standards](#documentation-standards)
- [Performance Considerations](#performance-considerations)
- [Testing API Endpoints](#testing-api-endpoints)

## 🎯 API Design Principles

### 1. RESTful Design
Follow REST principles for consistent and predictable APIs:
- **Resources**: Use nouns to represent entities
- **HTTP Methods**: Use appropriate verbs for actions
- **Stateless**: Each request contains all necessary information
- **Cacheable**: Design responses to be cacheable when appropriate

### 2. Domain-Driven URLs
Structure URLs to reflect your domain model:

```
/api/v1/users/                    # Users collection
/api/v1/users/{user_id}/          # Specific user
/api/v1/users/{user_id}/posts/    # User's posts
/api/v1/posts/                    # Posts collection
/api/v1/posts/{post_id}/          # Specific post
/api/v1/posts/{post_id}/comments/ # Post's comments
```

### 3. Consistency
Maintain consistent patterns across all endpoints:
- URL naming conventions
- Response formats
- Error structures
- Parameter patterns

## 🔗 URL Structure and Naming

### Base Structure

```
https://api.example.com/api/v1/{resource}/{id}/{sub-resource}
```

### Naming Conventions

#### 1. Resource Names
- Use **plural nouns** for collections: `/users`, `/posts`, `/comments`
- Use **kebab-case** for multi-word resources: `/blog-posts`, `/user-profiles`
- Keep names simple and descriptive

#### 2. URL Parameters
- Use **snake_case** for query parameters: `?created_after=2023-01-01&is_active=true`
- Use descriptive parameter names: `?page=1&limit=20&sort_by=created_at`

#### 3. Path Conventions

```python
# Good URL patterns
/api/v1/users/                          # GET: List users, POST: Create user
/api/v1/users/{user_id}/                # GET: Get user, PUT: Update user, DELETE: Delete user
/api/v1/users/{user_id}/posts/          # GET: List user's posts, POST: Create post for user
/api/v1/users/{user_id}/posts/{post_id}/ # GET: Get specific post by user

# Avoid these patterns
/api/v1/getUsers/                       # Don't use verbs in URLs
/api/v1/user/{user_id}/                 # Use plural forms
/api/v1/users/{user_id}/delete/         # Use HTTP methods instead
```

### Router Organization

```python
# src/apps/users/views.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.apps.users import schemas, services

router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[schemas.UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of users with pagination"""
    users = services.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}/", response_model=schemas.UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific user by ID"""
    user = services.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new user"""
    return services.create_user(db=db, user=user)
```

## 🔧 HTTP Methods and Status Codes

### HTTP Methods Usage

| Method | Purpose | Example |
|--------|---------|---------|
| GET | Retrieve resources | `GET /api/v1/users/` |
| POST | Create new resources | `POST /api/v1/users/` |
| PUT | Update entire resource | `PUT /api/v1/users/123/` |
| PATCH | Partial resource update | `PATCH /api/v1/users/123/` |
| DELETE | Remove resources | `DELETE /api/v1/users/123/` |

### Status Codes

#### Success Codes
```python
from fastapi import status

# 200 OK - Successful GET, PUT, PATCH
@router.get("/users/{user_id}/")
async def get_user(user_id: int):
    # Returns 200 by default
    pass

# 201 Created - Successful POST
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    pass

# 204 No Content - Successful DELETE
@router.delete("/{user_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int):
    pass
```

#### Error Codes
```python
from fastapi import HTTPException, status

# 400 Bad Request - Invalid input
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Invalid email format"
)

# 401 Unauthorized - Authentication required
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication required",
    headers={"WWW-Authenticate": "Bearer"},
)

# 403 Forbidden - Insufficient permissions
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Insufficient permissions"
)

# 404 Not Found - Resource doesn't exist
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="User not found"
)

# 409 Conflict - Resource conflict
raise HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Email already registered"
)

# 422 Unprocessable Entity - Validation error
# Handled automatically by FastAPI/Pydantic

# 500 Internal Server Error - Server error
# Should be handled by global exception handler
```

## 📋 Request and Response Patterns

### Request Schemas

```python
# src/apps/users/schemas.py
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    
    class Config:
        # Allow partial updates
        extra = "forbid"  # Reject unknown fields

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Enable ORM mode
```

### Response Patterns

#### 1. Single Resource Response
```python
{
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "created_at": "2023-01-15T10:30:00Z",
    "updated_at": "2023-01-15T10:30:00Z"
}
```

#### 2. Collection Response with Pagination
```python
# Response schema
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int

# Usage
@router.get("/", response_model=PaginatedResponse[schemas.UserResponse])
async def list_users(
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db)
):
    skip = (page - 1) * size
    users = services.get_users(db, skip=skip, limit=size)
    total = services.count_users(db)
    
    return PaginatedResponse(
        items=users,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )
```

#### 3. Nested Resource Response
```python
class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    author: UserResponse  # Nested user data
    
    class Config:
        from_attributes = True

class UserWithPostsResponse(UserResponse):
    posts: List[PostResponse] = []
```

### Request Patterns

#### 1. Query Parameters
```python
@router.get("/")
async def list_users(
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    
    # Filtering
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    created_after: Optional[datetime] = Query(None, description="Filter by creation date"),
    
    # Searching
    search: Optional[str] = Query(None, min_length=3, description="Search in name and email"),
    
    # Sorting
    sort_by: str = Query("created_at", regex="^(created_at|email|full_name)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    
    db: Session = Depends(get_db)
):
    pass
```

#### 2. Path Parameters
```python
@router.get("/{user_id}/posts/{post_id}/")
async def get_user_post(
    user_id: int = Path(..., gt=0, description="User ID"),
    post_id: int = Path(..., gt=0, description="Post ID"),
    db: Session = Depends(get_db)
):
    pass
```

#### 3. Request Body
```python
@router.post("/")
async def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    pass

@router.patch("/{user_id}/")
async def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db)
):
    pass
```

## ✅ Validation and Error Handling

### Input Validation

```python
from pydantic import BaseModel, validator, Field
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name")
    password: str = Field(..., min_length=8, description="Password")
    age: Optional[int] = Field(None, ge=0, le=150, description="User age")
    
    @validator('email')
    def email_must_be_lowercase(cls, v):
        return v.lower()
    
    @validator('full_name')
    def name_must_not_contain_numbers(cls, v):
        if any(char.isdigit() for char in v):
            raise ValueError('Name cannot contain numbers')
        return v.title()
    
    @validator('password')
    def validate_password(cls, v):
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        return v
```

### Error Response Format

```python
# src/core/exceptions.py
from fastapi import HTTPException
from typing import Any, Dict, Optional

class APIException(HTTPException):
    def __init__(
        self,
        status_code: int,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.details = details or {}
        self.error_code = error_code
        
        detail = {
            "message": message,
            "error_code": error_code,
            "details": details
        }
        super().__init__(status_code=status_code, detail=detail)

# Custom exceptions
class UserNotFoundError(APIException):
    def __init__(self, user_id: int):
        super().__init__(
            status_code=404,
            message=f"User with ID {user_id} not found",
            error_code="USER_NOT_FOUND",
            details={"user_id": user_id}
        )

class EmailAlreadyExistsError(APIException):
    def __init__(self, email: str):
        super().__init__(
            status_code=409,
            message="Email address already registered",
            error_code="EMAIL_ALREADY_EXISTS",
            details={"email": email}
        )
```

### Global Exception Handler

```python
# src/core/exception_handlers.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "message": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "details": exc.errors()
        }
    )

async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors"""
    logger.error(f"Database integrity error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "message": "Data conflict occurred",
            "error_code": "INTEGRITY_ERROR",
            "details": {"database_error": str(exc.orig)}
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Internal server error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "details": {}
        }
    )

# Register handlers in main.py
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(Exception, general_exception_handler)
```

## 🔐 Authentication and Authorization

### JWT Authentication

```python
# src/core/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

security = HTTPBearer()

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    user = get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user

# Usage in routes
@router.get("/me/", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    return current_user
```

### Role-Based Authorization

```python
# src/core/permissions.py
from functools import wraps
from fastapi import HTTPException, status
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"

def require_role(required_role: UserRole):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if current_user.role != required_role and current_user.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required role: {required_role}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
@router.delete("/{user_id}/")
@require_role(UserRole.ADMIN)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pass
```

## 📅 Versioning Strategies

### URL Path Versioning

```python
# Version 1
v1_router = APIRouter(prefix="/api/v1")

@v1_router.get("/users/")
async def list_users_v1():
    # Version 1 implementation
    pass

# Version 2
v2_router = APIRouter(prefix="/api/v2")

@v2_router.get("/users/")
async def list_users_v2():
    # Version 2 implementation with breaking changes
    pass

# Register both versions
app.include_router(v1_router)
app.include_router(v2_router)
```

### Header Versioning

```python
from fastapi import Header

@router.get("/users/")
async def list_users(
    api_version: str = Header(alias="X-API-Version", default="v1")
):
    if api_version == "v1":
        # Version 1 logic
        pass
    elif api_version == "v2":
        # Version 2 logic
        pass
    else:
        raise HTTPException(400, "Unsupported API version")
```

### Content Type Versioning

```python
@router.get("/users/")
async def list_users(
    accept: str = Header(default="application/json")
):
    if "application/vnd.api.v1+json" in accept:
        # Version 1 response
        pass
    elif "application/vnd.api.v2+json" in accept:
        # Version 2 response
        pass
```

## 📚 Documentation Standards

### OpenAPI Configuration

```python
# main.py
from fastapi import FastAPI

app = FastAPI(
    title="My API",
    description="A comprehensive API for my application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)
```

### Endpoint Documentation

```python
@router.post(
    "/",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user with the provided information",
    response_description="The created user",
    responses={
        409: {
            "description": "Email already exists",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Email address already registered",
                        "error_code": "EMAIL_ALREADY_EXISTS"
                    }
                }
            }
        }
    }
)
async def create_user(
    user: schemas.UserCreate = Body(
        ...,
        example={
            "email": "user@example.com",
            "full_name": "John Doe",
            "password": "securepassword123"
        }
    ),
    db: Session = Depends(get_db)
):
    """
    Create a new user account.
    
    - **email**: Valid email address (required)
    - **full_name**: User's full name (required)
    - **password**: Secure password (required, min 8 characters)
    """
    return services.create_user(db=db, user=user)
```

### Schema Documentation

```python
class UserCreate(BaseModel):
    """Schema for creating a new user"""
    
    email: EmailStr = Field(..., description="User's email address", example="user@example.com")
    full_name: str = Field(..., description="User's full name", example="John Doe")
    password: str = Field(..., min_length=8, description="User's password", example="securepass123")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "full_name": "John Doe",
                "password": "securepass123"
            }
        }
```

## ⚡ Performance Considerations

### Response Optimization

```python
# Use response models to control output
@router.get("/users/", response_model=List[schemas.UserListResponse])
async def list_users():
    # UserListResponse excludes heavy fields like 'bio'
    pass

# Implement field selection
@router.get("/users/{user_id}/")
async def get_user(
    user_id: int,
    fields: Optional[str] = Query(None, description="Comma-separated fields to include")
):
    user = get_user_by_id(user_id)
    
    if fields:
        field_list = fields.split(',')
        return {field: getattr(user, field) for field in field_list if hasattr(user, field)}
    
    return user
```

### Caching

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

# Setup caching
FastAPICache.init(RedisBackend(url="redis://localhost"), prefix="fastapi-cache")

@router.get("/users/{user_id}/")
@cache(expire=300)  # Cache for 5 minutes
async def get_user(user_id: int):
    return get_user_by_id(user_id)
```

### Pagination

```python
from fastapi import Query

@router.get("/users/")
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * size
    users = db.query(User).offset(offset).limit(size).all()
    total = db.query(User).count()
    
    return {
        "items": users,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }
```

## 🧪 Testing API Endpoints

### Test Setup

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.fixture
def client(db_session: Session):
    from main import app
    from src.core.database import get_db
    
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()
```

### API Tests

```python
def test_create_user(client: TestClient):
    user_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpass123"
    }
    
    response = client.post("/api/v1/users/", json=user_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert "id" in data
    assert "password" not in data  # Ensure password is not returned

def test_get_user(client: TestClient, db_session: Session):
    # Create test user
    user = User(email="test@example.com", full_name="Test User")
    db_session.add(user)
    db_session.commit()
    
    response = client.get(f"/api/v1/users/{user.id}/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user.id
    assert data["email"] == user.email

def test_user_not_found(client: TestClient):
    response = client.get("/api/v1/users/999/")
    
    assert response.status_code == 404
    data = response.json()
    assert "User not found" in data["detail"]["message"]

def test_invalid_email(client: TestClient):
    user_data = {
        "email": "invalid-email",
        "full_name": "Test User",
        "password": "testpass123"
    }
    
    response = client.post("/api/v1/users/", json=user_data)
    
    assert response.status_code == 422
    data = response.json()
    assert "email" in str(data["detail"])
```

## 📋 API Design Checklist

### ✅ URL Design
- [ ] Use plural nouns for collections
- [ ] Use consistent naming conventions
- [ ] Follow REST principles
- [ ] Include version in URL path

### ✅ HTTP Methods
- [ ] Use appropriate HTTP methods
- [ ] Return correct status codes
- [ ] Implement idempotent operations where appropriate

### ✅ Request/Response
- [ ] Define clear request schemas
- [ ] Use consistent response formats
- [ ] Implement proper error responses
- [ ] Include pagination for collections

### ✅ Validation
- [ ] Validate all input data
- [ ] Provide clear error messages
- [ ] Handle edge cases
- [ ] Sanitize user input

### ✅ Security
- [ ] Implement authentication
- [ ] Add authorization checks
- [ ] Validate permissions
- [ ] Protect against common attacks

### ✅ Documentation
- [ ] Add comprehensive endpoint documentation
- [ ] Include request/response examples
- [ ] Document error scenarios
- [ ] Provide API usage examples

### ✅ Performance
- [ ] Implement caching where appropriate
- [ ] Add pagination for large datasets
- [ ] Optimize database queries
- [ ] Monitor API performance

### ✅ Testing
- [ ] Write comprehensive API tests
- [ ] Test error scenarios
- [ ] Test authentication/authorization
- [ ] Performance testing

This API design guide provides comprehensive patterns and best practices for creating well-designed, maintainable, and scalable APIs in FastAPI applications following DDD principles.
