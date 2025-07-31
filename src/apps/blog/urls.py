"""
Blog App URLs - Route configuration
"""

from fastapi import APIRouter
from src.apps.blog.views import router as blog_router

# Create app router with prefix
router = APIRouter(
    prefix="/blog",
    tags=["blog"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)

# Include all blog routes
router.include_router(blog_router)


# Health check endpoint
@router.get("/health")
def blog_health_check():
    """Blog app health check"""
    return {"status": "healthy", "app": "blog"}
