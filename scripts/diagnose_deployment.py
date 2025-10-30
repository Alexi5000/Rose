#!/usr/bin/env python3
"""
🔍 Rose Deployment Diagnostic Tool

Checks all prerequisites and configuration for local development and deployment.
Provides actionable feedback with emojis for easy scanning.

Usage:
    python scripts/diagnose_deployment.py
    OR
    uv run python scripts/diagnose_deployment.py
"""

import os
import shutil
import subprocess
import sys
from importlib.util import find_spec
from pathlib import Path
from typing import List, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Color codes for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


class DiagnosticCheck:
    """Represents a single diagnostic check."""

    def __init__(self, name: str, check_func, fix_hint: str = ""):
        self.name = name
        self.check_func = check_func
        self.fix_hint = fix_hint
        self.passed = False
        self.message = ""

    def run(self) -> bool:
        """Run the check and return True if passed."""
        try:
            self.passed, self.message = self.check_func()
            return self.passed
        except Exception as e:
            self.passed = False
            self.message = f"Error: {str(e)}"
            return False


def print_header(text: str):
    """Print a section header."""
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")


def print_check(name: str, passed: bool, message: str, fix_hint: str = ""):
    """Print a check result."""
    emoji = "✅" if passed else "❌"
    color = GREEN if passed else RED
    print(f"{emoji} {color}{name}{RESET}")
    if message:
        print(f"   {message}")
    if not passed and fix_hint:
        print(f"   {YELLOW}💡 Fix: {fix_hint}{RESET}")
    print()


def check_python_version() -> Tuple[bool, str]:
    """Check Python version is 3.12+."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 12:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    return False, f"Python {version.major}.{version.minor}.{version.micro} (need 3.12+)"


def check_uv_installed() -> Tuple[bool, str]:
    """Check if uv is installed."""
    if shutil.which("uv"):
        try:
            result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
            return True, result.stdout.strip()
        except Exception as e:
            return False, str(e)
    return False, "uv not found in PATH"


def check_npm_installed() -> Tuple[bool, str]:
    """Check if npm is installed."""
    npm_cmd = shutil.which("npm") or shutil.which("npm.cmd")
    if npm_cmd:
        try:
            result = subprocess.run([npm_cmd, "--version"], capture_output=True, text=True)
            return True, f"npm {result.stdout.strip()}"
        except Exception as e:
            return False, str(e)
    return False, "npm not found in PATH"


def check_env_file() -> Tuple[bool, str]:
    """Check if .env file exists."""
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        return True, f"Found at {env_path}"
    return False, ".env file not found"


def check_required_env_vars() -> Tuple[bool, str]:
    """Check if required environment variables are set."""
    from dotenv import load_dotenv
    load_dotenv()

    required_vars = [
        "GROQ_API_KEY",
        "ELEVENLABS_API_KEY",
        "ELEVENLABS_VOICE_ID",
        "QDRANT_URL",
    ]

    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)

    if not missing:
        return True, "All required variables set"
    return False, f"Missing: {', '.join(missing)}"


def check_qdrant_url_config() -> Tuple[bool, str]:
    """Check if Qdrant URL is configured correctly for local dev."""
    from dotenv import load_dotenv
    load_dotenv()

    qdrant_url = os.getenv("QDRANT_URL", "")

    # Check if running in Docker
    in_docker = os.path.exists("/.dockerenv")

    if in_docker:
        # In Docker, should use service name
        if "qdrant:6333" in qdrant_url:
            return True, f"Correct for Docker: {qdrant_url}"
        return False, f"Should be 'http://qdrant:6333' in Docker, got: {qdrant_url}"
    else:
        # Local dev, should use localhost
        if "localhost:6333" in qdrant_url or "127.0.0.1:6333" in qdrant_url:
            return True, f"Correct for local dev: {qdrant_url}"
        return False, f"Should be 'http://localhost:6333' for local dev, got: {qdrant_url}"


def check_qdrant_connectivity() -> Tuple[bool, str]:
    """Check if Qdrant is accessible."""
    from dotenv import load_dotenv
    load_dotenv()

    try:
        from qdrant_client import QdrantClient

        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")

        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=5)
        collections = client.get_collections()
        return True, f"Connected to Qdrant at {qdrant_url} ({len(collections.collections)} collections)"
    except Exception as e:
        return False, f"Cannot connect to Qdrant: {str(e)}"


def check_frontend_dependencies() -> Tuple[bool, str]:
    """Check if frontend dependencies are installed."""
    node_modules = PROJECT_ROOT / "frontend" / "node_modules"
    if node_modules.exists():
        return True, "Frontend dependencies installed"
    return False, "Frontend node_modules not found"


def check_frontend_build() -> Tuple[bool, str]:
    """Check if frontend is built."""
    static_dir = PROJECT_ROOT / "src" / "ai_companion" / "interfaces" / "web" / "static"
    index_html = static_dir / "index.html"

    if index_html.exists():
        return True, f"Frontend built at {static_dir}"
    return False, "Frontend not built"


def check_python_dependencies() -> Tuple[bool, str]:
    """Check if Python dependencies are installed."""
    required_packages = ["langchain", "groq", "elevenlabs", "qdrant_client"]
    missing = [pkg for pkg in required_packages if find_spec(pkg) is None]

    if not missing:
        return True, "Core Python dependencies installed"
    return False, f"Missing Python dependencies: {', '.join(missing)}"


def check_docker_compose() -> Tuple[bool, str]:
    """Check if docker-compose.yml is valid."""
    docker_compose = PROJECT_ROOT / "docker-compose.yml"
    if not docker_compose.exists():
        return False, "docker-compose.yml not found"

    # Check for common issues
    content = docker_compose.read_text()
    issues = []

    if "Dockerfile.chainlit" in content:
        issues.append("References non-existent Dockerfile.chainlit")

    if "chainlit:" in content and "rose:" not in content:
        issues.append("Service still named 'chainlit' instead of 'rose'")

    if issues:
        return False, "; ".join(issues)

    return True, "docker-compose.yml looks good"


def check_short_term_memory_dir() -> Tuple[bool, str]:
    """Check if short-term memory directory exists."""
    memory_dir = PROJECT_ROOT / "short_term_memory"
    if memory_dir.exists():
        return True, f"Directory exists at {memory_dir}"
    return False, "short_term_memory directory not found (will be created on first run)"


def check_long_term_memory_dir() -> Tuple[bool, str]:
    """Check if long-term memory directory exists."""
    memory_dir = PROJECT_ROOT / "long_term_memory"
    if memory_dir.exists():
        return True, f"Directory exists at {memory_dir}"
    return False, "long_term_memory directory not found (will be created by Qdrant)"


def main():
    """Run all diagnostic checks."""
    # Fix Windows console encoding for emojis
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    print(f"\n{BLUE}🔍 Rose Deployment Diagnostic Tool{RESET}")
    print(f"{BLUE}Checking prerequisites and configuration...{RESET}\n")

    # Define all checks
    checks: List[DiagnosticCheck] = [
        # System prerequisites
        DiagnosticCheck(
            "Python Version (3.12+)",
            check_python_version,
            "Install Python 3.12+ from https://www.python.org/"
        ),
        DiagnosticCheck(
            "uv Package Manager",
            check_uv_installed,
            "Install uv: https://docs.astral.sh/uv/getting-started/installation/"
        ),
        DiagnosticCheck(
            "npm Package Manager",
            check_npm_installed,
            "Install Node.js from https://nodejs.org/"
        ),

        # Configuration
        DiagnosticCheck(
            ".env File Exists",
            check_env_file,
            "Copy .env.example to .env and fill in API keys"
        ),
        DiagnosticCheck(
            "Required Environment Variables",
            check_required_env_vars,
            "Set missing variables in .env file"
        ),
        DiagnosticCheck(
            "Qdrant URL Configuration",
            check_qdrant_url_config,
            "Update QDRANT_URL in .env: 'http://localhost:6333' for local dev"
        ),

        # Dependencies
        DiagnosticCheck(
            "Python Dependencies Installed",
            check_python_dependencies,
            "Run: uv sync"
        ),
        DiagnosticCheck(
            "Frontend Dependencies Installed",
            check_frontend_dependencies,
            "Run: cd frontend && npm install"
        ),

        # Services
        DiagnosticCheck(
            "Qdrant Connectivity",
            check_qdrant_connectivity,
            "Start Qdrant: docker run -p 6333:6333 qdrant/qdrant:latest"
        ),

        # Build artifacts
        DiagnosticCheck(
            "Frontend Build",
            check_frontend_build,
            "Build frontend: cd frontend && npm run build"
        ),

        # Docker
        DiagnosticCheck(
            "Docker Compose Configuration",
            check_docker_compose,
            "Fix docker-compose.yml (see DEPLOYMENT_READINESS_ANALYSIS.md)"
        ),

        # Directories
        DiagnosticCheck(
            "Short-term Memory Directory",
            check_short_term_memory_dir,
            "Will be created automatically on first run"
        ),
        DiagnosticCheck(
            "Long-term Memory Directory",
            check_long_term_memory_dir,
            "Will be created by Qdrant on first connection"
        ),
    ]

    # Run checks by category
    categories = {
        "System Prerequisites": checks[0:3],
        "Configuration": checks[3:6],
        "Dependencies": checks[6:8],
        "Services": checks[8:9],
        "Build Artifacts": checks[9:10],
        "Docker": checks[10:11],
        "Directories": checks[11:13],
    }

    all_passed = True
    results = {}

    for category, category_checks in categories.items():
        print_header(category)
        category_passed = True

        for check in category_checks:
            passed = check.run()
            print_check(check.name, passed, check.message, check.fix_hint)

            if not passed:
                category_passed = False
                all_passed = False

        results[category] = category_passed

    # Print summary
    print_header("Summary")

    for category, passed in results.items():
        emoji = "✅" if passed else "❌"
        color = GREEN if passed else RED
        print(f"{emoji} {color}{category}{RESET}")

    print()

    if all_passed:
        print(f"{GREEN}🎉 All checks passed! You're ready to deploy.{RESET}\n")
        print(f"{BLUE}Next steps:{RESET}")
        print("  1. Start development server: python scripts/run_dev_server.py")
        print("  2. Open browser: http://localhost:3000")
        print("  3. Test voice interaction")
        print()
        return 0
    else:
        print(f"{RED}❌ Some checks failed. Please fix the issues above.{RESET}\n")
        print(f"{BLUE}Quick fixes:{RESET}")
        print("  1. Fix Qdrant URL: Edit .env and set QDRANT_URL=http://localhost:6333")
        print("  2. Start Qdrant: docker run -p 6333:6333 qdrant/qdrant:latest")
        print("  3. Install dependencies: uv sync && cd frontend && npm install")
        print("  4. Build frontend: cd frontend && npm run build")
        print()
        print(f"{YELLOW}📖 For detailed guidance, see: DEPLOYMENT_READINESS_ANALYSIS.md{RESET}\n")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⚠️  Diagnostic interrupted by user{RESET}\n")
        sys.exit(130)
    except Exception as e:
        print(f"\n{RED}❌ Diagnostic failed with error: {e}{RESET}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
