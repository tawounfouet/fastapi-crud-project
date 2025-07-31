"""
Users App - User Management Domain

This app handles user authentication, user management, and user-related operations.
Provides REST API for user registration, authentication, profile management, and admin operations.
"""

__version__ = "1.0.0"
__author__ = "FastAPI CRUD Team"
__description__ = "User management and authentication system"

# Export main components for easy importing
from .models import User
from .services import UserService

__all__ = ["User", "UserService"]
