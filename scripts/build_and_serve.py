#!/usr/bin/env python3
"""
📦 Production Build and Serve

Builds the frontend and starts the FastAPI server in production mode.

This script:
- Verifies required dependencies (uv, npm) are installed
- Builds the frontend for production (optimized bundle)
- Verifies build output exists
- Starts FastAPI server in production mode (no auto-reload)

Usage:
    python scripts/build_and_serve.py
    OR
    uv run python scripts/build_and_serve.py

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
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Add project root to Python path for imports
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils import run_command_sync  # noqa: E402
from src.ai_companion.config.server_config import (  # noqa: E402
    FRONTEND_BUILD_DIR,
    LOG_EMOJI_ERROR,
    LOG_EMOJI_FRONTEND,
    LOG_EMOJI_STARTUP,
    LOG_EMOJI_SUCCESS,
    WEB_SERVER_HOST,
    WEB_SERVER_PORT,
)
from src.ai_companion.core.logging_config import configure_logging, get_logger  # noqa: E402

# Configure structured logging
configure_logging()
logger = get_logger(__name__)


def check_dependencies() -> None:
    """Verify required commands are available before starting."""
    missing_deps = []

    # Check for npm - on Windows it might be npm.cmd or npm.ps1
    npm_found = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm_found:
        missing_deps.append("npm (install Node.js from https://nodejs.org)")

    # Check for uv (required to run uvicorn)
    if not shutil.which("uv"):
        missing_deps.append("uv (install from https://docs.astral.sh/uv/)")

    if missing_deps:
        logger.error(f"{LOG_EMOJI_ERROR} missing_dependencies", dependencies=missing_deps)
        for dep in missing_deps:
            print(f"❌ Missing: {dep}")
        sys.exit(1)

    logger.info(f"{LOG_EMOJI_SUCCESS} dependencies_verified")


def build_frontend() -> None:
    """
    🎨 Build frontend for production

    Runs npm build in the frontend directory and verifies success.

    Raises:
        SystemExit: If build fails or output is not found
    """
    logger.info(f"{LOG_EMOJI_FRONTEND} building_frontend")
    print("🎨 Building frontend...")

    frontend_dir = PROJECT_ROOT / "frontend"

    if not frontend_dir.exists():
        logger.error(f"{LOG_EMOJI_ERROR} frontend_directory_not_found", path=str(frontend_dir))
        print(f"❌ Frontend directory not found: {frontend_dir}")
        sys.exit(1)

    try:
        build_result = run_command_sync(
            ["npm", "run", "build"],
            cwd=frontend_dir,
            capture_output=True,
            text=True,
        )

        if build_result.returncode != 0:
            logger.error(
                f"{LOG_EMOJI_ERROR} frontend_build_failed",
                returncode=build_result.returncode,
                stderr=build_result.stderr,
            )
            print("❌ Frontend build failed!")
            if build_result.stderr:
                print(build_result.stderr)
            sys.exit(1)

        # Verify build output exists
        index_file = FRONTEND_BUILD_DIR / "index.html"
        if not index_file.exists():
            logger.error(
                f"{LOG_EMOJI_ERROR} build_output_not_found",
                expected_path=str(index_file),
            )
            print(f"❌ Build succeeded but output not found at: {index_file}")
            sys.exit(1)

        logger.info(f"{LOG_EMOJI_SUCCESS} frontend_build_complete", output_dir=str(FRONTEND_BUILD_DIR))
        print("✅ Frontend build complete!")

    except FileNotFoundError as e:
        logger.error(
            f"{LOG_EMOJI_ERROR} npm_command_not_found",
            command="npm",
            error=str(e),
            hint="Install Node.js from https://nodejs.org",
        )
        print("❌ npm command not found. Install Node.js from https://nodejs.org")
        sys.exit(1)
    except PermissionError as e:
        logger.error(
            f"{LOG_EMOJI_ERROR} build_permission_denied",
            error=str(e),
            hint="Check file permissions or run with appropriate privileges",
        )
        print(f"❌ Permission denied: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"{LOG_EMOJI_ERROR} frontend_build_exception", error=str(e))
        print(f"❌ Build error: {e}")
        sys.exit(1)


def start_production_server() -> None:
    """
    🚀 Start production server

    Starts uvicorn without reload flag, binding to all interfaces.

    Raises:
        SystemExit: If server fails to start
    """
    logger.info(
        f"{LOG_EMOJI_STARTUP} starting_production_server",
        host=WEB_SERVER_HOST,
        port=WEB_SERVER_PORT,
    )
    print(f"🚀 Starting production server on http://{WEB_SERVER_HOST}:{WEB_SERVER_PORT}...")

    try:
        # Use uv run to ensure proper environment
        run_command_sync(
            [
                "uv",
                "run",
                "uvicorn",
                "src.ai_companion.interfaces.web.app:app",
                "--host",
                WEB_SERVER_HOST,
                "--port",
                str(WEB_SERVER_PORT),
            ],
            cwd=PROJECT_ROOT,
        )
    except KeyboardInterrupt:
        logger.info(f"{LOG_EMOJI_SUCCESS} server_stopped_by_user")
        print("\n✅ Server stopped")
        sys.exit(0)
    except FileNotFoundError as e:
        logger.error(
            f"{LOG_EMOJI_ERROR} uv_command_not_found",
            command="uv",
            error=str(e),
            hint="Install uv from https://docs.astral.sh/uv/",
        )
        print("❌ uv command not found. Install from https://docs.astral.sh/uv/")
        sys.exit(1)
    except PermissionError as e:
        logger.error(
            f"{LOG_EMOJI_ERROR} server_permission_denied",
            error=str(e),
            hint="Check file permissions or run with appropriate privileges",
        )
        print(f"❌ Permission denied: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"{LOG_EMOJI_ERROR} server_start_failed", error=str(e))
        print(f"❌ Server error: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for production build and serve"""
    # Set UTF-8 encoding for Windows console to support emojis
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    logger.info(f"{LOG_EMOJI_STARTUP} production_build_starting")
    print("📦 Building Rose for production...")
    print()

    check_dependencies()

    build_frontend()
    print()

    start_production_server()


if __name__ == "__main__":
    main()
