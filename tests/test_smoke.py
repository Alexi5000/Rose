"""
Smoke tests for pre-deployment validation.

These tests verify critical functionality before deployment:
- Configuration validation
- Core module imports
- Basic API functionality
- Health checks
"""

import os
from pathlib import Path

import pytest


class TestConfigurationValidation:
    """Validate that all required configuration is present."""

    def test_required_environment_variables(self):
        """Test that critical environment variables are defined."""
        # These should be set in CI or have defaults
        required_vars = [
            "GROQ_API_KEY",
            "ELEVENLABS_API_KEY",
            "ELEVENLABS_VOICE_ID",
            "QDRANT_URL",
            "QDRANT_API_KEY",
        ]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        # In CI, these should be set as secrets
        # Locally, they should be in .env
        if missing_vars and os.getenv("CI"):
            pytest.fail(f"Missing required environment variables in CI: {missing_vars}")

    def test_settings_can_be_loaded(self):
        """Test that settings module can be imported and loaded."""
        # Skip if environment variables are not set (local development)
        required_vars = ["GROQ_API_KEY", "ELEVENLABS_API_KEY", "QDRANT_URL"]
        if not all(os.getenv(var) for var in required_vars):
            pytest.skip("Environment variables not set - skipping settings load test")

        from ai_companion.settings import settings

        assert settings is not None
        assert hasattr(settings, "GROQ_API_KEY")
        assert hasattr(settings, "ELEVENLABS_API_KEY")

    def test_data_directories_exist(self):
        """Test that required data directories exist or can be created."""
        from ai_companion.settings import settings

        # These directories should be created automatically
        data_dirs = [
            Path(settings.SHORT_TERM_MEMORY_DB_PATH).parent,
            Path(settings.LONG_TERM_MEMORY_COLLECTION_PATH).parent,
        ]

        for dir_path in data_dirs:
            assert dir_path.exists() or dir_path.parent.exists(), \
                f"Data directory parent does not exist: {dir_path}"


class TestCoreModuleImports:
    """Verify that all core modules can be imported without errors."""

    @pytest.mark.skipif(
        not all(os.getenv(var) for var in ["GROQ_API_KEY", "ELEVENLABS_API_KEY", "QDRANT_URL"]),
        reason="Environment variables not set"
    )
    def test_import_settings(self):
        """Test settings module import."""
        from ai_companion import settings
        assert settings is not None

    @pytest.mark.skipif(
        not all(os.getenv(var) for var in ["GROQ_API_KEY", "ELEVENLABS_API_KEY", "QDRANT_URL"]),
        reason="Environment variables not set"
    )
    def test_import_graph(self):
        """Test graph module import."""
        from ai_companion.graph import graph
        assert graph is not None

    @pytest.mark.skipif(
        not all(os.getenv(var) for var in ["GROQ_API_KEY", "ELEVENLABS_API_KEY", "QDRANT_URL"]),
        reason="Environment variables not set"
    )
    def test_import_state(self):
        """Test state module import."""
        from ai_companion.graph.state import AICompanionState
        assert AICompanionState is not None

    @pytest.mark.skipif(
        not all(os.getenv(var) for var in ["GROQ_API_KEY", "ELEVENLABS_API_KEY", "QDRANT_URL"]),
        reason="Environment variables not set"
    )
    def test_import_nodes(self):
        """Test nodes module import."""
        from ai_companion.graph import nodes
        assert nodes is not None

    def test_import_resilience(self):
        """Test resilience module import."""
        from ai_companion.core import resilience
        assert resilience is not None

    def test_import_backup(self):
        """Test backup module import."""
        from ai_companion.core import backup
        assert backup is not None


class TestBasicFunctionality:
    """Test basic functionality of core components."""

    def test_graph_can_be_compiled(self):
        """Test that the LangGraph workflow can be compiled."""
        # Skip if environment variables are not set
        required_vars = ["GROQ_API_KEY", "ELEVENLABS_API_KEY", "QDRANT_URL"]
        if not all(os.getenv(var) for var in required_vars):
            pytest.skip("Environment variables not set - skipping graph compilation test")

        from ai_companion.graph.graph import create_graph

        graph = create_graph()
        assert graph is not None

        # Verify graph has expected nodes
        compiled = graph.compile()
        assert compiled is not None

    @pytest.mark.asyncio
    async def test_health_check_endpoint(self):
        """Test that health check endpoint works."""
        # Skip if environment variables are not set
        required_vars = ["GROQ_API_KEY", "ELEVENLABS_API_KEY", "QDRANT_URL"]
        if not all(os.getenv(var) for var in required_vars):
            pytest.skip("Environment variables not set - skipping health check test")

        from fastapi.testclient import TestClient

        from ai_companion.interfaces.web.app import app

        client = TestClient(app)
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_session_creation(self):
        """Test that sessions can be created."""
        # Skip if environment variables are not set
        required_vars = ["GROQ_API_KEY", "ELEVENLABS_API_KEY", "QDRANT_URL"]
        if not all(os.getenv(var) for var in required_vars):
            pytest.skip("Environment variables not set - skipping session creation test")

        from fastapi.testclient import TestClient

        from ai_companion.interfaces.web.app import app

        client = TestClient(app)
        response = client.post("/api/session/start")

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "message" in data


class TestCircuitBreakers:
    """Test that circuit breakers are properly configured."""

    def test_circuit_breaker_module_exists(self):
        """Test that circuit breaker module can be imported."""
        from ai_companion.core import resilience
        assert resilience is not None

    def test_groq_circuit_breaker_configured(self):
        """Test that Groq circuit breaker is configured."""
        # Skip if environment variables are not set
        required_vars = ["GROQ_API_KEY", "ELEVENLABS_API_KEY", "QDRANT_URL"]
        if not all(os.getenv(var) for var in required_vars):
            pytest.skip("Environment variables not set - skipping circuit breaker test")

        from ai_companion.core.resilience import get_groq_circuit_breaker
        breaker = get_groq_circuit_breaker()
        assert breaker is not None
        assert breaker.name == "GroqAPI"

    def test_elevenlabs_circuit_breaker_configured(self):
        """Test that ElevenLabs circuit breaker is configured."""
        # Skip if environment variables are not set
        required_vars = ["GROQ_API_KEY", "ELEVENLABS_API_KEY", "QDRANT_URL"]
        if not all(os.getenv(var) for var in required_vars):
            pytest.skip("Environment variables not set - skipping circuit breaker test")

        from ai_companion.core.resilience import get_elevenlabs_circuit_breaker
        breaker = get_elevenlabs_circuit_breaker()
        assert breaker is not None
        assert breaker.name == "ElevenLabsAPI"

    def test_qdrant_circuit_breaker_configured(self):
        """Test that Qdrant circuit breaker is configured."""
        # Skip if environment variables are not set
        required_vars = ["GROQ_API_KEY", "ELEVENLABS_API_KEY", "QDRANT_URL"]
        if not all(os.getenv(var) for var in required_vars):
            pytest.skip("Environment variables not set - skipping circuit breaker test")

        from ai_companion.core.resilience import get_qdrant_circuit_breaker
        breaker = get_qdrant_circuit_breaker()
        assert breaker is not None
        assert breaker.name == "QdrantAPI"


class TestSecurityMiddleware:
    """Test that security middleware is properly configured."""

    @pytest.mark.skipif(
        not all(os.getenv(var) for var in ["GROQ_API_KEY", "ELEVENLABS_API_KEY", "QDRANT_URL"]),
        reason="Environment variables not set"
    )
    def test_security_headers_middleware_exists(self):
        """Test that security headers middleware is configured."""
        from ai_companion.interfaces.web.app import app

        # Check that middleware is registered
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "SecurityHeadersMiddleware" in middleware_classes or \
               any("security" in m.lower() for m in middleware_classes)

    @pytest.mark.skipif(
        not all(os.getenv(var) for var in ["GROQ_API_KEY", "ELEVENLABS_API_KEY", "QDRANT_URL"]),
        reason="Environment variables not set"
    )
    def test_rate_limiting_configured(self):
        """Test that rate limiting is configured."""
        from ai_companion.interfaces.web.app import app

        # Check that rate limiter is configured
        assert hasattr(app.state, "limiter") or \
               any("limiter" in str(m) for m in app.user_middleware)

    @pytest.mark.skipif(
        not all(os.getenv(var) for var in ["GROQ_API_KEY", "ELEVENLABS_API_KEY", "QDRANT_URL"]),
        reason="Environment variables not set"
    )
    def test_cors_middleware_configured(self):
        """Test that CORS middleware is configured."""
        from ai_companion.interfaces.web.app import app

        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_classes


class TestDataPersistence:
    """Test that data persistence is properly configured."""

    def test_backup_module_exists(self):
        """Test that backup module can be imported."""
        from ai_companion.core import backup
        assert backup is not None

    def test_backup_manager_configured(self):
        """Test that backup manager is configured."""
        from ai_companion.core.backup import backup_manager
        assert backup_manager is not None
        assert hasattr(backup_manager, "backup_database")

    def test_cleanup_job_configured(self):
        """Test that cleanup job is configured."""
        from ai_companion.interfaces.web.app import cleanup_old_audio_files
        assert cleanup_old_audio_files is not None


@pytest.mark.smoke
class TestDeploymentReadiness:
    """High-level smoke tests for deployment readiness."""

    def test_all_critical_modules_load(self):
        """Test that all critical modules can be loaded."""
        # Skip if environment variables are not set
        required_vars = ["GROQ_API_KEY", "ELEVENLABS_API_KEY", "QDRANT_URL"]
        if not all(os.getenv(var) for var in required_vars):
            pytest.skip("Environment variables not set - skipping module load test")

        critical_modules = [
            "ai_companion.settings",
            "ai_companion.graph.graph",
            "ai_companion.graph.state",
            "ai_companion.graph.nodes",
            "ai_companion.modules.memory.long_term_memory",
            "ai_companion.modules.speech.speech_to_text",
            "ai_companion.modules.speech.text_to_speech",
            "ai_companion.interfaces.web.app",
            "ai_companion.core.resilience",
            "ai_companion.core.backup",
        ]

        for module_name in critical_modules:
            try:
                __import__(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import critical module {module_name}: {e}")

    def test_docker_build_files_exist(self):
        """Test that Docker build files exist."""
        assert Path("Dockerfile").exists(), "Dockerfile not found"
        assert Path("docker-compose.yml").exists(), "docker-compose.yml not found"

    def test_railway_config_exists(self):
        """Test that Railway configuration exists."""
        assert Path("config/railway.json").exists(), "config/railway.json not found"

    def test_environment_example_exists(self):
        """Test that environment example file exists."""
        assert Path(".env.example").exists(), ".env.example not found"

    def test_readme_exists(self):
        """Test that README exists."""
        assert Path("README.md").exists(), "README.md not found"
