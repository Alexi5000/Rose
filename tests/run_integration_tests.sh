#!/bin/bash
# Script to run integration and E2E tests
# Usage: ./tests/run_integration_tests.sh [test_type]
# test_type: integration, e2e, smoke, or all (default: all)

set -e

TEST_TYPE=${1:-all}

echo "=========================================="
echo "Running Integration and E2E Tests"
echo "=========================================="
echo ""

# Check if required environment variables are set
if [ -z "$GROQ_API_KEY" ] || [ -z "$ELEVENLABS_API_KEY" ] || [ -z "$QDRANT_URL" ]; then
    echo "⚠️  Warning: Some API keys are not set"
    echo "Integration tests will be skipped"
    echo ""
    echo "Required environment variables:"
    echo "  - GROQ_API_KEY"
    echo "  - ELEVENLABS_API_KEY"
    echo "  - QDRANT_URL"
    echo "  - QDRANT_API_KEY"
    echo ""
fi

# Function to run tests
run_tests() {
    local marker=$1
    local description=$2
    
    echo "Running $description..."
    echo "----------------------------------------"
    
    if [ "$marker" == "e2e" ]; then
        # E2E tests require server to be running
        echo "⚠️  Note: E2E tests require the server to be running on http://localhost:8080"
        echo "Start server with: uvicorn ai_companion.interfaces.web.app:app --port 8080"
        echo ""
        pytest tests/test_e2e_playwright.py -v -m e2e --tb=short
    else
        pytest tests/ -v -m "$marker" --tb=short
    fi
    
    echo ""
}

# Run tests based on type
case $TEST_TYPE in
    integration)
        run_tests "integration" "Integration Tests"
        ;;
    e2e)
        run_tests "e2e" "End-to-End Tests"
        ;;
    smoke)
        run_tests "smoke" "Smoke Tests"
        ;;
    all)
        echo "Running all integration and E2E tests..."
        echo ""
        
        # Integration tests
        if [ -n "$GROQ_API_KEY" ] && [ -n "$ELEVENLABS_API_KEY" ] && [ -n "$QDRANT_URL" ]; then
            run_tests "integration" "Integration Tests"
        else
            echo "⚠️  Skipping integration tests (API keys not set)"
            echo ""
        fi
        
        # Smoke tests
        run_tests "smoke" "Smoke Tests"
        
        # E2E tests (optional)
        echo "⚠️  E2E tests require manual server startup"
        echo "To run E2E tests:"
        echo "  1. Start server: uvicorn ai_companion.interfaces.web.app:app --port 8080"
        echo "  2. Run: pytest tests/test_e2e_playwright.py -v -m e2e"
        echo ""
        ;;
    *)
        echo "❌ Invalid test type: $TEST_TYPE"
        echo "Valid options: integration, e2e, smoke, all"
        exit 1
        ;;
esac

echo "=========================================="
echo "✅ Test run complete"
echo "=========================================="
