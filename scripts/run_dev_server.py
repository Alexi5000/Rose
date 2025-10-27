#!/usr/bin/env python3
"""
🚀 Development Server Launcher

Starts both the Vite dev server (frontend) and FastAPI server (backend)
for local development with hot reload.

Usage:
    python scripts/run_dev_server.py
    OR
    uv run python scripts/run_dev_server.py
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

# Startup delay to allow servers to initialize (in seconds)
BACKEND_STARTUP_DELAY = 2
FRONTEND_STARTUP_DELAY = 2
GRACEFUL_SHUTDOWN_TIMEOUT = 5


def check_dependencies() -> None:
    """Verify required commands are available before starting servers."""
    missing_deps = []

    if not shutil.which("uvicorn"):
        missing_deps.append("uvicorn (run 'uv sync' to install)")

    if not shutil.which("npm"):
        missing_deps.append("npm (install Node.js from https://nodejs.org)")

    if missing_deps:
        logger.error(f"{LOG_EMOJI_ERROR} missing_dependencies", dependencies=missing_deps)
        for dep in missing_deps:
            print(f"❌ Missing: {dep}")
        sys.exit(1)

    logger.info(f"{LOG_EMOJI_SUCCESS} dependencies_verified")


def start_backend() -> subprocess.Popen:
    """🔌 Start FastAPI backend server"""
    logger.info(f"{LOG_EMOJI_STARTUP} starting_backend", port=DEV_BACKEND_PORT)
    try:
        backend_process = subprocess.Popen(
            ["uvicorn", "src.ai_companion.interfaces.web.app:app", "--reload", "--port", str(DEV_BACKEND_PORT)],
            cwd=PROJECT_ROOT,
        )
        logger.info(f"{LOG_EMOJI_SUCCESS} backend_started", pid=backend_process.pid, port=DEV_BACKEND_PORT)
        return backend_process
    except Exception as e:
        logger.error(f"{LOG_EMOJI_ERROR} backend_start_failed", error=str(e))
        raise


def start_frontend() -> subprocess.Popen:
    """🎨 Start Vite frontend dev server"""
    logger.info(f"{LOG_EMOJI_STARTUP} starting_frontend", port=DEV_FRONTEND_PORT)
    try:
        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=PROJECT_ROOT / "frontend",
        )
        logger.info(f"{LOG_EMOJI_SUCCESS} frontend_started", pid=frontend_process.pid, port=DEV_FRONTEND_PORT)
        return frontend_process
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
        backend.terminate()
        frontend.terminate()

        # Wait for graceful shutdown
        try:
            backend.wait(timeout=GRACEFUL_SHUTDOWN_TIMEOUT)
            frontend.wait(timeout=GRACEFUL_SHUTDOWN_TIMEOUT)
            logger.info(f"{LOG_EMOJI_SUCCESS} servers_stopped_gracefully")
        except subprocess.TimeoutExpired:
            # Force kill if graceful shutdown fails
            logger.warning(f"{LOG_EMOJI_WARNING} graceful_shutdown_timeout_forcing_kill")
            backend.kill()
            frontend.kill()
            logger.info(f"{LOG_EMOJI_SUCCESS} servers_force_killed")

        print("✅ Servers stopped successfully")
        sys.exit(0)

    except Exception as e:
        logger.error(f"{LOG_EMOJI_ERROR} dev_server_launcher_failed", error=str(e))
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
