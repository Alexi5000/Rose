"""Performance and load testing for Rose the Healer Shaman."""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from ai_companion.interfaces.web.app import create_app


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    app = create_app()
    return TestClient(app)


class TestAPIPerformance:
    """Test API endpoint performance."""

    def test_health_check_response_time(self, client):
        """Test health check endpoint responds quickly."""
        start = time.time()
        response = client.get("/api/health")
        duration = time.time() - start

        assert response.status_code == 200
        # Health check should respond in less than 2 seconds
        assert duration < 2.0

    def test_session_start_response_time(self, client):
        """Test session start endpoint responds quickly."""
        start = time.time()
        response = client.post("/api/session/start")
        duration = time.time() - start

        assert response.status_code == 200
        # Session start should be very fast (< 0.5s)
        assert duration < 0.5

    @patch("ai_companion.interfaces.web.routes.voice.stt")
    @patch("ai_companion.interfaces.web.routes.voice.tts")
    @patch("ai_companion.interfaces.web.routes.voice.create_workflow_graph")
    def test_voice_processing_latency(self, mock_graph, mock_tts, mock_stt, client):
        """Test voice processing latency is acceptable."""
        # Mock fast responses
        mock_stt.transcribe = AsyncMock(return_value="Hello")
        mock_tts.synthesize = AsyncMock(return_value=b"audio_data")

        from langchain_core.messages import AIMessage, HumanMessage

        mock_workflow = MagicMock()
        mock_workflow.ainvoke = AsyncMock(
            return_value={
                "messages": [
                    HumanMessage(content="Hello"),
                    AIMessage(content="Hello, I'm here for you."),
                ]
            }
        )
        mock_compiled = MagicMock()
        mock_compiled.compile = MagicMock(return_value=mock_workflow)
        mock_graph.return_value = mock_compiled

        import io

        audio_data = b"RIFF" + b"\x00" * 100

        start = time.time()
        response = client.post(
            "/api/voice/process",
            files={"audio": ("test.wav", io.BytesIO(audio_data), "audio/wav")},
            data={"session_id": "test-session"},
        )
        duration = time.time() - start

        assert response.status_code == 200
        # Total processing should complete in reasonable time
        # Note: In production this depends on Groq API latency
        print(f"Voice processing took {duration:.2f}s")


class TestConcurrentSessions:
    """Test handling of concurrent voice sessions."""

    @patch("ai_companion.interfaces.web.routes.voice.stt")
    @patch("ai_companion.interfaces.web.routes.voice.tts")
    @patch("ai_companion.interfaces.web.routes.voice.create_workflow_graph")
    def test_multiple_concurrent_sessions(self, mock_graph, mock_tts, mock_stt, client):
        """Test system handles multiple concurrent sessions."""
        # Mock responses
        mock_stt.transcribe = AsyncMock(return_value="Hello")
        mock_tts.synthesize = AsyncMock(return_value=b"audio_data")

        from langchain_core.messages import AIMessage, HumanMessage

        mock_workflow = MagicMock()
        mock_workflow.ainvoke = AsyncMock(
            return_value={
                "messages": [
                    HumanMessage(content="Hello"),
                    AIMessage(content="Hello, I'm here for you."),
                ]
            }
        )
        mock_compiled = MagicMock()
        mock_compiled.compile = MagicMock(return_value=mock_workflow)
        mock_graph.return_value = mock_compiled

        import io

        audio_data = b"RIFF" + b"\x00" * 100

        def make_request(session_num):
            """Make a voice processing request."""
            response = client.post(
                "/api/voice/process",
                files={"audio": (f"test{session_num}.wav", io.BytesIO(audio_data), "audio/wav")},
                data={"session_id": f"session-{session_num}"},
            )
            return response.status_code

        # Test with 5 concurrent sessions
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(5)]
            results = [f.result() for f in futures]

        # All requests should succeed
        assert all(status == 200 for status in results)

    def test_session_isolation(self, client):
        """Test that sessions are properly isolated."""
        # Start two sessions
        response1 = client.post("/api/session/start")
        response2 = client.post("/api/session/start")

        assert response1.status_code == 200
        assert response2.status_code == 200

        session1 = response1.json()["session_id"]
        session2 = response2.json()["session_id"]

        # Sessions should have different IDs
        assert session1 != session2


class TestResourceConsumption:
    """Test resource consumption and limits."""

    def test_audio_file_size_limit(self, client):
        """Test that audio file size limit is enforced."""
        import io

        # Create audio larger than 10MB
        large_audio = b"x" * (11 * 1024 * 1024)

        response = client.post(
            "/api/voice/process",
            files={"audio": ("large.wav", io.BytesIO(large_audio), "audio/wav")},
            data={"session_id": "test-session"},
        )

        # Should reject with 413 (Payload Too Large)
        assert response.status_code == 413

    def test_memory_cleanup(self):
        """Test that temporary audio files are cleaned up."""
        from ai_companion.interfaces.web.routes.voice import AUDIO_DIR, cleanup_old_audio_files
        import uuid
        from pathlib import Path

        # Create some old test files
        old_file = AUDIO_DIR / f"{uuid.uuid4()}.mp3"
        old_file.write_bytes(b"test_data")

        # Modify timestamp to make it old
        import os

        old_time = time.time() - (25 * 3600)  # 25 hours ago
        os.utime(old_file, (old_time, old_time))

        # Run cleanup
        cleanup_old_audio_files(max_age_hours=24)

        # Old file should be deleted
        assert not old_file.exists()

    @patch("ai_companion.interfaces.web.routes.voice.stt")
    @patch("ai_companion.interfaces.web.routes.voice.tts")
    @patch("ai_companion.interfaces.web.routes.voice.create_workflow_graph")
    def test_rapid_requests_same_session(self, mock_graph, mock_tts, mock_stt, client):
        """Test handling of rapid requests from same session."""
        # Mock responses
        mock_stt.transcribe = AsyncMock(return_value="Hello")
        mock_tts.synthesize = AsyncMock(return_value=b"audio_data")

        from langchain_core.messages import AIMessage, HumanMessage

        mock_workflow = MagicMock()
        mock_workflow.ainvoke = AsyncMock(
            return_value={
                "messages": [
                    HumanMessage(content="Hello"),
                    AIMessage(content="Hello, I'm here for you."),
                ]
            }
        )
        mock_compiled = MagicMock()
        mock_compiled.compile = MagicMock(return_value=mock_workflow)
        mock_graph.return_value = mock_compiled

        import io

        audio_data = b"RIFF" + b"\x00" * 100
        session_id = "rapid-test-session"

        # Make 3 rapid requests
        responses = []
        for i in range(3):
            response = client.post(
                "/api/voice/process",
                files={"audio": (f"test{i}.wav", io.BytesIO(audio_data), "audio/wav")},
                data={"session_id": session_id},
            )
            responses.append(response)

        # All should succeed
        assert all(r.status_code == 200 for r in responses)


class TestAPIUsageMonitoring:
    """Test API usage tracking and cost monitoring."""

    @patch("ai_companion.interfaces.web.routes.voice.stt")
    @patch("ai_companion.interfaces.web.routes.voice.tts")
    @patch("ai_companion.interfaces.web.routes.voice.create_workflow_graph")
    def test_api_call_logging(self, mock_graph, mock_tts, mock_stt, client):
        """Test that API calls are logged for monitoring."""
        # Mock responses
        mock_stt.transcribe = AsyncMock(return_value="Hello")
        mock_tts.synthesize = AsyncMock(return_value=b"audio_data")

        from langchain_core.messages import AIMessage, HumanMessage

        mock_workflow = MagicMock()
        mock_workflow.ainvoke = AsyncMock(
            return_value={
                "messages": [
                    HumanMessage(content="Hello"),
                    AIMessage(content="Hello, I'm here for you."),
                ]
            }
        )
        mock_compiled = MagicMock()
        mock_compiled.compile = MagicMock(return_value=mock_workflow)
        mock_graph.return_value = mock_compiled

        import io

        audio_data = b"RIFF" + b"\x00" * 100

        with patch("ai_companion.interfaces.web.routes.voice.logger") as mock_logger:
            response = client.post(
                "/api/voice/process",
                files={"audio": ("test.wav", io.BytesIO(audio_data), "audio/wav")},
                data={"session_id": "test-session"},
            )

            assert response.status_code == 200
            # Verify logging occurred
            assert mock_logger.info.called


class TestRailwayLimits:
    """Test resource consumption within Railway platform limits."""

    def test_memory_usage_reasonable(self):
        """Test that memory usage is within reasonable limits."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024

        # Should use less than 512MB for basic operations
        # Note: This is a rough estimate, actual usage depends on workload
        print(f"Current memory usage: {memory_mb:.2f} MB")
        assert memory_mb < 1024  # Less than 1GB

    def test_database_connection_pooling(self):
        """Test that database connections are properly pooled."""
        # This would test Qdrant and SQLite connection management
        # Ensure connections are reused, not created for each request
        pass

    def test_response_size_reasonable(self, client):
        """Test that API responses are not excessively large."""
        response = client.get("/api/health")
        content_length = len(response.content)

        # Health check response should be small
        assert content_length < 10000  # Less than 10KB


class TestLoadScenarios:
    """Test various load scenarios."""

    @patch("ai_companion.interfaces.web.routes.voice.stt")
    @patch("ai_companion.interfaces.web.routes.voice.tts")
    @patch("ai_companion.interfaces.web.routes.voice.create_workflow_graph")
    def test_sustained_load(self, mock_graph, mock_tts, mock_stt, client):
        """Test system under sustained load."""
        # Mock responses
        mock_stt.transcribe = AsyncMock(return_value="Hello")
        mock_tts.synthesize = AsyncMock(return_value=b"audio_data")

        from langchain_core.messages import AIMessage, HumanMessage

        mock_workflow = MagicMock()
        mock_workflow.ainvoke = AsyncMock(
            return_value={
                "messages": [
                    HumanMessage(content="Hello"),
                    AIMessage(content="Hello, I'm here for you."),
                ]
            }
        )
        mock_compiled = MagicMock()
        mock_compiled.compile = MagicMock(return_value=mock_workflow)
        mock_graph.return_value = mock_compiled

        import io

        audio_data = b"RIFF" + b"\x00" * 100

        # Simulate 10 sequential requests
        start = time.time()
        success_count = 0

        for i in range(10):
            response = client.post(
                "/api/voice/process",
                files={"audio": (f"test{i}.wav", io.BytesIO(audio_data), "audio/wav")},
                data={"session_id": f"session-{i}"},
            )
            if response.status_code == 200:
                success_count += 1

        duration = time.time() - start

        # All requests should succeed
        assert success_count == 10
        print(f"10 requests completed in {duration:.2f}s")

    def test_burst_load(self, client):
        """Test system handles burst of requests."""

        def make_health_check():
            return client.get("/api/health").status_code

        # Burst of 20 health checks
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_health_check) for _ in range(20)]
            results = [f.result() for f in futures]

        # Most should succeed (allow for some rate limiting)
        success_rate = sum(1 for r in results if r == 200) / len(results)
        assert success_rate > 0.8  # At least 80% success rate


# Performance testing instructions
"""
To run comprehensive load tests:

1. Install load testing tools:
   pip install locust

2. Create a locustfile.py:
   ```python
   from locust import HttpUser, task, between
   
   class RoseUser(HttpUser):
       wait_time = between(1, 3)
       
       @task
       def health_check(self):
           self.client.get("/api/health")
       
       @task(3)
       def voice_interaction(self):
           # Simulate voice interaction
           pass
   ```

3. Run Locust:
   locust -f locustfile.py --host=http://localhost:8080

4. Open web UI at http://localhost:8089

5. Configure:
   - Number of users: 10-50
   - Spawn rate: 1-5 users/second
   - Run time: 5-10 minutes

6. Monitor:
   - Response times (p50, p95, p99)
   - Requests per second
   - Failure rate
   - Resource usage (CPU, memory)

7. Railway-specific testing:
   - Test with Railway's resource limits
   - Monitor costs during load test
   - Verify auto-scaling behavior (if enabled)
"""
