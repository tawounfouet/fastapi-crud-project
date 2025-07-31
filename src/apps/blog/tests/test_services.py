"""
Tests for blog app services
"""

import pytest
import uuid
from datetime import datetime
from sqlmodel import Session
from fastapi import HTTPException

from src.apps.blog.models import (
    BlogPost,
    Category,
    Tag,
    Comment,
    PostStatus,
    CommentStatus,
)
from src.apps.blog.schemas import (
    BlogPostCreate,
    BlogPostUpdate,
    CategoryCreate,
    TagCreate,
    CommentCreate,
)
from src.apps.blog.services import (
    BlogPostService,
    CategoryService,
    TagService,
    CommentService,
    BlogStatsService,
)


class TestCategoryService:
    """Test category service functionality"""

    def test_create_category_success(self, db: Session):
        """Test successful category creation"""
        category_data = CategoryCreate(
            name="Technology", slug="technology", description="Tech-related posts"
        )

        result = CategoryService.create_category(
            db=session, category_in=category_data
        )

        assert result.name == "Technology"
        assert result.slug == "technology"
        assert result.is_active is True

    def test_create_category_duplicate_slug(self, db: Session):
        """Test duplicate slug validation"""
        # Create first category
        CategoryService.create_category(
            db=session, category_in=CategoryCreate(name="Tech", slug="technology")
        )

        # Try to create duplicate
        with pytest.raises(HTTPException) as exc_info:
            CategoryService.create_category(
                db=session,
                category_in=CategoryCreate(name="Technology", slug="technology"),
            )

        assert exc_info.value.status_code == 400
        assert "already exists" in exc_info.value.detail

    def test_get_category_by_slug(self, db: Session):
        """Test getting category by slug"""
        # Create category
        category = CategoryService.create_category(
            db=session, category_in=CategoryCreate(name="Python", slug="python")
        )

        # Get by slug
        result = CategoryService.get_category_by_slug(db=session, slug="python")

        assert result is not None
        assert result.id == category.id
        assert result.name == "Python"


class TestTagService:
    """Test tag service functionality"""

    def test_create_tag_success(self, db: Session):
        """Test successful tag creation"""
        tag_data = TagCreate(
            name="Python", slug="python", description="Python programming"
        )

        result = TagService.create_tag(db=session, tag_in=tag_data)

        assert result.name == "Python"
        assert result.slug == "python"
        assert result.is_active is True

    def test_create_tag_duplicate_slug(self, db: Session):
        """Test duplicate slug validation"""
        # Create first tag
        TagService.create_tag(
            db=session, tag_in=TagCreate(name="Python", slug="python")
        )

        # Try to create duplicate
        with pytest.raises(HTTPException) as exc_info:
            TagService.create_tag(
                db=session,
                tag_in=TagCreate(name="Python Programming", slug="python"),
            )

        assert exc_info.value.status_code == 400
        assert "already exists" in exc_info.value.detail


class TestBlogPostService:
    """Test blog post service functionality"""

    def test_create_post_success(self, db: Session):
        """Test successful post creation"""
        author_id = uuid.uuid4()

        post_data = BlogPostCreate(
            title="Test Post",
            slug="test-post",
            content="This is test content",
            excerpt="Test excerpt",
            status=PostStatus.DRAFT,
        )

        result = BlogPostService.create_post(
            db=session, post_in=post_data, author_id=author_id
        )

        assert result.title == "Test Post"
        assert result.slug == "test-post"
        assert result.author_id == author_id
        assert result.status == PostStatus.DRAFT

    def test_create_post_duplicate_slug(self, db: Session):
        """Test duplicate slug validation"""
        author_id = uuid.uuid4()

        # Create first post
        BlogPostService.create_post(
            db=session,
            post_in=BlogPostCreate(
                title="First Post", slug="test-post", content="Content"
            ),
            author_id=author_id,
        )

        # Try to create duplicate
        with pytest.raises(HTTPException) as exc_info:
            BlogPostService.create_post(
                db=session,
                post_in=BlogPostCreate(
                    title="Second Post", slug="test-post", content="Different content"
                ),
                author_id=author_id,
            )

        assert exc_info.value.status_code == 400
        assert "already exists" in exc_info.value.detail

    def test_create_post_with_category(self, db: Session):
        """Test post creation with category"""
        author_id = uuid.uuid4()

        # Create category first
        category = CategoryService.create_category(
            db=session, category_in=CategoryCreate(name="Tech", slug="tech")
        )

        post_data = BlogPostCreate(
            title="Tech Post",
            slug="tech-post",
            content="Tech content",
            category_id=category.id,
        )

        result = BlogPostService.create_post(
            db=session, post_in=post_data, author_id=author_id
        )

        assert result.category_id == category.id

    def test_create_post_with_invalid_category(self, db: Session):
        """Test post creation with invalid category"""
        author_id = uuid.uuid4()
        invalid_category_id = uuid.uuid4()

        post_data = BlogPostCreate(
            title="Test Post",
            slug="test-post",
            content="Content",
            category_id=invalid_category_id,
        )

        with pytest.raises(HTTPException) as exc_info:
            BlogPostService.create_post(
                db=session, post_in=post_data, author_id=author_id
            )

        assert exc_info.value.status_code == 400
        assert "Category not found" in exc_info.value.detail

    def test_get_post_by_slug(self, db: Session):
        """Test getting post by slug"""
        author_id = uuid.uuid4()

        # Create post
        post = BlogPostService.create_post(
            db=session,
            post_in=BlogPostCreate(
                title="Slug Test", slug="slug-test", content="Content"
            ),
            author_id=author_id,
        )

        # Get by slug
        result = BlogPostService.get_post_by_slug(db=session, slug="slug-test")

        assert result is not None
        assert result.id == post.id
        assert result.title == "Slug Test"

    def test_increment_view_count(self, db: Session):
        """Test view count increment"""
        author_id = uuid.uuid4()

        # Create post
        post = BlogPostService.create_post(
            db=session,
            post_in=BlogPostCreate(
                title="View Test", slug="view-test", content="Content"
            ),
            author_id=author_id,
        )

        initial_count = post.view_count

        # Increment view count
        success = BlogPostService.increment_view_count(db=session, post_id=post.id)

        assert success is True

        # Refresh and check
        session.refresh(post)
        assert post.view_count == initial_count + 1


class TestCommentService:
    """Test comment service functionality"""

    def test_create_comment_success(self, db: Session):
        """Test successful comment creation"""
        author_id = uuid.uuid4()

        # Create a published post first
        post = BlogPostService.create_post(
            db=session,
            post_in=BlogPostCreate(
                title="Comment Test",
                slug="comment-test",
                content="Content",
                status=PostStatus.PUBLISHED,
                published_at=datetime.now(),
            ),
            author_id=author_id,
        )

        comment_data = CommentCreate(
            content="This is a test comment",
            author_name="John Doe",
            author_email="john@example.com",
            post_id=post.id,
        )

        result = CommentService.create_comment(db=session, comment_in=comment_data)

        assert result.content == "This is a test comment"
        assert result.author_name == "John Doe"
        assert result.post_id == post.id
        assert result.status == CommentStatus.PENDING

    def test_create_comment_invalid_post(self, db: Session):
        """Test comment creation with invalid post"""
        invalid_post_id = uuid.uuid4()

        comment_data = CommentCreate(
            content="Test comment",
            author_name="John Doe",
            author_email="john@example.com",
            post_id=invalid_post_id,
        )

        with pytest.raises(HTTPException) as exc_info:
            CommentService.create_comment(db=session, comment_in=comment_data)

        assert exc_info.value.status_code == 400
        assert "Post not found" in exc_info.value.detail

    def test_moderate_comment(self, db: Session):
        """Test comment moderation"""
        author_id = uuid.uuid4()
        moderator_id = uuid.uuid4()

        # Create post and comment
        post = BlogPostService.create_post(
            db=session,
            post_in=BlogPostCreate(
                title="Moderation Test",
                slug="moderation-test",
                content="Content",
                status=PostStatus.PUBLISHED,
                published_at=datetime.now(),
            ),
            author_id=author_id,
        )

        comment = CommentService.create_comment(
            db=session,
            comment_in=CommentCreate(
                content="Test comment",
                author_name="Jane Doe",
                author_email="jane@example.com",
                post_id=post.id,
            ),
        )

        # Moderate comment
        result = CommentService.moderate_comment(
            db=session,
            comment_id=comment.id,
            status=CommentStatus.APPROVED,
            moderated_by_id=moderator_id,
        )

        assert result is not None
        assert result.status == CommentStatus.APPROVED
        assert result.moderated_by_id == moderator_id
        assert result.moderated_at is not None


class TestBlogStatsService:
    """Test blog statistics service"""

    def test_get_blog_stats(self, db: Session):
        """Test blog statistics generation"""
        author_id = uuid.uuid4()

        # Create some test data
        category = CategoryService.create_category(
            db=session, category_in=CategoryCreate(name="Test", slug="test")
        )

        tag = TagService.create_tag(
            db=session, tag_in=TagCreate(name="Test", slug="test")
        )

        # Create posts
        draft_post = BlogPostService.create_post(
            db=session,
            post_in=BlogPostCreate(
                title="Draft Post",
                slug="draft-post",
                content="Content",
                status=PostStatus.DRAFT,
            ),
            author_id=author_id,
        )

        published_post = BlogPostService.create_post(
            db=session,
            post_in=BlogPostCreate(
                title="Published Post",
                slug="published-post",
                content="Content",
                status=PostStatus.PUBLISHED,
                published_at=datetime.now(),
            ),
            author_id=author_id,
        )

        # Create comment
        CommentService.create_comment(
            db=session,
            comment_in=CommentCreate(
                content="Test comment",
                author_name="John Doe",
                author_email="john@example.com",
                post_id=published_post.id,
            ),
        )

        # Get stats
        stats = BlogStatsService.get_blog_stats(db=session)

        assert stats.total_posts >= 2
        assert stats.published_posts >= 1
        assert stats.draft_posts >= 1
        assert stats.total_comments >= 1
        assert stats.pending_comments >= 1
        assert stats.total_categories >= 1
        assert stats.total_tags >= 1
