"""
Blog App Models - Domain entities and database models
"""

from datetime import datetime
from enum import Enum
import uuid
from sqlmodel import SQLModel, Field, Relationship, Index
from typing import Optional, TYPE_CHECKING

from src.apps.shared import BaseModel, AuditMixin

if TYPE_CHECKING:
    from src.apps.users.models import User


# Enums
class PostStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class CommentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# Association table for many-to-many relationship between posts and tags
class PostTag(SQLModel, table=True):
    """Association table for posts and tags"""

    __tablename__ = "blog_post_tag"

    post_id: uuid.UUID = Field(foreign_key="blog_post.id", primary_key=True)
    tag_id: uuid.UUID = Field(foreign_key="blog_tag.id", primary_key=True)

    __table_args__ = (
        Index("ix_posttag_post", "post_id"),
        Index("ix_posttag_tag", "tag_id"),
    )


# Domain models
class Category(BaseModel, table=True):
    """Blog category model with hierarchy support"""

    __tablename__ = "blog_category"

    name: str = Field(max_length=100, index=True)
    slug: str = Field(max_length=100, unique=True, index=True)
    description: Optional[str] = Field(default=None, max_length=500)

    # Hierarchy support
    parent_id: Optional[uuid.UUID] = Field(default=None, foreign_key="blog_category.id")
    parent: Optional["Category"] = Relationship(
        back_populates="children", sa_relationship_kwargs={"remote_side": "Category.id"}
    )
    children: list["Category"] = Relationship(back_populates="parent")

    # Relationships
    posts: list["BlogPost"] = Relationship(back_populates="category")

    __table_args__ = (Index("ix_category_name_active", "name", "is_active"),)


class Tag(BaseModel, table=True):
    """Blog tag model for content tagging"""

    __tablename__ = "blog_tag"

    name: str = Field(max_length=50, unique=True, index=True)
    slug: str = Field(max_length=50, unique=True, index=True)
    description: Optional[str] = Field(default=None, max_length=200)


class BlogPost(BaseModel, AuditMixin, table=True):
    """Main blog post model"""

    __tablename__ = "blog_post"

    # Content
    title: str = Field(max_length=200, index=True)
    slug: str = Field(max_length=200, unique=True, index=True)
    content: str
    excerpt: Optional[str] = Field(default=None, max_length=500)

    # Publishing
    published_at: Optional[datetime] = Field(default=None, index=True)
    view_count: int = Field(default=0, ge=0)

    # Metadata
    status: PostStatus = Field(default=PostStatus.DRAFT, index=True)
    featured_image: Optional[str] = Field(default=None, max_length=500)
    meta_title: Optional[str] = Field(default=None, max_length=60)
    meta_description: Optional[str] = Field(default=None, max_length=160)

    # Foreign Keys
    author_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    category_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="blog_category.id", index=True
    )

    # Relationships
    author: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "BlogPost.author_id"}
    )
    category: Optional[Category] = Relationship(back_populates="posts")
    comments: list["Comment"] = Relationship(back_populates="post", cascade_delete=True)

    # Business methods
    def is_published(self) -> bool:
        """Check if post is published and public"""
        return (
            self.status == PostStatus.PUBLISHED
            and self.published_at is not None
            and self.published_at <= datetime.now()
        )

    def can_be_commented(self) -> bool:
        """Check if post allows comments"""
        return self.is_published() and self.is_active

    __table_args__ = (
        Index("ix_post_status_published", "status", "published_at"),
        Index("ix_post_author_status", "author_id", "status"),
    )


class Comment(BaseModel, table=True):
    """Blog comment model with moderation"""

    __tablename__ = "blog_comment"

    # Content
    content: str = Field(max_length=1000)
    author_name: str = Field(max_length=100)
    author_email: str = Field(max_length=255)
    author_website: Optional[str] = Field(default=None, max_length=255)

    # Moderation
    status: CommentStatus = Field(default=CommentStatus.PENDING, index=True)
    moderated_at: Optional[datetime] = Field(default=None)
    moderated_by_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")

    # Relationships
    post_id: uuid.UUID = Field(foreign_key="blog_post.id", index=True)
    parent_id: Optional[uuid.UUID] = Field(default=None, foreign_key="blog_comment.id")

    post: BlogPost = Relationship(back_populates="comments")
    parent: Optional["Comment"] = Relationship(
        back_populates="replies", sa_relationship_kwargs={"remote_side": "Comment.id"}
    )
    replies: list["Comment"] = Relationship(back_populates="parent")

    # Moderation relationship
    moderated_by: Optional["User"] = Relationship()

    def is_approved(self) -> bool:
        """Check if comment is approved"""
        return self.status == CommentStatus.APPROVED

    __table_args__ = (Index("ix_comment_post_status", "post_id", "status"),)
