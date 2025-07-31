"""
Blog App - Content Management Domain

This app handles blog posts, comments, categories, and tags.
Provides REST API for content management and public content access.
"""

__version__ = "1.0.0"
__author__ = "Your Team"
__description__ = "Blog content management system"

# Export main components for easy importing
from .models import BlogPost, Comment, Category, Tag
from .services import BlogPostService, CommentService, CategoryService

# Note: views import is removed to avoid circular import issues
# from .views import router as blog_router

__all__ = [
    "BlogPost",
    "Comment",
    "Category",
    "Tag",
    "BlogPostService",
    "CommentService",
    "CategoryService",
    # "blog_router",  # Removed to avoid circular imports
]
