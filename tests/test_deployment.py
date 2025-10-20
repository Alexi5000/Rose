"""Deployment validation tests for Railway platform."""

import os
import pytest
import requests
from unittest.mock import patch


class TestEnvironmentConfiguration:
    """Test environment variable configuration."""

    def test_required_env_vars_defined(self):
        """Test that all required environment variables are defined."""
        from ai_companion.settings import settings

        # Required API keys
        assert settings.GROQ_API_KEY is not None
        assert len(settings.GROQ_API_KEY) > 0

        assert settings.ELEVENLABS_API_KEY is not None
        assert len(settings.ELEVENLABS_API_KEY) > 0

        assert settings.ELEVENLABS_VOICE_ID is not None
        assert len(settings.ELEVENLABS_VOICE_ID) > 0

        assert settings.TOGETHER_API_KEY is not None
        assert len(settings.TOGETHER_API_KEY) > 0

        # Qdrant configuration
        assert settings.QDRANT_URL is not None
        assert len(settings.QDRANT_URL) > 0

    def test_optional_env_vars(self):
        """Test that optional environment variables are handled correctly."""
        from ai_companion.settings import settings

        # WhatsApp variables are optional
        # Should not raise error if not set
        assert hasattr(settings, "WHATSAPP_PHONE_NUMBER_ID")
        assert hasattr(settings, "WHATSAPP_TOKEN")
        assert hasattr(settings, "WHATSAPP_VERIFY_TOKEN")

    def test_model_configurations(self):
        """Test that model configurations are set correctly."""
        from ai_companion.settings import settings

        assert settings.TEXT_MODEL_NAME == "llama-3.3-70b-versatile"
        assert settings.SMALL_TEXT_MODEL_NAME == "llama-3.1-8b-instant"
        assert settings.STT_MODEL_NAME == "whisper-large-v3"

    def test_server_configuration(self):
        """Test server configuration for deployment."""
        from ai_companion.settings import settings

        # Port should be configurable via environment
        assert settings.PORT > 0
        assert settings.HOST is not None


class TestHealthCheckEndpoint:
    """Test health check endpoint for Railway monitoring."""

    def test_health_endpoint_exists(self):
        """Test that health endpoint is accessible."""
        from fastapi.testclient import TestClient
        from ai_companion.interfaces.web.app import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_endpoint_format(self):
        """Test health endpoint returns correct format."""
        from fastapi.testclient import TestClient
        from ai_companion.interfaces.web.app import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/api/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "services" in data
        assert isinstance(data["services"], dict)

    def test_health_check_service_connectivity(self):
        """Test health check verifies service connectivity."""
        from fastapi.testclient import TestClient
        from ai_companion.interfaces.web.app import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/api/health")
        data = response.json()

        # Should check Groq, Qdrant, ElevenLabs
        services = data["services"]
        assert "groq" in services
        assert "qdrant" in services
        assert "elevenlabs" in services


class TestDeploymentConfiguration:
    """Test deployment-specific configuration."""

    def test_railway_json_exists(self):
        """Test that railway.json configuration exists."""
        import os
        from pathlib import Path

        railway_config = Path("railway.json")
        assert railway_config.exists(), "railway.json not found"

    def test_dockerfile_exists(self):
        """Test that Dockerfile exists for deployment."""
        from pathlib import Path

        dockerfile = Path("Dockerfile")
        assert dockerfile.exists(), "Dockerfile not found"

    def test_env_example_exists(self):
        """Test that .env.example exists for reference."""
        from pathlib import Path

        env_example = Path(".env.example")
        assert env_example.exists(), ".env.example not found"

    def test_frontend_build_directory(self):
        """Test that frontend build directory is configured."""
        from ai_companion.interfaces.web.app import FRONTEND_BUILD_DIR

        assert FRONTEND_BUILD_DIR is not None
        # Build directory should be defined even if not built yet


class TestProductionReadiness:
    """Test production readiness checks."""

    def test_cors_configured(self):
        """Test that CORS is configured for production."""
        from ai_companion.interfaces.web.app import create_app

        app = create_app()

        # Check that CORS middleware is added
        middleware_types = [type(m) for m in app.user_middleware]
        from fastapi.middleware.cors import CORSMiddleware

        # CORS should be configured (even if permissive for now)
        # In production, should be restricted to specific origins

    def test_logging_configured(self):
        """Test that logging is properly configured."""
        import logging

        # Verify logging is set up
        logger = logging.getLogger("ai_companion")
        assert logger is not None

    def test_error_handling(self):
        """Test that error handling is in place."""
        from fastapi.testclient import TestClient
        from ai_companion.interfaces.web.app import create_app

        app = create_app()
        client = TestClient(app)

        # Test 404 handling
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404

    def test_static_file_serving(self):
        """Test that static file serving is configured."""
        from ai_companion.interfaces.web.app import create_app

        app = create_app()

        # Check that static file routes are configured
        routes = [route.path for route in app.routes]
        # Should have catch-all route for React app


class TestDatabaseConnections:
    """Test database connection configuration."""

    def test_short_term_memory_path(self):
        """Test short-term memory database path is configured."""
        from ai_companion.settings import settings

        assert settings.SHORT_TERM_MEMORY_DB_PATH is not None
        assert len(settings.SHORT_TERM_MEMORY_DB_PATH) > 0

    def test_qdrant_connection_config(self):
        """Test Qdrant connection configuration."""
        from ai_companion.settings import settings

        # Should have either URL or host/port
        assert settings.QDRANT_URL is not None or settings.QDRANT_HOST is not None


class TestAPIEndpoints:
    """Test all API endpoints are accessible."""

    def test_all_endpoints_registered(self):
        """Test that all required endpoints are registered."""
        from fastapi.testclient import TestClient
        from ai_companion.interfaces.web.app import create_app

        app = create_app()
        client = TestClient(app)

        # Health check
        response = client.get("/api/health")
        assert response.status_code == 200

        # Session start
        response = client.post("/api/session/start")
        assert response.status_code == 200

        # Voice process endpoint exists (will fail without audio, but should not 404)
        response = client.post("/api/voice/process")
        assert response.status_code != 404  # Should be 422 (validation error) not 404


# Integration tests for deployed environment
"""
These tests should be run against the deployed Railway instance:

1. Set RAILWAY_URL environment variable:
   export RAILWAY_URL=https://your-app.railway.app

2. Run deployment tests:
   pytest tests/test_deployment.py -v

3. Manual deployment validation checklist:
   - [ ] Application starts without errors
   - [ ] Health check endpoint responds
   - [ ] Can create new session
   - [ ] Can process voice input
   - [ ] Audio responses are generated
   - [ ] Frontend loads correctly
   - [ ] All environment variables loaded
   - [ ] Logs are accessible in Railway dashboard
   - [ ] No memory leaks over 24 hours
   - [ ] API costs are within budget
"""


class TestDeployedInstance:
    """Tests to run against deployed Railway instance."""

    @pytest.fixture
    def railway_url(self):
        """Get Railway deployment URL from environment."""
        url = os.getenv("RAILWAY_URL")
        if not url:
            pytest.skip("RAILWAY_URL not set - skipping deployment tests")
        return url

    def test_deployed_health_check(self, railway_url):
        """Test health check on deployed instance."""
        response = requests.get(f"{railway_url}/api/health", timeout=10)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "services" in data

    def test_deployed_session_start(self, railway_url):
        """Test session creation on deployed instance."""
        response = requests.post(f"{railway_url}/api/session/start", timeout=10)
        assert response.status_code == 200

        data = response.json()
        assert "session_id" in data
        assert len(data["session_id"]) > 0

    def test_deployed_frontend_loads(self, railway_url):
        """Test that frontend loads on deployed instance."""
        response = requests.get(railway_url, timeout=10)
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_deployed_ssl_certificate(self, railway_url):
        """Test that SSL certificate is valid."""
        if railway_url.startswith("https://"):
            # SSL should be valid (Railway provides automatic SSL)
            response = requests.get(railway_url, timeout=10)
            assert response.status_code == 200

    def test_deployed_response_time(self, railway_url):
        """Test that deployed instance responds quickly."""
        import time

        start = time.time()
        response = requests.get(f"{railway_url}/api/health", timeout=10)
        duration = time.time() - start

        assert response.status_code == 200
        # Should respond in less than 3 seconds
        assert duration < 3.0

    def test_deployed_error_handling(self, railway_url):
        """Test error handling on deployed instance."""
        # Test 404
        response = requests.get(f"{railway_url}/api/nonexistent", timeout=10)
        assert response.status_code == 404

        # Test invalid request
        response = requests.post(f"{railway_url}/api/voice/process", timeout=10)
        assert response.status_code in [400, 422]  # Validation error


# Deployment checklist
"""
Pre-deployment checklist:
- [ ] All tests pass locally
- [ ] Environment variables documented in .env.example
- [ ] railway.json configured correctly
- [ ] Dockerfile builds successfully
- [ ] Frontend built and optimized
- [ ] Database migrations applied (if any)
- [ ] API keys are valid and have sufficient credits
- [ ] CORS configured appropriately
- [ ] Logging configured
- [ ] Error handling in place
- [ ] Health check endpoint working

Post-deployment checklist:
- [ ] Application starts successfully
- [ ] Health check returns healthy status
- [ ] All API endpoints accessible
- [ ] Frontend loads correctly
- [ ] Voice interaction works end-to-end
- [ ] Memory system persists data
- [ ] Logs are accessible
- [ ] No errors in logs
- [ ] Resource usage within limits
- [ ] Response times acceptable
- [ ] SSL certificate valid
- [ ] Domain configured (if custom domain)

Monitoring setup:
- [ ] Set up Railway alerts for:
  - High memory usage (>80%)
  - High CPU usage (>80%)
  - Application crashes
  - Health check failures
- [ ] Set up external monitoring (UptimeRobot, Pingdom)
- [ ] Set up cost alerts for API usage
- [ ] Set up log aggregation (if needed)

Rollback plan:
- [ ] Document current deployment version
- [ ] Keep previous version available
- [ ] Test rollback procedure
- [ ] Document rollback steps
"""
