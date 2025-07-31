"""
Auth URL Configuration

This module configures the FastAPI router for authentication endpoints.
"""

from fastapi import APIRouter

from .views import router as views_router

# Export the views router directly (it already has proper tags and prefix)
router = views_router
