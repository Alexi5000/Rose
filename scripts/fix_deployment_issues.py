#!/usr/bin/env python3
"""
🔧 Rose Deployment Auto-Fix Tool

Automatically fixes common deployment issues identified by the diagnostic tool.
Applies Uncle Bob's clean code principles with proper logging and error handling.

Usage:
    python scripts/fix_deployment_issues.py [--dry-run]

Options:
    --dry-run    Show what would be fixed without making changes
"""

import argparse
import shutil
import subprocess
import sys
from importlib.util import find_spec
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Emoji constants for logging (Uncle Bob: No Magic Strings!)
LOG_EMOJI_START = "🚀"
LOG_EMOJI_SUCCESS = "✅"
LOG_EMOJI_ERROR = "❌"
LOG_EMOJI_WARNING = "⚠️"
LOG_EMOJI_INFO = "ℹ️"
LOG_EMOJI_FIX = "🔧"
LOG_EMOJI_SKIP = "⏭️"

# Color codes
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


class Fix:
    """Represents a single fix operation."""

    def __init__(self, name: str, description: str, fix_func, check_func=None):
        self.name = name
        self.description = description
        self.fix_func = fix_func
        self.check_func = check_func
        self.applied = False
        self.skipped = False
        self.error = None

    def needs_fix(self) -> bool:
        """Check if this fix is needed."""
        if self.check_func is None:
            return True
        try:
            return not self.check_func()
        except Exception:
            return True

    def apply(self, dry_run: bool = False) -> bool:
        """Apply the fix."""
        try:
            if dry_run:
                print(f"{LOG_EMOJI_INFO} {BLUE}[DRY RUN]{RESET} Would apply: {self.name}")
                print(f"   {self.description}")
                return True

            print(f"{LOG_EMOJI_FIX} {BLUE}Applying:{RESET} {self.name}")
            print(f"   {self.description}")

            self.fix_func()
            self.applied = True

            print(f"{LOG_EMOJI_SUCCESS} {GREEN}Fixed:{RESET} {self.name}\n")
            return True
        except Exception as e:
            self.error = str(e)
            print(f"{LOG_EMOJI_ERROR} {RED}Failed:{RESET} {self.name}")
            print(f"   Error: {str(e)}\n")
            return False


def log_section(title: str):
    """Print a section header."""
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")


# Fix functions (Uncle Bob: Small, focused functions with single responsibility)

def fix_qdrant_url_local():
    """Fix Qdrant URL for local development."""
    env_path = PROJECT_ROOT / ".env"

    if not env_path.exists():
        raise FileNotFoundError(".env file not found")

    # Read current .env
    content = env_path.read_text()
    lines = content.split("\n")

    # Find and update QDRANT_URL
    updated = False
    for i, line in enumerate(lines):
        if line.startswith("QDRANT_URL="):
            # Check if it's using Docker service name
            if "qdrant:6333" in line and "localhost" not in line:
                lines[i] = 'QDRANT_URL="http://localhost:6333"'
                updated = True
                print(f"   {LOG_EMOJI_INFO} Changed from Docker URL to localhost")
                break

    if updated:
        # Write back
        env_path.write_text("\n".join(lines))
        print(f"   {LOG_EMOJI_SUCCESS} Updated .env file")
    else:
        print(f"   {LOG_EMOJI_SKIP} QDRANT_URL already correct or not found")


def fix_frontend_dependencies():
    """Install frontend dependencies."""
    frontend_dir = PROJECT_ROOT / "frontend"

    if not frontend_dir.exists():
        raise FileNotFoundError("frontend directory not found")

    print(f"   {LOG_EMOJI_INFO} Running npm install in frontend/...")

    npm_cmd = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm_cmd:
        raise RuntimeError("npm not found in PATH")

    result = subprocess.run(
        [npm_cmd, "install"],
        cwd=frontend_dir,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"npm install failed: {result.stderr}")

    print(f"   {LOG_EMOJI_SUCCESS} Frontend dependencies installed")


def fix_python_dependencies():
    """Install Python dependencies."""
    print(f"   {LOG_EMOJI_INFO} Running uv sync...")

    if not shutil.which("uv"):
        raise RuntimeError("uv not found in PATH")

    result = subprocess.run(
        ["uv", "sync"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"uv sync failed: {result.stderr}")

    print(f"   {LOG_EMOJI_SUCCESS} Python dependencies installed")


def fix_frontend_build():
    """Build frontend for production."""
    frontend_dir = PROJECT_ROOT / "frontend"

    if not frontend_dir.exists():
        raise FileNotFoundError("frontend directory not found")

    print(f"   {LOG_EMOJI_INFO} Building frontend (this may take a minute)...")

    npm_cmd = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm_cmd:
        raise RuntimeError("npm not found in PATH")

    result = subprocess.run(
        [npm_cmd, "run", "build"],
        cwd=frontend_dir,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"npm run build failed: {result.stderr}")

    # Verify build output
    static_dir = PROJECT_ROOT / "src" / "ai_companion" / "interfaces" / "web" / "static"
    if not (static_dir / "index.html").exists():
        raise RuntimeError("Build completed but index.html not found")

    print(f"   {LOG_EMOJI_SUCCESS} Frontend built successfully")


def fix_docker_compose():
    """Fix docker-compose.yml issues."""
    docker_compose_path = PROJECT_ROOT / "docker-compose.yml"

    if not docker_compose_path.exists():
        raise FileNotFoundError("docker-compose.yml not found")

    content = docker_compose_path.read_text()
    original_content = content

    # Fix 1: Replace Dockerfile.chainlit with Dockerfile
    if "Dockerfile.chainlit" in content:
        content = content.replace("docker/Dockerfile.chainlit", "Dockerfile")
        print(f"   {LOG_EMOJI_INFO} Fixed Dockerfile reference")

    # Fix 2: Rename chainlit service to rose
    if "chainlit:" in content and "rose:" not in content:
        content = content.replace("chainlit:", "rose:")
        print(f"   {LOG_EMOJI_INFO} Renamed service from 'chainlit' to 'rose'")

    # Fix 3: Update whatsapp service to use correct Dockerfile
    if "whatsapp:" in content:
        # Remove whatsapp service as it's frozen for future release
        lines = content.split("\n")
        in_whatsapp_section = False
        filtered_lines = []

        for line in lines:
            if line.strip().startswith("whatsapp:"):
                in_whatsapp_section = True
                print(f"   {LOG_EMOJI_INFO} Removing frozen whatsapp service")
                continue
            elif in_whatsapp_section and line and not line[0].isspace():
                in_whatsapp_section = False

            if not in_whatsapp_section:
                filtered_lines.append(line)

        content = "\n".join(filtered_lines)

    if content != original_content:
        docker_compose_path.write_text(content)
        print(f"   {LOG_EMOJI_SUCCESS} Updated docker-compose.yml")
    else:
        print(f"   {LOG_EMOJI_SKIP} docker-compose.yml already correct")


def fix_create_memory_dirs():
    """Create memory directories if they don't exist."""
    dirs = [
        PROJECT_ROOT / "short_term_memory",
        PROJECT_ROOT / "long_term_memory",
    ]

    for dir_path in dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"   {LOG_EMOJI_SUCCESS} Created {dir_path.name}/")
        else:
            print(f"   {LOG_EMOJI_SKIP} {dir_path.name}/ already exists")


def fix_add_docker_env_flag():
    """Add DOCKER_ENV flag to docker-compose.yml."""
    docker_compose_path = PROJECT_ROOT / "docker-compose.yml"

    if not docker_compose_path.exists():
        raise FileNotFoundError("docker-compose.yml not found")

    content = docker_compose_path.read_text()

    # Check if DOCKER_ENV is already set
    if "DOCKER_ENV=true" in content:
        print(f"   {LOG_EMOJI_SKIP} DOCKER_ENV already configured")
        return

    # Add DOCKER_ENV to rose service environment
    lines = content.split("\n")
    updated_lines = []
    in_rose_env = False
    added = False

    for i, line in enumerate(lines):
        updated_lines.append(line)

        # Find rose service environment section
        if "rose:" in line or "chainlit:" in line:
            in_rose_env = True
        elif in_rose_env and "environment:" in line:
            # Add DOCKER_ENV after environment: line
            if i + 1 < len(lines):
                indent = len(lines[i + 1]) - len(lines[i + 1].lstrip())
                updated_lines.append(" " * indent + "- DOCKER_ENV=true")
                added = True
                in_rose_env = False
                print(f"   {LOG_EMOJI_INFO} Added DOCKER_ENV=true to environment")

    if added:
        docker_compose_path.write_text("\n".join(updated_lines))
        print(f"   {LOG_EMOJI_SUCCESS} Updated docker-compose.yml")
    else:
        print(f"   {LOG_EMOJI_WARNING} Could not add DOCKER_ENV (manual fix needed)")


# Check functions (Uncle Bob: Separate query from command)

def check_qdrant_url_correct() -> bool:
    """Check if Qdrant URL is correct for local dev."""
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return False

    content = env_path.read_text()
    for line in content.split("\n"):
        if line.startswith("QDRANT_URL="):
            return "localhost:6333" in line or "127.0.0.1:6333" in line
    return False


def check_frontend_deps_installed() -> bool:
    """Check if frontend dependencies are installed."""
    return (PROJECT_ROOT / "frontend" / "node_modules").exists()


def check_python_deps_installed() -> bool:
    """Check if Python dependencies are installed."""
    required_packages = ["langchain", "groq", "elevenlabs"]
    return all(find_spec(pkg) is not None for pkg in required_packages)


def check_frontend_built() -> bool:
    """Check if frontend is built."""
    static_dir = PROJECT_ROOT / "src" / "ai_companion" / "interfaces" / "web" / "static"
    return (static_dir / "index.html").exists()


def check_docker_compose_valid() -> bool:
    """Check if docker-compose.yml is valid."""
    docker_compose_path = PROJECT_ROOT / "docker-compose.yml"
    if not docker_compose_path.exists():
        return False

    content = docker_compose_path.read_text()

    # Check for known issues
    if "Dockerfile.chainlit" in content:
        return False
    if "whatsapp:" in content:
        return False

    return True


def check_memory_dirs_exist() -> bool:
    """Check if memory directories exist."""
    return (
        (PROJECT_ROOT / "short_term_memory").exists() and
        (PROJECT_ROOT / "long_term_memory").exists()
    )


def main():
    """Main entry point."""
    # Fix Windows console encoding for emojis
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Auto-fix Rose deployment issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/fix_deployment_issues.py              # Apply all fixes
  python scripts/fix_deployment_issues.py --dry-run    # Show what would be fixed
        """
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without making changes"
    )

    args = parser.parse_args()

    print(f"\n{BLUE}{LOG_EMOJI_START} Rose Deployment Auto-Fix Tool{RESET}")
    if args.dry_run:
        print(f"{YELLOW}Running in DRY RUN mode - no changes will be made{RESET}")
    print()

    # Define all fixes (Uncle Bob: Declare dependencies explicitly)
    fixes = [
        Fix(
            "Qdrant URL for Local Development",
            "Update QDRANT_URL in .env to use localhost instead of Docker service name",
            fix_qdrant_url_local,
            check_qdrant_url_correct
        ),
        Fix(
            "Python Dependencies",
            "Install Python dependencies using uv sync",
            fix_python_dependencies,
            check_python_deps_installed
        ),
        Fix(
            "Frontend Dependencies",
            "Install frontend dependencies using npm install",
            fix_frontend_dependencies,
            check_frontend_deps_installed
        ),
        Fix(
            "Frontend Build",
            "Build frontend for production using npm run build",
            fix_frontend_build,
            check_frontend_built
        ),
        Fix(
            "Docker Compose Configuration",
            "Fix docker-compose.yml issues (Dockerfile references, service names)",
            fix_docker_compose,
            check_docker_compose_valid
        ),
        Fix(
            "Memory Directories",
            "Create short_term_memory and long_term_memory directories",
            fix_create_memory_dirs,
            check_memory_dirs_exist
        ),
        Fix(
            "Docker Environment Flag",
            "Add DOCKER_ENV=true to docker-compose.yml for environment detection",
            fix_add_docker_env_flag,
            None  # Always apply this fix
        ),
    ]

    # Check which fixes are needed
    log_section("Checking what needs to be fixed...")

    fixes_needed = []
    fixes_skipped = []

    for fix in fixes:
        if fix.needs_fix():
            fixes_needed.append(fix)
            print(f"{LOG_EMOJI_FIX} {fix.name}")
            print(f"   {fix.description}")
        else:
            fixes_skipped.append(fix)
            print(f"{LOG_EMOJI_SKIP} {GREEN}{fix.name}{RESET} (already correct)")

    print()

    if not fixes_needed:
        print(f"{LOG_EMOJI_SUCCESS} {GREEN}All checks passed! No fixes needed.{RESET}\n")
        return 0

    # Apply fixes
    log_section(f"Applying {len(fixes_needed)} fixes...")

    applied = []
    failed = []

    for fix in fixes_needed:
        if fix.apply(dry_run=args.dry_run):
            applied.append(fix)
        else:
            failed.append(fix)

    # Print summary
    log_section("Summary")

    if applied:
        print(f"{LOG_EMOJI_SUCCESS} {GREEN}Applied {len(applied)} fixes:{RESET}")
        for fix in applied:
            print(f"  ✓ {fix.name}")
        print()

    if fixes_skipped:
        print(f"{LOG_EMOJI_SKIP} {BLUE}Skipped {len(fixes_skipped)} (already correct):{RESET}")
        for fix in fixes_skipped:
            print(f"  ✓ {fix.name}")
        print()

    if failed:
        print(f"{LOG_EMOJI_ERROR} {RED}Failed {len(failed)} fixes:{RESET}")
        for fix in failed:
            print(f"  ✗ {fix.name}")
            if fix.error:
                print(f"    Error: {fix.error}")
        print()

    if args.dry_run:
        print(f"{YELLOW}This was a dry run. Run without --dry-run to apply fixes.{RESET}\n")
        return 0

    if failed:
        print(f"{RED}Some fixes failed. Please review errors above and fix manually.{RESET}\n")
        return 1

    print(f"{GREEN}{LOG_EMOJI_SUCCESS} All fixes applied successfully!{RESET}\n")
    print(f"{BLUE}Next steps:{RESET}")
    print("  1. Start Qdrant: docker run -p 6333:6333 qdrant/qdrant:latest")
    print("  2. Run diagnostic: python scripts/diagnose_deployment.py")
    print("  3. Start dev server: python scripts/run_dev_server.py")
    print()

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}{LOG_EMOJI_WARNING} Fix process interrupted by user{RESET}\n")
        sys.exit(130)
    except Exception as e:
        print(f"\n{RED}{LOG_EMOJI_ERROR} Fix process failed: {e}{RESET}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
