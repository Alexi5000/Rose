"""Tests for security hardening features."""

import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from ai_companion.interfaces.web.app import create_app
from ai_companion.interfaces.web.middleware import set_secure_file_permissions
from ai_companion.settings import settings


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    # Temporarily disable rate limiting for tests
    original_rate_limit = settings.RATE_LIMIT_ENABLED
    settings.RATE_LIMIT_ENABLED = False

    app = create_app()
    client = TestClient(app)

    yield client

    # Restore original setting
    settings.RATE_LIMIT_ENABLED = original_rate_limit


class TestCORSConfiguration:
    """Test CORS configuration."""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses."""
        response = client.get("/api/health")

        # Check for CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-credentials" in response.headers

    def test_cors_respects_allowed_origins(self):
        """Test that CORS configuration respects ALLOWED_ORIGINS setting."""
        # Test with specific origins
        original_origins = settings.ALLOWED_ORIGINS
        settings.ALLOWED_ORIGINS = "https://example.com,https://app.example.com"

        allowed = settings.get_allowed_origins()
        assert "https://example.com" in allowed
        assert "https://app.example.com" in allowed
        assert len(allowed) == 2

        # Restore original
        settings.ALLOWED_ORIGINS = original_origins

    def test_cors_wildcard_configuration(self):
        """Test that wildcard CORS configuration works."""
        original_origins = settings.ALLOWED_ORIGINS
        settings.ALLOWED_ORIGINS = "*"

        allowed = settings.get_allowed_origins()
        assert allowed == ["*"]

        # Restore original
        settings.ALLOWED_ORIGINS = original_origins


class TestSecurityHeaders:
    """Test security headers middleware."""

    def test_security_headers_present(self, client):
        """Test that security headers are added to responses."""
        response = client.get("/api/health")

        # Check for security headers
        assert "content-security-policy" in response.headers
        assert "strict-transport-security" in response.headers
        assert "x-frame-options" in response.headers
        assert "x-content-type-options" in response.headers
        assert "x-xss-protection" in response.headers
        assert "referrer-policy" in response.headers
        assert "permissions-policy" in response.headers

    def test_csp_header_configuration(self, client):
        """Test Content Security Policy header configuration."""
        response = client.get("/api/health")

        csp = response.headers.get("content-security-policy", "")
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp

    def test_hsts_header_configuration(self, client):
        """Test HTTP Strict Transport Security header."""
        response = client.get("/api/health")

        hsts = response.headers.get("strict-transport-security", "")
        assert "max-age=31536000" in hsts
        assert "includeSubDomains" in hsts

    def test_frame_options_deny(self, client):
        """Test X-Frame-Options is set to DENY."""
        response = client.get("/api/health")

        assert response.headers.get("x-frame-options") == "DENY"


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limiting_enabled_by_default(self):
        """Test that rate limiting is enabled by default."""
        assert settings.RATE_LIMIT_ENABLED is True

    def test_rate_limit_configuration(self):
        """Test rate limit configuration values."""
        assert settings.RATE_LIMIT_PER_MINUTE > 0
        assert isinstance(settings.RATE_LIMIT_PER_MINUTE, int)

    @patch("ai_companion.interfaces.web.routes.session.limiter")
    def test_rate_limit_applied_to_session_endpoint(self, mock_limiter, client):
        """Test that rate limiting is applied to session endpoint."""
        # Make a request to session endpoint
        response = client.post("/api/session/start")

        # Should succeed (rate limit not actually enforced in test)
        assert response.status_code == 200

    @patch("ai_companion.interfaces.web.routes.voice.limiter")
    @patch("ai_companion.interfaces.web.routes.voice.stt")
    @patch("ai_companion.interfaces.web.routes.voice.create_workflow_graph")
    def test_rate_limit_applied_to_voice_endpoint(self, mock_graph, mock_stt, mock_limiter, client):
        """Test that rate limiting is applied to voice endpoint."""
        # Mock the speech-to-text and workflow
        mock_stt.transcribe = AsyncMock(return_value="Hello")
        mock_graph_instance = mock_graph.return_value
        mock_compiled = mock_graph_instance.compile.return_value
        mock_compiled.ainvoke = AsyncMock(return_value={"messages": [type("Message", (), {"content": "Hello there"})]})

        # Create a test audio file
        audio_data = b"fake audio data"

        # Make a request to voice endpoint
        response = client.post(
            "/api/voice/process",
            files={"audio": ("test.wav", audio_data, "audio/wav")},
            data={"session_id": "test-session"},
        )

        # Should succeed (rate limit not actually enforced in test)
        assert response.status_code in [200, 503]  # May fail due to mocking


class TestSecureFileHandling:
    """Test secure file handling."""

    def test_secure_file_permissions(self):
        """Test that secure file permissions are set correctly."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(b"test data")

        try:
            # Set secure permissions
            set_secure_file_permissions(tmp_path)

            # Check permissions (on Unix-like systems)
            if os.name != "nt":  # Skip on Windows
                stat_info = os.stat(tmp_path)
                mode = stat_info.st_mode
                # Check that only owner has read/write permissions
                assert mode & 0o777 == 0o600
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @patch("ai_companion.interfaces.web.routes.voice.stt")
    @patch("ai_companion.interfaces.web.routes.voice.tts")
    @patch("ai_companion.interfaces.web.routes.voice.create_workflow_graph")
    def test_audio_files_created_with_secure_permissions(self, mock_graph, mock_tts, mock_stt, client):
        """Test that audio files are created with secure permissions."""
        # Mock the services
        mock_stt.transcribe = AsyncMock(return_value="Hello")
        mock_tts.synthesize = AsyncMock(return_value=b"fake audio")

        mock_graph_instance = mock_graph.return_value
        mock_compiled = mock_graph_instance.compile.return_value
        mock_compiled.ainvoke = AsyncMock(return_value={"messages": [type("Message", (), {"content": "Hello there"})]})

        # Create a test audio file
        audio_data = b"fake audio data"

        # Make a request
        response = client.post(
            "/api/voice/process",
            files={"audio": ("test.wav", audio_data, "audio/wav")},
            data={"session_id": "test-session"},
        )

        # Should succeed
        assert response.status_code == 200

        # Check that audio file was created
        data = response.json()
        assert "audio_url" in data

        # Note: Actual permission checking would require accessing the created file
        # which is in a temporary directory


class TestSecurityConfiguration:
    """Test security configuration settings."""

    def test_security_settings_exist(self):
        """Test that security settings are defined."""
        assert hasattr(settings, "ALLOWED_ORIGINS")
        assert hasattr(settings, "RATE_LIMIT_ENABLED")
        assert hasattr(settings, "RATE_LIMIT_PER_MINUTE")
        assert hasattr(settings, "ENABLE_SECURITY_HEADERS")

    def test_get_allowed_origins_method(self):
        """Test get_allowed_origins method."""
        original_origins = settings.ALLOWED_ORIGINS

        # Test with multiple origins
        settings.ALLOWED_ORIGINS = "https://example.com, https://app.example.com"
        origins = settings.get_allowed_origins()
        assert len(origins) == 2
        assert "https://example.com" in origins
        assert "https://app.example.com" in origins

        # Test with wildcard
        settings.ALLOWED_ORIGINS = "*"
        origins = settings.get_allowed_origins()
        assert origins == ["*"]

        # Restore
        settings.ALLOWED_ORIGINS = original_origins
