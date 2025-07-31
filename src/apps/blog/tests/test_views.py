"""
Tests for blog app views/endpoints
"""

import pytest
import uuid
from datetime import datetime
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.core.config import settings


class TestCategoryEndpoints:
    """Test category API endpoints"""

    def test_create_category_success(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ) -> None:
        """Test successful category creation"""
        data = {
            "name": "Technology",
            "slug": "technology",
            "description": "Tech-related posts",
        }

        response = client.post(
            f"{settings.API_V1_STR}/blog/categories/",
            headers=superuser_token_headers,
            json=data,
        )

        assert response.status_code == 200
        content = response.json()
        assert content["name"] == "Technology"
        assert content["slug"] == "technology"
        assert content["is_active"] is True

    def test_create_category_permission_denied(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        """Test category creation requires admin permissions"""
        data = {"name": "Technology", "slug": "technology"}

        response = client.post(
            f"{settings.API_V1_STR}/blog/categories/",
            headers=normal_user_token_headers,
            json=data,
        )

        assert response.status_code == 403

    def test_get_categories_public(self, client: TestClient) -> None:
        """Test public access to categories list"""
        response = client.get(f"{settings.API_V1_STR}/blog/categories/")

        assert response.status_code == 200
        content = response.json()
        assert "items" in content
        assert "total" in content

    def test_get_category_by_id(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Test getting category by ID"""
        # First create a category
        create_data = {"name": "Python", "slug": "python"}

        create_response = client.post(
            f"{settings.API_V1_STR}/blog/categories/",
            headers=superuser_token_headers,
            json=create_data,
        )

        category_id = create_response.json()["id"]

        # Get the category
        response = client.get(f"{settings.API_V1_STR}/blog/categories/{category_id}")

        assert response.status_code == 200
        content = response.json()
        assert content["name"] == "Python"
        assert content["slug"] == "python"


class TestTagEndpoints:
    """Test tag API endpoints"""

    def test_create_tag_success(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Test successful tag creation"""
        data = {
            "name": "FastAPI",
            "slug": "fastapi",
            "description": "FastAPI framework",
        }

        response = client.post(
            f"{settings.API_V1_STR}/blog/tags/",
            headers=superuser_token_headers,
            json=data,
        )

        assert response.status_code == 200
        content = response.json()
        assert content["name"] == "FastAPI"
        assert content["slug"] == "fastapi"

    def test_get_tags_public(self, client: TestClient) -> None:
        """Test public access to tags list"""
        response = client.get(f"{settings.API_V1_STR}/blog/tags/")

        assert response.status_code == 200
        content = response.json()
        assert "items" in content
        assert "total" in content


class TestBlogPostEndpoints:
    """Test blog post API endpoints"""

    def test_create_post_success(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        """Test successful post creation"""
        data = {
            "title": "My First Blog Post",
            "slug": "my-first-blog-post",
            "content": "This is the content of my first blog post.",
            "excerpt": "First post excerpt",
            "status": "draft",
        }

        response = client.post(
            f"{settings.API_V1_STR}/blog/posts/",
            headers=normal_user_token_headers,
            json=data,
        )

        assert response.status_code == 200
        content = response.json()
        assert content["title"] == "My First Blog Post"
        assert content["slug"] == "my-first-blog-post"
        assert content["status"] == "draft"

    def test_create_post_validation_error(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        """Test post creation validation"""
        data = {
            "title": "",  # Invalid: empty title
            "slug": "invalid-slug!",  # Invalid: special characters
            "content": "",  # Invalid: empty content
        }

        response = client.post(
            f"{settings.API_V1_STR}/blog/posts/",
            headers=normal_user_token_headers,
            json=data,
        )

        assert response.status_code == 422

    def test_get_posts_public(self, client: TestClient) -> None:
        """Test public access to posts list"""
        response = client.get(f"{settings.API_V1_STR}/blog/posts/")

        assert response.status_code == 200
        content = response.json()
        assert "items" in content
        assert "total" in content

    def test_get_posts_with_filters(self, client: TestClient) -> None:
        """Test posts filtering"""
        response = client.get(
            f"{settings.API_V1_STR}/blog/posts/?published_only=true&limit=10"
        )

        assert response.status_code == 200
        content = response.json()
        assert isinstance(content["items"], list)

    def test_get_post_by_slug_not_found(self, client: TestClient) -> None:
        """Test getting non-existent post by slug"""
        response = client.get(f"{settings.API_V1_STR}/blog/posts/non-existent-slug")

        assert response.status_code == 404

    def test_update_post_permission_denied(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        """Test that users can only update their own posts"""
        # This would require creating a post by another user first
        # For now, test with a non-existent post
        fake_id = str(uuid.uuid4())

        data = {"title": "Updated Title"}

        response = client.put(
            f"{settings.API_V1_STR}/blog/posts/{fake_id}",
            headers=normal_user_token_headers,
            json=data,
        )

        assert response.status_code == 404


class TestCommentEndpoints:
    """Test comment API endpoints"""

    def test_create_comment_public(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Test public comment creation"""
        # First create a published post
        post_data = {
            "title": "Comment Test Post",
            "slug": "comment-test-post",
            "content": "This is a test post for comments.",
            "status": "published",
            "published_at": datetime.now().isoformat(),
        }

        post_response = client.post(
            f"{settings.API_V1_STR}/blog/posts/",
            headers=superuser_token_headers,
            json=post_data,
        )

        post_id = post_response.json()["id"]

        # Create comment
        comment_data = {
            "content": "This is a test comment.",
            "author_name": "John Doe",
            "author_email": "john@example.com",
            "post_id": post_id,
        }

        response = client.post(
            f"{settings.API_V1_STR}/blog/comments/",
            json=comment_data,
        )

        assert response.status_code == 200
        content = response.json()
        assert content["content"] == "This is a test comment."
        assert content["author_name"] == "John Doe"
        assert content["status"] == "pending"

    def test_get_comments_public(self, client: TestClient) -> None:
        """Test public access to comments"""
        response = client.get(f"{settings.API_V1_STR}/blog/comments/")

        assert response.status_code == 200
        content = response.json()
        assert "items" in content
        assert "total" in content

    def test_moderate_comment_admin_only(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        """Test comment moderation requires admin permissions"""
        fake_comment_id = str(uuid.uuid4())

        response = client.put(
            f"{settings.API_V1_STR}/blog/comments/{fake_comment_id}/moderate?status=approved",
            headers=normal_user_token_headers,
        )

        assert response.status_code == 403


class TestBlogStatsEndpoints:
    """Test blog statistics endpoints"""

    def test_get_blog_stats_admin_only(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ) -> None:
        """Test blog stats endpoint (admin only)"""
        response = client.get(
            f"{settings.API_V1_STR}/blog/stats/",
            headers=superuser_token_headers,
        )

        assert response.status_code == 200
        content = response.json()
        assert "total_posts" in content
        assert "published_posts" in content
        assert "total_comments" in content

    def test_get_blog_stats_permission_denied(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        """Test blog stats requires admin permissions"""
        response = client.get(
            f"{settings.API_V1_STR}/blog/stats/",
            headers=normal_user_token_headers,
        )

        assert response.status_code == 403


class TestBlogHealthCheck:
    """Test blog app health check"""

    def test_blog_health_check(self, client: TestClient) -> None:
        """Test blog health check endpoint"""
        response = client.get(f"{settings.API_V1_STR}/blog/health")

        assert response.status_code == 200
        content = response.json()
        assert content["status"] == "healthy"
        assert content["app"] == "blog"
