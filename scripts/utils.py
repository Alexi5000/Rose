#!/usr/bin/env python3
"""
🛠️ Script Utilities

Shared utilities for development and production scripts.
Provides platform-aware subprocess execution and server health checking.
"""

import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

from src.ai_companion.config.server_config import LOG_EMOJI_ERROR, LOG_EMOJI_SUCCESS, LOG_EMOJI_WARNING
from src.ai_companion.core.logging_config import get_logger

logger = get_logger(__name__)


def run_command(
    command: str | list[str],
    cwd: Path | None = None,
    shell: bool | None = None,
    **kwargs: Any,
) -> subprocess.Popen:
    """
    Run a command with platform-appropriate settings.

    On Windows, uses shell=True to find executables in PATH.
    On Unix-like systems, uses list format for better security.

    Args:
        command: Command string (Windows) or list (Unix)
        cwd: Working directory
        shell: Override shell setting (auto-detected if None)
        **kwargs: Additional arguments passed to Popen

    Returns:
        subprocess.Popen: Running process

    Raises:
        FileNotFoundError: If command executable is not found
        PermissionError: If insufficient permissions to execute
        subprocess.SubprocessError: For other subprocess-related errors
    """
    if shell is None:
        shell = sys.platform == "win32"

    # Convert list to string on Windows if needed
    if shell and isinstance(command, list):
        command = " ".join(command)
    # Convert string to list on Unix if needed
    elif not shell and isinstance(command, str):
        command = command.split()

    try:
        return subprocess.Popen(command, cwd=cwd, shell=shell, **kwargs)
    except FileNotFoundError as e:
        # Extract command name for better error message
        cmd_name = command if isinstance(command, str) else command[0]
        logger.error(
            f"{LOG_EMOJI_ERROR} command_not_found",
            command=cmd_name,
            error=str(e),
        )
        raise
    except PermissionError as e:
        logger.error(
            f"{LOG_EMOJI_ERROR} permission_denied",
            command=command,
            error=str(e),
        )
        raise


def run_command_sync(
    command: str | list[str],
    cwd: Path | None = None,
    shell: bool | None = None,
    **kwargs: Any,
) -> subprocess.CompletedProcess:
    """
    Run a command synchronously with platform-appropriate settings.

    Similar to run_command but waits for completion and returns result.

    Args:
        command: Command string (Windows) or list (Unix)
        cwd: Working directory
        shell: Override shell setting (auto-detected if None)
        **kwargs: Additional arguments passed to subprocess.run

    Returns:
        subprocess.CompletedProcess: Completed process result

    Raises:
        FileNotFoundError: If command executable is not found
        PermissionError: If insufficient permissions to execute
        subprocess.SubprocessError: For other subprocess-related errors
    """
    if shell is None:
        shell = sys.platform == "win32"

    # Convert list to string on Windows if needed
    if shell and isinstance(command, list):
        command = " ".join(command)
    # Convert string to list on Unix if needed
    elif not shell and isinstance(command, str):
        command = command.split()

    try:
        return subprocess.run(command, cwd=cwd, shell=shell, **kwargs)
    except FileNotFoundError as e:
        cmd_name = command if isinstance(command, str) else command[0]
        logger.error(
            f"{LOG_EMOJI_ERROR} command_not_found",
            command=cmd_name,
            error=str(e),
        )
        raise
    except PermissionError as e:
        logger.error(
            f"{LOG_EMOJI_ERROR} permission_denied",
            command=command,
            error=str(e),
        )
        raise


def wait_for_server(url: str, timeout: int = 30, check_interval: float = 0.5) -> bool:
    """
    Wait for a server to become responsive.

    Polls the given URL until it responds successfully or timeout is reached.

    Args:
        url: URL to check (e.g., http://localhost:8000/api/v1/health)
        timeout: Maximum time to wait in seconds
        check_interval: Time between checks in seconds

    Returns:
        bool: True if server is responsive, False if timeout

    Example:
        >>> if wait_for_server("http://localhost:8000/api/v1/health", timeout=10):
        ...     print("Server is ready!")
        ... else:
        ...     print("Server failed to start")
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    logger.info(f"{LOG_EMOJI_SUCCESS} server_health_check_passed", url=url)
                    return True
        except Exception:
            # Server not ready yet, continue waiting
            time.sleep(check_interval)

    logger.error(f"{LOG_EMOJI_ERROR} server_health_check_timeout", url=url, timeout=timeout)
    return False


def terminate_process_gracefully(
    process: subprocess.Popen,
    name: str,
    timeout: int = 5,
) -> bool:
    """
    Terminate a process gracefully with fallback to force kill.

    Attempts graceful termination first, then force kills if necessary.

    Args:
        process: Process to terminate
        name: Process name for logging
        timeout: Seconds to wait for graceful shutdown

    Returns:
        bool: True if terminated gracefully, False if force killed

    Example:
        >>> process = subprocess.Popen(["python", "server.py"])
        >>> if terminate_process_gracefully(process, "server"):
        ...     print("Stopped gracefully")
        ... else:
        ...     print("Had to force kill")
    """
    # Check if process is already terminated
    if process.poll() is not None:
        logger.info(f"{LOG_EMOJI_SUCCESS} process_already_terminated", name=name)
        return True

    # Attempt graceful termination
    process.terminate()

    try:
        process.wait(timeout=timeout)
        logger.info(f"{LOG_EMOJI_SUCCESS} process_terminated_gracefully", name=name)
        return True
    except subprocess.TimeoutExpired:
        # Force kill if graceful shutdown fails
        logger.error(
            f"{LOG_EMOJI_ERROR} graceful_shutdown_timeout_forcing_kill",
            name=name,
            timeout=timeout,
        )

        # Only kill if still running
        if process.poll() is None:
            process.kill()
            process.wait()  # Wait for kill to complete
            logger.info(f"{LOG_EMOJI_SUCCESS} process_force_killed", name=name)

        return False


def check_command_exists(command: str) -> bool:
    """
    Check if a command exists in PATH.

    Args:
        command: Command name to check (e.g., 'npm', 'docker', 'uv')

    Returns:
        bool: True if command is found, False otherwise

    Example:
        >>> if check_command_exists("npm"):
        ...     print("npm is installed")
        ... else:
        ...     print("npm not found")
    """
    # On Windows, check for .cmd and .ps1 variants
    if sys.platform == "win32":
        found = shutil.which(command) or shutil.which(f"{command}.cmd") or shutil.which(f"{command}.ps1")
    else:
        found = shutil.which(command)

    if found:
        logger.info(f"{LOG_EMOJI_SUCCESS} command_found", command=command, path=found)
        return True

    logger.warning(f"{LOG_EMOJI_WARNING} command_not_found", command=command)
    return False


def check_port_available(port: int, host: str = "localhost") -> bool:
    """
    Check if a port is available for binding.

    Args:
        port: Port number to check
        host: Host address to check (default: localhost)

    Returns:
        bool: True if port is available, False if in use

    Example:
        >>> if check_port_available(8000):
        ...     print("Port 8000 is available")
        ... else:
        ...     print("Port 8000 is in use")
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            if result == 0:
                # Port is in use
                logger.warning(f"{LOG_EMOJI_WARNING} port_in_use", port=port, host=host)
                return False
            # Port is available
            logger.info(f"{LOG_EMOJI_SUCCESS} port_available", port=port, host=host)
            return True
    except socket.error as e:
        logger.error(f"{LOG_EMOJI_ERROR} port_check_failed", port=port, host=host, error=str(e))
        return False


def check_url_accessible(url: str, timeout: int = 5) -> bool:
    """
    Check if a URL is accessible.

    Args:
        url: URL to check (e.g., http://localhost:6333)
        timeout: Request timeout in seconds

    Returns:
        bool: True if URL is accessible, False otherwise

    Example:
        >>> if check_url_accessible("http://localhost:6333"):
        ...     print("Qdrant is running")
        ... else:
        ...     print("Qdrant is not accessible")
    """
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            if response.status == 200:
                logger.info(f"{LOG_EMOJI_SUCCESS} url_accessible", url=url)
                return True
            logger.warning(f"{LOG_EMOJI_WARNING} url_returned_non_200", url=url, status=response.status)
            return False
    except Exception as e:
        logger.warning(f"{LOG_EMOJI_WARNING} url_not_accessible", url=url, error=str(e))
        return False
