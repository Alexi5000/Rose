"""Security middleware for FastAPI application."""

import logging
import os
import stat
from typing import Callable
from uuid import uuid4

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add unique request ID to each request for tracing."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request ID to request state and response headers.

        Args:
            request: Incoming request
            call_next: Next middleware/handler in chain

        Returns:
            Response with X-Request-ID header
        """
        # Generate unique request ID
        request_id = str(uuid4())

        # Store in request state for access in route handlers
        request.state.request_id = request_id

        # Bind request ID to structlog context for all logs in this request
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response.

        Args:
            request: Incoming request
            call_next: Next middleware/handler in chain

        Returns:
            Response with security headers added
        """
        response = await call_next(request)

        # Content Security Policy - restrict resource loading
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "media-src 'self' blob:; "
            "frame-ancestors 'none';"
        )

        # HTTP Strict Transport Security - enforce HTTPS
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(self), camera=()"

        return response


def set_secure_file_permissions(file_path: str) -> None:
    """Set secure permissions on a file (owner read/write only).

    Args:
        file_path: Path to the file to secure
    """
    try:
        # Set permissions to 0o600 (owner read/write only)
        os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)
        logger.debug(f"Set secure permissions on {file_path}")
    except Exception as e:
        logger.error(f"Failed to set secure permissions on {file_path}: {e}")


def create_secure_temp_file(directory: str, filename: str) -> str:
    """Create a temporary file with secure permissions.

    Args:
        directory: Directory to create file in
        filename: Name of the file

    Returns:
        Full path to the created file
    """
    file_path = os.path.join(directory, filename)

    # Create file with secure permissions
    # Use os.open with specific flags for secure creation
    fd = os.open(file_path, os.O_CREAT | os.O_WRONLY | os.O_EXCL, stat.S_IRUSR | stat.S_IWUSR)
    os.close(fd)

    logger.debug(f"Created secure temp file: {file_path}")
    return file_path
