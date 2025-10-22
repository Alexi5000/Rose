#!/usr/bin/env python3
"""Verification script for error handling and observability improvements.

This script verifies that all the observability improvements are properly
implemented and can be imported without errors.
"""

import sys


def verify_imports():
    """Verify all new modules can be imported."""
    print("Verifying imports...")

    try:
        from ai_companion.core.error_responses import (
            ErrorResponse,
            ai_companion_error_handler,
            global_exception_handler,
            sanitize_error_message,
            validation_error_handler,
        )
        print("✓ Error response module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import error response module: {e}")
        return False

    try:
        from ai_companion.core.metrics import (
            MetricsCollector,
            metrics,
            track_performance,
        )
        print("✓ Metrics module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import metrics module: {e}")
        return False

    # Note: Metrics route requires environment variables, so we skip importing it
    # The route itself is verified by checking the file exists
    import os
    metrics_route_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "src",
        "ai_companion",
        "interfaces",
        "web",
        "routes",
        "metrics.py"
    )
    if os.path.exists(metrics_route_path):
        print("✓ Metrics route file exists")
    else:
        print("✗ Metrics route file not found")
        return False

    return True


def verify_error_response_model():
    """Verify ErrorResponse model structure."""
    print("\nVerifying ErrorResponse model...")

    from ai_companion.core.error_responses import ErrorResponse

    # Create a sample error response
    error = ErrorResponse(
        error="test_error",
        message="Test error message",
        request_id="test-request-id"
    )

    # Verify fields
    assert error.error == "test_error"
    assert error.message == "Test error message"
    assert error.request_id == "test-request-id"
    assert error.details is None

    print("✓ ErrorResponse model structure verified")
    return True


def verify_metrics_collector():
    """Verify MetricsCollector functionality."""
    print("\nVerifying MetricsCollector...")

    from ai_companion.core.metrics import MetricsCollector

    collector = MetricsCollector()

    # Test counter
    collector.increment_counter("test_counter", value=5)
    assert collector._counters["test_counter"] == 5
    print("✓ Counter increment works")

    # Test gauge
    collector.set_gauge("test_gauge", value=42.5)
    assert collector._gauges["test_gauge"] == 42.5
    print("✓ Gauge setting works")

    # Test histogram
    collector.record_histogram("test_histogram", value=100.0)
    assert len(collector._histograms["test_histogram"]) == 1
    assert collector._histograms["test_histogram"][0] == 100.0
    print("✓ Histogram recording works")

    # Test metrics summary
    summary = collector.get_metrics_summary()
    assert "counters" in summary
    assert "gauges" in summary
    assert "histograms" in summary
    assert "timestamp" in summary
    print("✓ Metrics summary generation works")

    return True


def verify_performance_decorator():
    """Verify track_performance decorator."""
    print("\nVerifying track_performance decorator...")

    import asyncio

    from ai_companion.core.metrics import track_performance

    # Test with async function
    @track_performance("test_async")
    async def test_async_func():
        await asyncio.sleep(0.01)
        return "success"

    # Test with sync function
    @track_performance("test_sync")
    def test_sync_func():
        return "success"

    # Run async test
    result = asyncio.run(test_async_func())
    assert result == "success"
    print("✓ Async function tracking works")

    # Run sync test
    result = test_sync_func()
    assert result == "success"
    print("✓ Sync function tracking works")

    return True


def verify_logging_config():
    """Verify logging configuration."""
    print("\nVerifying logging configuration...")

    from ai_companion.core.logging_config import configure_logging, get_logger

    # Configure logging
    configure_logging()
    print("✓ Logging configured successfully")

    # Get logger
    logger = get_logger(__name__)
    assert logger is not None
    print("✓ Logger instance created successfully")

    # Test structured logging
    logger.info("test_event", test_key="test_value")
    print("✓ Structured logging works")

    return True


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Error Handling and Observability Verification")
    print("=" * 60)

    tests = [
        ("Import Verification", verify_imports),
        ("ErrorResponse Model", verify_error_response_model),
        ("MetricsCollector", verify_metrics_collector),
        ("Performance Decorator", verify_performance_decorator),
        ("Logging Configuration", verify_logging_config),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"✗ {test_name} failed")
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)
    else:
        print("\n✓ All verification tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
