#!/usr/bin/env python3
"""
🚀 Development Server Launcher

Starts both the Vite dev server (frontend) and FastAPI server (backend)
for local development with hot reload.

This script:
- Verifies required dependencies (uv, npm) are installed
- Starts FastAPI backend on port 8000 with auto-reload
- Starts Vite frontend dev server on port 3000 with HMR
- Performs health checks to verify servers are responsive
- Handles graceful shutdown on Ctrl+C

Usage:
    python scripts/run_dev_server.py
    OR
    uv run python scripts/run_dev_server.py

Requirements:
    - uv (Python package manager)
    - npm (Node.js package manager)
    - Backend dependencies installed (uv sync)
    - Frontend dependencies installed (cd frontend && npm install)

Environment:
    Reads configuration from src/ai_companion/config/server_config.py
"""
import io
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Add project root to Python path for imports
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils import run_command, terminate_process_gracefully, wait_for_server  # noqa: E402
from src.ai_companion.config.server_config import (  # noqa: E402
    API_DOCS_PATH,
    DEV_BACKEND_PORT,
    DEV_FRONTEND_PORT,
    LOG_EMOJI_ERROR,
    LOG_EMOJI_STARTUP,
    LOG_EMOJI_SUCCESS,
    LOG_EMOJI_WARNING,
)
from src.ai_companion.core.logging_config import configure_logging, get_logger  # noqa: E402

# Configure structured logging
configure_logging()
logger = get_logger(__name__)

# Startup delays to allow servers to initialize before proceeding
# Backend needs time to import modules and bind to port
BACKEND_STARTUP_DELAY = 2  # seconds

# Frontend needs time to start Vite dev server
FRONTEND_STARTUP_DELAY = 2  # seconds

# Maximum time to wait for graceful shutdown before force killing
GRACEFUL_SHUTDOWN_TIMEOUT = 5  # seconds

# Health check configuration
HEALTH_CHECK_TIMEOUT = 30  # seconds
BACKEND_HEALTH_URL = f"http://localhost:{DEV_BACKEND_PORT}/api/v1/health"


def check_dependencies() -> None:
    """Verify required commands are available before starting servers."""
    missing_deps = []

    # Check for uv (required to run uvicorn)
    if not shutil.which("uv"):
        missing_deps.append("uv (install from https://docs.astral.sh/uv/)")

    # Check for npm - on Windows it might be npm.cmd or npm.ps1
    npm_found = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm_found:
        missing_deps.append("npm (install Node.js from https://nodejs.org)")

    if missing_deps:
        logger.error(f"{LOG_EMOJI_ERROR} missing_dependencies", dependencies=missing_deps)
        for dep in missing_deps:
            print(f"❌ Missing: {dep}")
        sys.exit(1)

    logger.info(f"{LOG_EMOJI_SUCCESS} dependencies_verified")


def start_backend() -> subprocess.Popen:
    """
    🔌 Start FastAPI backend server

    Starts uvicorn with auto-reload enabled for development.

    Returns:
        subprocess.Popen: Running backend process

    Raises:
        FileNotFoundError: If uv command is not found
        PermissionError: If insufficient permissions to execute
        subprocess.SubprocessError: For other subprocess-related errors
    """
    logger.info(f"{LOG_EMOJI_STARTUP} starting_backend", port=DEV_BACKEND_PORT)
    try:
        # Use uv run to ensure proper environment
        backend_process = run_command(
            [
                "uv",
                "run",
                "uvicorn",
                "src.ai_companion.interfaces.web.app:app",
                "--reload",
                "--port",
                str(DEV_BACKEND_PORT),
            ],
            cwd=PROJECT_ROOT,
        )
        logger.info(f"{LOG_EMOJI_SUCCESS} backend_started", pid=backend_process.pid, port=DEV_BACKEND_PORT)
        return backend_process
    except FileNotFoundError as e:
        logger.error(
            f"{LOG_EMOJI_ERROR} backend_command_not_found",
            command="uv",
            error=str(e),
            hint="Install uv from https://docs.astral.sh/uv/",
        )
        raise
    except PermissionError as e:
        logger.error(
            f"{LOG_EMOJI_ERROR} backend_permission_denied",
            error=str(e),
            hint="Check file permissions or run with appropriate privileges",
        )
        raise
    except Exception as e:
        logger.error(f"{LOG_EMOJI_ERROR} backend_start_failed", error=str(e))
        raise


def start_frontend() -> subprocess.Popen:
    """
    🎨 Start Vite frontend dev server

    Starts Vite with HMR (Hot Module Replacement) enabled for development.

    Returns:
        subprocess.Popen: Running frontend process

    Raises:
        FileNotFoundError: If npm command is not found
        PermissionError: If insufficient permissions to execute
        subprocess.SubprocessError: For other subprocess-related errors
    """
    logger.info(f"{LOG_EMOJI_STARTUP} starting_frontend", port=DEV_FRONTEND_PORT)
    try:
        frontend_process = run_command(
            ["npm", "run", "dev"],
            cwd=PROJECT_ROOT / "frontend",
        )
        logger.info(f"{LOG_EMOJI_SUCCESS} frontend_started", pid=frontend_process.pid, port=DEV_FRONTEND_PORT)
        return frontend_process
    except FileNotFoundError as e:
        logger.error(
            f"{LOG_EMOJI_ERROR} frontend_command_not_found",
            command="npm",
            error=str(e),
            hint="Install Node.js from https://nodejs.org",
        )
        raise
    except PermissionError as e:
        logger.error(
            f"{LOG_EMOJI_ERROR} frontend_permission_denied",
            error=str(e),
            hint="Check file permissions or run with appropriate privileges",
        )
        raise
    except Exception as e:
        logger.error(f"{LOG_EMOJI_ERROR} frontend_start_failed", error=str(e))
        raise


def main() -> None:
    """Main entry point for development server launcher"""
    # Set UTF-8 encoding for Windows console to support emojis
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    logger.info(f"{LOG_EMOJI_STARTUP} dev_server_launcher_starting")
    print("🚀 Starting Rose development servers...")
    print()

    # Check dependencies before attempting to start servers
    check_dependencies()

    try:
        backend = start_backend()
        time.sleep(BACKEND_STARTUP_DELAY)  # Give backend time to start

        # Wait for backend to be ready
        print("⏳ Waiting for backend to be ready...")
        if wait_for_server(BACKEND_HEALTH_URL, timeout=HEALTH_CHECK_TIMEOUT):
            print("✅ Backend is ready!")
        else:
            print("⚠️  Backend health check timed out, but continuing...")
            logger.warning(
                f"{LOG_EMOJI_WARNING} backend_health_check_timeout",
                url=BACKEND_HEALTH_URL,
                hint="Backend may not be fully ready",
            )

        frontend = start_frontend()
        time.sleep(FRONTEND_STARTUP_DELAY)  # Give frontend time to start

        print()
        print("✅ Development servers running!")
        print()
        print(f"   🎨 Frontend: http://localhost:{DEV_FRONTEND_PORT}")
        print(f"   🔌 Backend:  http://localhost:{DEV_BACKEND_PORT}")
        print(f"   📚 API Docs: http://localhost:{DEV_BACKEND_PORT}{API_DOCS_PATH}")
        print()
        print("   Press Ctrl+C to stop all servers")
        print()

        logger.info(
            f"{LOG_EMOJI_SUCCESS} dev_servers_running",
            frontend_url=f"http://localhost:{DEV_FRONTEND_PORT}",
            backend_url=f"http://localhost:{DEV_BACKEND_PORT}",
            api_docs_url=f"http://localhost:{DEV_BACKEND_PORT}{API_DOCS_PATH}",
        )

        # Wait for processes to complete (they won't unless interrupted)
        backend.wait()
        frontend.wait()

    except KeyboardInterrupt:
        print()
        logger.info(f"{LOG_EMOJI_WARNING} shutdown_requested")
        print("🛑 Stopping servers...")

        # Terminate processes gracefully
        backend_graceful = terminate_process_gracefully(backend, "backend", GRACEFUL_SHUTDOWN_TIMEOUT)
        frontend_graceful = terminate_process_gracefully(frontend, "frontend", GRACEFUL_SHUTDOWN_TIMEOUT)

        if backend_graceful and frontend_graceful:
            print("✅ Servers stopped gracefully")
        else:
            print("✅ Servers stopped (some required force kill)")

        sys.exit(0)

    except Exception as e:
        logger.error(f"{LOG_EMOJI_ERROR} dev_server_launcher_failed", error=str(e))
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
