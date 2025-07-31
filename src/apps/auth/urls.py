"""
Auth URL Configuration

This module configures the FastAPI router for authentication endpoints.
"""

from fastapi import APIRouter
from .views import router as views_router

# Create auth app router
router = APIRouter(
    tags=["Authentication"],
    responses={
        401: {"description": "Unauthorized"},
        429: {"description": "Too Many Requests"},
    },
)

# Include views router (already has /auth prefix)
router.include_router(views_router)
