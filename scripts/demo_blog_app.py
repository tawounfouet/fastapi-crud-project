#!/usr/bin/env python3
"""
Blog App Demo Script

This script demonstrates the Blog app functionality by:
1. Creating sample blog content
2. Testing CRUD operations
3. Verifying the API endpoints
"""

import sys
import os
import asyncio
import httpx
from datetime import datetime, timezone

# Add the src directory to Python path (go up one level from scripts/ to root, then into src/)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from sqlmodel import Session, select
from src.core.database import engine
from src.core.config import settings
from src.apps.blog.models import BlogPost, Category, Tag, Comment, PostStatus
from src.apps.blog.services import (
    BlogPostService,
    CategoryService,
    TagService,
    CommentService,
)
from src.apps.blog.schemas import (
    CategoryCreate,
    TagCreate,
    BlogPostCreate,
    CommentCreate,
)
from src.apps.users.models import User


async def get_admin_token(base_url: str) -> str:
    """Get authentication token for admin user"""
    async with httpx.AsyncClient() as client:
        login_data = {
            "username": str(settings.FIRST_SUPERUSER),
            "password": str(settings.FIRST_SUPERUSER_PASSWORD),
        }

        response = await client.post(
            f"{base_url}/api/v1/auth/login/access-token",
            data=login_data,
        )

        if response.status_code == 200:
            token_data = response.json()
            return token_data["access_token"]
        else:
            raise Exception(f"Login failed: {response.status_code} - {response.text}")


async def test_blog_endpoints():
    """Test Blog app API endpoints"""
    base_url = "http://localhost:8000"

    try:
        # Get admin authentication token
        print("🔐 Authenticating as admin user...")
        token = await get_admin_token(base_url)
        headers = {"Authorization": f"Bearer {token}"}
        print(f"✅ Successfully authenticated as: {settings.FIRST_SUPERUSER}")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("   Make sure the server is running and admin user exists")
        return False

    async with httpx.AsyncClient() as client:
        try:
            # Test health endpoint
            response = await client.get(f"{base_url}/api/v1/blog/health")
            print(f"✅ Health check: {response.status_code} - {response.json()}")

            # Test categories endpoint (public access)
            response = await client.get(f"{base_url}/api/v1/blog/categories/")
            print(f"✅ Categories endpoint: {response.status_code}")

            # Test posts endpoint (public access)
            response = await client.get(f"{base_url}/api/v1/blog/posts/")
            print(f"✅ Posts endpoint: {response.status_code}")

            # Test tags endpoint
            response = await client.get(f"{base_url}/api/v1/blog/tags/")
            print(f"✅ Tags endpoint: {response.status_code}")

            # Test authenticated endpoints
            print("\n🔒 Testing authenticated endpoints...")

            # Create a category via API
            import time

            timestamp = int(time.time())
            category_data = {
                "name": f"API Technology {timestamp}",
                "slug": f"api-technology-{timestamp}",
                "description": "Technology posts created via API",
            }
            response = await client.post(
                f"{base_url}/api/v1/blog/categories/",
                headers=headers,
                json=category_data,
            )
            if response.status_code == 200:
                print(f"✅ Created category via API: {response.json()['name']}")
            else:
                print(f"⚠️  Category creation status: {response.status_code}")

            # Create a tag via API
            tag_data = {
                "name": f"API Testing {timestamp}",
                "slug": f"api-testing-{timestamp}",
                "description": "Tag for API testing posts",
            }
            response = await client.post(
                f"{base_url}/api/v1/blog/tags/",
                headers=headers,
                json=tag_data,
            )
            if response.status_code == 200:
                print(f"✅ Created tag via API: {response.json()['name']}")
            else:
                print(f"⚠️  Tag creation status: {response.status_code}")

            # Create a blog post via API
            post_data = {
                "title": f"API Demo Post {timestamp}",
                "slug": f"api-demo-post-{timestamp}",
                "content": "This post was created via the API to demonstrate functionality.",
                "excerpt": "API demo post excerpt",
                "status": "published",
            }
            response = await client.post(
                f"{base_url}/api/v1/blog/posts/",
                headers=headers,
                json=post_data,
            )
            if response.status_code == 200:
                print(f"✅ Created post via API: {response.json()['title']}")
            else:
                print(f"⚠️  Post creation status: {response.status_code}")

        except httpx.RequestError as e:
            print(f"❌ API test failed: {e}")
            return False

    return True


def test_blog_models():
    """Test Blog app models and services"""
    with Session(engine) as session:
        try:
            # Find the superuser to use as author
            user = session.exec(
                select(User).where(User.email == settings.FIRST_SUPERUSER)
            ).first()

            if not user:
                print("❌ No superuser found for testing")
                print(f"   Expected superuser email: {settings.FIRST_SUPERUSER}")
                print("   Run 'make db-init' to create initial data")
                return False

            print(f"✅ Using user: {user.email}")

            # Test Category creation
            category_data = CategoryCreate(
                name="Demo Technology",
                slug="demo-technology",
                description="Tech-related blog posts for demo",
            )
            try:
                category = CategoryService.create_category(
                    session=session, category_in=category_data
                )
                print(f"✅ Created category: {category.name}")
            except Exception as e:
                print(f"⚠️  Category already exists or error: {str(e)}")
                # Get existing category for further tests
                from src.apps.blog.models import Category

                category = session.exec(
                    select(Category).where(Category.slug == "demo-technology")
                ).first()
                if not category:
                    # If demo-technology doesn't exist, try to get any category
                    category = session.exec(select(Category)).first()
                if category:
                    print(f"✅ Using existing category: {category.name}")

            # Test Tag creation
            tag_data = TagCreate(
                name="Demo Python",
                slug="demo-python",
                description="Python programming for demo",
            )
            try:
                tag = TagService.create_tag(session=session, tag_in=tag_data)
                print(f"✅ Created tag: {tag.name}")
            except Exception as e:
                print(f"⚠️  Tag already exists or error: {str(e)}")
                # Get existing tag for further tests
                from src.apps.blog.models import Tag

                tag = session.exec(select(Tag).where(Tag.slug == "demo-python")).first()
                if not tag:
                    # If demo-python doesn't exist, try to get any tag
                    tag = session.exec(select(Tag)).first()
                if tag:
                    print(f"✅ Using existing tag: {tag.name}")

            # Test BlogPost creation
            import time

            timestamp = int(time.time())
            post_data = BlogPostCreate(
                title=f"Demo Blog Post {timestamp}",
                slug=f"demo-blog-post-{timestamp}",
                content="This is a demo blog post created by the Blog app demo script!",
                excerpt="Demo blog post created for testing",
                status=PostStatus.PUBLISHED,
                category_id=category.id if category else None,
                published_at=datetime.now(timezone.utc),
            )
            try:
                post = BlogPostService.create_post(
                    session=session, post_in=post_data, author_id=user.id
                )
                print(f"✅ Created blog post: {post.title}")
            except Exception as e:
                print(f"⚠️  Blog post creation error: {str(e)}")
                return False

            # Test Comment creation
            comment_data = CommentCreate(
                content="Great first post!",
                author_name="Demo User",
                author_email="demo@example.com",
                post_id=post.id,
            )
            comment = CommentService.create_comment(
                session=session, comment_in=comment_data
            )
            print(f"✅ Created comment: {comment.content[:30]}...")

            # Test retrieval
            retrieved_post = BlogPostService.get_post(session=session, post_id=post.id)
            if retrieved_post:
                print(f"✅ Retrieved post: {retrieved_post.title}")

            # Test business methods
            is_published = post.is_published()
            print(f"✅ Post is published: {is_published}")

            # Test view count increment
            BlogPostService.increment_view_count(session=session, post_id=post.id)
            updated_post = BlogPostService.get_post(session=session, post_id=post.id)
            print(f"✅ View count after increment: {updated_post.view_count}")

            return True

        except Exception as e:
            print(f"❌ Model test failed: {e}")
            return False


def main():
    """Main demo function"""
    print("🚀 Blog App Demo Starting...")
    print("=" * 50)
    print(f"🔐 Will authenticate as: {settings.FIRST_SUPERUSER}")
    print("💡 Make sure the server is running: make dev")
    print("💡 Make sure database is initialized: make db-init")

    # Test models and services
    print("\n📊 Testing Models and Services:")
    models_ok = test_blog_models()

    # Test API endpoints
    print("\n🌐 Testing API Endpoints:")
    print("Note: Make sure the FastAPI server is running on http://localhost:8000")
    try:
        endpoints_ok = asyncio.run(test_blog_endpoints())
    except Exception as e:
        print(f"❌ Could not test endpoints: {e}")
        endpoints_ok = False

    print("\n" + "=" * 50)
    if models_ok and endpoints_ok:
        print("🎉 Blog App Demo Completed Successfully!")
        print("\n📝 Summary of created content:")
        print("- ✅ Technology category (via service)")
        print("- ✅ Python tag (via service)")
        print("- ✅ Welcome blog post (via service)")
        print("- ✅ Demo comment (via service)")
        print("- ✅ API Technology category (via API)")
        print("- ✅ API Testing tag (via API)")
        print("- ✅ API Demo Post (via API)")
        print("\n🔗 You can now:")
        print("- Visit http://localhost:8000/docs to explore the API")
        print("- Test the blog endpoints via the interactive documentation")
        print("- Create more content using the API")
        print("- View posts at http://localhost:8000/api/v1/blog/posts/")
    elif models_ok:
        print("✅ Models and Services work correctly!")
        print("❌ API endpoints could not be tested (server not running?)")
        print("💡 Start the server with: make dev")
    else:
        print("❌ Demo failed - check the error messages above")
        print("💡 Common issues:")
        print("   - No superuser exists: run 'make db-init'")
        print("   - Database not ready: run 'make db-init'")
        print("   - Blog models not migrated: run 'make migrate'")


if __name__ == "__main__":
    main()
