"""
Utility modules for the FastAPI CRUD application.

This package contains various utility functions organized by domain:
- email: Email sending and template rendering utilities
- auth: Authentication token and security utilities
- common: General purpose utility functions
"""

# Import commonly used utilities for convenience
from .email import (
    EmailData,
    generate_new_account_email,
    generate_reset_password_email,
    generate_test_email,
    render_email_template,
    send_email,
)
from .auth import (
    generate_password_reset_token,
    verify_password_reset_token,
)

__all__ = [
    # Email utilities
    "EmailData",
    "send_email",
    "render_email_template",
    "generate_test_email",
    "generate_reset_password_email",
    "generate_new_account_email",
    # Auth utilities
    "generate_password_reset_token",
    "verify_password_reset_token",
]
