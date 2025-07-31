"""
Tests for blog app models
"""

import pytest
import uuid
from datetime import datetime
from sqlmodel import Session

from src.apps.blog.models import (
    BlogPost,
    Category,
    Tag,
    Comment,
    PostStatus,
    CommentStatus,
)


class TestBlogModels:
    """Test blog model functionality"""

    def test_category_creation(self, db: Session):
        """Test category model creation"""
        category = Category(
            name="Technology", slug="technology", description="Tech-related posts"
        )

        db.add(category)
        db.commit()
        db.refresh(category)

        assert category.id is not None
        assert category.name == "Technology"
        assert category.slug == "technology"
        assert category.is_active is True
        assert category.created_at is not None

    def test_tag_creation(self, db: Session):
        """Test tag model creation"""
        tag = Tag(
            name="Python", slug="python", description="Python programming language"
        )

        db.add(tag)
        db.commit()
        db.refresh(tag)

        assert tag.id is not None
        assert tag.name == "Python"
        assert tag.slug == "python"
        assert tag.is_active is True

    def test_blog_post_creation(self, db: Session):
        """Test blog post model creation"""
        author_id = uuid.uuid4()

        post = BlogPost(
            title="Test Post",
            slug="test-post",
            content="This is a test post content",
            excerpt="Test excerpt",
            status=PostStatus.DRAFT,
            author_id=author_id,
            created_by_id=author_id,
        )

        db.add(post)
        db.commit()
        db.refresh(post)

        assert post.id is not None
        assert post.title == "Test Post"
        assert post.slug == "test-post"
        assert post.status == PostStatus.DRAFT
        assert post.view_count == 0
        assert post.is_active is True

    def test_blog_post_business_methods(self, db: Session):
        """Test blog post business methods"""
        author_id = uuid.uuid4()

        # Test draft post
        draft_post = BlogPost(
            title="Draft Post",
            slug="draft-post",
            content="Draft content",
            status=PostStatus.DRAFT,
            author_id=author_id,
            created_by_id=author_id,
        )

        assert not draft_post.is_published()
        assert not draft_post.can_be_commented()

        # Test published post
        published_post = BlogPost(
            title="Published Post",
            slug="published-post",
            content="Published content",
            status=PostStatus.PUBLISHED,
            published_at=datetime.now(),
            author_id=author_id,
            created_by_id=author_id,
        )

        assert published_post.is_published()
        assert published_post.can_be_commented()

    def test_comment_creation(self, db: Session):
        """Test comment model creation"""
        author_id = uuid.uuid4()

        # Create a post first
        post = BlogPost(
            title="Test Post",
            slug="test-post",
            content="Test content",
            author_id=author_id,
            created_by_id=author_id,
        )
        db.add(post)
        db.flush()

        comment = Comment(
            content="This is a test comment",
            author_name="John Doe",
            author_email="john@example.com",
            post_id=post.id,
            status=CommentStatus.PENDING,
        )

        db.add(comment)
        db.commit()
        db.refresh(comment)

        assert comment.id is not None
        assert comment.content == "This is a test comment"
        assert comment.author_name == "John Doe"
        assert comment.status == CommentStatus.PENDING
        assert not comment.is_approved()

    def test_comment_approval(self, db: Session):
        """Test comment approval"""
        author_id = uuid.uuid4()

        # Create a post first
        post = BlogPost(
            title="Test Post",
            slug="test-post",
            content="Test content",
            author_id=author_id,
            created_by_id=author_id,
        )
        db.add(post)
        db.flush()

        comment = Comment(
            content="Test comment",
            author_name="Jane Doe",
            author_email="jane@example.com",
            post_id=post.id,
            status=CommentStatus.APPROVED,
        )

        assert comment.is_approved()

    def test_category_hierarchy(self, db: Session):
        """Test category parent-child relationships"""
        parent_category = Category(name="Technology", slug="technology")
        db.add(parent_category)
        db.flush()

        child_category = Category(
            name="Programming", slug="programming", parent_id=parent_category.id
        )
        db.add(child_category)
        db.commit()

        db.refresh(parent_category)
        db.refresh(child_category)

        assert child_category.parent_id == parent_category.id
        # Note: Relationship loading would require proper setup
