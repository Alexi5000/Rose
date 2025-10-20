"""Tests for complete voice interaction flow."""

import io
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage

from ai_companion.interfaces.web.app import create_app


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    app = create_app()
    return TestClient(app)


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

    @patch("ai_companion.interfaces.web.routes.voice.stt")
    @patch("ai_companion.interfaces.web.routes.voice.tts")
    @patch("ai_companion.interfaces.web.routes.voice.create_workflow_graph")
    def test_complete_voice_flow(self, mock_graph, mock_tts, mock_stt, client, mock_audio_data, session_id):
        """Test complete voice interaction: record → transcribe → process → respond → play audio."""
        # Mock speech-to-text
        mock_stt.transcribe = AsyncMock(return_value="I'm feeling sad today")

        # Mock LangGraph workflow
        mock_workflow = MagicMock()
        mock_workflow.ainvoke = AsyncMock(
            return_value={
                "messages": [
                    HumanMessage(content="I'm feeling sad today"),
                    AIMessage(content="I hear your sadness. Tell me more about what you're experiencing."),
                ]
            }
        )
        mock_compiled = MagicMock()
        mock_compiled.compile = MagicMock(return_value=mock_workflow)
        mock_graph.return_value = mock_compiled

        # Mock text-to-speech
        mock_tts.synthesize = AsyncMock(return_value=b"audio_response_data")

        # Send voice request
        response = client.post(
            "/api/voice/process",
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

    @patch("ai_companion.interfaces.web.routes.voice.stt")
    @patch("ai_companion.interfaces.web.routes.voice.tts")
    @patch("ai_companion.interfaces.web.routes.voice.create_workflow_graph")
    def test_session_continuity(self, mock_graph, mock_tts, mock_stt, client, mock_audio_data, session_id):
        """Test session continuity across multiple interactions."""
        # Mock STT
        mock_stt.transcribe = AsyncMock(side_effect=["My name is Sarah", "Do you remember my name?"])

        # Mock workflow with memory
        call_count = [0]

        async def mock_invoke(input_data, config):
            call_count[0] += 1
            if call_count[0] == 1:
                return {
                    "messages": [
                        HumanMessage(content="My name is Sarah"),
                        AIMessage(content="Hello Sarah, it's wonderful to meet you."),
                    ]
                }
            else:
                return {
                    "messages": [
                        HumanMessage(content="Do you remember my name?"),
                        AIMessage(content="Yes, Sarah. I remember you."),
                    ]
                }

        mock_workflow = MagicMock()
        mock_workflow.ainvoke = mock_invoke
        mock_compiled = MagicMock()
        mock_compiled.compile = MagicMock(return_value=mock_workflow)
        mock_graph.return_value = mock_compiled

        # Mock TTS
        mock_tts.synthesize = AsyncMock(return_value=b"audio_data")

        # First interaction
        response1 = client.post(
            "/api/voice/process",
            files={"audio": ("test1.wav", io.BytesIO(mock_audio_data), "audio/wav")},
            data={"session_id": session_id},
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert "Sarah" in data1["text"]

        # Second interaction with same session
        response2 = client.post(
            "/api/voice/process",
            files={"audio": ("test2.wav", io.BytesIO(mock_audio_data), "audio/wav")},
            data={"session_id": session_id},
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert "Sarah" in data2["text"]
        assert "remember" in data2["text"].lower()

    @patch("ai_companion.interfaces.web.routes.voice.stt")
    def test_stt_error_recovery(self, mock_stt, client, mock_audio_data, session_id):
        """Test error recovery when speech-to-text fails."""
        # Mock STT failure
        mock_stt.transcribe = AsyncMock(side_effect=Exception("STT API error"))

        # Send voice request
        response = client.post(
            "/api/voice/process",
            files={"audio": ("test.wav", io.BytesIO(mock_audio_data), "audio/wav")},
            data={"session_id": session_id},
        )

        # Should return error with retry message
        assert response.status_code == 503
        assert "try again" in response.json()["detail"].lower()

    @patch("ai_companion.interfaces.web.routes.voice.stt")
    @patch("ai_companion.interfaces.web.routes.voice.create_workflow_graph")
    def test_workflow_error_recovery(self, mock_graph, mock_stt, client, mock_audio_data, session_id):
        """Test error recovery when LangGraph workflow fails."""
        # Mock STT success
        mock_stt.transcribe = AsyncMock(return_value="Hello")

        # Mock workflow failure
        mock_workflow = MagicMock()
        mock_workflow.ainvoke = AsyncMock(side_effect=Exception("Workflow error"))
        mock_compiled = MagicMock()
        mock_compiled.compile = MagicMock(return_value=mock_workflow)
        mock_graph.return_value = mock_compiled

        # Send voice request
        response = client.post(
            "/api/voice/process",
            files={"audio": ("test.wav", io.BytesIO(mock_audio_data), "audio/wav")},
            data={"session_id": session_id},
        )

        # Should return error with connection message
        assert response.status_code == 503
        assert "trouble connecting" in response.json()["detail"].lower()

    @patch("ai_companion.interfaces.web.routes.voice.stt")
    @patch("ai_companion.interfaces.web.routes.voice.tts")
    @patch("ai_companion.interfaces.web.routes.voice.create_workflow_graph")
    def test_tts_fallback(self, mock_graph, mock_tts, mock_stt, client, mock_audio_data, session_id):
        """Test fallback to text-only when TTS fails."""
        # Mock STT
        mock_stt.transcribe = AsyncMock(return_value="Hello")

        # Mock workflow
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

        # Mock TTS failure
        mock_tts.synthesize = AsyncMock(side_effect=Exception("TTS error"))

        # Send voice request
        response = client.post(
            "/api/voice/process",
            files={"audio": ("test.wav", io.BytesIO(mock_audio_data), "audio/wav")},
            data={"session_id": session_id},
        )

        # Should still return 200 with text response
        assert response.status_code == 200

    def test_audio_size_validation(self, client, session_id):
        """Test audio file size validation."""
        # Create oversized audio data (>10MB)
        large_audio = b"x" * (11 * 1024 * 1024)

        response = client.post(
            "/api/voice/process",
            files={"audio": ("large.wav", io.BytesIO(large_audio), "audio/wav")},
            data={"session_id": session_id},
        )

        assert response.status_code == 413
        assert "too large" in response.json()["detail"].lower()

    def test_empty_audio_validation(self, client, session_id):
        """Test empty audio file validation."""
        response = client.post(
            "/api/voice/process",
            files={"audio": ("empty.wav", io.BytesIO(b""), "audio/wav")},
            data={"session_id": session_id},
        )

        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()


class TestAudioServing:
    """Test audio file serving endpoint."""

    def test_serve_existing_audio(self, client):
        """Test serving an existing audio file."""
        # Create a temporary audio file
        from ai_companion.interfaces.web.routes.voice import AUDIO_DIR

        audio_id = str(uuid.uuid4())
        audio_path = AUDIO_DIR / f"{audio_id}.mp3"
        audio_path.write_bytes(b"test_audio_data")

        try:
            response = client.get(f"/api/voice/audio/{audio_id}")
            assert response.status_code == 200
            assert response.headers["content-type"] == "audio/mpeg"
            assert response.content == b"test_audio_data"
        finally:
            # Cleanup
            if audio_path.exists():
                audio_path.unlink()

    def test_serve_nonexistent_audio(self, client):
        """Test serving a non-existent audio file."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/voice/audio/{fake_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
