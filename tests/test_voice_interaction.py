"""Tests for complete voice interaction flow."""

import io
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage

from ai_companion.interfaces.web.app import create_app
from ai_companion.interfaces.web.routes.voice import get_compiled_graph, get_stt, get_tts


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    return create_app()


@pytest.fixture
def mock_audio_data():
    """Create mock audio data for testing."""
    # Create a simple WAV-like byte sequence
    return b"RIFF" + b"\x00" * 100


@pytest.fixture
def session_id():
    """Generate a test session ID."""
    return str(uuid.uuid4())


class TestVoiceInteractionFlow:
    """Test complete voice interaction flow: audio → transcribe → process → respond → audio."""

    def test_complete_voice_flow(self, app, mock_audio_data, session_id):
        """Test complete voice interaction: record → transcribe → process → respond → play audio."""
        # Mock speech-to-text
        mock_stt = MagicMock()
        mock_stt.transcribe = AsyncMock(return_value="I'm feeling sad today")

        # Mock LangGraph compiled graph
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(
            return_value={
                "messages": [
                    HumanMessage(content="I'm feeling sad today"),
                    AIMessage(content="I hear your sadness. Tell me more about what you're experiencing."),
                ],
                "audio_buffer": None,
            }
        )

        # Mock text-to-speech
        mock_tts = MagicMock()
        mock_tts.synthesize = AsyncMock(return_value=b"audio_response_data")

        # Override dependencies
        app.dependency_overrides[get_stt] = lambda: mock_stt
        app.dependency_overrides[get_tts] = lambda: mock_tts
        app.dependency_overrides[get_compiled_graph] = lambda: mock_graph

        try:
            client = TestClient(app)

            # Send voice request
            response = client.post(
                "/api/v1/voice/process",
                files={"audio": ("test.wav", io.BytesIO(mock_audio_data), "audio/wav")},
                data={"session_id": session_id},
            )

            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert "text" in data
            assert "audio_url" in data
            assert "session_id" in data
            assert data["session_id"] == session_id
            assert "sadness" in data["text"].lower()

            # Verify STT was called
            mock_stt.transcribe.assert_called_once()

            # Verify TTS was called
            mock_tts.synthesize.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    def test_silence_handling(self, app, mock_audio_data, session_id):
        """Test that silence returns a gentle acknowledgment."""
        # Mock speech-to-text returning empty (silence)
        mock_stt = MagicMock()
        mock_stt.transcribe = AsyncMock(return_value="")

        # Mock text-to-speech for silence response
        mock_tts = MagicMock()
        mock_tts.synthesize = AsyncMock(return_value=b"silence_audio")

        # Mock graph (shouldn't be called for silence)
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock()

        app.dependency_overrides[get_stt] = lambda: mock_stt
        app.dependency_overrides[get_tts] = lambda: mock_tts
        app.dependency_overrides[get_compiled_graph] = lambda: mock_graph

        try:
            client = TestClient(app)

            response = client.post(
                "/api/v1/voice/process",
                files={"audio": ("test.wav", io.BytesIO(mock_audio_data), "audio/wav")},
                data={"session_id": session_id},
            )

            assert response.status_code == 200
            data = response.json()
            # Should return a silence response, not empty
            assert data["text"] == "I'm here whenever you're ready."

            # Graph should NOT be called for silence
            mock_graph.ainvoke.assert_not_called()
        finally:
            app.dependency_overrides.clear()

    def test_stt_error_recovery(self, app, mock_audio_data, session_id):
        """Test error recovery when speech-to-text fails."""
        mock_stt = MagicMock()
        mock_stt.transcribe = AsyncMock(side_effect=Exception("STT API error"))

        mock_tts = MagicMock()
        mock_graph = MagicMock()

        app.dependency_overrides[get_stt] = lambda: mock_stt
        app.dependency_overrides[get_tts] = lambda: mock_tts
        app.dependency_overrides[get_compiled_graph] = lambda: mock_graph

        try:
            client = TestClient(app)

            response = client.post(
                "/api/v1/voice/process",
                files={"audio": ("test.wav", io.BytesIO(mock_audio_data), "audio/wav")},
                data={"session_id": session_id},
            )

            # Should return error
            assert response.status_code in [500, 503]
        finally:
            app.dependency_overrides.clear()

    def test_workflow_error_recovery(self, app, mock_audio_data, session_id):
        """Test error recovery when LangGraph workflow fails."""
        mock_stt = MagicMock()
        mock_stt.transcribe = AsyncMock(return_value="Hello")

        mock_tts = MagicMock()

        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(side_effect=Exception("Workflow error"))

        app.dependency_overrides[get_stt] = lambda: mock_stt
        app.dependency_overrides[get_tts] = lambda: mock_tts
        app.dependency_overrides[get_compiled_graph] = lambda: mock_graph

        try:
            client = TestClient(app)

            response = client.post(
                "/api/v1/voice/process",
                files={"audio": ("test.wav", io.BytesIO(mock_audio_data), "audio/wav")},
                data={"session_id": session_id},
            )

            # Should return error
            assert response.status_code in [500, 503]
        finally:
            app.dependency_overrides.clear()

    def test_audio_size_validation(self, app, session_id):
        """Test audio file size validation."""
        mock_stt = MagicMock()
        mock_tts = MagicMock()
        mock_graph = MagicMock()

        app.dependency_overrides[get_stt] = lambda: mock_stt
        app.dependency_overrides[get_tts] = lambda: mock_tts
        app.dependency_overrides[get_compiled_graph] = lambda: mock_graph

        try:
            client = TestClient(app)

            # Create oversized audio data (>10MB)
            large_audio = b"x" * (11 * 1024 * 1024)

            response = client.post(
                "/api/v1/voice/process",
                files={"audio": ("large.wav", io.BytesIO(large_audio), "audio/wav")},
                data={"session_id": session_id},
            )

            assert response.status_code == 413
            data = response.json()
            # May come from middleware (error/message) or endpoint (detail)
            msg = data.get("detail", data.get("message", "")).lower()
            assert "too large" in msg or "maximum" in msg
        finally:
            app.dependency_overrides.clear()

    def test_empty_audio_validation(self, app, session_id):
        """Test empty audio file validation."""
        mock_stt = MagicMock()
        mock_tts = MagicMock()
        mock_graph = MagicMock()

        app.dependency_overrides[get_stt] = lambda: mock_stt
        app.dependency_overrides[get_tts] = lambda: mock_tts
        app.dependency_overrides[get_compiled_graph] = lambda: mock_graph

        try:
            client = TestClient(app)

            response = client.post(
                "/api/v1/voice/process",
                files={"audio": ("empty.wav", io.BytesIO(b""), "audio/wav")},
                data={"session_id": session_id},
            )

            assert response.status_code == 400
            detail = response.json()["detail"].lower()
            assert "audio" in detail
        finally:
            app.dependency_overrides.clear()


class TestAudioServing:
    """Test audio file serving endpoint."""

    def test_serve_existing_audio(self, app):
        """Test serving an existing audio file."""
        from ai_companion.interfaces.web.routes.voice import AUDIO_DIR

        mock_graph = MagicMock()
        app.dependency_overrides[get_compiled_graph] = lambda: mock_graph

        try:
            client = TestClient(app)

            audio_id = str(uuid.uuid4())
            audio_path = AUDIO_DIR / f"{audio_id}.mp3"
            audio_path.write_bytes(b"test_audio_data")

            try:
                response = client.get(f"/api/v1/voice/audio/{audio_id}")
                assert response.status_code == 200
                assert response.headers["content-type"] == "audio/mpeg"
                assert response.content == b"test_audio_data"
            finally:
                # Cleanup
                if audio_path.exists():
                    audio_path.unlink()
        finally:
            app.dependency_overrides.clear()

    def test_serve_nonexistent_audio(self, app):
        """Test serving a non-existent audio file."""
        mock_graph = MagicMock()
        app.dependency_overrides[get_compiled_graph] = lambda: mock_graph

        try:
            client = TestClient(app)

            fake_id = str(uuid.uuid4())
            response = client.get(f"/api/v1/voice/audio/{fake_id}")
            assert response.status_code == 404
            detail = response.json()["detail"].lower()
            assert "expired" in detail or "doesn't exist" in detail
        finally:
            app.dependency_overrides.clear()
