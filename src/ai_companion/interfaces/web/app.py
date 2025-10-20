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
from ai_companion.interfaces.web.middleware import SecurityHeadersMiddleware
from ai_companion.interfaces.web.routes import health, session, voice
from ai_companion.settings import settings

logger = logging.getLogger(__name__)

# Path to React frontend build directory
FRONTEND_BUILD_DIR = Path(__file__).parent.parent.parent.parent.parent / "frontend" / "build"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    logger.info("Starting Rose the Healer Shaman web interface")
    
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
    
    # Start the scheduler
    scheduler.start()
    logger.info("Background scheduler started - audio cleanup and database backup jobs scheduled")
    
    yield
    
    # Shutdown scheduler
    scheduler.shutdown()
    logger.info("Shutting down Rose the Healer Shaman web interface")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Rose the Healer Shaman",
        description="AI grief counselor and holistic healing companion",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Configure CORS with environment-based origins
    allowed_origins = settings.get_allowed_origins()
    logger.info(f"Configuring CORS with allowed origins: {allowed_origins}")
    
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
        logger.info("Security headers middleware enabled")
    
    # Configure rate limiting
    if settings.RATE_LIMIT_ENABLED:
        limiter = Limiter(key_func=get_remote_address)
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        logger.info(f"Rate limiting enabled: {settings.RATE_LIMIT_PER_MINUTE} requests/minute per IP")
    else:
        # Create a no-op limiter if rate limiting is disabled
        app.state.limiter = None
        logger.info("Rate limiting disabled")

    # Register API routes
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(session.router, prefix="/api", tags=["session"])
    app.include_router(voice.router, prefix="/api", tags=["voice"])

    # Serve React frontend static files (if build directory exists)
    if FRONTEND_BUILD_DIR.exists():
        logger.info(f"Serving React frontend from {FRONTEND_BUILD_DIR}")

        # Mount static assets (JS, CSS, images, etc.)
        app.mount("/static", StaticFiles(directory=FRONTEND_BUILD_DIR / "static"), name="static")

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
        logger.warning(f"Frontend build directory not found: {FRONTEND_BUILD_DIR}")
        logger.warning("React frontend will not be served. Build the frontend first.")

    return app


app = create_app()
