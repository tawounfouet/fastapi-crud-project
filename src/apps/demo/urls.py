"""
Demo App URLs - Route configuration
Similar to Django urls.py
"""

from fastapi import APIRouter

from src.apps.demo.views import router as demo_router

# Create app-specific router with prefix
router = APIRouter(
    prefix="/demo",
    tags=["demo"],
    responses={404: {"description": "Not found"}},
)

# Include all demo routes
router.include_router(demo_router)
