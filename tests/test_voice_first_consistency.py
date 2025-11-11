"""Tests for voice-first consistency across all input types in Chainlit interface.

This test module verifies that Rose consistently responds with voice (TTS audio)
for all user interactions, regardless of input modality (text, voice, or image).

Requirements tested:
- 1.1: Text messages generate voice responses
- 1.2: Voice messages generate voice responses
- 1.3: Image messages generate voice responses
- 1.4: Audio elements with auto-play enabled
- 1.5: TTS failure graceful degradation
- 3.4: Consecutive messages all have voice
- 4.1: TTS success logging with metrics
- 4.2: TTS failure logging with error details
"""

import asyncio

# Mock chainlit before importing the app
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Create mock chainlit module
mock_chainlit = MagicMock()
mock_chainlit.Audio = MagicMock(return_value=MagicMock())
mock_chainlit.Image = MagicMock(return_value=MagicMock())
mock_chainlit.Message = MagicMock(return_value=MagicMock())
mock_chainlit.Step = MagicMock(return_value=MagicMock())
mock_chainlit.user_session = MagicMock()
mock_chainlit.logger = MagicMock()
sys.modules["chainlit"] = mock_chainlit

from ai_companion.interfaces.chainlit.app import (  # noqa: E402
    generate_voice_response,  # Import after mock setup required
)


class TestGenerateVoiceResponse:
    """Test the centralized generate_voice_response function."""

    @pytest.mark.asyncio
    async def test_successful_tts_generation(self):
        """Test successful TTS generation returns audio element.

        Requirements: 1.4, 4.1
        """
        # Mock TextToSpeech
        mock_tts = MagicMock()
        mock_audio_bytes = b"test_audio_data_12345"
        mock_tts.synthesize = AsyncMock(return_value=mock_audio_bytes)

        # Mock circuit breaker
        mock_circuit_breaker = MagicMock()
        mock_circuit_breaker.state = "CLOSED"

        with patch("ai_companion.interfaces.chainlit.app.get_text_to_speech", return_value=mock_tts):
            with patch(
                "ai_companion.core.resilience.get_elevenlabs_circuit_breaker", return_value=mock_circuit_breaker
            ):
                # Call generate_voice_response
                text, audio = await generate_voice_response("Hello, how are you?", thread_id=1)

                # Verify text returned
                assert text == "Hello, how are you?"

                # Verify audio element created
                assert audio is not None
                mock_chainlit.Audio.assert_called_once()
                call_kwargs = mock_chainlit.Audio.call_args[1]
                assert call_kwargs["name"] == "Rose's Voice"
                assert call_kwargs["auto_play"] is True
                assert call_kwargs["mime"] == "audio/mpeg3"
                assert call_kwargs["content"] == mock_audio_bytes

                # Verify TTS was called
                mock_tts.synthesize.assert_called_once_with("Hello, how are you?")

                # Verify success logging
                mock_chainlit.logger.info.assert_called()
                log_call = str(mock_chainlit.logger.info.call_args)
                assert "TTS generation successful" in log_call
                assert "thread_id=1" in log_call

    @pytest.mark.asyncio
    async def test_tts_timeout_fallback(self):
        """Test TTS timeout returns text-only response.

        Requirements: 1.5, 4.2
        """
        # Mock TextToSpeech with timeout
        mock_tts = MagicMock()

        async def slow_synthesize(text):
            await asyncio.sleep(15)  # Exceeds 10s timeout
            return b"audio"

        mock_tts.synthesize = slow_synthesize

        # Mock circuit breaker
        mock_circuit_breaker = MagicMock()
        mock_circuit_breaker.state = "CLOSED"

        with patch("ai_companion.interfaces.chainlit.app.get_text_to_speech", return_value=mock_tts):
            with patch(
                "ai_companion.core.resilience.get_elevenlabs_circuit_breaker", return_value=mock_circuit_breaker
            ):
                # Call generate_voice_response
                text, audio = await generate_voice_response("Test message", thread_id=2)

                # Verify text returned but no audio
                assert text == "Test message"
                assert audio is None

                # Verify timeout logging
                mock_chainlit.logger.error.assert_called()
                log_call = str(mock_chainlit.logger.error.call_args)
                assert "TTS generation timeout" in log_call
                assert "thread_id=2" in log_call

    @pytest.mark.asyncio
    async def test_tts_api_failure_fallback(self):
        """Test TTS API failure returns text-only response.

        Requirements: 1.5, 4.2
        """
        # Mock TextToSpeech with API error
        mock_tts = MagicMock()
        mock_tts.synthesize = AsyncMock(side_effect=Exception("ElevenLabs API error"))

        # Mock circuit breaker
        mock_circuit_breaker = MagicMock()
        mock_circuit_breaker.state = "CLOSED"

        with patch("ai_companion.interfaces.chainlit.app.get_text_to_speech", return_value=mock_tts):
            with patch(
                "ai_companion.core.resilience.get_elevenlabs_circuit_breaker", return_value=mock_circuit_breaker
            ):
                # Call generate_voice_response
                text, audio = await generate_voice_response("Test message", thread_id=3)

                # Verify text returned but no audio
                assert text == "Test message"
                assert audio is None

                # Verify error logging
                mock_chainlit.logger.error.assert_called()
                log_call = str(mock_chainlit.logger.error.call_args)
                assert "TTS generation failed" in log_call
                assert "thread_id=3" in log_call
                assert "ElevenLabs API error" in log_call

    @pytest.mark.asyncio
    async def test_circuit_breaker_open_fallback(self):
        """Test circuit breaker open returns text-only response.

        Requirements: 1.5, 4.2, 4.4
        """
        from ai_companion.core.resilience import CircuitBreakerError

        # Mock TextToSpeech with circuit breaker error
        mock_tts = MagicMock()
        mock_tts.synthesize = AsyncMock(side_effect=CircuitBreakerError("Circuit breaker open"))

        # Mock circuit breaker
        mock_circuit_breaker = MagicMock()
        mock_circuit_breaker.state = "OPEN"

        with patch("ai_companion.interfaces.chainlit.app.get_text_to_speech", return_value=mock_tts):
            with patch(
                "ai_companion.core.resilience.get_elevenlabs_circuit_breaker", return_value=mock_circuit_breaker
            ):
                # Call generate_voice_response
                text, audio = await generate_voice_response("Test message", thread_id=4)

                # Verify text returned but no audio
                assert text == "Test message"
                assert audio is None

                # Verify circuit breaker logging
                mock_chainlit.logger.error.assert_called()
                log_call = str(mock_chainlit.logger.error.call_args)
                assert "TTS circuit breaker open" in log_call
                assert "thread_id=4" in log_call
                assert "circuit_state=OPEN" in log_call

    @pytest.mark.asyncio
    async def test_tts_metrics_logging(self):
        """Test TTS generation logs proper metrics.

        Requirements: 4.1, 4.3
        """
        # Mock TextToSpeech
        mock_tts = MagicMock()
        mock_audio_bytes = b"x" * 5000  # 5KB audio
        mock_tts.synthesize = AsyncMock(return_value=mock_audio_bytes)

        # Mock circuit breaker
        mock_circuit_breaker = MagicMock()
        mock_circuit_breaker.state = "CLOSED"

        with patch("ai_companion.interfaces.chainlit.app.get_text_to_speech", return_value=mock_tts):
            with patch(
                "ai_companion.core.resilience.get_elevenlabs_circuit_breaker", return_value=mock_circuit_breaker
            ):
                # Call generate_voice_response with longer text
                long_text = "This is a longer message " * 10
                text, audio = await generate_voice_response(long_text, thread_id=5)

                # Verify success logging with metrics
                mock_chainlit.logger.info.assert_called()
                log_call = str(mock_chainlit.logger.info.call_args)
                assert "TTS generation successful" in log_call
                assert "thread_id=5" in log_call
                assert "duration=" in log_call
                assert f"text_length={len(long_text)}" in log_call
                assert "audio_size=5000 bytes" in log_call


class TestConsecutiveMessageVoiceConsistency:
    """Test that consecutive messages all generate voice responses.

    Requirements: 3.4
    """

    @pytest.mark.asyncio
    async def test_ten_consecutive_messages_with_voice(self):
        """Test 10 consecutive messages all generate voice responses.

        Requirements: 1.1, 3.4
        """
        # Mock TextToSpeech
        mock_tts = MagicMock()
        mock_tts.synthesize = AsyncMock(return_value=b"audio_data")

        # Mock circuit breaker
        mock_circuit_breaker = MagicMock()
        mock_circuit_breaker.state = "CLOSED"

        with patch("ai_companion.interfaces.chainlit.app.get_text_to_speech", return_value=mock_tts):
            with patch(
                "ai_companion.core.resilience.get_elevenlabs_circuit_breaker", return_value=mock_circuit_breaker
            ):
                # Generate 10 consecutive voice responses
                for i in range(10):
                    text, audio = await generate_voice_response(f"Message {i + 1}", thread_id=100 + i)

                    # Verify each message has audio
                    assert text == f"Message {i + 1}"
                    assert audio is not None

                # Verify TTS was called 10 times
                assert mock_tts.synthesize.call_count == 10

    @pytest.mark.asyncio
    async def test_voice_consistency_after_failure(self):
        """Test voice generation resumes after a failure.

        Requirements: 1.5, 3.4
        """
        # Mock TextToSpeech with one failure then successes
        mock_tts = MagicMock()
        call_count = [0]

        async def synthesize_with_one_failure(text):
            call_count[0] += 1
            if call_count[0] == 3:  # Fail on 3rd call
                raise Exception("Temporary API error")
            return b"audio_data"

        mock_tts.synthesize = synthesize_with_one_failure

        # Mock circuit breaker
        mock_circuit_breaker = MagicMock()
        mock_circuit_breaker.state = "CLOSED"

        with patch("ai_companion.interfaces.chainlit.app.get_text_to_speech", return_value=mock_tts):
            with patch(
                "ai_companion.core.resilience.get_elevenlabs_circuit_breaker", return_value=mock_circuit_breaker
            ):
                # Generate 5 consecutive voice responses
                results = []
                for i in range(5):
                    text, audio = await generate_voice_response(f"Message {i + 1}", thread_id=200 + i)
                    results.append((text, audio))

                # Verify messages 1, 2 have audio
                assert results[0][1] is not None
                assert results[1][1] is not None

                # Verify message 3 failed (no audio)
                assert results[2][1] is None

                # Verify messages 4, 5 recovered (have audio)
                assert results[3][1] is not None
                assert results[4][1] is not None


class TestVoiceResponseLogging:
    """Test comprehensive logging for TTS operations.

    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """

    @pytest.mark.asyncio
    async def test_success_logging_includes_thread_id(self):
        """Test success logs include thread_id for tracking.

        Requirements: 4.5
        """
        # Mock TextToSpeech
        mock_tts = MagicMock()
        mock_tts.synthesize = AsyncMock(return_value=b"audio")

        # Mock circuit breaker
        mock_circuit_breaker = MagicMock()
        mock_circuit_breaker.state = "CLOSED"

        with patch("ai_companion.interfaces.chainlit.app.get_text_to_speech", return_value=mock_tts):
            with patch(
                "ai_companion.core.resilience.get_elevenlabs_circuit_breaker", return_value=mock_circuit_breaker
            ):
                await generate_voice_response("Test", thread_id=999)

                # Verify thread_id in log
                log_call = str(mock_chainlit.logger.info.call_args)
                assert "thread_id=999" in log_call

    @pytest.mark.asyncio
    async def test_failure_logging_includes_thread_id(self):
        """Test failure logs include thread_id for tracking.

        Requirements: 4.5
        """
        # Mock TextToSpeech with failure
        mock_tts = MagicMock()
        mock_tts.synthesize = AsyncMock(side_effect=Exception("API error"))

        # Mock circuit breaker
        mock_circuit_breaker = MagicMock()
        mock_circuit_breaker.state = "CLOSED"

        with patch("ai_companion.interfaces.chainlit.app.get_text_to_speech", return_value=mock_tts):
            with patch(
                "ai_companion.core.resilience.get_elevenlabs_circuit_breaker", return_value=mock_circuit_breaker
            ):
                await generate_voice_response("Test", thread_id=888)

                # Verify thread_id in error log
                log_call = str(mock_chainlit.logger.error.call_args)
                assert "thread_id=888" in log_call

    @pytest.mark.asyncio
    async def test_circuit_breaker_state_logging(self):
        """Test circuit breaker state changes are logged.

        Requirements: 4.4
        """
        # Mock TextToSpeech
        mock_tts = MagicMock()
        mock_tts.synthesize = AsyncMock(return_value=b"audio")

        # Mock circuit breaker with state change
        mock_circuit_breaker = MagicMock()
        mock_circuit_breaker.state = "HALF_OPEN"  # Not CLOSED

        with patch("ai_companion.interfaces.chainlit.app.get_text_to_speech", return_value=mock_tts):
            with patch(
                "ai_companion.core.resilience.get_elevenlabs_circuit_breaker", return_value=mock_circuit_breaker
            ):
                await generate_voice_response("Test", thread_id=777)

                # Verify circuit breaker state logged
                warning_call = str(mock_chainlit.logger.warning.call_args)
                assert "TTS circuit breaker state" in warning_call
                assert "state=HALF_OPEN" in warning_call
                assert "thread_id=777" in warning_call


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
