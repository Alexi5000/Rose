"""FastAPI application for Rose the Healer Shaman web interface."""

from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from ai_companion.config.server_config import (
    API_BASE_PATH,
    API_CACHE_SECONDS,
    API_DOCS_PATH,
    API_OPENAPI_PATH,
    API_REDOC_PATH,
    APP_DESCRIPTION,
    APP_TITLE,
    APP_VERSION,
    AUDIO_CLEANUP_INTERVAL_HOURS,
    AUDIO_CLEANUP_MAX_AGE_HOURS,
    DATABASE_BACKUP_CRON_HOUR,
    DATABASE_BACKUP_CRON_MINUTE,
    DATABASE_BACKUP_RETENTION_DAYS,
    DEV_ALLOWED_ORIGINS,
    FRONTEND_BUILD_DIR,
    HTML_CACHE_SECONDS,
    LOG_EMOJI_CONNECTION,
    LOG_EMOJI_ERROR,
    LOG_EMOJI_FRONTEND,
    LOG_EMOJI_STARTUP,
    LOG_EMOJI_SUCCESS,
    LOG_EMOJI_WARNING,
    MAX_REQUEST_SIZE_BYTES,
    RATE_LIMIT_ENABLED,
    RATE_LIMIT_REQUESTS_PER_MINUTE,
    SESSION_CLEANUP_CRON_HOUR,
    SESSION_CLEANUP_CRON_MINUTE,
    STATIC_ASSET_CACHE_SECONDS,
    WEB_SERVER_PORT,
)
from ai_companion.core.backup import backup_manager
from ai_companion.core.error_responses import (
    ai_companion_error_handler,
    global_exception_handler,
    validation_error_handler,
)
from ai_companion.core.exceptions import AICompanionError
from ai_companion.core.logging_config import configure_logging, get_logger
from ai_companion.core.monitoring_scheduler import scheduler as monitoring_scheduler
from ai_companion.core.session_cleanup import cleanup_old_sessions
from ai_companion.graph.graph import create_workflow_graph
from ai_companion.interfaces.web.middleware import RequestIDMiddleware, SecurityHeadersMiddleware
from ai_companion.interfaces.web.routes import admin, health, monitoring, session, voice, voice_websocket
from ai_companion.interfaces.web.routes import metrics as metrics_route
from ai_companion.settings import settings
from ai_companion.modules.memory.long_term.vector_store import get_vector_store
from ai_companion.modules.speech.text_to_speech import TextToSpeech

# Configure structured logging before any other imports
configure_logging()

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    logger.info("app_starting", emoji=LOG_EMOJI_STARTUP, service="rose_web_interface")

    # Validate external connectivity (Qdrant, DB)
    try:
        settings.validate_connectivity()
    except Exception:
        logger.warning("⚠️ Connectivity validation encountered issues; continuing in degraded mode", exc_info=True)

    # Initialize Qdrant collection and validate vector dimensions
    try:
        store = get_vector_store()
        initialized = store.initialize_collection()
        if initialized:
            logger.info("✅ Qdrant collection initialization succeeded")
        else:
            logger.warning("⚠️ Qdrant collection initialization returned False; check logs for details")
    except Exception:
        logger.warning("⚠️ Qdrant collection initialization check failed; continuing in degraded mode", exc_info=True)

    # Initialize scheduler for background jobs
    scheduler = AsyncIOScheduler()

    # Schedule automatic audio file cleanup (runs every hour)
    scheduler.add_job(
        voice.cleanup_old_audio_files,
        "interval",
        hours=AUDIO_CLEANUP_INTERVAL_HOURS,
        args=[AUDIO_CLEANUP_MAX_AGE_HOURS],
        id="audio_cleanup",
        name="Cleanup old audio files",
        replace_existing=True,
    )

    # Schedule automatic database backups (runs daily at 2 AM)
    scheduler.add_job(
        backup_manager.backup_database,
        "cron",
        hour=DATABASE_BACKUP_CRON_HOUR,
        minute=DATABASE_BACKUP_CRON_MINUTE,
        args=[DATABASE_BACKUP_RETENTION_DAYS],
        id="database_backup",
        name="Daily database backup",
        replace_existing=True,
    )

    # Schedule automatic session cleanup (runs daily at 3 AM)
    scheduler.add_job(
        cleanup_old_sessions,
        "cron",
        hour=SESSION_CLEANUP_CRON_HOUR,
        minute=SESSION_CLEANUP_CRON_MINUTE,
        args=[settings.SESSION_RETENTION_DAYS],
        id="session_cleanup",
        name="Daily session cleanup",
        replace_existing=True,
    )

    # Start the scheduler
    scheduler.start()
    logger.info("scheduler_started", emoji=LOG_EMOJI_SUCCESS, jobs=["audio_cleanup", "database_backup", "session_cleanup"])

    # Start monitoring scheduler
    await monitoring_scheduler.start()
    logger.info(
        "monitoring_scheduler_started", emoji=LOG_EMOJI_SUCCESS, evaluation_interval=settings.MONITORING_EVALUATION_INTERVAL
    )

    # Phase 1 Optimization: Warm TTS cache on startup
    # Pre-generate common therapeutic phrases to improve first-response latency
    if settings.FEATURE_TTS_CACHE_ENABLED:
        try:
            tts = TextToSpeech(enable_cache=True)
            await tts.warm_cache()
            logger.info("tts_cache_warmed", emoji=LOG_EMOJI_SUCCESS, phrases_cached=len(tts._cache))
        except Exception as e:
            logger.warning(f"⚠️ TTS cache warming failed (non-critical): {e}", exc_info=True)

    # Initialize shared checkpointer and compiled graph (once, for app lifetime)
    # This eliminates per-request SQLite connection creation and graph recompilation.
    db_path = Path(settings.SHORT_TERM_MEMORY_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with AsyncSqliteSaver.from_conn_string(str(db_path)) as checkpointer:
        compiled_graph = create_workflow_graph().compile(checkpointer=checkpointer)
        app.state.checkpointer = checkpointer
        app.state.compiled_graph = compiled_graph
        logger.info("graph_and_checkpointer_initialized", emoji=LOG_EMOJI_SUCCESS)

        yield

        # Shutdown monitoring scheduler
        await monitoring_scheduler.stop()
        logger.info("monitoring_scheduler_stopped", emoji=LOG_EMOJI_SUCCESS)

        # Shutdown scheduler
        scheduler.shutdown()

    logger.info("app_shutdown", emoji=LOG_EMOJI_SUCCESS, service="rose_web_interface")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=APP_TITLE,
        description=APP_DESCRIPTION,
        version=APP_VERSION,
        lifespan=lifespan,
        docs_url=API_DOCS_PATH if settings.ENABLE_API_DOCS else None,
        redoc_url=API_REDOC_PATH if settings.ENABLE_API_DOCS else None,
        openapi_url=API_OPENAPI_PATH if settings.ENABLE_API_DOCS else None,
    )

    # Configure request size limits to prevent memory exhaustion
    # This is set at the application level and applies to all endpoints
    app.state.max_request_size = MAX_REQUEST_SIZE_BYTES
    logger.info("request_size_limit_configured", emoji=LOG_EMOJI_SUCCESS, max_size_mb=MAX_REQUEST_SIZE_BYTES / 1024 / 1024)

    if settings.ENABLE_API_DOCS:
        logger.info("api_documentation_enabled", emoji=LOG_EMOJI_SUCCESS, docs_url=API_DOCS_PATH, redoc_url=API_REDOC_PATH)
    else:
        logger.info("api_documentation_disabled", emoji=LOG_EMOJI_SUCCESS)

    # Add request ID middleware (should be first to track all requests)
    app.add_middleware(RequestIDMiddleware)
    logger.info("request_id_middleware_enabled", emoji=LOG_EMOJI_SUCCESS)

    # Add request size limit middleware
    @app.middleware("http")
    async def limit_request_size(request: Request, call_next):
        """Middleware to enforce request size limits."""
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > MAX_REQUEST_SIZE_BYTES:
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "request_too_large",
                        "message": f"Request body too large. Maximum size is {MAX_REQUEST_SIZE_BYTES / 1024 / 1024}MB",
                        "max_size_bytes": MAX_REQUEST_SIZE_BYTES,
                    },
                )
        return await call_next(request)

    # Configure CORS with environment-based origins
    # In development, use DEV_ALLOWED_ORIGINS; in production, use settings
    if settings.ENVIRONMENT == "development":
        allowed_origins = DEV_ALLOWED_ORIGINS
    else:
        allowed_origins = settings.get_allowed_origins()

    logger.info(
        "cors_configured", emoji=LOG_EMOJI_CONNECTION, allowed_origins=allowed_origins, environment=settings.ENVIRONMENT
    )

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
        logger.info("security_headers_enabled", emoji=LOG_EMOJI_SUCCESS)

    # Configure rate limiting
    if RATE_LIMIT_ENABLED:
        limiter = Limiter(key_func=get_remote_address)
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        logger.info("rate_limiting_enabled", emoji=LOG_EMOJI_SUCCESS, requests_per_minute=RATE_LIMIT_REQUESTS_PER_MINUTE)
    else:
        # Create a no-op limiter if rate limiting is disabled
        app.state.limiter = None
        logger.info("rate_limiting_disabled", emoji=LOG_EMOJI_SUCCESS)

    # Register exception handlers
    app.add_exception_handler(AICompanionError, ai_companion_error_handler)
    app.add_exception_handler(ValueError, validation_error_handler)
    app.add_exception_handler(Exception, global_exception_handler)
    logger.info("exception_handlers_registered", emoji=LOG_EMOJI_SUCCESS)

    # Register API routes with v1 versioning
    app.include_router(health.router, prefix=API_BASE_PATH, tags=["Health"])
    app.include_router(session.router, prefix=API_BASE_PATH, tags=["Session Management"])
    app.include_router(voice.router, prefix=API_BASE_PATH, tags=["Voice Processing"])
    app.include_router(voice_websocket.router, prefix=API_BASE_PATH, tags=["Voice WebSocket"])
    app.include_router(metrics_route.router, prefix=API_BASE_PATH, tags=["Metrics"])
    app.include_router(monitoring.router, prefix=API_BASE_PATH, tags=["Monitoring"])
    app.include_router(admin.router, prefix=API_BASE_PATH, tags=["Admin"])

    logger.info("api_routes_registered", emoji=LOG_EMOJI_SUCCESS, version="v1")

    # Serve React frontend static files (if build directory exists)
    if FRONTEND_BUILD_DIR.exists():
        logger.info("frontend_serving_enabled", emoji=LOG_EMOJI_FRONTEND, build_dir=str(FRONTEND_BUILD_DIR))

        # Check if assets directory exists
        assets_dir = FRONTEND_BUILD_DIR / "assets"
        if assets_dir.exists():
            # Mount static assets (JS, CSS, images, etc.) with cache headers
            # Static files are immutable and can be cached for 1 year
            app.mount("/assets", StaticFiles(directory=assets_dir, html=False), name="assets")
            logger.info("static_assets_mounted", emoji=LOG_EMOJI_SUCCESS, assets_dir=str(assets_dir))
        else:
            logger.warning("assets_directory_not_found", emoji=LOG_EMOJI_WARNING, expected_path=str(assets_dir))

        # Add cache headers for static files
        @app.middleware("http")
        async def add_cache_headers(request: Request, call_next):
            """Add cache headers for static assets."""
            response = await call_next(request)

            # Cache static assets (JS, CSS, images) for 1 year
            if request.url.path.startswith("/assets/"):
                response.headers["Cache-Control"] = f"public, max-age={STATIC_ASSET_CACHE_SECONDS}, immutable"
            # Don't cache API responses
            elif request.url.path.startswith("/api/"):
                response.headers["Cache-Control"] = f"no-cache, no-store, must-revalidate, max-age={API_CACHE_SECONDS}"
            # Cache index.html for 5 minutes (allows updates to propagate quickly)
            elif request.url.path == "/" or request.url.path.endswith(".html"):
                response.headers["Cache-Control"] = f"public, max-age={HTML_CACHE_SECONDS}"

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

            logger.error("index_html_not_found", emoji=LOG_EMOJI_ERROR, expected_path=str(index_path))
            return {"detail": "Frontend not found"}

    else:
        logger.error("frontend_build_not_found", emoji=LOG_EMOJI_ERROR, expected_path=str(FRONTEND_BUILD_DIR))
        logger.warning("frontend_not_served", emoji=LOG_EMOJI_WARNING, message="run 'npm run build' in frontend directory")

    logger.info(
        "server_ready", emoji=LOG_EMOJI_CONNECTION, port=WEB_SERVER_PORT, frontend_enabled=FRONTEND_BUILD_DIR.exists()
    )

    return app


app = create_app()
