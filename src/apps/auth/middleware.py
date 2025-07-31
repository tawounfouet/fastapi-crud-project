"""
Auth Middleware Module

This module contains middleware for authentication and authorization.
"""

import time
from collections.abc import Callable

from fastapi import HTTPException, Request, Response, status
from fastapi.security.utils import get_authorization_scheme_param

from src.apps.users.models import User
from src.core.database import get_session
from src.core.security import decode_access_token


class AuthenticationMiddleware:
    """
    Authentication middleware that adds user context to requests.

    This middleware:
    - Extracts and validates JWT tokens
    - Adds user information to request state
    - Handles authentication errors gracefully
    - Provides rate limiting for authentication attempts
    """

    def __init__(
        self,
        app: Callable,
        exempt_paths: list[str] | None = None,
        rate_limit_attempts: int = 100,
        rate_limit_window: int = 3600,  # 1 hour
    ):
        self.app = app
        self.exempt_paths = exempt_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/auth/login",
            "/auth/signup",
            "/auth/password-recovery",
            "/auth/reset-password",
            "/login/access-token",  # Legacy
        ]
        self.rate_limit_attempts = rate_limit_attempts
        self.rate_limit_window = rate_limit_window
        self.rate_limit_storage = {}  # In production, use Redis

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process the request through authentication middleware."""

        # Check if path is exempt from authentication
        if self._is_exempt_path(request.url.path):
            response = await call_next(request)
            return response

        # Rate limiting check
        client_ip = self._get_client_ip(request)
        if not self._check_rate_limit(client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many authentication attempts",
            )

        # Extract and validate token
        token = self._extract_token(request)
        user = None

        if token:
            try:
                user = await self._validate_token(token)
            except HTTPException:
                # Token is invalid, but we'll let the endpoint handle it
                pass

        # Add user context to request state
        request.state.user = user
        request.state.authenticated = user is not None
        request.state.is_superuser = user.is_superuser if user else False

        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        return response

    def _is_exempt_path(self, path: str) -> bool:
        """Check if the path is exempt from authentication."""
        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return True
        return False

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers (for load balancers/proxies)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct client IP
        if request.client:
            return request.client.host

        return "unknown"

    def _check_rate_limit(self, client_ip: str) -> bool:
        """Check if client is within rate limits."""
        now = time.time()
        window_start = now - self.rate_limit_window

        # Clean old entries
        if client_ip in self.rate_limit_storage:
            self.rate_limit_storage[client_ip] = [
                timestamp
                for timestamp in self.rate_limit_storage[client_ip]
                if timestamp > window_start
            ]
        else:
            self.rate_limit_storage[client_ip] = []

        # Check if within limits
        if len(self.rate_limit_storage[client_ip]) >= self.rate_limit_attempts:
            return False

        # Add current attempt
        self.rate_limit_storage[client_ip].append(now)
        return True

    def _extract_token(self, request: Request) -> str | None:
        """Extract JWT token from request."""
        # Check Authorization header
        authorization = request.headers.get("Authorization")
        if authorization:
            scheme, token = get_authorization_scheme_param(authorization)
            if scheme.lower() == "bearer":
                return token

        # Check query parameter (for WebSocket or special cases)
        token = request.query_params.get("token")
        if token:
            return token

        # Check cookies (if using cookie-based auth)
        token = request.cookies.get("access_token")
        if token:
            return token

        return None

    async def _validate_token(self, token: str) -> User | None:
        """Validate JWT token and return user."""
        try:
            # Decode token
            payload = decode_access_token(token)
            if not payload:
                return None

            user_id = payload.get("sub")
            if not user_id:
                return None

            # Get user from database
            session = next(get_session())
            try:
                user = session.get(User, user_id)
                if user and user.is_active:
                    return user
            finally:
                session.close()

            return None

        except Exception:
            return None


class CORSAndSecurityMiddleware:
    """
    CORS and Security middleware.

    Handles:
    - CORS headers
    - Security headers
    - Content Security Policy
    """

    def __init__(
        self,
        app: Callable,
        allow_origins: list[str] = None,
        allow_credentials: bool = True,
        allow_methods: list[str] = None,
        allow_headers: list[str] = None,
    ):
        self.app = app
        self.allow_origins = allow_origins or ["*"]
        self.allow_credentials = allow_credentials
        self.allow_methods = allow_methods or ["*"]
        self.allow_headers = allow_headers or ["*"]

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process CORS and security headers."""

        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            self._add_cors_headers(response, request)
            return response

        # Process request
        response = await call_next(request)

        # Add CORS headers
        self._add_cors_headers(response, request)

        # Add security headers
        self._add_security_headers(response)

        return response

    def _add_cors_headers(self, response: Response, request: Request) -> None:
        """Add CORS headers to response."""
        origin = request.headers.get("origin")

        if self.allow_origins == ["*"] or (origin and origin in self.allow_origins):
            response.headers["Access-Control-Allow-Origin"] = origin or "*"

        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"

        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        response.headers["Access-Control-Max-Age"] = "86400"  # 24 hours

    def _add_security_headers(self, response: Response) -> None:
        """Add security headers to response."""
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp

        # Additional security headers
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=(), usb=(), "
            "magnetometer=(), gyroscope=(), accelerometer=(), ambient-light-sensor=(), "
            "autoplay=()"
        )


class RequestLoggingMiddleware:
    """
    Request logging middleware for audit and monitoring.
    """

    def __init__(self, app: Callable, log_level: str = "INFO"):
        self.app = app
        self.log_level = log_level

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Log request details."""
        import logging

        logger = logging.getLogger("auth.requests")

        # Start timing
        start_time = time.time()

        # Extract request info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        method = request.method
        url = str(request.url)

        # Get user if available
        user_id = "anonymous"
        if hasattr(request.state, "user") and request.state.user:
            user_id = request.state.user.id

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log request
        logger.info(
            f"{method} {url} - {response.status_code} - "
            f"{duration:.3f}s - IP: {client_ip} - User: {user_id} - "
            f"UA: {user_agent[:100]}"
        )

        return response
