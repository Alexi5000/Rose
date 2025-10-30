# Code Review: scripts/verify_deployment.py

**Date:** October 30, 2025  
**File:** `scripts/verify_deployment.py`  
**Status:** 🔴 CRITICAL ISSUES - Script Will Not Run

---

## 🚨 Critical Issues (Blocking)

### 1. Missing Utility Functions - Script Cannot Run

**Severity:** 🔴 CRITICAL - Script will crash on import

**Problem:** The script imports three functions from `scripts.utils` that don't exist:
```python
from scripts.utils import check_command_exists, check_port_available, check_url_accessible
```

**Impact:** 
- Script will fail immediately with `ImportError`
- Cannot be executed at all
- Blocks deployment verification workflow

**Evidence:**
```bash
# These functions are referenced but don't exist in scripts/utils.py:
- check_command_exists()
- check_port_available()
- check_url_accessible()
```

**Fix Required:** Add these utility functions to `scripts/utils.py`

**Implementation:**

```python
# Add to scripts/utils.py

import shutil
import socket
import urllib.request
from typing import Optional


def check_command_exists(command: str) -> bool:
    """
    Check if a command exists in PATH.
    
    Args:
        command: Command name to check (e.g., 'npm', 'docker', 'uv')
        
    Returns:
        bool: True if command is available, False otherwise
        
    Example:
        >>> if check_command_exists('npm'):
        ...     print("npm is installed")
    """
    # shutil.which handles cross-platform PATH lookup
    # On Windows, it also checks .cmd, .bat, .exe extensions
    return shutil.which(command) is not None


def check_port_available(port: int, host: str = "127.0.0.1") -> bool:
    """
    Check if a port is available (not in use).
    
    Args:
        port: Port number to check
        host: Host address to check (default: localhost)
        
    Returns:
        bool: True if port is available, False if in use
        
    Example:
        >>> if check_port_available(8000):
        ...     print("Port 8000 is free")
        ... else:
        ...     print("Port 8000 is in use")
    """
    try:
        # Try to bind to the port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            # If bind succeeds, port is available
            sock.bind((host, port))
            return True
    except (socket.error, OSError):
        # Port is in use or other error
        return False


def check_url_accessible(url: str, timeout: int = 5) -> bool:
    """
    Check if a URL is accessible and returns 200 OK.
    
    Args:
        url: URL to check (e.g., 'http://localhost:6333/health')
        timeout: Request timeout in seconds
        
    Returns:
        bool: True if URL is accessible, False otherwise
        
    Example:
        >>> if check_url_accessible('http://localhost:6333'):
        ...     print("Qdrant is running")
    """
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status == 200
    except Exception:
        # Any error means URL is not accessible
        return False
```

**Priority:** 🔴 CRITICAL - Must fix before script can run

---

### 2. Unused Imports

**Severity:** 🟡 IMPORTANT - Code quality issue

**Problem:** Two imports are unused:
```python
from src.ai_companion.config.server_config import (
    DEV_BACKEND_PORT,  # ❌ Imported but never used
    DEV_FRONTEND_PORT,
    FRONTEND_BUILD_DIR,
    LOG_EMOJI_ERROR,
    LOG_EMOJI_SUCCESS,
    LOG_EMOJI_WARNING,  # ❌ Imported but never used
    WEB_SERVER_PORT,
)
```

**Why it matters:**
- Clutters namespace
- Confuses readers about what's actually used
- Violates clean code principles
- Fails linting checks

**Fix:**

```python
from src.ai_companion.config.server_config import (
    DEV_FRONTEND_PORT,
    FRONTEND_BUILD_DIR,
    LOG_EMOJI_ERROR,
    LOG_EMOJI_SUCCESS,
    WEB_SERVER_PORT,
)
```

**Priority:** 🟡 IMPORTANT - Fix for code quality

---

## 🟡 Important Issues (Code Quality)

### 3. Inconsistent Error Handling Pattern

**Problem:** The `VerificationResult` class and verification methods mix concerns.

**Current Pattern:**
```python
def verify_environment_file(self) -> VerificationResult:
    """Verify .env file exists and has required keys."""
    env_file = PROJECT_ROOT / ".env"
    
    if not env_file.exists():
        return VerificationResult(
            "Environment File",
            False,
            ".env file not found",
            "Copy .env.example to .env and fill in your API keys"
        )
    # ... more checks
```

**Issue:** Each verification method returns a `VerificationResult` directly, but the class also has an `add_result` method that logs. This creates two responsibilities.

**Better Pattern - Separate Concerns:**

```python
class VerificationCheck:
    """Represents a single verification check (data only)."""
    
    def __init__(
        self,
        name: str,
        check_func: Callable[[], tuple[bool, str, str]],
        category: str = "General"
    ):
        self.name = name
        self.check_func = check_func
        self.category = category
        self.result: Optional[VerificationResult] = None
    
    def run(self) -> VerificationResult:
        """Execute the check and store result."""
        try:
            passed, message, details = self.check_func()
            self.result = VerificationResult(self.name, passed, message, details)
        except Exception as e:
            self.result = VerificationResult(
                self.name,
                False,
                f"Check failed with exception: {type(e).__name__}",
                str(e)
            )
        return self.result


class DeploymentVerifier:
    """Orchestrates verification checks (single responsibility)."""
    
    def __init__(self):
        self.checks: list[VerificationCheck] = []
        self.results: list[VerificationResult] = []
    
    def add_check(self, check: VerificationCheck) -> None:
        """Register a check to run."""
        self.checks.append(check)
    
    def run_all_checks(self) -> bool:
        """Run all registered checks."""
        for check in self.checks:
            result = check.run()
            self.results.append(result)
            self._log_result(result)
        
        return all(r.passed for r in self.results)
    
    def _log_result(self, result: VerificationResult) -> None:
        """Log a single result (private helper)."""
        if result.passed:
            logger.info(
                f"{LOG_EMOJI_SUCCESS} verification_passed",
                check=result.name,
                message=result.message
            )
        else:
            logger.error(
                f"{LOG_EMOJI_ERROR} verification_failed",
                check=result.name,
                message=result.message,
                details=result.details
            )
```

**Benefits:**
- Single Responsibility: Each class does one thing
- Easier to test: Can test checks independently
- More flexible: Can add checks dynamically
- Better separation: Data vs. orchestration

**Priority:** 🟡 IMPORTANT - Improves maintainability

---

### 4. Hardcoded Print Statements Instead of Logging

**Problem:** The script mixes `print()` and `logger` calls inconsistently.

**Current:**
```python
def run_all_checks(self) -> bool:
    """Run all verification checks."""
    print("🔍 Rose Deployment Verification")  # ❌ Should use logger
    print("=" * 60)
    print()
    
    print("📋 Phase 1: Environment Setup")  # ❌ Should use logger
    self.add_result(self.verify_environment_file())
```

**Why it matters:**
- Inconsistent logging approach
- Can't control output level (always prints)
- Doesn't integrate with structured logging
- Hard to test (can't capture output easily)

**Better Approach:**

```python
def run_all_checks(self) -> bool:
    """Run all verification checks."""
    # Use logger for structured output
    logger.info("🔍 deployment_verification_starting")
    
    # Phase 1
    logger.info("📋 phase_starting", phase=1, name="Environment Setup")
    self.add_result(self.verify_environment_file())
    self.add_result(self.verify_python_version())
    
    # ... rest of phases
    
    # Summary
    logger.info(
        "📊 verification_summary",
        passed=self.passed_count,
        failed=self.failed_count,
        total=len(self.results)
    )
    
    return self.failed_count == 0
```

**For User-Facing Output:** If you need pretty console output, create a separate formatter:

```python
class ConsoleReporter:
    """Formats verification results for console output."""
    
    @staticmethod
    def print_header(text: str) -> None:
        """Print a section header."""
        print(f"\n{text}")
        print("=" * 60)
    
    @staticmethod
    def print_phase(phase_num: int, phase_name: str) -> None:
        """Print phase header."""
        print(f"\n📋 Phase {phase_num}: {phase_name}")
    
    @staticmethod
    def print_result(result: VerificationResult) -> None:
        """Print a single result."""
        emoji = "✅" if result.passed else "❌"
        print(f"{emoji} {result.name}: {result.message}")
        if result.details:
            print(f"   {result.details}")
```

**Priority:** 🟡 IMPORTANT - Consistency and testability

---

### 5. Magic Strings for Phase Names

**Problem:** Phase names are hardcoded strings scattered throughout the code.

**Current:**
```python
print("📋 Phase 1: Environment Setup")
# ... later ...
print("📦 Phase 2: Dependencies")
# ... later ...
print("🎨 Phase 3: Build Artifacts")
```

**Better - Extract Constants:**

```python
# At module level
class VerificationPhase:
    """Verification phase constants."""
    ENVIRONMENT = "Environment Setup"
    DEPENDENCIES = "Dependencies"
    BUILD_ARTIFACTS = "Build Artifacts"
    SERVICES = "Services"
    PORT_AVAILABILITY = "Port Availability"


# Usage
print(f"📋 Phase 1: {VerificationPhase.ENVIRONMENT}")
```

**Even Better - Use Enum:**

```python
from enum import Enum

class VerificationPhase(Enum):
    """Verification phases with metadata."""
    ENVIRONMENT = (1, "📋", "Environment Setup")
    DEPENDENCIES = (2, "📦", "Dependencies")
    BUILD_ARTIFACTS = (3, "🎨", "Build Artifacts")
    SERVICES = (4, "🔌", "Services")
    PORT_AVAILABILITY = (5, "🌐", "Port Availability")
    
    def __init__(self, number: int, emoji: str, name: str):
        self.number = number
        self.emoji = emoji
        self.phase_name = name
    
    def __str__(self) -> str:
        return f"{self.emoji} Phase {self.number}: {self.phase_name}"


# Usage
print(str(VerificationPhase.ENVIRONMENT))
# Output: 📋 Phase 1: Environment Setup
```

**Priority:** 🟢 NICE-TO-HAVE - Improves maintainability

---

## 🟢 Nice-to-Have Improvements

### 6. Add Type Hints to VerificationResult.__str__

**Current:**
```python
def __str__(self) -> str:
    emoji = LOG_EMOJI_SUCCESS if self.passed else LOG_EMOJI_ERROR
    result = f"{emoji} {self.name}: {self.message}"
    if self.details:
        result += f"\n   {self.details}"
    return result
```

**Suggestion:** This is actually fine, but could be more explicit:

```python
def __str__(self) -> str:
    """Format result as human-readable string."""
    emoji: str = LOG_EMOJI_SUCCESS if self.passed else LOG_EMOJI_ERROR
    result: str = f"{emoji} {self.name}: {self.message}"
    if self.details:
        result += f"\n   {self.details}"
    return result
```

**Priority:** 🟢 NICE-TO-HAVE - Minor clarity improvement

---

### 7. Extract Verification Logic to Separate Functions

**Problem:** All verification methods are in the `DeploymentVerifier` class, making it large.

**Current Structure:**
```python
class DeploymentVerifier:
    def verify_environment_file(self) -> VerificationResult: ...
    def verify_python_version(self) -> VerificationResult: ...
    def verify_command_available(self, ...) -> VerificationResult: ...
    def verify_frontend_build(self) -> VerificationResult: ...
    def verify_qdrant_running(self) -> VerificationResult: ...
    def verify_port_available(self, ...) -> VerificationResult: ...
    def verify_memory_directories(self) -> VerificationResult: ...
    def run_all_checks(self) -> bool: ...
```

**Better - Extract to Module-Level Functions:**

```python
# Verification functions (pure, testable)
def check_environment_file() -> tuple[bool, str, str]:
    """Check if .env file exists with required keys."""
    env_file = PROJECT_ROOT / ".env"
    
    if not env_file.exists():
        return (
            False,
            ".env file not found",
            "Copy .env.example to .env and fill in your API keys"
        )
    
    # Check for required keys
    required_keys = ["GROQ_API_KEY", "ELEVENLABS_API_KEY", ...]
    env_content = env_file.read_text()
    missing_keys = [k for k in required_keys if f"{k}=" not in env_content]
    
    if missing_keys:
        return (
            False,
            "Missing required environment variables",
            f"Missing: {', '.join(missing_keys)}"
        )
    
    return (True, ".env file exists with required keys", "")


def check_python_version(
    required: tuple[int, int] = REQUIRED_PYTHON_VERSION
) -> tuple[bool, str, str]:
    """Check if Python version meets requirements."""
    current = sys.version_info[:2]
    
    if current < required:
        return (
            False,
            f"Python {required[0]}.{required[1]}+ required",
            f"Current version: {current[0]}.{current[1]}"
        )
    
    return (
        True,
        f"Python {current[0]}.{current[1]} meets requirements",
        ""
    )


# Simplified verifier class
class DeploymentVerifier:
    """Orchestrates deployment verification checks."""
    
    def __init__(self):
        self.results: list[VerificationResult] = []
        self._setup_checks()
    
    def _setup_checks(self) -> None:
        """Register all verification checks."""
        self.checks = [
            VerificationCheck("Environment File", check_environment_file),
            VerificationCheck("Python Version", check_python_version),
            # ... more checks
        ]
    
    def run_all_checks(self) -> bool:
        """Run all checks and return overall success."""
        for check in self.checks:
            result = check.run()
            self.results.append(result)
            self._log_result(result)
        
        return all(r.passed for r in self.results)
```

**Benefits:**
- Easier to test: Pure functions with clear inputs/outputs
- Better reusability: Can use checks in other scripts
- Smaller class: Single responsibility (orchestration)
- More maintainable: Each check is independent

**Priority:** 🟢 NICE-TO-HAVE - Improves testability

---

### 8. Add Progress Indicator for Long-Running Checks

**Problem:** Some checks (like Qdrant connectivity) may take several seconds with no feedback.

**Suggestion:** Add a simple spinner or progress indicator:

```python
import itertools
import threading
import time


class Spinner:
    """Simple spinner for long-running operations."""
    
    def __init__(self, message: str):
        self.message = message
        self.spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        self.running = False
        self.thread: Optional[threading.Thread] = None
    
    def __enter__(self):
        self.running = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.start()
        return self
    
    def __exit__(self, *args):
        self.running = False
        if self.thread:
            self.thread.join()
        # Clear the line
        print('\r' + ' ' * (len(self.message) + 10) + '\r', end='')
    
    def _spin(self):
        while self.running:
            print(f'\r{next(self.spinner)} {self.message}...', end='', flush=True)
            time.sleep(0.1)


# Usage
def verify_qdrant_running(self) -> VerificationResult:
    """Verify Qdrant is running and accessible."""
    with Spinner("Checking Qdrant connectivity"):
        accessible = check_url_accessible(QDRANT_HEALTH_URL, timeout=5)
    
    if accessible:
        return VerificationResult(
            "Qdrant Service",
            True,
            f"Qdrant is running on port {QDRANT_DEFAULT_PORT}"
        )
    
    return VerificationResult(
        "Qdrant Service",
        False,
        "Qdrant is not accessible",
        f"Start Qdrant with 'docker compose up qdrant -d'"
    )
```

**Priority:** 🟢 NICE-TO-HAVE - UX improvement

---

## 📊 Summary

### Critical Issues (Must Fix)
1. **Missing utility functions** - Script cannot run (ImportError)
2. **Unused imports** - Code quality issue

### Important Issues (Should Fix)
3. **Inconsistent error handling** - Mix of concerns
4. **Hardcoded print statements** - Should use logger
5. **Magic strings** - Extract phase names to constants

### Nice-to-Have (Optional)
6. **Type hints** - Minor clarity improvement
7. **Extract verification logic** - Better testability
8. **Progress indicators** - Better UX

---

## 🎯 Recommended Action Plan

### Immediate (Before Script Can Run)
1. **Add missing utility functions to `scripts/utils.py`** (15 minutes)
   - `check_command_exists()`
   - `check_port_available()`
   - `check_url_accessible()`

2. **Remove unused imports** (1 minute)
   - Remove `DEV_BACKEND_PORT`
   - Remove `LOG_EMOJI_WARNING`

### Short-term (This Week)
3. **Refactor verification pattern** (30 minutes)
   - Extract check functions
   - Simplify DeploymentVerifier class
   - Improve separation of concerns

4. **Standardize logging** (15 minutes)
   - Replace print() with logger calls
   - Add ConsoleReporter for user-facing output

### Long-term (Next Sprint)
5. **Add progress indicators** (20 minutes)
6. **Extract constants** (10 minutes)
7. **Add unit tests** (1 hour)

---

## 🧪 Testing Recommendations

Once the missing functions are added, test the script:

```bash
# Test the script runs without errors
python scripts/verify_deployment.py

# Test with missing .env
mv .env .env.backup
python scripts/verify_deployment.py
mv .env.backup .env

# Test with Qdrant not running
docker stop rose-qdrant
python scripts/verify_deployment.py
docker start rose-qdrant

# Test all checks pass
python scripts/verify_deployment.py
```

---

## 💡 Code Quality Score

| Aspect | Score | Notes |
|--------|-------|-------|
| **Functionality** | 0/10 | Cannot run (missing imports) |
| **Code Structure** | 7/10 | Good class design, but mixed concerns |
| **Type Safety** | 9/10 | Excellent type hints |
| **Documentation** | 9/10 | Good docstrings |
| **Error Handling** | 8/10 | Comprehensive, but could be more consistent |
| **Testability** | 6/10 | Hard to test due to tight coupling |
| **Maintainability** | 7/10 | Clear intent, but large class |
| **Overall** | **6.6/10** | Good foundation, critical bugs block execution |

---

**Bottom Line:** The script has excellent structure and documentation, but **cannot run** due to missing utility functions. Once those are added, it will be production-ready with minor improvements recommended for long-term maintainability.
