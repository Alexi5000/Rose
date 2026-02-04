"""Unit tests for Speech-to-Text module.

Tests audio transcription with various formats, retry logic, circuit breaker
integration, and error handling with mocked Groq client.
"""

from unittest.mock import MagicMock, patch

import pytest

from ai_companion.core.exceptions import SpeechToTextError
from ai_companion.core.resilience import CircuitBreakerError
from ai_companion.modules.speech.speech_to_text import SpeechToText


@pytest.mark.unit
class TestAudioTranscription:
    """Test basic audio transcription functionality."""

    @pytest.mark.asyncio
    async def test_transcribe_wav_format(self, sample_wav_audio, mock_groq_client):
        """Test transcribing WAV format audio."""
        mock_groq_client.audio.transcriptions.create.return_value = "This is a test transcription from WAV audio."

        with patch("ai_companion.modules.speech.speech_to_text.Groq", return_value=mock_groq_client):
            stt = SpeechToText()
            result = await stt.transcribe(sample_wav_audio, audio_format="wav")

            assert result == "This is a test transcription from WAV audio."
            mock_groq_client.audio.transcriptions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_transcribe_mp3_format(self, sample_mp3_audio, mock_groq_client):
        """Test transcribing MP3 format audio."""
        mock_groq_client.audio.transcriptions.create.return_value = "This is a test transcription from MP3 audio."

        with patch("ai_companion.modules.speech.speech_to_text.Groq", return_value=mock_groq_client):
            stt = SpeechToText()
            result = await stt.transcribe(sample_mp3_audio, audio_format="mp3")

            assert result == "This is a test transcription from MP3 audio."
            mock_groq_client.audio.transcriptions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_transcribe_with_explicit_format(self, sample_wav_audio, mock_groq_client):
        """Test transcription with explicitly specified audio format."""
        mock_groq_client.audio.transcriptions.create.return_value = "Transcription with explicit format."

        with patch("ai_companion.modules.speech.speech_to_text.Groq", return_value=mock_groq_client):
            stt = SpeechToText()
            result = await stt.transcribe(sample_wav_audio, audio_format="wav")

            assert result == "Transcription with explicit format."
            # Verify the API was called with correct parameters
            call_args = mock_groq_client.audio.transcriptions.create.call_args
            assert call_args[1]["model"] == "whisper-large-v3"
            assert call_args[1]["language"] == "en"
            assert call_args[1]["response_format"] == "text"


@pytest.mark.unit
class TestAudioFormatDetection:
    """Test audio format auto-detection."""

    @pytest.mark.asyncio
    async def test_detect_wav_format(self, sample_wav_audio, mock_groq_client):
        """Test auto-detection of WAV format from file header."""
        mock_groq_client.audio.transcriptions.create.return_value = "Detected WAV format."

        with patch("ai_companion.modules.speech.speech_to_text.Groq", return_value=mock_groq_client):
            stt = SpeechToText()
            # Don't specify format - should auto-detect
            result = await stt.transcribe(sample_wav_audio)

            assert result == "Detected WAV format."
            # Verify format was detected correctly
            detected_format = stt._detect_audio_format(sample_wav_audio)
            assert detected_format == ".wav"

    @pytest.mark.asyncio
    async def test_detect_mp3_format(self, sample_mp3_audio, mock_groq_client):
        """Test auto-detection of MP3 format from file header."""
        mock_groq_client.audio.transcriptions.create.return_value = "Detected MP3 format."

        with patch("ai_companion.modules.speech.speech_to_text.Groq", return_value=mock_groq_client):
            stt = SpeechToText()
            # Don't specify format - should auto-detect
            result = await stt.transcribe(sample_mp3_audio)

            assert result == "Detected MP3 format."
            # Verify format was detected correctly
            detected_format = stt._detect_audio_format(sample_mp3_audio)
            assert detected_format == ".mp3"

    def test_detect_format_from_header(self):
        """Test format detection from various audio file headers."""
        stt = SpeechToText()

        # WAV format (RIFF header)
        wav_data = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"\x00" * 100
        assert stt._detect_audio_format(wav_data) == ".wav"

        # MP3 format (ID3 tag)
        mp3_data_id3 = b"ID3" + b"\x00" * 100
        assert stt._detect_audio_format(mp3_data_id3) == ".mp3"

        # MP3 format (frame sync)
        mp3_data_sync = b"\xff\xfb" + b"\x00" * 100
        assert stt._detect_audio_format(mp3_data_sync) == ".mp3"

        # OGG format
        ogg_data = b"OggS" + b"\x00" * 100
        assert stt._detect_audio_format(ogg_data) == ".ogg"

        # FLAC format
        flac_data = b"fLaC" + b"\x00" * 100
        assert stt._detect_audio_format(flac_data) == ".flac"

        # M4A format (ftyp atom)
        m4a_data = b"\x00" * 4 + b"ftyp" + b"\x00" * 100
        assert stt._detect_audio_format(m4a_data) == ".m4a"

    def test_detect_unknown_format_defaults_to_wav(self):
        """Test that unknown formats default to WAV."""
        stt = SpeechToText()

        unknown_data = b"UNKNOWN_FORMAT" + b"\x00" * 100
        detected_format = stt._detect_audio_format(unknown_data)

        assert detected_format == ".wav"


@pytest.mark.unit
class TestRetryLogic:
    """Test retry logic with exponential backoff."""

    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self, sample_wav_audio, mock_groq_client):
        """Test that transient errors trigger retry with exponential backoff."""
        # First two calls fail, third succeeds
        mock_groq_client.audio.transcriptions.create.side_effect = [
            Exception("Temporary network error"),
            Exception("Temporary API error"),
            "Success after retries",
        ]

        with patch("ai_companion.modules.speech.speech_to_text.Groq", return_value=mock_groq_client):
            with patch("ai_companion.modules.speech.speech_to_text.get_groq_circuit_breaker") as mock_cb:
                # Mock circuit breaker to allow calls through (use call_async for async method)
                mock_breaker = MagicMock()

                async def mock_call_async(func, *args, **kwargs):
                    return await func(*args, **kwargs)

                mock_breaker.call_async.side_effect = mock_call_async
                mock_cb.return_value = mock_breaker

                with patch("time.sleep") as mock_sleep:  # Mock sleep to speed up test
                    stt = SpeechToText()
                    result = await stt.transcribe(sample_wav_audio)

                    assert result == "Success after retries"
                    # Verify retries occurred
                    assert mock_groq_client.audio.transcriptions.create.call_count == 3
                    # Verify exponential backoff was used
                    assert mock_sleep.call_count == 2  # 2 retries = 2 sleeps

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self, sample_wav_audio, mock_groq_client):
        """Test that exponential backoff increases wait time correctly."""
        mock_groq_client.audio.transcriptions.create.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            "Success",
        ]

        with patch("ai_companion.modules.speech.speech_to_text.Groq", return_value=mock_groq_client):
            with patch("ai_companion.modules.speech.speech_to_text.get_groq_circuit_breaker") as mock_cb:
                # Mock circuit breaker to allow calls through (use call_async for async method)
                mock_breaker = MagicMock()

                async def mock_call_async(func, *args, **kwargs):
                    return await func(*args, **kwargs)

                mock_breaker.call_async.side_effect = mock_call_async
                mock_cb.return_value = mock_breaker

                with patch("time.sleep") as mock_sleep:
                    stt = SpeechToText()
                    await stt.transcribe(sample_wav_audio)

                    # Verify backoff times: 1.0s, 2.0s (exponential)
                    sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
                    assert len(sleep_calls) == 2
                    assert sleep_calls[0] == 1.0  # Initial backoff
                    assert sleep_calls[1] == 2.0  # 2x backoff

    @pytest.mark.asyncio
    async def test_max_backoff_limit(self, sample_wav_audio, mock_groq_client):
        """Test that backoff time respects maximum limit."""
        # Create enough failures to exceed max backoff
        mock_groq_client.audio.transcriptions.create.side_effect = [
            Exception("Error"),
            Exception("Error"),
            "Success",
        ]

        with patch("ai_companion.modules.speech.speech_to_text.Groq", return_value=mock_groq_client):
            with patch("ai_companion.modules.speech.speech_to_text.get_groq_circuit_breaker") as mock_cb:
                # Mock circuit breaker to allow calls through (use call_async for async method)
                mock_breaker = MagicMock()

                async def mock_call_async(func, *args, **kwargs):
                    return await func(*args, **kwargs)

                mock_breaker.call_async.side_effect = mock_call_async
                mock_cb.return_value = mock_breaker

                with patch("time.sleep") as mock_sleep:
                    with patch("ai_companion.settings.settings.STT_MAX_BACKOFF", 5.0):
                        stt = SpeechToText()
                        await stt.transcribe(sample_wav_audio)

                        # Verify no backoff exceeds max
                        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
                        assert all(sleep_time <= 5.0 for sleep_time in sleep_calls)

    @pytest.mark.asyncio
    async def test_no_retry_on_validation_error(self, sample_empty_audio, mock_groq_client):
        """Test that validation errors are not retried."""
        with patch("ai_companion.modules.speech.speech_to_text.Groq", return_value=mock_groq_client):
            stt = SpeechToText()

            with pytest.raises(ValueError, match="Audio data cannot be empty"):
                await stt.transcribe(sample_empty_audio)

            # Verify no API calls were made
            mock_groq_client.audio.transcriptions.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_all_retries_exhausted(self, sample_wav_audio, mock_groq_client):
        """Test behavior when all retry attempts are exhausted."""
        # All attempts fail
        mock_groq_client.audio.transcriptions.create.side_effect = Exception("Persistent error")

        with patch("ai_companion.modules.speech.speech_to_text.Groq", return_value=mock_groq_client):
            with patch("ai_companion.modules.speech.speech_to_text.get_groq_circuit_breaker") as mock_cb:
                # Mock circuit breaker to allow calls through (use call_async for async method)
                mock_breaker = MagicMock()

                async def mock_call_async(func, *args, **kwargs):
                    return await func(*args, **kwargs)

                mock_breaker.call_async.side_effect = mock_call_async
                mock_cb.return_value = mock_breaker

                with patch("time.sleep"):  # Mock sleep to speed up test
                    stt = SpeechToText()

                    with pytest.raises(SpeechToTextError, match="failed after 3 attempts"):
                        await stt.transcribe(sample_wav_audio)

                    # Verify all retry attempts were made
                    assert mock_groq_client.audio.transcriptions.create.call_count == 3


@pytest.mark.unit
class TestCircuitBreakerIntegration:
    """Test circuit breaker integration."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_open_fails_fast(self, sample_wav_audio, mock_groq_client):
        """Test that open circuit breaker fails fast without retrying."""
        with patch("ai_companion.modules.speech.speech_to_text.Groq", return_value=mock_groq_client):
            with patch("ai_companion.modules.speech.speech_to_text.get_groq_circuit_breaker") as mock_cb:
                # Mock circuit breaker in OPEN state (use call_async for async method)
                mock_breaker = MagicMock()
                mock_breaker.call_async.side_effect = CircuitBreakerError("Circuit breaker is OPEN")
                mock_cb.return_value = mock_breaker

                stt = SpeechToText()

                with pytest.raises(SpeechToTextError, match="temporarily unavailable"):
                    await stt.transcribe(sample_wav_audio)

                # Verify circuit breaker was called
                mock_breaker.call_async.assert_called_once()
                # Verify no retries occurred (circuit breaker fails fast)
                assert mock_breaker.call_async.call_count == 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_success_path(self, sample_wav_audio, mock_groq_client):
        """Test successful transcription through circuit breaker."""
        mock_groq_client.audio.transcriptions.create.return_value = "Success through circuit breaker."

        with patch("ai_companion.modules.speech.speech_to_text.Groq", return_value=mock_groq_client):
            with patch("ai_companion.modules.speech.speech_to_text.get_groq_circuit_breaker") as mock_cb:
                # Mock circuit breaker in CLOSED state (allows calls, use call_async for async method)
                mock_breaker = MagicMock()

                async def mock_call_async(func, *args, **kwargs):
                    return await func(*args, **kwargs)

                mock_breaker.call_async.side_effect = mock_call_async
                mock_cb.return_value = mock_breaker

                stt = SpeechToText()
                result = await stt.transcribe(sample_wav_audio)

                assert result == "Success through circuit breaker."
                mock_breaker.call_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_circuit_breaker_records_failures(self, sample_wav_audio, mock_groq_client):
        """Test that circuit breaker records failures correctly."""
        mock_groq_client.audio.transcriptions.create.side_effect = Exception("API error")

        with patch("ai_companion.modules.speech.speech_to_text.Groq", return_value=mock_groq_client):
            with patch("ai_companion.modules.speech.speech_to_text.get_groq_circuit_breaker") as mock_cb:
                # Mock circuit breaker that allows calls but records failures (use call_async for async method)
                mock_breaker = MagicMock()

                async def mock_call_async(func, *args, **kwargs):
                    return await func(*args, **kwargs)

                mock_breaker.call_async.side_effect = mock_call_async
                mock_cb.return_value = mock_breaker

                with patch("time.sleep"):  # Speed up test
                    stt = SpeechToText()

                    with pytest.raises(SpeechToTextError):
                        await stt.transcribe(sample_wav_audio)

                    # Verify circuit breaker was called for each retry
                    assert mock_breaker.call_async.call_count == 3


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling for various edge cases."""

    @pytest.mark.asyncio
    async def test_empty_audio_error(self, sample_empty_audio):
        """Test handling of empty audio data."""
        stt = SpeechToText()

        with pytest.raises(ValueError, match="Audio data cannot be empty"):
            await stt.transcribe(sample_empty_audio)

    @pytest.mark.asyncio
    async def test_oversized_audio_error(self, sample_oversized_audio):
        """Test handling of oversized audio files."""
        stt = SpeechToText()

        with pytest.raises(ValueError, match="Audio file too large"):
            await stt.transcribe(sample_oversized_audio)

    @pytest.mark.asyncio
    async def test_invalid_format_warning(self, sample_invalid_audio, mock_groq_client):
        """Test handling of invalid audio format."""
        mock_groq_client.audio.transcriptions.create.return_value = "Transcription despite invalid format."

        with patch("ai_companion.modules.speech.speech_to_text.Groq", return_value=mock_groq_client):
            with patch("ai_companion.modules.speech.speech_to_text.get_groq_circuit_breaker") as mock_cb:
                # Mock circuit breaker to allow calls through (use call_async for async method)
                mock_breaker = MagicMock()

                async def mock_call_async(func, *args, **kwargs):
                    return await func(*args, **kwargs)

                mock_breaker.call_async.side_effect = mock_call_async
                mock_cb.return_value = mock_breaker

                stt = SpeechToText()
                # Should attempt transcription even with invalid format
                result = await stt.transcribe(sample_invalid_audio, audio_format="xyz")

                assert result == "Transcription despite invalid format."

    @pytest.mark.asyncio
    async def test_empty_transcription_result(self, sample_wav_audio, mock_groq_client):
        """Test handling of empty transcription result from API."""
        mock_groq_client.audio.transcriptions.create.return_value = ""

        with patch("ai_companion.modules.speech.speech_to_text.Groq", return_value=mock_groq_client):
            with patch("ai_companion.modules.speech.speech_to_text.get_groq_circuit_breaker") as mock_cb:
                # Mock circuit breaker to allow calls through (use call_async for async method)
                mock_breaker = MagicMock()

                async def mock_call_async(func, *args, **kwargs):
                    return await func(*args, **kwargs)

                mock_breaker.call_async.side_effect = mock_call_async
                mock_cb.return_value = mock_breaker

                with patch("time.sleep"):
                    stt = SpeechToText()

                    with pytest.raises(SpeechToTextError, match="Transcription result is empty"):
                        await stt.transcribe(sample_wav_audio)

    @pytest.mark.asyncio
    async def test_api_timeout_error(self, sample_wav_audio, mock_groq_client):
        """Test handling of API timeout errors."""
        mock_groq_client.audio.transcriptions.create.side_effect = TimeoutError("API timeout")

        with patch("ai_companion.modules.speech.speech_to_text.Groq", return_value=mock_groq_client):
            with patch("ai_companion.modules.speech.speech_to_text.get_groq_circuit_breaker") as mock_cb:
                # Mock circuit breaker to allow calls through (use call_async for async method)
                mock_breaker = MagicMock()

                async def mock_call_async(func, *args, **kwargs):
                    return await func(*args, **kwargs)

                mock_breaker.call_async.side_effect = mock_call_async
                mock_cb.return_value = mock_breaker

                with patch("time.sleep"):
                    stt = SpeechToText()

                    with pytest.raises(SpeechToTextError, match="failed after 3 attempts"):
                        await stt.transcribe(sample_wav_audio)

    @pytest.mark.asyncio
    async def test_temporary_file_cleanup(self, sample_wav_audio, mock_groq_client):
        """Test that temporary files are cleaned up after transcription."""
        mock_groq_client.audio.transcriptions.create.return_value = "Transcription successful."

        with patch("ai_companion.modules.speech.speech_to_text.Groq", return_value=mock_groq_client):
            with patch("ai_companion.modules.speech.speech_to_text.get_groq_circuit_breaker") as mock_cb:
                # Mock circuit breaker to allow calls through (use call_async for async method)
                mock_breaker = MagicMock()

                async def mock_call_async(func, *args, **kwargs):
                    return await func(*args, **kwargs)

                mock_breaker.call_async.side_effect = mock_call_async
                mock_cb.return_value = mock_breaker

                with patch("os.unlink") as mock_unlink:
                    stt = SpeechToText()
                    await stt.transcribe(sample_wav_audio)

                    # Verify temp file was deleted
                    mock_unlink.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_on_error(self, sample_wav_audio, mock_groq_client):
        """Test that temporary files are cleaned up even when errors occur."""
        mock_groq_client.audio.transcriptions.create.side_effect = Exception("API error")

        with patch("ai_companion.modules.speech.speech_to_text.Groq", return_value=mock_groq_client):
            with patch("ai_companion.modules.speech.speech_to_text.get_groq_circuit_breaker") as mock_cb:
                # Mock circuit breaker to allow calls through (use call_async for async method)
                mock_breaker = MagicMock()

                async def mock_call_async(func, *args, **kwargs):
                    return await func(*args, **kwargs)

                mock_breaker.call_async.side_effect = mock_call_async
                mock_cb.return_value = mock_breaker

                with patch("os.unlink") as mock_unlink:
                    with patch("time.sleep"):
                        stt = SpeechToText()

                        with pytest.raises(SpeechToTextError):
                            await stt.transcribe(sample_wav_audio)

                        # Verify temp file was deleted on each attempt
                        assert mock_unlink.call_count == 3  # Once per retry attempt


@pytest.mark.unit
class TestClientInitialization:
    """Test Groq client initialization and singleton pattern."""

    def test_client_lazy_initialization(self):
        """Test that Groq client is initialized lazily."""
        stt = SpeechToText()

        # Client should not be initialized yet
        assert stt._client is None

        # Access client property
        with patch("ai_companion.modules.speech.speech_to_text.Groq") as mock_groq:
            mock_instance = MagicMock()
            mock_groq.return_value = mock_instance

            client = stt.client

            # Verify client was created
            assert client is mock_instance
            mock_groq.assert_called_once()

    def test_client_singleton_pattern(self):
        """Test that client instance is reused (singleton pattern)."""
        stt = SpeechToText()

        with patch("ai_companion.modules.speech.speech_to_text.Groq") as mock_groq:
            mock_instance = MagicMock()
            mock_groq.return_value = mock_instance

            # Access client multiple times
            client1 = stt.client
            client2 = stt.client

            # Verify same instance is returned
            assert client1 is client2
            # Verify Groq was only called once
            mock_groq.assert_called_once()

    def test_client_initialization_with_settings(self):
        """Test that client is initialized with correct settings."""
        with patch("ai_companion.modules.speech.speech_to_text.Groq") as mock_groq:
            stt = SpeechToText()
            _ = stt.client

            # Verify client was initialized with correct parameters
            call_args = mock_groq.call_args
            assert "api_key" in call_args[1]
            assert "timeout" in call_args[1]
