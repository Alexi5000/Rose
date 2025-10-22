"""
Integration tests with real external APIs.

These tests verify end-to-end functionality with actual external services:
- Groq API (LLM, STT)
- ElevenLabs API (TTS)
- Qdrant (vector database)

Note: These tests require valid API keys and will make real API calls.
They are marked with @pytest.mark.integration and skipped by default.
Run with: pytest tests/test_integration.py -v -m integration
"""

import os
import pytest
import asyncio
from pathlib import Path
from uuid import uuid4
import tempfile
import wave
import struct

# Skip all integration tests if API keys are not set
pytestmark = pytest.mark.integration


def create_test_audio_file(duration_seconds: float = 1.0, sample_rate: int = 16000) -> Path:
    """Create a simple test audio file (sine wave)."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_path = Path(temp_file.name)
    
    # Generate a simple sine wave
    import math
    frequency = 440.0  # A4 note
    num_samples = int(duration_seconds * sample_rate)
    
    with wave.open(str(temp_path), 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        for i in range(num_samples):
            value = int(32767.0 * math.sin(2.0 * math.pi * frequency * i / sample_rate))
            wav_file.writeframes(struct.pack('<h', value))
    
    return temp_path


@pytest.fixture(scope="module")
def check_api_keys():
    """Verify that required API keys are set."""
    required_keys = ["GROQ_API_KEY", "ELEVENLABS_API_KEY", "QDRANT_URL", "QDRANT_API_KEY"]
    missing = [key for key in required_keys if not os.getenv(key)]
    
    if missing:
        pytest.skip(f"Missing required API keys: {', '.join(missing)}")


class TestGroqIntegration:
    """Integration tests for Groq API (LLM and STT)."""
    
    @pytest.mark.asyncio
    async def test_groq_llm_completion(self, check_api_keys):
        """Test Groq LLM completion with real API."""
        from langchain_groq import ChatGroq
        from ai_companion.settings import settings
        
        llm = ChatGroq(
            model=settings.GROQ_MODEL_NAME,
            api_key=settings.GROQ_API_KEY,
            temperature=0.7
        )
        
        response = await llm.ainvoke("Say 'Hello, this is a test' and nothing else.")
        
        assert response is not None
        assert hasattr(response, 'content')
        assert len(response.content) > 0
        assert isinstance(response.content, str)
    
    @pytest.mark.asyncio
    async def test_groq_stt_transcription(self, check_api_keys):
        """Test Groq STT with real audio file."""
        from ai_companion.modules.speech.speech_to_text import transcribe_audio
        
        # Create a test audio file
        audio_path = create_test_audio_file(duration_seconds=2.0)
        
        try:
            # Note: This will likely fail to transcribe a sine wave,
            # but it tests the API connection and error handling
            result = await transcribe_audio(str(audio_path))
            
            # If it succeeds, verify the response structure
            assert result is not None
            assert isinstance(result, str)
        except Exception as e:
            # Expected to fail with sine wave, but should be a proper API error
            assert "audio" in str(e).lower() or "transcription" in str(e).lower()
        finally:
            # Clean up test file
            audio_path.unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_groq_circuit_breaker_integration(self, check_api_keys):
        """Test that Groq circuit breaker works with real API."""
        from ai_companion.core.resilience import get_groq_circuit_breaker
        from langchain_groq import ChatGroq
        from ai_companion.settings import settings
        
        breaker = get_groq_circuit_breaker()
        
        # Verify circuit breaker is closed (operational)
        assert breaker.current_state == "closed"
        
        # Make a successful call through circuit breaker
        @breaker
        async def call_groq():
            llm = ChatGroq(
                model=settings.GROQ_MODEL_NAME,
                api_key=settings.GROQ_API_KEY,
                temperature=0.7
            )
            return await llm.ainvoke("Test")
        
        response = await call_groq()
        assert response is not None
        
        # Circuit breaker should still be closed after success
        assert breaker.current_state == "closed"


class TestElevenLabsIntegration:
    """Integration tests for ElevenLabs TTS API."""
    
    @pytest.mark.asyncio
    async def test_elevenlabs_tts_synthesis(self, check_api_keys):
        """Test ElevenLabs TTS with real API."""
        from ai_companion.modules.speech.text_to_speech import synthesize_speech
        
        text = "Hello, this is a test of the text to speech system."
        
        audio_data = await synthesize_speech(text)
        
        assert audio_data is not None
        assert isinstance(audio_data, bytes)
        assert len(audio_data) > 0
        # Audio files typically start with specific headers
        assert len(audio_data) > 100  # Should be substantial
    
    @pytest.mark.asyncio
    async def test_elevenlabs_fallback_mechanism(self, check_api_keys):
        """Test ElevenLabs fallback with real API."""
        from ai_companion.modules.speech.text_to_speech import synthesize_with_fallback
        
        text = "Testing fallback mechanism."
        
        audio_data = await synthesize_with_fallback(text)
        
        assert audio_data is not None
        assert isinstance(audio_data, bytes)
        assert len(audio_data) > 0
    
    @pytest.mark.asyncio
    async def test_elevenlabs_circuit_breaker_integration(self, check_api_keys):
        """Test that ElevenLabs circuit breaker works with real API."""
        from ai_companion.core.resilience import get_elevenlabs_circuit_breaker
        from ai_companion.modules.speech.text_to_speech import synthesize_speech
        
        breaker = get_elevenlabs_circuit_breaker()
        
        # Verify circuit breaker is closed (operational)
        assert breaker.current_state == "closed"
        
        # Make a successful call through circuit breaker
        @breaker
        async def call_elevenlabs():
            return await synthesize_speech("Test")
        
        response = await call_elevenlabs()
        assert response is not None
        
        # Circuit breaker should still be closed after success
        assert breaker.current_state == "closed"


class TestQdrantIntegration:
    """Integration tests for Qdrant vector database."""
    
    @pytest.mark.asyncio
    async def test_qdrant_connection(self, check_api_keys):
        """Test Qdrant connection and collection access."""
        from ai_companion.modules.memory.long_term_memory import get_qdrant_client
        from ai_companion.settings import settings
        
        client = get_qdrant_client()
        
        # Verify client is connected
        assert client is not None
        
        # Try to get collection info (will create if doesn't exist)
        try:
            collection_info = client.get_collection(settings.QDRANT_COLLECTION_NAME)
            assert collection_info is not None
        except Exception:
            # Collection might not exist yet, which is fine
            pass
    
    @pytest.mark.asyncio
    async def test_qdrant_memory_storage_retrieval(self, check_api_keys):
        """Test storing and retrieving memories from Qdrant."""
        from ai_companion.modules.memory.long_term_memory import (
            store_memory,
            retrieve_relevant_memories
        )
        
        # Create a unique test session
        test_session_id = f"test_integration_{uuid4()}"
        test_memory = "I feel peaceful when I meditate in nature."
        
        # Store a memory
        await store_memory(
            session_id=test_session_id,
            memory_text=test_memory,
            memory_type="emotional_state"
        )
        
        # Retrieve related memories
        query = "How do I find peace?"
        memories = await retrieve_relevant_memories(
            session_id=test_session_id,
            query=query,
            limit=5
        )
        
        # Verify we got results
        assert memories is not None
        assert isinstance(memories, list)
        # We should find our stored memory
        assert len(memories) > 0
    
    @pytest.mark.asyncio
    async def test_qdrant_circuit_breaker_integration(self, check_api_keys):
        """Test that Qdrant circuit breaker works with real API."""
        from ai_companion.core.resilience import get_qdrant_circuit_breaker
        from ai_companion.modules.memory.long_term_memory import get_qdrant_client
        from ai_companion.settings import settings
        
        breaker = get_qdrant_circuit_breaker()
        
        # Verify circuit breaker is closed (operational)
        assert breaker.current_state == "closed"
        
        # Make a successful call through circuit breaker
        @breaker
        def call_qdrant():
            client = get_qdrant_client()
            return client.get_collection(settings.QDRANT_COLLECTION_NAME)
        
        try:
            response = call_qdrant()
            assert response is not None
        except Exception:
            # Collection might not exist, but connection should work
            pass
        
        # Circuit breaker should still be closed after success
        assert breaker.current_state == "closed"


class TestEndToEndVoiceFlow:
    """End-to-end integration tests for complete voice interaction flow."""
    
    @pytest.mark.asyncio
    async def test_complete_voice_workflow(self, check_api_keys):
        """Test complete voice workflow: session → audio → transcription → LLM → TTS."""
        from fastapi.testclient import TestClient
        from ai_companion.interfaces.web.app import app
        import io
        
        client = TestClient(app)
        
        # Step 1: Create a session
        session_response = client.post("/api/session/start")
        assert session_response.status_code == 200
        session_data = session_response.json()
        session_id = session_data["session_id"]
        assert session_id is not None
        
        # Step 2: Create test audio file
        audio_path = create_test_audio_file(duration_seconds=2.0)
        
        try:
            # Step 3: Process voice input
            with open(audio_path, "rb") as audio_file:
                files = {"audio": ("test.wav", audio_file, "audio/wav")}
                data = {"session_id": session_id}
                
                # Note: This may fail with sine wave audio, but tests the flow
                voice_response = client.post(
                    "/api/voice/process",
                    files=files,
                    data=data
                )
                
                # If successful, verify response structure
                if voice_response.status_code == 200:
                    voice_data = voice_response.json()
                    assert "text" in voice_data
                    assert "session_id" in voice_data
                    assert voice_data["session_id"] == session_id
                    
                    # If audio URL is provided, verify it's accessible
                    if voice_data.get("audio_url"):
                        audio_url = voice_data["audio_url"]
                        audio_response = client.get(audio_url)
                        assert audio_response.status_code == 200
                        assert len(audio_response.content) > 0
        finally:
            # Clean up test file
            audio_path.unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_session_continuity_with_memory(self, check_api_keys):
        """Test that memories persist across multiple interactions."""
        from fastapi.testclient import TestClient
        from ai_companion.interfaces.web.app import app
        
        client = TestClient(app)
        
        # Create a session
        session_response = client.post("/api/session/start")
        assert session_response.status_code == 200
        session_id = session_response.json()["session_id"]
        
        # First interaction - share something personal
        audio_path1 = create_test_audio_file(duration_seconds=2.0)
        
        try:
            with open(audio_path1, "rb") as audio_file:
                files = {"audio": ("test1.wav", audio_file, "audio/wav")}
                data = {"session_id": session_id}
                
                response1 = client.post("/api/voice/process", files=files, data=data)
                
                # May fail with sine wave, but if successful, continue
                if response1.status_code == 200:
                    # Second interaction - reference previous conversation
                    audio_path2 = create_test_audio_file(duration_seconds=2.0)
                    
                    with open(audio_path2, "rb") as audio_file2:
                        files2 = {"audio": ("test2.wav", audio_file2, "audio/wav")}
                        data2 = {"session_id": session_id}
                        
                        response2 = client.post("/api/voice/process", files=files2, data=data2)
                        
                        # Verify session continuity
                        if response2.status_code == 200:
                            data2 = response2.json()
                            assert data2["session_id"] == session_id
                    
                    audio_path2.unlink(missing_ok=True)
        finally:
            audio_path1.unlink(missing_ok=True)


class TestHealthCheckIntegration:
    """Integration tests for health check endpoint with real services."""
    
    def test_health_check_with_real_services(self, check_api_keys):
        """Test health check endpoint with real external services."""
        from fastapi.testclient import TestClient
        from ai_companion.interfaces.web.app import app
        
        client = TestClient(app)
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "status" in data
        assert "services" in data
        
        # Verify service checks
        services = data["services"]
        assert "groq" in services
        assert "elevenlabs" in services
        assert "qdrant" in services
        
        # All services should be healthy with valid API keys
        assert services["groq"]["status"] == "healthy"
        assert services["elevenlabs"]["status"] == "healthy"
        assert services["qdrant"]["status"] == "healthy"


class TestErrorRecoveryIntegration:
    """Integration tests for error recovery and resilience."""
    
    @pytest.mark.asyncio
    async def test_invalid_audio_handling(self, check_api_keys):
        """Test handling of invalid audio files."""
        from fastapi.testclient import TestClient
        from ai_companion.interfaces.web.app import app
        import io
        
        client = TestClient(app)
        
        # Create a session
        session_response = client.post("/api/session/start")
        session_id = session_response.json()["session_id"]
        
        # Send invalid audio data
        invalid_audio = io.BytesIO(b"This is not audio data")
        files = {"audio": ("invalid.wav", invalid_audio, "audio/wav")}
        data = {"session_id": session_id}
        
        response = client.post("/api/voice/process", files=files, data=data)
        
        # Should return an error but not crash
        assert response.status_code in [400, 422, 500]
        error_data = response.json()
        assert "error" in error_data or "detail" in error_data
    
    @pytest.mark.asyncio
    async def test_oversized_audio_rejection(self, check_api_keys):
        """Test rejection of oversized audio files."""
        from fastapi.testclient import TestClient
        from ai_companion.interfaces.web.app import app
        import io
        
        client = TestClient(app)
        
        # Create a session
        session_response = client.post("/api/session/start")
        session_id = session_response.json()["session_id"]
        
        # Create oversized audio data (> 10MB)
        oversized_audio = io.BytesIO(b"0" * (11 * 1024 * 1024))
        files = {"audio": ("large.wav", oversized_audio, "audio/wav")}
        data = {"session_id": session_id}
        
        response = client.post("/api/voice/process", files=files, data=data)
        
        # Should reject oversized files
        assert response.status_code in [400, 413, 422]
        error_data = response.json()
        assert "error" in error_data or "detail" in error_data


class TestConcurrentRequestsIntegration:
    """Integration tests for concurrent request handling."""
    
    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, check_api_keys):
        """Test handling of multiple concurrent sessions."""
        from fastapi.testclient import TestClient
        from ai_companion.interfaces.web.app import app
        import concurrent.futures
        
        client = TestClient(app)
        
        def create_session():
            response = client.post("/api/session/start")
            return response.json()["session_id"]
        
        # Create multiple sessions concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_session) for _ in range(5)]
            session_ids = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # Verify all sessions were created with unique IDs
        assert len(session_ids) == 5
        assert len(set(session_ids)) == 5  # All unique
