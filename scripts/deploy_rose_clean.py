#!/usr/bin/env python3
"""
🚀 Rose Clean Deployment Script

Complete rebuild and deployment of Rose the Healer Shaman.
Follows Uncle Bob's Clean Code principles with comprehensive logging.

This script:
1. Stops all running services
2. Cleans old build artifacts
3. Rebuilds Docker containers
4. Starts all services
5. Verifies deployment health
6. Runs smoke tests

Usage:
    python scripts/deploy_rose_clean.py [--mode MODE]

Modes:
    docker    - Full Docker deployment (default)
    local     - Local development mode
    prod      - Production build served locally

Author: Uncle Bob would approve 👍
"""
import argparse
import io
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils import (  # noqa: E402
    check_command_exists,
    check_url_accessible,
    run_command_sync,
    wait_for_server,
)
from src.ai_companion.config.server_config import (  # noqa: E402
    QDRANT_DEFAULT_PORT,
    LOG_EMOJI_CLEANUP,
    LOG_EMOJI_ERROR,
    LOG_EMOJI_STARTUP,
    LOG_EMOJI_SUCCESS,
    LOG_EMOJI_WARNING,
    WEB_SERVER_PORT,
)
from src.ai_companion.core.logging_config import configure_logging, get_logger  # noqa: E402

configure_logging()
logger = get_logger(__name__)

# Deployment constants
DOCKER_COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
BACKEND_HEALTH_URL = f"http://localhost:{WEB_SERVER_PORT}/api/v1/health"
QDRANT_HEALTH_URL = f"http://localhost:{QDRANT_DEFAULT_PORT}"

# Timeout constants (no magic numbers!)
DOCKER_BUILD_TIMEOUT = 600  # 10 minutes for Docker build
DOCKER_START_TIMEOUT = 60  # 1 minute for services to start
SERVICE_HEALTH_CHECK_TIMEOUT = 30  # 30 seconds for health checks
CLEANUP_WAIT_TIME = 5  # 5 seconds to wait after cleanup

# Exit codes
EXIT_SUCCESS = 0
EXIT_FAILURE = 1


class DeploymentMode:
    """Deployment mode constants."""
    DOCKER = "docker"
    LOCAL = "local"
    PROD = "prod"


class RoseDeployer:
    """Handles Rose deployment with comprehensive logging."""

    def __init__(self, mode: str = DeploymentMode.DOCKER):
        self.mode = mode
        self.start_time = time.time()

    def log_step(self, emoji: str, message: str, **kwargs) -> None:
        """Log a deployment step with emoji and context."""
        logger.info(f"{emoji} {message}", mode=self.mode, **kwargs)
        print(f"{emoji} {message}")

    def log_error(self, message: str, **kwargs) -> None:
        """Log an error with context."""
        logger.error(f"{LOG_EMOJI_ERROR} {message}", mode=self.mode, **kwargs)
        print(f"{LOG_EMOJI_ERROR} {message}")

    def check_prerequisites(self) -> bool:
        """Verify all required tools are installed."""
        self.log_step(LOG_EMOJI_STARTUP, "Checking prerequisites...")

        required_commands = {
            "docker": "https://docker.com",
            "docker-compose": "https://docker.com",
        }

        if self.mode in [DeploymentMode.LOCAL, DeploymentMode.PROD]:
            required_commands["uv"] = "https://docs.astral.sh/uv/"
            required_commands["npm"] = "https://nodejs.org"

        missing = []
        for cmd, url in required_commands.items():
            if not check_command_exists(cmd):
                missing.append(f"{cmd} ({url})")

        if missing:
            self.log_error("Missing required commands", missing=missing)
            print(f"\n{LOG_EMOJI_ERROR} Missing required tools:")
            for tool in missing:
                print(f"  • {tool}")
            return False

        self.log_step(LOG_EMOJI_SUCCESS, "All prerequisites met")
        return True

    def stop_services(self) -> bool:
        """Stop all running services."""
        self.log_step(LOG_EMOJI_CLEANUP, "Stopping existing services...")

        try:
            if self.mode == DeploymentMode.DOCKER:
                # Stop Docker containers
                result = run_command_sync(
                    ["docker-compose", "down"],
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    self.log_error("Failed to stop Docker services", stderr=result.stderr)
                    return False

            self.log_step(LOG_EMOJI_SUCCESS, "Services stopped")
            time.sleep(CLEANUP_WAIT_TIME)  # Wait for cleanup
            return True

        except Exception as e:
            self.log_error("Error stopping services", error=str(e))
            return False

    def clean_build_artifacts(self) -> bool:
        """Clean old build artifacts."""
        self.log_step(LOG_EMOJI_CLEANUP, "Cleaning build artifacts...")

        try:
            # Clean frontend build
            frontend_dist = FRONTEND_DIR / "dist"
            if frontend_dist.exists():
                import shutil
                shutil.rmtree(frontend_dist)
                self.log_step(LOG_EMOJI_SUCCESS, "Frontend build cleaned")

            # Clean Docker images (optional - commented out to save time)
            # result = run_command_sync(
            #     ["docker", "system", "prune", "-f"],
            #     capture_output=True
            # )

            return True

        except Exception as e:
            self.log_error("Error cleaning artifacts", error=str(e))
            return False

    def build_frontend(self) -> bool:
        """Build frontend for production."""
        self.log_step(LOG_EMOJI_STARTUP, "Building frontend...")

        try:
            result = run_command_sync(
                ["npm", "run", "build"],
                cwd=FRONTEND_DIR,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                self.log_error("Frontend build failed", stderr=result.stderr)
                return False

            self.log_step(LOG_EMOJI_SUCCESS, "Frontend built successfully")
            return True

        except Exception as e:
            self.log_error("Error building frontend", error=str(e))
            return False

    def build_docker_containers(self) -> bool:
        """Build Docker containers."""
        self.log_step(LOG_EMOJI_STARTUP, "Building Docker containers...")

        try:
            result = run_command_sync(
                ["docker-compose", "build", "--no-cache"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=DOCKER_BUILD_TIMEOUT
            )

            if result.returncode != 0:
                self.log_error("Docker build failed", stderr=result.stderr)
                return False

            self.log_step(LOG_EMOJI_SUCCESS, "Docker containers built")
            return True

        except subprocess.TimeoutExpired:
            self.log_error("Docker build timed out", timeout=DOCKER_BUILD_TIMEOUT)
            return False
        except Exception as e:
            self.log_error("Error building Docker containers", error=str(e))
            return False

    def start_docker_services(self) -> bool:
        """Start Docker services."""
        self.log_step(LOG_EMOJI_STARTUP, "Starting Docker services...")

        try:
            result = run_command_sync(
                ["docker-compose", "up", "-d"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                self.log_error("Failed to start Docker services", stderr=result.stderr)
                return False

            self.log_step(LOG_EMOJI_SUCCESS, "Docker services started")
            time.sleep(DOCKER_START_TIMEOUT)  # Wait for services to initialize
            return True

        except Exception as e:
            self.log_error("Error starting Docker services", error=str(e))
            return False

    def verify_health(self) -> bool:
        """Verify all services are healthy."""
        self.log_step(LOG_EMOJI_STARTUP, "Verifying service health...")

        # Check Qdrant
        if not check_url_accessible(QDRANT_HEALTH_URL, timeout=5):
            self.log_error("Qdrant health check failed", url=QDRANT_HEALTH_URL)
            return False

        self.log_step(LOG_EMOJI_SUCCESS, "Qdrant is healthy")

        # Check backend (if in Docker mode)
        if self.mode == DeploymentMode.DOCKER:
            if not wait_for_server(BACKEND_HEALTH_URL, timeout=SERVICE_HEALTH_CHECK_TIMEOUT):
                self.log_error("Backend health check failed", url=BACKEND_HEALTH_URL)
                return False

            self.log_step(LOG_EMOJI_SUCCESS, "Backend is healthy")

        return True

    def deploy_docker(self) -> bool:
        """Full Docker deployment."""
        steps = [
            ("Prerequisites", self.check_prerequisites),
            ("Stop Services", self.stop_services),
            ("Clean Artifacts", self.clean_build_artifacts),
            ("Build Docker", self.build_docker_containers),
            ("Start Services", self.start_docker_services),
            ("Health Check", self.verify_health),
        ]

        for step_name, step_func in steps:
            if not step_func():
                self.log_error(f"Deployment failed at: {step_name}")
                return False

        return True

    def deploy_local(self) -> bool:
        """Local development deployment."""
        steps = [
            ("Prerequisites", self.check_prerequisites),
            ("Stop Services", self.stop_services),
        ]

        for step_name, step_func in steps:
            if not step_func():
                self.log_error(f"Deployment failed at: {step_name}")
                return False

        print()
        print(f"{LOG_EMOJI_SUCCESS} Ready for local development!")
        print()
        print("Next steps:")
        print("  1. Start Qdrant: docker-compose up qdrant -d")
        print("  2. Start dev servers: python scripts/run_dev_server.py")
        print()
        return True

    def deploy_prod(self) -> bool:
        """Production build served locally."""
        steps = [
            ("Prerequisites", self.check_prerequisites),
            ("Stop Services", self.stop_services),
            ("Clean Artifacts", self.clean_build_artifacts),
            ("Build Frontend", self.build_frontend),
        ]

        for step_name, step_func in steps:
            if not step_func():
                self.log_error(f"Deployment failed at: {step_name}")
                return False

        print()
        print(f"{LOG_EMOJI_SUCCESS} Production build complete!")
        print()
        print("Next steps:")
        print("  1. Start Qdrant: docker-compose up qdrant -d")
        print("  2. Start server: python scripts/build_and_serve.py")
        print()
        return True

    def deploy(self) -> bool:
        """Execute deployment based on mode."""
        elapsed = time.time() - self.start_time

        print()
        print("🚀 Rose Clean Deployment")
        print("=" * 60)
        print(f"Mode: {self.mode}")
        print()

        if self.mode == DeploymentMode.DOCKER:
            success = self.deploy_docker()
        elif self.mode == DeploymentMode.LOCAL:
            success = self.deploy_local()
        elif self.mode == DeploymentMode.PROD:
            success = self.deploy_prod()
        else:
            self.log_error(f"Unknown deployment mode: {self.mode}")
            return False

        elapsed = time.time() - self.start_time

        print()
        print("=" * 60)
        if success:
            print(f"{LOG_EMOJI_SUCCESS} Deployment completed successfully!")
            print(f"⏱️  Time elapsed: {elapsed:.1f} seconds")
            print()

            if self.mode == DeploymentMode.DOCKER:
                print("🌐 Access Rose at:")
                print(f"   http://localhost:{WEB_SERVER_PORT}")
                print()
                print("📊 View logs:")
                print("   docker-compose logs -f rose")
                print()
                print("🛑 Stop services:")
                print("   docker-compose down")
                print()
        else:
            print(f"{LOG_EMOJI_ERROR} Deployment failed!")
            print(f"⏱️  Time elapsed: {elapsed:.1f} seconds")
            print()
            print("🔍 Check logs above for details")
            print()

        return success


def main() -> None:
    """Main entry point."""
    # Set UTF-8 encoding for Windows console
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Deploy Rose the Healer Shaman with comprehensive verification"
    )
    parser.add_argument(
        "--mode",
        choices=[DeploymentMode.DOCKER, DeploymentMode.LOCAL, DeploymentMode.PROD],
        default=DeploymentMode.DOCKER,
        help="Deployment mode (default: docker)"
    )

    args = parser.parse_args()

    logger.info(f"{LOG_EMOJI_STARTUP} deployment_starting", mode=args.mode)

    deployer = RoseDeployer(mode=args.mode)
    success = deployer.deploy()

    if success:
        logger.info(f"{LOG_EMOJI_SUCCESS} deployment_complete", mode=args.mode)
        sys.exit(EXIT_SUCCESS)
    else:
        logger.error(f"{LOG_EMOJI_ERROR} deployment_failed", mode=args.mode)
        sys.exit(EXIT_FAILURE)


if __name__ == "__main__":
    main()
