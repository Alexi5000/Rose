@echo off
REM Script to run integration and E2E tests on Windows
REM Usage: tests\run_integration_tests.bat [test_type]
REM test_type: integration, e2e, smoke, or all (default: all)

setlocal enabledelayedexpansion

set TEST_TYPE=%1
if "%TEST_TYPE%"=="" set TEST_TYPE=all

echo ==========================================
echo Running Integration and E2E Tests
echo ==========================================
echo.

REM Check if required environment variables are set
if "%GROQ_API_KEY%"=="" (
    echo Warning: GROQ_API_KEY is not set
    echo Integration tests will be skipped
    echo.
)

if "%ELEVENLABS_API_KEY%"=="" (
    echo Warning: ELEVENLABS_API_KEY is not set
    echo Integration tests will be skipped
    echo.
)

if "%QDRANT_URL%"=="" (
    echo Warning: QDRANT_URL is not set
    echo Integration tests will be skipped
    echo.
)

REM Run tests based on type
if "%TEST_TYPE%"=="integration" (
    echo Running Integration Tests...
    echo ----------------------------------------
    pytest tests/test_integration.py -v -m integration --tb=short
    goto :end
)

if "%TEST_TYPE%"=="e2e" (
    echo Running End-to-End Tests...
    echo ----------------------------------------
    echo Note: E2E tests require the server to be running on http://localhost:8080
    echo Start server with: uvicorn ai_companion.interfaces.web.app:app --port 8080
    echo.
    pytest tests/test_e2e_playwright.py -v -m e2e --tb=short
    goto :end
)

if "%TEST_TYPE%"=="smoke" (
    echo Running Smoke Tests...
    echo ----------------------------------------
    pytest tests/ -v -m smoke --tb=short
    goto :end
)

if "%TEST_TYPE%"=="all" (
    echo Running all integration and E2E tests...
    echo.
    
    REM Integration tests
    if not "%GROQ_API_KEY%"=="" if not "%ELEVENLABS_API_KEY%"=="" if not "%QDRANT_URL%"=="" (
        echo Running Integration Tests...
        echo ----------------------------------------
        pytest tests/test_integration.py -v -m integration --tb=short
        echo.
    ) else (
        echo Skipping integration tests ^(API keys not set^)
        echo.
    )
    
    REM Smoke tests
    echo Running Smoke Tests...
    echo ----------------------------------------
    pytest tests/ -v -m smoke --tb=short
    echo.
    
    REM E2E tests info
    echo Note: E2E tests require manual server startup
    echo To run E2E tests:
    echo   1. Start server: uvicorn ai_companion.interfaces.web.app:app --port 8080
    echo   2. Run: pytest tests/test_e2e_playwright.py -v -m e2e
    echo.
    goto :end
)

echo Invalid test type: %TEST_TYPE%
echo Valid options: integration, e2e, smoke, all
exit /b 1

:end
echo ==========================================
echo Test run complete
echo ==========================================
