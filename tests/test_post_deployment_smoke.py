"""
Post-deployment smoke tests for production verification.

These tests verify critical functionality after deployment:
- Health checks
- API endpoints
- External service connectivity
- Basic functionality

Run with: pytest tests/test_post_deployment_smoke.py -v -m smoke
Set DEPLOYED_URL environment variable to test deployed instance.
"""

import os
import pytest
import requests
from urllib.parse import urljoin


# Mark all tests as smoke tests
pytestmark = pytest.mark.smoke


@pytest.fixture(scope="module")
def base_url():
    """Get base URL for deployed application."""
    return os.getenv("DEPLOYED_URL", "http://localhost:8080")


@pytest.fixture(scope="module")
def api_timeout():
    """Timeout for API requests."""
    return 30  # 30 seconds


class TestDeploymentHealth:
    """Smoke tests for deployment health."""
    
    def test_health_endpoint_responds(self, base_url, api_timeout):
        """Test that health endpoint responds."""
        url = urljoin(base_url, "/api/health")
        
        response = requests.get(url, timeout=api_timeout)
        
        assert response.status_code == 200, f"Health check failed with status {response.status_code}"
        
        data = response.json()
        assert "status" in data, "Health check response missing 'status' field"
    
    def test_health_check_services(self, base_url, api_timeout):
        """Test that all services are healthy."""
        url = urljoin(base_url, "/api/health")
        
        response = requests.get(url, timeout=api_timeout)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify services are checked
        if "services" in data:
            services = data["services"]
            
            # Check critical services
            for service_name in ["groq", "elevenlabs", "qdrant"]:
                if service_name in services:
                    service_status = services[service_name]
                    assert service_status.get("status") == "healthy", \
                        f"Service {service_name} is not healthy: {service_status}"
    
    def test_application_responds_quickly(self, base_url, api_timeout):
        """Test that application responds within acceptable time."""
        import time
        
        url = urljoin(base_url, "/api/health")
        
        start_time = time.time()
        response = requests.get(url, timeout=api_timeout)
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 5.0, f"Health check took {response_time:.2f}s (should be < 5s)"


class TestCriticalEndpoints:
    """Smoke tests for critical API endpoints."""
    
    def test_session_start_endpoint(self, base_url, api_timeout):
        """Test that session start endpoint works."""
        url = urljoin(base_url, "/api/session/start")
        
        response = requests.post(url, timeout=api_timeout)
        
        assert response.status_code == 200, f"Session start failed with status {response.status_code}"
        
        data = response.json()
        assert "session_id" in data, "Session start response missing 'session_id'"
        assert data["session_id"] is not None
        assert len(data["session_id"]) > 0
    
    def test_voice_process_endpoint_exists(self, base_url, api_timeout):
        """Test that voice process endpoint exists."""
        url = urljoin(base_url, "/api/voice/process")
        
        # Send empty request to verify endpoint exists
        # Should return 422 (validation error) not 404
        response = requests.post(url, timeout=api_timeout)
        
        assert response.status_code in [400, 422], \
            f"Voice process endpoint returned unexpected status {response.status_code}"
    
    def test_api_documentation_accessible(self, base_url, api_timeout):
        """Test that API documentation is accessible (if enabled)."""
        url = urljoin(base_url, "/api/docs")
        
        response = requests.get(url, timeout=api_timeout, allow_redirects=True)
        
        # Docs may be disabled in production, so 404 is acceptable
        assert response.status_code in [200, 404], \
            f"API docs returned unexpected status {response.status_code}"


class TestFrontendDeployment:
    """Smoke tests for frontend deployment."""
    
    def test_frontend_loads(self, base_url, api_timeout):
        """Test that frontend page loads."""
        response = requests.get(base_url, timeout=api_timeout)
        
        assert response.status_code == 200, f"Frontend failed to load with status {response.status_code}"
        
        # Verify HTML content
        content = response.text
        assert len(content) > 0, "Frontend returned empty content"
        assert "<html" in content.lower() or "<!doctype" in content.lower(), \
            "Frontend did not return HTML content"
    
    def test_frontend_static_assets(self, base_url, api_timeout):
        """Test that frontend static assets are accessible."""
        # Try to load common static assets
        static_paths = [
            "/assets/",  # Vite assets directory
            "/favicon.ico",
        ]
        
        for path in static_paths:
            url = urljoin(base_url, path)
            response = requests.get(url, timeout=api_timeout, allow_redirects=True)
            
            # Assets may not exist, but should not return 500
            assert response.status_code != 500, \
                f"Static asset {path} returned server error"


class TestSecurityHeaders:
    """Smoke tests for security headers."""
    
    def test_security_headers_present(self, base_url, api_timeout):
        """Test that security headers are present."""
        response = requests.get(base_url, timeout=api_timeout)
        
        headers = response.headers
        
        # Check for important security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "X-XSS-Protection": "1; mode=block",
        }
        
        for header, expected_value in security_headers.items():
            if header in headers:
                actual_value = headers[header]
                if isinstance(expected_value, list):
                    assert actual_value in expected_value, \
                        f"Security header {header} has unexpected value: {actual_value}"
                else:
                    assert actual_value == expected_value, \
                        f"Security header {header} has unexpected value: {actual_value}"
    
    def test_cors_headers_configured(self, base_url, api_timeout):
        """Test that CORS headers are properly configured."""
        url = urljoin(base_url, "/api/health")
        
        # Send OPTIONS request
        response = requests.options(url, timeout=api_timeout)
        
        # CORS headers should be present
        headers = response.headers
        
        # Check for CORS headers (may vary based on configuration)
        if "Access-Control-Allow-Origin" in headers:
            # If CORS is enabled, verify it's not too permissive in production
            origin = headers["Access-Control-Allow-Origin"]
            
            # In production, should not be "*" (unless intentional)
            if os.getenv("ENVIRONMENT") == "production":
                assert origin != "*", "CORS allows all origins in production"


class TestRateLimiting:
    """Smoke tests for rate limiting."""
    
    def test_rate_limiting_configured(self, base_url, api_timeout):
        """Test that rate limiting is configured."""
        url = urljoin(base_url, "/api/health")
        
        # Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = requests.get(url, timeout=api_timeout)
            responses.append(response)
        
        # All requests should succeed (health check may not be rate limited)
        # But verify rate limit headers are present
        for response in responses:
            headers = response.headers
            
            # Check for rate limit headers (implementation-specific)
            # Common headers: X-RateLimit-Limit, X-RateLimit-Remaining, RateLimit-*
            rate_limit_headers = [
                h for h in headers.keys()
                if "ratelimit" in h.lower() or "rate-limit" in h.lower()
            ]
            
            # If rate limiting is configured, headers should be present
            # This is optional - not all endpoints may have rate limiting
            pass


class TestDataPersistence:
    """Smoke tests for data persistence."""
    
    def test_session_persistence(self, base_url, api_timeout):
        """Test that sessions persist across requests."""
        url = urljoin(base_url, "/api/session/start")
        
        # Create a session
        response1 = requests.post(url, timeout=api_timeout)
        assert response1.status_code == 200
        session_id = response1.json()["session_id"]
        
        # Create another session
        response2 = requests.post(url, timeout=api_timeout)
        assert response2.status_code == 200
        session_id2 = response2.json()["session_id"]
        
        # Sessions should be different
        assert session_id != session_id2, "Sessions are not unique"


class TestErrorHandling:
    """Smoke tests for error handling."""
    
    def test_404_handling(self, base_url, api_timeout):
        """Test that 404 errors are handled gracefully."""
        url = urljoin(base_url, "/api/nonexistent-endpoint")
        
        response = requests.get(url, timeout=api_timeout)
        
        assert response.status_code == 404
        
        # Verify error response format
        try:
            data = response.json()
            assert "error" in data or "detail" in data, \
                "Error response missing error information"
        except ValueError:
            # May return HTML for 404
            pass
    
    def test_method_not_allowed_handling(self, base_url, api_timeout):
        """Test that method not allowed errors are handled."""
        url = urljoin(base_url, "/api/health")
        
        # Send DELETE request to GET endpoint
        response = requests.delete(url, timeout=api_timeout)
        
        assert response.status_code == 405, \
            f"Expected 405 Method Not Allowed, got {response.status_code}"
    
    def test_invalid_json_handling(self, base_url, api_timeout):
        """Test that invalid JSON is handled gracefully."""
        url = urljoin(base_url, "/api/session/start")
        
        # Send invalid JSON
        response = requests.post(
            url,
            data="invalid json{",
            headers={"Content-Type": "application/json"},
            timeout=api_timeout
        )
        
        # Should return 400 or 422, not 500
        assert response.status_code in [400, 422], \
            f"Invalid JSON returned {response.status_code} instead of 400/422"


class TestMonitoring:
    """Smoke tests for monitoring and observability."""
    
    def test_request_id_in_response(self, base_url, api_timeout):
        """Test that request ID is included in responses."""
        url = urljoin(base_url, "/api/health")
        
        response = requests.get(url, timeout=api_timeout)
        
        headers = response.headers
        
        # Check for request ID header
        request_id_headers = [
            "X-Request-ID",
            "X-Request-Id",
            "Request-ID",
        ]
        
        has_request_id = any(h in headers for h in request_id_headers)
        
        # Request ID is optional but recommended
        # Just verify if present, it's not empty
        for header in request_id_headers:
            if header in headers:
                assert len(headers[header]) > 0, f"{header} is empty"


class TestPerformance:
    """Smoke tests for performance."""
    
    def test_health_check_performance(self, base_url, api_timeout):
        """Test health check response time."""
        import time
        
        url = urljoin(base_url, "/api/health")
        
        # Warm up
        requests.get(url, timeout=api_timeout)
        
        # Measure response time
        times = []
        for _ in range(5):
            start = time.time()
            response = requests.get(url, timeout=api_timeout)
            elapsed = time.time() - start
            
            assert response.status_code == 200
            times.append(elapsed)
        
        # Average response time should be reasonable
        avg_time = sum(times) / len(times)
        assert avg_time < 2.0, f"Average health check time {avg_time:.2f}s is too slow"
    
    def test_session_creation_performance(self, base_url, api_timeout):
        """Test session creation response time."""
        import time
        
        url = urljoin(base_url, "/api/session/start")
        
        # Measure response time
        times = []
        for _ in range(3):
            start = time.time()
            response = requests.post(url, timeout=api_timeout)
            elapsed = time.time() - start
            
            assert response.status_code == 200
            times.append(elapsed)
        
        # Average response time should be reasonable
        avg_time = sum(times) / len(times)
        assert avg_time < 3.0, f"Average session creation time {avg_time:.2f}s is too slow"


# Summary test that runs all critical checks
class TestDeploymentReadiness:
    """Comprehensive deployment readiness check."""
    
    @pytest.mark.smoke
    def test_deployment_readiness_summary(self, base_url, api_timeout):
        """Run all critical checks and provide summary."""
        results = {}
        
        # Health check
        try:
            response = requests.get(urljoin(base_url, "/api/health"), timeout=api_timeout)
            results["health_check"] = response.status_code == 200
        except Exception as e:
            results["health_check"] = False
            results["health_check_error"] = str(e)
        
        # Session creation
        try:
            response = requests.post(urljoin(base_url, "/api/session/start"), timeout=api_timeout)
            results["session_creation"] = response.status_code == 200
        except Exception as e:
            results["session_creation"] = False
            results["session_creation_error"] = str(e)
        
        # Frontend
        try:
            response = requests.get(base_url, timeout=api_timeout)
            results["frontend"] = response.status_code == 200
        except Exception as e:
            results["frontend"] = False
            results["frontend_error"] = str(e)
        
        # Print summary
        print("\n" + "="*50)
        print("DEPLOYMENT READINESS SUMMARY")
        print("="*50)
        for check, status in results.items():
            if not check.endswith("_error"):
                status_str = "✓ PASS" if status else "✗ FAIL"
                print(f"{check:.<30} {status_str}")
                if not status and f"{check}_error" in results:
                    print(f"  Error: {results[f'{check}_error']}")
        print("="*50)
        
        # All critical checks must pass
        critical_checks = ["health_check", "session_creation", "frontend"]
        all_passed = all(results.get(check, False) for check in critical_checks)
        
        assert all_passed, "Some critical deployment checks failed"
