"""FastAPI application for Rose the Healer Shaman web interface."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ai_companion.interfaces.web.routes import health, session, voice

logger = logging.getLogger(__name__)

# Path to React frontend build directory
FRONTEND_BUILD_DIR = Path(__file__).parent.parent.parent.parent.parent / "frontend" / "build"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    logger.info("Starting Rose the Healer Shaman web interface")
    yield
    logger.info("Shutting down Rose the Healer Shaman web interface")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Rose the Healer Shaman",
        description="AI grief counselor and holistic healing companion",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
