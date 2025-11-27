#!/usr/bin/env python3
"""
🎯 Rose Quick Start Script

Interactive guide to get Rose up and running quickly.
Asks user questions and runs appropriate deployment.

Usage:
    python scripts/quick_start.py
"""

import io
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ai_companion.config.server_config import LOG_EMOJI_STARTUP, LOG_EMOJI_SUCCESS  # noqa: E402
from src.ai_companion.core.logging_config import configure_logging, get_logger  # noqa: E402

configure_logging()
logger = get_logger(__name__)


def print_banner() -> None:
    """Print welcome banner."""
    print()
    print("🌹" * 30)
    print()
    print("     ROSE THE HEALER SHAMAN")
    print("     Quick Start Guide")
    print()
    print("🌹" * 30)
    print()


def ask_question(question: str, options: list[str], default: str = "") -> str:
    """Ask user a question with options."""
    print(f"\n{question}")
    for i, option in enumerate(options, 1):
        default_marker = " (default)" if option == default else ""
        print(f"  {i}. {option}{default_marker}")

    while True:
        choice = input("\nYour choice (number or Enter for default): ").strip()

        if not choice and default:
            return default

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            pass

        print("❌ Invalid choice. Please enter a number from the list.")


def check_env_file() -> bool:
    """Check if .env file exists."""
    env_file = PROJECT_ROOT / ".env"
    return env_file.exists()


def main() -> None:
    """Main entry point."""
    # Set UTF-8 encoding for Windows console
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    logger.info(f"{LOG_EMOJI_STARTUP} quick_start_beginning")

    print_banner()

    print("Welcome! Let's get Rose up and running.")
    print()

    # Check environment file
    if not check_env_file():
        print("⚠️  No .env file found!")
        print()
        print("Before we continue, you need to:")
        print("  1. Copy .env.example to .env")
        print("  2. Fill in your API keys:")
        print("     • GROQ_API_KEY (https://console.groq.com/)")
        print("     • ELEVENLABS_API_KEY (https://elevenlabs.io/)")
        print("     • ELEVENLABS_VOICE_ID (https://elevenlabs.io/)")
        print("     • QDRANT_URL (https://cloud.qdrant.io/)")
        print()
        print("Run this command to copy the example:")
        print("  copy .env.example .env")
        print()
        sys.exit(1)

    print(f"{LOG_EMOJI_SUCCESS} .env file found!")
    print()

    # Ask about deployment mode
    mode = ask_question(
        "How would you like to run Rose?",
        [
            "Docker (Production-like, isolated)",
            "Local Development (Hot reload, debugging)",
            "Just verify setup (Don't start anything)",
        ],
        default="Docker (Production-like, isolated)",
    )

    print()
    print("=" * 60)
    print()

    if "Docker" in mode:
        print("🐳 Starting Docker deployment...")
        print()
        print("This will:")
        print("  1. Stop any running services")
        print("  2. Build Docker containers")
        print("  3. Start all services")
        print("  4. Verify health")
        print()
        print("This may take a few minutes...")
        print()

        import subprocess

        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "deploy_rose_clean.py"), "--mode", "docker"],
            cwd=PROJECT_ROOT,
        )

        if result.returncode == 0:
            print()
            print(f"{LOG_EMOJI_SUCCESS} Rose is ready!")
            print()
            print("🌐 Open your browser to: http://localhost:8000")
            print()
        else:
            print()
            print("❌ Deployment failed. Check the logs above for details.")
            print()

    elif "Local" in mode:
        print("💻 Setting up local development...")
        print()
        print("This will:")
        print("  1. Verify prerequisites")
        print("  2. Start Qdrant in Docker")
        print("  3. Start development servers")
        print()

        import subprocess

        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "deploy_rose_clean.py"), "--mode", "local"],
            cwd=PROJECT_ROOT,
        )

        if result.returncode == 0:
            print()
            print("Ready to start development servers!")
            print()
            start_now = input("Start dev servers now? (y/n): ").strip().lower()

            if start_now == "y":
                subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "run_dev_server.py")], cwd=PROJECT_ROOT)

    else:  # Verify only
        print("🔍 Running verification checks...")
        print()

        import subprocess

        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "verify_deployment.py")], cwd=PROJECT_ROOT
        )

        if result.returncode == 0:
            print()
            print("All checks passed! You're ready to deploy.")
            print()
            print("Run this script again to start Rose.")
            print()

    logger.info(f"{LOG_EMOJI_SUCCESS} quick_start_complete")


if __name__ == "__main__":
    main()
