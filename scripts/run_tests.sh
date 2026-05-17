#!/bin/bash
# Test runner script for Rose the Healer Shaman

set -e

echo "================================"
echo "Rose Testing Suite"
echo "================================"
echo ""

# Check if test dependencies are installed
if ! uv pip list | grep -q pytest; then
    echo "Installing test dependencies..."
    uv pip install -e ".[test]"
fi

# Parse command line arguments
TEST_TYPE=${1:-all}
VERBOSE=${2:--v}

case $TEST_TYPE in
    "all")
        echo "Running all tests..."
        uv run pytest tests/ $VERBOSE
        ;;
    "voice")
        echo "Running voice interaction tests..."
        uv run pytest tests/test_voice_interaction.py $VERBOSE
        ;;
    "character")
        echo "Running Rose character tests..."
        uv run pytest tests/test_rose_character.py $VERBOSE
        ;;
    "memory")
        echo "Running memory system tests..."
        uv run pytest tests/test_memory_therapeutic.py $VERBOSE
        ;;
    "performance")
        echo "Running performance tests..."
        uv run pytest tests/test_performance.py $VERBOSE
        ;;
    "deployment")
        echo "Running deployment tests..."
        uv run pytest tests/test_deployment.py $VERBOSE
        ;;
    "core")
        echo "Running core tests..."
        uv run pytest tests/test_core.py $VERBOSE
        ;;
    "coverage")
        echo "Running tests with coverage..."
        uv run pytest tests/ --cov=ai_companion --cov-report=html --cov-report=term
        echo ""
        echo "Coverage report generated in htmlcov/index.html"
        ;;
    "quick")
        echo "Running quick tests (excluding slow tests)..."
        uv run pytest tests/ -v -m "not slow"
        ;;
    *)
        echo "Unknown test type: $TEST_TYPE"
        echo ""
        echo "Usage: ./run_tests.sh [test_type] [options]"
        echo ""
        echo "Test types:"
        echo "  all         - Run all tests (default)"
        echo "  voice       - Voice interaction tests"
        echo "  character   - Rose character tests"
        echo "  memory      - Memory system tests"
        echo "  performance - Performance tests"
        echo "  deployment  - Deployment tests"
        echo "  core        - Core utility tests"
        echo "  coverage    - Run with coverage report"
        echo "  quick       - Run quick tests only"
        echo ""
        echo "Options:"
        echo "  -v          - Verbose output (default)"
        echo "  -vv         - Very verbose output"
        echo "  -q          - Quiet output"
        exit 1
        ;;
esac

echo ""
echo "================================"
echo "Tests complete!"
echo "================================"
