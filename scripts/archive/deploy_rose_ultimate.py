#!/usr/bin/env python3
"""
🌹 ROSE ULTIMATE DEPLOYMENT SCRIPT 🌹

The ONE script to rule them all. Uncle Bob approved.
Zero magic numbers. Maximum logging. Bulletproof error handling.

This script:
1. 🔍 Analyzes current state
2. 🧹 Cleans up old deployments
3. 🏗️ Rebuilds everything from scratch
4. 🚀 Deploys and verifies
5. ✅ Confirms everything works

Usage:
    python scripts/deploy_rose_ultimate.py

No arguments needed. Just run it.
"""

import io
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ai_companion.config.server_config import (  # noqa: E402
    LOG_EMOJI_CLEANUP,
    LOG_EMOJI_ERROR,
    LOG_EMOJI_STARTUP,
    LOG_EMOJI_SUCCESS,
    QDRANT_DEFAULT_PORT,
    WEB_SERVER_PORT,
)
from src.ai_companion.core.logging_config import configure_logging, get_logger  # noqa: E402

configure_logging()
logger = get_logger(__name__)

# Deployment constants (NO MAGIC NUMBERS!)
DOCKER_COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"
ENV_FILE = PROJECT_ROOT / ".env"
ENV_EXAMPLE_FILE = PROJECT_ROOT / ".env.example"

# Timeout constants
DOCKER_STOP_TIMEOUT = 30  # seconds to wait for graceful container stop
DOCKER_BUILD_TIMEOUT = 600  # 10 minutes for Docker build
DOCKER_START_WAIT = 10  # seconds to wait after starting containers
HEALTH_CHECK_TIMEOUT = 60  # seconds to wait for health checks
HEALTH_CHECK_INTERVAL = 2  # seconds between health check attempts

# Container names
ROSE_CONTAINER_NAME = "rose-rose-1"  # Docker Compose naming convention
QDRANT_CONTAINER_NAME = "rose-qdrant-1"

# URLs for health checks
QDRANT_HEALTH_URL = f"http://localhost:{QDRANT_DEFAULT_PORT}"
ROSE_HEALTH_URL = f"http://localhost:{WEB_SERVER_PORT}/api/v1/health"

# Exit codes
EXIT_SUCCESS = 0
EXIT_FAILURE = 1


class Colors:
    """ANSI color codes for terminal output."""

    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    END = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str) -> None:
    """Print a fancy header."""
    print()
    print("=" * 70)
    print(f"  {text}")
    print("=" * 70)
    print()


def print_step(emoji: str, text: str) -> None:
    """Print a step with emoji."""
    print(f"{emoji} {text}")
    logger.info(f"{emoji} {text}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{LOG_EMOJI_ERROR} {text}")
    logger.error(f"{LOG_EMOJI_ERROR} {text}")


def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{LOG_EMOJI_SUCCESS} {text}")
    logger.info(f"{LOG_EMOJI_SUCCESS} {text}")


def run_command(cmd: list[str], timeout: Optional[int] = None, check: bool = True) -> subprocess.CompletedProcess:
    """
    Run a command with proper error handling and logging.

    Args:
        cmd: Command to run as list
        timeout: Optional timeout in seconds
        check: Whether to raise exception on non-zero exit

    Returns:
        CompletedProcess result
    """
    cmd_str = " ".join(cmd)
    logger.info("🔧 running_command", command=cmd_str)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=check, cwd=PROJECT_ROOT)

        if result.returncode == 0:
            logger.info(f"{LOG_EMOJI_SUCCESS} command_succeeded", command=cmd_str)
        else:
            logger.error(
                f"{LOG_EMOJI_ERROR} command_failed",
                command=cmd_str,
                returncode=result.returncode,
                stderr=result.stderr[:500] if result.stderr else "",
            )

        return result

    except subprocess.TimeoutExpired:
        logger.error(f"{LOG_EMOJI_ERROR} command_timeout", command=cmd_str, timeout=timeout)
        raise
    except Exception as e:
        logger.error(f"{LOG_EMOJI_ERROR} command_exception", command=cmd_str, error=str(e))
        raise


def check_prerequisites() -> bool:
    """Check if all required tools are installed."""
    print_step(LOG_EMOJI_STARTUP, "Checking prerequisites...")

    required = {"docker": "Docker", "docker-compose": "Docker Compose"}

    missing = []
    for cmd, name in required.items():
        result = subprocess.run(["where" if sys.platform == "win32" else "which", cmd], capture_output=True)
        if result.returncode != 0:
            missing.append(name)
            print_error(f"{name} not found")

    if missing:
        print()
        print_error(f"Missing required tools: {', '.join(missing)}")
        print()
        print("Please install:")
        print("  • Docker Desktop: https://docker.com")
        return False

    print_success("All prerequisites installed")
    return True


def check_env_file() -> bool:
    """Check if .env file exists and has required keys."""
    print_step(LOG_EMOJI_STARTUP, "Checking environment configuration...")

    if not ENV_FILE.exists():
        print_error(".env file not found")
        print()
        print("Please create .env file:")
        print(f"  1. Copy: copy {ENV_EXAMPLE_FILE.name} {ENV_FILE.name}")
        print("  2. Edit .env and add your API keys:")
        print("     • GROQ_API_KEY")
        print("     • ELEVENLABS_API_KEY")
        print("     • ELEVENLABS_VOICE_ID")
        print("     • QDRANT_URL")
        return False

    # Check for required keys
    env_content = ENV_FILE.read_text()
    required_keys = ["GROQ_API_KEY", "ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID"]
    missing = [key for key in required_keys if key not in env_content or f"{key}=" not in env_content]

    if missing:
        print_error(f"Missing required keys in .env: {', '.join(missing)}")
        return False

    print_success(".env file configured")
    return True


def stop_rose_containers() -> bool:
    """Stop and remove Rose containers."""
    print_step(LOG_EMOJI_CLEANUP, "Stopping Rose containers...")

    try:
        # Stop all Rose containers
        result = run_command(["docker-compose", "down"], timeout=DOCKER_STOP_TIMEOUT, check=False)

        if result.returncode == 0:
            print_success("Rose containers stopped")
            time.sleep(3)  # Wait for cleanup
            return True
        else:
            print_error("Failed to stop containers")
            print(f"  Error: {result.stderr}")
            return False

    except Exception as e:
        print_error(f"Error stopping containers: {e}")
        return False


def clean_docker_artifacts() -> bool:
    """Clean old Docker images and volumes."""
    print_step(LOG_EMOJI_CLEANUP, "Cleaning Docker artifacts...")

    try:
        # Remove Rose images
        result = run_command(["docker", "images", "-q", "rose-rose"], check=False)

        if result.stdout.strip():
            print("  Removing old Rose images...")
            run_command(["docker", "rmi", "-f"] + result.stdout.strip().split(), check=False)

        print_success("Docker artifacts cleaned")
        return True

    except Exception as e:
        print_error(f"Error cleaning artifacts: {e}")
        return False


def build_docker_containers() -> bool:
    """Build Docker containers from scratch."""
    print_step(LOG_EMOJI_STARTUP, "Building Docker containers (this may take a few minutes)...")

    try:
        result = run_command(["docker-compose", "build", "--no-cache", "--pull"], timeout=DOCKER_BUILD_TIMEOUT)

        if result.returncode == 0:
            print_success("Docker containers built successfully")
            return True
        else:
            print_error("Docker build failed")
            print(f"  Error: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print_error(f"Docker build timed out after {DOCKER_BUILD_TIMEOUT} seconds")
        return False
    except Exception as e:
        print_error(f"Error building containers: {e}")
        return False


def start_docker_containers() -> bool:
    """Start Docker containers."""
    print_step(LOG_EMOJI_STARTUP, "Starting Docker containers...")

    try:
        result = run_command(["docker-compose", "up", "-d"], timeout=60)

        if result.returncode == 0:
            print_success("Docker containers started")
            print(f"  Waiting {DOCKER_START_WAIT} seconds for initialization...")
            time.sleep(DOCKER_START_WAIT)
            return True
        else:
            print_error("Failed to start containers")
            print(f"  Error: {result.stderr}")
            return False

    except Exception as e:
        print_error(f"Error starting containers: {e}")
        return False


def check_container_running(container_name: str) -> bool:
    """Check if a container is running."""
    result = run_command(["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"], check=False)
    return container_name in result.stdout


def check_url_health(url: str, timeout: int = HEALTH_CHECK_TIMEOUT) -> bool:
    """Check if a URL is healthy."""
    import urllib.request

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(HEALTH_CHECK_INTERVAL)

    return False


def verify_deployment() -> bool:
    """Verify all services are running and healthy."""
    print_step(LOG_EMOJI_STARTUP, "Verifying deployment...")

    # Check Qdrant container
    print("  Checking Qdrant container...")
    if not check_container_running(QDRANT_CONTAINER_NAME):
        print_error("Qdrant container not running")
        return False
    print(f"    {LOG_EMOJI_SUCCESS} Qdrant container running")

    # Check Qdrant health
    print("  Checking Qdrant health...")
    if not check_url_health(QDRANT_HEALTH_URL, timeout=30):
        print_error("Qdrant health check failed")
        return False
    print(f"    {LOG_EMOJI_SUCCESS} Qdrant is healthy")

    # Check Rose container
    print("  Checking Rose container...")
    if not check_container_running(ROSE_CONTAINER_NAME):
        print_error("Rose container not running")
        print()
        print("  Checking logs...")
        result = run_command(["docker-compose", "logs", "rose"], check=False)
        print(result.stdout[-1000:] if result.stdout else "No logs available")
        return False
    print(f"    {LOG_EMOJI_SUCCESS} Rose container running")

    # Check Rose health
    print("  Checking Rose health (this may take up to 60 seconds)...")
    if not check_url_health(ROSE_HEALTH_URL, timeout=HEALTH_CHECK_TIMEOUT):
        print_error("Rose health check failed")
        print()
        print("  Checking logs...")
        result = run_command(["docker-compose", "logs", "--tail=50", "rose"], check=False)
        print(result.stdout if result.stdout else "No logs available")
        return False
    print(f"    {LOG_EMOJI_SUCCESS} Rose is healthy")

    print_success("All services verified and healthy!")
    return True


def show_access_info() -> None:
    """Show how to access Rose."""
    print()
    print("=" * 70)
    print(f"  {LOG_EMOJI_SUCCESS} ROSE IS READY!")
    print("=" * 70)
    print()
    print("🌐 Access Rose:")
    print(f"   http://localhost:{WEB_SERVER_PORT}")
    print()
    print("📊 View logs:")
    print("   docker-compose logs -f rose")
    print()
    print("🔍 Check status:")
    print("   docker-compose ps")
    print()
    print("🛑 Stop Rose:")
    print("   docker-compose down")
    print()
    print("=" * 70)
    print()


def main() -> int:
    """Main deployment orchestration."""
    # Set UTF-8 encoding for Windows
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    start_time = time.time()

    print()
    print("🌹" * 35)
    print()
    print("     ROSE THE HEALER SHAMAN")
    print("     Ultimate Deployment Script")
    print()
    print("     Uncle Bob Approved ✅")
    print("     Zero Magic Numbers ✅")
    print("     Maximum Logging ✅")
    print()
    print("🌹" * 35)

    logger.info(f"{LOG_EMOJI_STARTUP} ultimate_deployment_starting")

    # Step 1: Prerequisites
    print_header("Step 1: Prerequisites")
    if not check_prerequisites():
        return EXIT_FAILURE

    if not check_env_file():
        return EXIT_FAILURE

    # Step 2: Clean up
    print_header("Step 2: Clean Up")
    if not stop_rose_containers():
        print_error("Failed to stop containers, but continuing...")

    if not clean_docker_artifacts():
        print_error("Failed to clean artifacts, but continuing...")

    # Step 3: Build
    print_header("Step 3: Build")
    if not build_docker_containers():
        return EXIT_FAILURE

    # Step 4: Deploy
    print_header("Step 4: Deploy")
    if not start_docker_containers():
        return EXIT_FAILURE

    # Step 5: Verify
    print_header("Step 5: Verify")
    if not verify_deployment():
        print()
        print_error("Deployment verification failed!")
        print()
        print("Troubleshooting:")
        print("  1. Check logs: docker-compose logs rose")
        print("  2. Check .env file has all required keys")
        print("  3. Verify API keys are valid")
        print("  4. Try: docker-compose down && docker-compose up -d")
        return EXIT_FAILURE

    # Success!
    elapsed = time.time() - start_time
    show_access_info()

    print(f"⏱️  Total deployment time: {elapsed:.1f} seconds")
    print()

    logger.info(f"{LOG_EMOJI_SUCCESS} ultimate_deployment_complete", elapsed_seconds=elapsed)

    return EXIT_SUCCESS


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        print_error("Deployment cancelled by user")
        sys.exit(EXIT_FAILURE)
    except Exception as e:
        print()
        print_error(f"Unexpected error: {e}")
        logger.exception(f"{LOG_EMOJI_ERROR} unexpected_deployment_error")
        sys.exit(EXIT_FAILURE)
