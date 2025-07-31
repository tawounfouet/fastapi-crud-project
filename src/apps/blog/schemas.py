"""
Blog App Schemas - API input/output data models
"""

from datetime import datetime
from typing import Optional, Annotated
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.apps.blog.models import PostStatus, CommentStatus


# Base schema
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# Category schemas
class CategoryCreate(BaseSchema):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    slug: Annotated[str, Field(min_length=1, max_length=100)]
    description: Optional[str] = Field(None, max_length=500)
    parent_id: Optional[uuid.UUID] = None


class CategoryUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    parent_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class CategoryResponse(BaseSchema):
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str]
    parent_id: Optional[uuid.UUID]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    post_count: int = Field(default=0, description="Number of posts in category")


class CategoryListResponse(BaseSchema):
    items: list[CategoryResponse]
    total: int
    page: int
    pages: int


# Tag schemas
class TagCreate(BaseSchema):
    name: Annotated[str, Field(min_length=1, max_length=50)]
    slug: Annotated[str, Field(min_length=1, max_length=50)]
    description: Optional[str] = Field(None, max_length=200)


class TagUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    slug: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None


class TagResponse(BaseSchema):
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    post_count: int = Field(default=0, description="Number of posts with this tag")


class TagListResponse(BaseSchema):
    items: list[TagResponse]
    total: int


# Blog post schemas
class BlogPostCreate(BaseSchema):
    title: Annotated[str, Field(min_length=1, max_length=200)]
    slug: Annotated[str, Field(min_length=1, max_length=200)]
    content: Annotated[str, Field(min_length=1)]
    excerpt: Optional[str] = Field(None, max_length=500)
    status: PostStatus = PostStatus.DRAFT
    featured_image: Optional[str] = Field(None, max_length=500)
    meta_title: Optional[str] = Field(None, max_length=60)
    meta_description: Optional[str] = Field(None, max_length=160)
    category_id: Optional[uuid.UUID] = None
    tag_ids: Optional[list[uuid.UUID]] = Field(None, max_length=10)
    published_at: Optional[datetime] = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug format"""
        import re

        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                "Slug must contain only lowercase letters, numbers, and hyphens"
            )
        return v


class BlogPostUpdate(BaseSchema):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    excerpt: Optional[str] = Field(None, max_length=500)
    status: Optional[PostStatus] = None
    featured_image: Optional[str] = Field(None, max_length=500)
    meta_title: Optional[str] = Field(None, max_length=60)
    meta_description: Optional[str] = Field(None, max_length=160)
    category_id: Optional[uuid.UUID] = None
    tag_ids: Optional[list[uuid.UUID]] = Field(None, max_length=10)
    published_at: Optional[datetime] = None
    is_active: Optional[bool] = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        """Validate slug format"""
        if v is not None:
            import re

            if not re.match(r"^[a-z0-9-]+$", v):
                raise ValueError(
                    "Slug must contain only lowercase letters, numbers, and hyphens"
                )
        return v


class BlogPostResponse(BaseSchema):
    id: uuid.UUID
    title: str
    slug: str
    content: str
    excerpt: Optional[str]
    status: PostStatus
    featured_image: Optional[str]
    meta_title: Optional[str]
    meta_description: Optional[str]
    published_at: Optional[datetime]
    view_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Author information
    author_id: uuid.UUID

    # Category information
    category_id: Optional[uuid.UUID]
    category: Optional[CategoryResponse] = None

    # Tags
    tags: list[TagResponse] = Field(default_factory=list)

    # Comment count
    comment_count: int = Field(default=0, description="Number of approved comments")


class BlogPostListResponse(BaseSchema):
    items: list[BlogPostResponse]
    total: int
    page: int
    pages: int


# Comment schemas
class CommentCreate(BaseSchema):
    content: Annotated[str, Field(min_length=1, max_length=1000)]
    author_name: Annotated[str, Field(min_length=1, max_length=100)]
    author_email: Annotated[str, Field(max_length=255)]
    author_website: Optional[str] = Field(None, max_length=255)
    post_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None

    @field_validator("author_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation"""
        import re

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, v):
            raise ValueError("Invalid email format")
        return v.lower()


class CommentUpdate(BaseSchema):
    content: Optional[str] = Field(None, min_length=1, max_length=1000)
    status: Optional[CommentStatus] = None


class CommentResponse(BaseSchema):
    id: uuid.UUID
    content: str
    author_name: str
    author_email: str
    author_website: Optional[str]
    status: CommentStatus
    created_at: datetime
    updated_at: datetime
    moderated_at: Optional[datetime]
    moderated_by_id: Optional[uuid.UUID]

    # Post information
    post_id: uuid.UUID

    # Hierarchy
    parent_id: Optional[uuid.UUID]
    replies: list["CommentResponse"] = Field(default_factory=list)


class CommentListResponse(BaseSchema):
    items: list[CommentResponse]
    total: int
    page: int
    pages: int


# Statistics schemas
class BlogStats(BaseSchema):
    total_posts: int = Field(ge=0)
    published_posts: int = Field(ge=0)
    draft_posts: int = Field(ge=0)
    total_comments: int = Field(ge=0)
    pending_comments: int = Field(ge=0)
    total_categories: int = Field(ge=0)
    total_tags: int = Field(ge=0)
    total_views: int = Field(ge=0)


# Search and filter schemas
class BlogPostFilter(BaseSchema):
    status: Optional[PostStatus] = None
    category_id: Optional[uuid.UUID] = None
    tag_id: Optional[uuid.UUID] = None
    author_id: Optional[uuid.UUID] = None
    search: Optional[str] = Field(None, min_length=1, max_length=100)
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None


class CommentFilter(BaseSchema):
    status: Optional[CommentStatus] = None
    post_id: Optional[uuid.UUID] = None
    author_email: Optional[str] = None
