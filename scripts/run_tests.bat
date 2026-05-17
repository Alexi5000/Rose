@echo off
REM Test runner script for Rose the Healer Shaman (Windows)

echo ================================
echo Rose Testing Suite
echo ================================
echo.

REM Check if test dependencies are installed
uv pip list | findstr /C:"pytest" >nul
if errorlevel 1 (
    echo Installing test dependencies...
    uv pip install -e ".[test]"
)

REM Parse command line arguments
set TEST_TYPE=%1
if "%TEST_TYPE%"=="" set TEST_TYPE=all
set VERBOSE=%2
if "%VERBOSE%"=="" set VERBOSE=-v

if "%TEST_TYPE%"=="all" (
    echo Running all tests...
    uv run pytest tests/ %VERBOSE%
    goto :end
)

if "%TEST_TYPE%"=="voice" (
    echo Running voice interaction tests...
    uv run pytest tests/test_voice_interaction.py %VERBOSE%
    goto :end
)

if "%TEST_TYPE%"=="character" (
    echo Running Rose character tests...
    uv run pytest tests/test_rose_character.py %VERBOSE%
    goto :end
)

if "%TEST_TYPE%"=="memory" (
    echo Running memory system tests...
    uv run pytest tests/test_memory_therapeutic.py %VERBOSE%
    goto :end
)

if "%TEST_TYPE%"=="performance" (
    echo Running performance tests...
    uv run pytest tests/test_performance.py %VERBOSE%
    goto :end
)

if "%TEST_TYPE%"=="deployment" (
    echo Running deployment tests...
    uv run pytest tests/test_deployment.py %VERBOSE%
    goto :end
)

if "%TEST_TYPE%"=="core" (
    echo Running core tests...
    uv run pytest tests/test_core.py %VERBOSE%
    goto :end
)

if "%TEST_TYPE%"=="coverage" (
    echo Running tests with coverage...
    uv run pytest tests/ --cov=ai_companion --cov-report=html --cov-report=term
    echo.
    echo Coverage report generated in htmlcov/index.html
    goto :end
)

if "%TEST_TYPE%"=="quick" (
    echo Running quick tests (excluding slow tests)...
    uv run pytest tests/ -v -m "not slow"
    goto :end
)

echo Unknown test type: %TEST_TYPE%
echo.
echo Usage: run_tests.bat [test_type] [options]
echo.
echo Test types:
echo   all         - Run all tests (default)
echo   voice       - Voice interaction tests
echo   character   - Rose character tests
echo   memory      - Memory system tests
echo   performance - Performance tests
echo   deployment  - Deployment tests
echo   core        - Core utility tests
echo   coverage    - Run with coverage report
echo   quick       - Run quick tests only
echo.
echo Options:
echo   -v          - Verbose output (default)
echo   -vv         - Very verbose output
echo   -q          - Quiet output
exit /b 1

:end
echo.
echo ================================
echo Tests complete!
echo ================================
