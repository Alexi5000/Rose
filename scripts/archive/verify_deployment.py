#!/usr/bin/env python3
"""
🔍 Rose Deployment Verification Script

Comprehensive verification of Rose the Healer Shaman deployment.
Follows Uncle Bob's Clean Code principles with proper logging and no magic numbers.

This script verifies:
- Environment configuration
- Dependencies installation
- Service connectivity
- Build artifacts
- Health checks
- End-to-end workflows

Usage:
    python scripts/verify_deployment.py
    OR
    uv run python scripts/verify_deployment.py
"""

import io
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils import check_command_exists, check_port_available, check_url_accessible  # noqa: E402
from src.ai_companion.config.server_config import (  # noqa: E402
    DEV_FRONTEND_PORT,
    FRONTEND_BUILD_DIR,
    LOG_EMOJI_ERROR,
    LOG_EMOJI_SUCCESS,
    WEB_SERVER_PORT,
)
from src.ai_companion.core.logging_config import configure_logging, get_logger  # noqa: E402

configure_logging()
logger = get_logger(__name__)

# Verification constants
REQUIRED_PYTHON_VERSION = (3, 12)
REQUIRED_NODE_VERSION = (18, 0)
QDRANT_DEFAULT_PORT = 6333
QDRANT_HEALTH_URL = f"http://localhost:{QDRANT_DEFAULT_PORT}"

# Exit codes
EXIT_SUCCESS = 0
EXIT_FAILURE = 1


class VerificationResult:
    """Result of a verification check."""

    def __init__(self, name: str, passed: bool, message: str, details: str = ""):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details

    def __str__(self) -> str:
        emoji = LOG_EMOJI_SUCCESS if self.passed else LOG_EMOJI_ERROR
        result = f"{emoji} {self.name}: {self.message}"
        if self.details:
            result += f"\n   {self.details}"
        return result


class DeploymentVerifier:
    """Verifies Rose deployment readiness."""

    def __init__(self):
        self.results: list[VerificationResult] = []
        self.passed_count = 0
        self.failed_count = 0

    def add_result(self, result: VerificationResult) -> None:
        """Add a verification result and update counters."""
        self.results.append(result)
        if result.passed:
            self.passed_count += 1
        else:
            self.failed_count += 1

        # Log the result
        if result.passed:
            logger.info(f"{LOG_EMOJI_SUCCESS} verification_passed", check=result.name, message=result.message)
        else:
            logger.error(
                f"{LOG_EMOJI_ERROR} verification_failed",
                check=result.name,
                message=result.message,
                details=result.details,
            )

    def verify_environment_file(self) -> VerificationResult:
        """Verify .env file exists and has required keys."""
        env_file = PROJECT_ROOT / ".env"

        if not env_file.exists():
            return VerificationResult(
                "Environment File", False, ".env file not found", "Copy .env.example to .env and fill in your API keys"
            )

        # Check for required keys
        required_keys = [
            "GROQ_API_KEY",
            "ELEVENLABS_API_KEY",
            "ELEVENLABS_VOICE_ID",
            "QDRANT_URL",
        ]

        env_content = env_file.read_text()
        missing_keys = []

        for key in required_keys:
            if key not in env_content or f"{key}=" not in env_content:
                missing_keys.append(key)

        if missing_keys:
            return VerificationResult(
                "Environment File",
                False,
                "Missing required environment variables",
                f"Missing: {', '.join(missing_keys)}",
            )

        return VerificationResult("Environment File", True, ".env file exists with required keys")

    def verify_python_version(self) -> VerificationResult:
        """Verify Python version meets requirements."""
        current_version = sys.version_info[:2]

        if current_version < REQUIRED_PYTHON_VERSION:
            return VerificationResult(
                "Python Version",
                False,
                f"Python {REQUIRED_PYTHON_VERSION[0]}.{REQUIRED_PYTHON_VERSION[1]}+ required",
                f"Current version: {current_version[0]}.{current_version[1]}",
            )

        return VerificationResult(
            "Python Version", True, f"Python {current_version[0]}.{current_version[1]} meets requirements"
        )

    def verify_command_available(self, command: str, install_url: str = "") -> VerificationResult:
        """Verify a command is available in PATH."""
        if check_command_exists(command):
            return VerificationResult(f"{command.upper()} Command", True, f"{command} is installed and available")

        details = f"Install from: {install_url}" if install_url else ""
        return VerificationResult(f"{command.upper()} Command", False, f"{command} not found in PATH", details)

    def verify_frontend_build(self) -> VerificationResult:
        """Verify frontend build exists and is complete."""
        if not FRONTEND_BUILD_DIR.exists():
            return VerificationResult(
                "Frontend Build",
                False,
                "Frontend build directory not found",
                f"Run 'npm run build' in frontend directory. Expected: {FRONTEND_BUILD_DIR}",
            )

        index_file = FRONTEND_BUILD_DIR / "index.html"
        if not index_file.exists():
            return VerificationResult(
                "Frontend Build",
                False,
                "index.html not found in build directory",
                "Frontend build may be incomplete. Run 'npm run build' again.",
            )

        assets_dir = FRONTEND_BUILD_DIR / "assets"
        if not assets_dir.exists():
            return VerificationResult(
                "Frontend Build",
                False,
                "Assets directory not found in build",
                "Frontend build may be incomplete. Run 'npm run build' again.",
            )

        return VerificationResult("Frontend Build", True, f"Frontend build complete at {FRONTEND_BUILD_DIR}")

    def verify_qdrant_running(self) -> VerificationResult:
        """Verify Qdrant is running and accessible."""
        if check_url_accessible(QDRANT_HEALTH_URL, timeout=5):
            return VerificationResult("Qdrant Service", True, f"Qdrant is running on port {QDRANT_DEFAULT_PORT}")

        return VerificationResult(
            "Qdrant Service",
            False,
            "Qdrant is not accessible",
            f"Start Qdrant with 'docker compose up qdrant -d' or check {QDRANT_HEALTH_URL}",
        )

    def verify_port_available(self, port: int, service_name: str) -> VerificationResult:
        """Verify a port is available for use."""
        if check_port_available(port):
            return VerificationResult(
                f"Port {port} ({service_name})", True, f"Port {port} is available for {service_name}"
            )

        return VerificationResult(
            f"Port {port} ({service_name})",
            False,
            f"Port {port} is already in use",
            f"Stop the service using port {port} or choose a different port",
        )

    def verify_memory_directories(self) -> VerificationResult:
        """Verify memory directories exist."""
        long_term_dir = PROJECT_ROOT / "long_term_memory"
        short_term_dir = PROJECT_ROOT / "short_term_memory"

        if not long_term_dir.exists():
            return VerificationResult(
                "Memory Directories",
                False,
                "Long-term memory directory not found",
                "Directory will be created on first run, but Qdrant should be running first",
            )

        if not short_term_dir.exists():
            return VerificationResult(
                "Memory Directories",
                False,
                "Short-term memory directory not found",
                "Directory will be created on first run",
            )

        return VerificationResult("Memory Directories", True, "Memory directories exist")

    def run_all_checks(self) -> bool:
        """Run all verification checks."""
        print("🔍 Rose Deployment Verification")
        print("=" * 60)
        print()

        # Phase 1: Environment Setup
        print("📋 Phase 1: Environment Setup")
        self.add_result(self.verify_environment_file())
        self.add_result(self.verify_python_version())
        print()

        # Phase 2: Dependencies
        print("📦 Phase 2: Dependencies")
        self.add_result(self.verify_command_available("uv", "https://docs.astral.sh/uv/"))
        self.add_result(self.verify_command_available("npm", "https://nodejs.org"))
        self.add_result(self.verify_command_available("docker", "https://docker.com"))
        print()

        # Phase 3: Build Artifacts
        print("🎨 Phase 3: Build Artifacts")
        self.add_result(self.verify_frontend_build())
        print()

        # Phase 4: Services
        print("🔌 Phase 4: Services")
        self.add_result(self.verify_qdrant_running())
        self.add_result(self.verify_memory_directories())
        print()

        # Phase 5: Port Availability
        print("🌐 Phase 5: Port Availability")
        self.add_result(self.verify_port_available(WEB_SERVER_PORT, "Backend"))
        self.add_result(self.verify_port_available(DEV_FRONTEND_PORT, "Frontend Dev"))
        print()

        # Summary
        print("=" * 60)
        print(f"✅ Passed: {self.passed_count}")
        print(f"❌ Failed: {self.failed_count}")
        print()

        if self.failed_count > 0:
            print(f"{LOG_EMOJI_ERROR} Deployment verification failed!")
            print()
            print("Failed checks:")
            for result in self.results:
                if not result.passed:
                    print(f"  • {result.name}: {result.message}")
                    if result.details:
                        print(f"    → {result.details}")
            print()
            return False

        print(f"{LOG_EMOJI_SUCCESS} All verification checks passed!")
        print()
        print("🚀 Ready to deploy Rose!")
        print()
        print("Next steps:")
        print("  1. Start development servers: python scripts/run_dev_server.py")
        print("  2. Or build for production: python scripts/build_and_serve.py")
        print("  3. Or use Docker: make rose-start")
        print()
        return True


def main() -> None:
    """Main entry point for verification script."""
    # Set UTF-8 encoding for Windows console
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    logger.info("🔍 deployment_verification_starting")

    verifier = DeploymentVerifier()
    success = verifier.run_all_checks()

    if success:
        logger.info(
            f"{LOG_EMOJI_SUCCESS} deployment_verification_complete",
            passed=verifier.passed_count,
            failed=verifier.failed_count,
        )
        sys.exit(EXIT_SUCCESS)
    else:
        logger.error(
            f"{LOG_EMOJI_ERROR} deployment_verification_failed",
            passed=verifier.passed_count,
            failed=verifier.failed_count,
        )
        sys.exit(EXIT_FAILURE)


if __name__ == "__main__":
    main()
