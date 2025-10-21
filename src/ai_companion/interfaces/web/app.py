"""FastAPI application for Rose the Healer Shaman web interface."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from ai_companion.core.backup import backup_manager
from ai_companion.core.error_responses import (
    ai_companion_error_handler,
    global_exception_handler,
    validation_error_handler,
)
from ai_companion.core.exceptions import AICompanionError
from ai_companion.core.logging_config import configure_logging, get_logger
from ai_companion.core.session_cleanup import cleanup_old_sessions
from ai_companion.interfaces.web.middleware import RequestIDMiddleware, SecurityHeadersMiddleware
from ai_companion.interfaces.web.routes import health, metrics as metrics_route, session, voice
from ai_companion.settings import settings

# Configure structured logging before any other imports
configure_logging()

logger = get_logger(__name__)

# Path to React frontend build directory
FRONTEND_BUILD_DIR = Path(__file__).parent.parent.parent.parent.parent / "frontend" / "build"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    logger.info("app_starting", service="rose_web_interface")
    
    # Initialize scheduler for background jobs
    scheduler = AsyncIOScheduler()
    
    # Schedule automatic audio file cleanup (runs every hour)
    scheduler.add_job(
        voice.cleanup_old_audio_files,
        'interval',
        hours=1,
        args=[24],  # Clean files older than 24 hours
        id='audio_cleanup',
        name='Cleanup old audio files',
        replace_existing=True
    )
    
    # Schedule automatic database backups (runs daily at 2 AM)
    scheduler.add_job(
        backup_manager.backup_database,
        'cron',
        hour=2,
        minute=0,
        args=[7],  # Keep 7 days of backups
        id='database_backup',
        name='Daily database backup',
        replace_existing=True
    )
    
    # Schedule automatic session cleanup (runs daily at 3 AM)
    scheduler.add_job(
        cleanup_old_sessions,
        'cron',
        hour=3,
        minute=0,
        args=[settings.SESSION_RETENTION_DAYS],
        id='session_cleanup',
        name='Daily session cleanup',
        replace_existing=True
    )
    
    # Start the scheduler
    scheduler.start()
    logger.info("scheduler_started", jobs=["audio_cleanup", "database_backup", "session_cleanup"])
    
    yield
    
    # Shutdown scheduler
    scheduler.shutdown()
    logger.info("app_shutdown", service="rose_web_interface")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Rose the Healer Shaman API",
        description="Voice-first AI grief counselor and holistic healing companion. "
                    "Provides conversational AI interactions with memory persistence, "
                    "voice processing, and therapeutic support.",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/v1/docs" if settings.ENABLE_API_DOCS else None,
        redoc_url="/api/v1/redoc" if settings.ENABLE_API_DOCS else None,
        openapi_url="/api/v1/openapi.json" if settings.ENABLE_API_DOCS else None,
    )
    
    # Configure request size limits to prevent memory exhaustion
    # This is set at the application level and applies to all endpoints
    app.state.max_request_size = settings.MAX_REQUEST_SIZE
    logger.info("request_size_limit_configured", max_size_mb=settings.MAX_REQUEST_SIZE / 1024 / 1024)
    
    if settings.ENABLE_API_DOCS:
        logger.info("api_documentation_enabled", docs_url="/api/v1/docs", redoc_url="/api/v1/redoc")
    else:
        logger.info("api_documentation_disabled")

    # Add request ID middleware (should be first to track all requests)
    app.add_middleware(RequestIDMiddleware)
    logger.info("request_id_middleware_enabled")
    
    # Add request size limit middleware
    @app.middleware("http")
    async def limit_request_size(request: Request, call_next):
        """Middleware to enforce request size limits."""
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > settings.MAX_REQUEST_SIZE:
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "request_too_large",
                        "message": f"Request body too large. Maximum size is {settings.MAX_REQUEST_SIZE / 1024 / 1024}MB",
                        "max_size_bytes": settings.MAX_REQUEST_SIZE
                    }
                )
        return await call_next(request)
    
    # Configure CORS with environment-based origins
    allowed_origins = settings.get_allowed_origins()
    logger.info("cors_configured", allowed_origins=allowed_origins)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )
    
    # Add security headers middleware
    if settings.ENABLE_SECURITY_HEADERS:
        app.add_middleware(SecurityHeadersMiddleware)
        logger.info("security_headers_enabled")
    
    # Configure rate limiting
    if settings.RATE_LIMIT_ENABLED:
        limiter = Limiter(key_func=get_remote_address)
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        logger.info("rate_limiting_enabled", requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)
    else:
        # Create a no-op limiter if rate limiting is disabled
        app.state.limiter = None
        logger.info("rate_limiting_disabled")

    # Register exception handlers
    app.add_exception_handler(AICompanionError, ai_companion_error_handler)
    app.add_exception_handler(ValueError, validation_error_handler)
    app.add_exception_handler(Exception, global_exception_handler)
    logger.info("exception_handlers_registered")

    # Register API routes with v1 versioning
    app.include_router(health.router, prefix="/api/v1", tags=["Health"])
    app.include_router(session.router, prefix="/api/v1", tags=["Session Management"])
    app.include_router(voice.router, prefix="/api/v1", tags=["Voice Processing"])
    app.include_router(metrics_route.router, prefix="/api/v1", tags=["Metrics"])
    
    # Maintain backward compatibility with non-versioned routes (deprecated)
    app.include_router(health.router, prefix="/api", tags=["Health (Deprecated)"], deprecated=True)
    app.include_router(session.router, prefix="/api", tags=["Session Management (Deprecated)"], deprecated=True)
    app.include_router(voice.router, prefix="/api", tags=["Voice Processing (Deprecated)"], deprecated=True)
    app.include_router(metrics_route.router, prefix="/api", tags=["Metrics (Deprecated)"], deprecated=True)
    
    logger.info("api_routes_registered", version="v1", backward_compatible=True)

    # Serve React frontend static files (if build directory exists)
    if FRONTEND_BUILD_DIR.exists():
        logger.info("frontend_serving_enabled", build_dir=str(FRONTEND_BUILD_DIR))

        # Mount static assets (JS, CSS, images, etc.) with cache headers
        # Static files are immutable and can be cached for 1 year
        app.mount("/static", StaticFiles(directory=FRONTEND_BUILD_DIR / "static", html=False), name="static")
        
        # Add cache headers for static files
        @app.middleware("http")
        async def add_cache_headers(request: Request, call_next):
            """Add cache headers for static assets."""
            response = await call_next(request)
            
            # Cache static assets (JS, CSS, images) for 1 year
            if request.url.path.startswith("/static/"):
                response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            # Don't cache API responses
            elif request.url.path.startswith("/api/"):
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            # Cache index.html for 5 minutes (allows updates to propagate quickly)
            elif request.url.path == "/" or request.url.path.endswith(".html"):
                response.headers["Cache-Control"] = "public, max-age=300"
            
            return response

        # Catch-all route for React Router (SPA)
        @app.get("/{full_path:path}")
        async def serve_react_app(request: Request, full_path: str):
            """Serve React app for all non-API routes."""
            # Don't serve React app for API routes
            if full_path.startswith("api/"):
                return {"detail": "Not found"}

            # Serve index.html for all other routes (React Router handles routing)
            index_path = FRONTEND_BUILD_DIR / "index.html"
            if index_path.exists():
                return FileResponse(index_path)

            return {"detail": "Frontend not found"}

    else:
        logger.warning("frontend_build_not_found", build_dir=str(FRONTEND_BUILD_DIR))
        logger.warning("frontend_not_served")

    return app


app = create_app()
