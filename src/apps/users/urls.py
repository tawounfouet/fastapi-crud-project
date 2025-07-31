"""
User URL Configuration

This module configures the URL routing for the users app.
It exports the router that can be included in the main application.
"""

from .views import router

# Export the router for inclusion in main application
__all__ = ["router"]
