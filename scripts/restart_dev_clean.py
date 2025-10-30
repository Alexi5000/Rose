#!/usr/bin/env python3
"""
🔄 Clean Restart Development Servers

Stops all servers, clears caches, and restarts everything fresh.
Use this when frontend CSS/JS isn't loading properly.

Usage:
    python scripts/restart_dev_clean.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_step(emoji: str, message: str):
    """Print a step message."""
    print(f"\n{emoji} {BLUE}{message}{RESET}")

def print_success(message: str):
    """Print a success message."""
    print(f"   {GREEN}✓ {message}{RESET}")

def print_error(message: str):
    """Print an error message."""
    print(f"   {RED}✗ {message}{RESET}")

def main():
    """Main entry point."""
    # Fix Windows console encoding
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    print(f"\n{BLUE}🔄 Clean Restart Development Servers{RESET}")
    print(f"{YELLOW}This will stop servers, clear caches, and restart fresh{RESET}\n")

    # Step 1: Clear Vite cache
    print_step("🧹", "Clearing Vite cache...")
    vite_cache = PROJECT_ROOT / "frontend" / "node_modules" / ".vite"
    if vite_cache.exists():
        try:
            shutil.rmtree(vite_cache)
            print_success("Vite cache cleared")
        except Exception as e:
            print_error(f"Failed to clear Vite cache: {e}")
    else:
        print_success("No Vite cache to clear")

    # Step 2: Clear frontend build
    print_step("🧹", "Clearing frontend build...")
    static_dir = PROJECT_ROOT / "src" / "ai_companion" / "interfaces" / "web" / "static"
    if static_dir.exists():
        try:
            shutil.rmtree(static_dir)
            print_success("Frontend build cleared")
        except Exception as e:
            print_error(f"Failed to clear build: {e}")
    else:
        print_success("No build to clear")

    # Step 3: Rebuild frontend
    print_step("🎨", "Building frontend...")
    try:
        npm_cmd = shutil.which("npm") or shutil.which("npm.cmd")
        if not npm_cmd:
            raise RuntimeError("npm not found")

        result = subprocess.run(
            [npm_cmd, "run", "build"],
            cwd=PROJECT_ROOT / "frontend",
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print_success("Frontend built successfully")
        else:
            print_error(f"Build failed: {result.stderr}")
            return 1
    except Exception as e:
        print_error(f"Failed to build frontend: {e}")
        return 1

    # Step 4: Start dev server
    print_step("🚀", "Starting development servers...")
    print(f"\n{YELLOW}Starting servers... (this will take ~10 seconds){RESET}")
    print(f"{YELLOW}Press Ctrl+C to stop when you're done testing{RESET}\n")

    try:
        # Start dev server (this will block)
        subprocess.run(
            ["python", "scripts/run_dev_server.py"],
            cwd=PROJECT_ROOT
        )
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}🛑 Stopping servers...{RESET}")
        print(f"{GREEN}✓ Servers stopped{RESET}\n")
        return 0
    except Exception as e:
        print_error(f"Failed to start servers: {e}")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⚠️  Interrupted by user{RESET}\n")
        sys.exit(130)
    except Exception as e:
        print(f"\n{RED}❌ Error: {e}{RESET}\n")
        sys.exit(1)
