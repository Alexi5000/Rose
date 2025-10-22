"""Unit tests for Text-to-Speech module.

Tests text-to-speech synthesis with caching, fallback behavior, circuit breaker
integration, and error handling with mocked ElevenLabs client.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from ai_companion.core.exceptions import TextToSpeechError
from ai_companion.core.resilience import CircuitBreakerError
from ai_companion.modules.speech.text_to_speech import TextToSpeech


@pytest.mark.unit
class TestBasicSynthesis:
    """Test basic text-to-speech synthesis functionality."""

    @pytest.mark.asyncio
    async def test_synthesize_basic_text(self, mock_elevenlabs_client):
        """Test basic text-to-speech synthesis."""
        mock_elevenlabs_client.generate.return_value = iter([b"audio_chunk_1", b"audio_chunk_2"])

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            tts = TextToSpeech()
            result = await tts.synthesize("Hello, I'm Rose. How are you feeling today?")

            assert result == b"audio_chunk_1audio_chunk_2"
            mock_elevenlabs_client.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_synthesize_with_custom_voice(self, mock_elevenlabs_client):
        """Test synthesis with custom voice ID."""
        mock_elevenlabs_client.generate.return_value = iter([b"custom_voice_audio"])

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            tts = TextToSpeech()
            result = await tts.synthesize("Test message", voice_id="custom_voice_123")

            assert result == b"custom_voice_audio"
            # Verify custom voice was used
            call_args = mock_elevenlabs_client.generate.call_args
            assert call_args[1]["voice"].voice_id == "custom_voice_123"

    @pytest.mark.asyncio
    async def test_synthesize_with_custom_stability(self, mock_elevenlabs_client):
        """Test synthesis with custom stability setting."""
        mock_elevenlabs_client.generate.return_value = iter([b"stable_audio"])

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            tts = TextToSpeech()
            result = await tts.synthesize("Test message", stability=0.9)

            assert result == b"stable_audio"
            # Verify stability was set
            call_args = mock_elevenlabs_client.generate.call_args
            assert call_args[1]["voice"].settings.stability == 0.9

    @pytest.mark.asyncio
    async def test_synthesize_with_custom_similarity(self, mock_elevenlabs_client):
        """Test synthesis with custom similarity boost."""
        mock_elevenlabs_client.generate.return_value = iter([b"similar_audio"])

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            tts = TextToSpeech()
            result = await tts.synthesize("Test message", similarity_boost=0.8)

            assert result == b"similar_audio"
            # Verify similarity was set
            call_args = mock_elevenlabs_client.generate.call_args
            assert call_args[1]["voice"].settings.similarity_boost == 0.8


@pytest.mark.unit
class TestCachingBehavior:
    """Test TTS caching functionality."""

    @pytest.mark.asyncio
    async def test_cache_miss_generates_audio(self, mock_elevenlabs_client):
        """Test that cache miss triggers audio generation."""
        mock_elevenlabs_client.generate.return_value = iter([b"generated_audio"])

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            tts = TextToSpeech(enable_cache=True)
            result = await tts.synthesize_cached("Hello, this is a test.")

            assert result == b"generated_audio"
            mock_elevenlabs_client.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_audio(self, mock_elevenlabs_client):
        """Test that cache hit returns cached audio without API call."""
        mock_elevenlabs_client.generate.return_value = iter([b"generated_audio"])

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            tts = TextToSpeech(enable_cache=True)

            # First call - cache miss
            result1 = await tts.synthesize_cached("Hello, this is a test.")
            assert result1 == b"generated_audio"

            # Second call - cache hit
            result2 = await tts.synthesize_cached("Hello, this is a test.")
            assert result2 == b"generated_audio"

            # Verify API was only called once
            assert mock_elevenlabs_client.generate.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_expiration(self, mock_elevenlabs_client):
        """Test that expired cache entries are regenerated."""
        mock_elevenlabs_client.generate.return_value = iter([b"fresh_audio"])

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            # Use very short TTL for testing
            tts = TextToSpeech(enable_cache=True, cache_ttl_hours=0)

            # First call - cache miss
            result1 = await tts.synthesize_cached("Test message")
            assert result1 == b"fresh_audio"

            # Manually expire the cache entry
            for key in list(tts._cache.keys()):
                audio, timestamp = tts._cache[key]
                tts._cache[key] = (audio, timestamp - timedelta(hours=1))

            # Second call - cache expired, should regenerate
            mock_elevenlabs_client.generate.return_value = iter([b"new_audio"])
            result2 = await tts.synthesize_cached("Test message")
            assert result2 == b"new_audio"

            # Verify API was called twice
            assert mock_elevenlabs_client.generate.call_count == 2

    @pytest.mark.asyncio
    async def test_cache_disabled(self, mock_elevenlabs_client):
        """Test that caching can be disabled."""
        # Return fresh iterator for each call
        mock_elevenlabs_client.generate.side_effect = [
            iter([b"audio_data_1"]),
            iter([b"audio_data_2"]),
        ]

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            with patch("ai_companion.modules.speech.text_to_speech.get_elevenlabs_circuit_breaker") as mock_cb:
                mock_breaker = MagicMock()
                mock_breaker.call.side_effect = lambda func: func()
                mock_cb.return_value = mock_breaker

                tts = TextToSpeech(enable_cache=False)

                # Make multiple calls with same text
                await tts.synthesize_cached("Test message")
                await tts.synthesize_cached("Test message")

                # Verify API was called each time (no caching)
                assert mock_elevenlabs_client.generate.call_count == 2

    @pytest.mark.asyncio
    async def test_cache_key_includes_parameters(self, mock_elevenlabs_client):
        """Test that cache key includes all synthesis parameters."""
        # Return fresh iterator for each call
        mock_elevenlabs_client.generate.side_effect = [
            iter([b"audio_data_1"]),
            iter([b"audio_data_2"]),
        ]

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            with patch("ai_companion.modules.speech.text_to_speech.get_elevenlabs_circuit_breaker") as mock_cb:
                mock_breaker = MagicMock()
                mock_breaker.call.side_effect = lambda func: func()
                mock_cb.return_value = mock_breaker

                tts = TextToSpeech(enable_cache=True)

                # Same text but different parameters should not hit cache
                await tts.synthesize_cached("Test", stability=0.5)
                await tts.synthesize_cached("Test", stability=0.9)

                # Verify API was called twice (different cache keys)
                assert mock_elevenlabs_client.generate.call_count == 2

    def test_clear_cache(self, mock_elevenlabs_client):
        """Test cache clearing functionality."""
        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            tts = TextToSpeech(enable_cache=True)

            # Add some entries to cache manually
            tts._cache["key1"] = (b"audio1", datetime.now())
            tts._cache["key2"] = (b"audio2", datetime.now())

            assert len(tts._cache) == 2

            # Clear cache
            tts.clear_cache()

            assert len(tts._cache) == 0

    def test_get_cache_stats(self, mock_elevenlabs_client):
        """Test cache statistics retrieval."""
        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            tts = TextToSpeech(enable_cache=True, cache_ttl_hours=24)

            # Add cache entries
            tts._cache["key1"] = (b"audio1", datetime.now())
            tts._cache["key2"] = (b"audio2", datetime.now())

            stats = tts.get_cache_stats()

            assert stats["enabled"] is True
            assert stats["size"] == 2
            assert stats["ttl_hours"] == 24
            assert len(stats["entries"]) == 2


@pytest.mark.unit
class TestFallbackBehavior:
    """Test graceful fallback when TTS fails."""

    @pytest.mark.asyncio
    async def test_fallback_on_api_error(self, mock_elevenlabs_client):
        """Test fallback to text-only when API fails."""
        mock_elevenlabs_client.generate.side_effect = Exception("API error")

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            with patch("ai_companion.modules.speech.text_to_speech.get_elevenlabs_circuit_breaker") as mock_cb:
                mock_breaker = MagicMock()
                mock_breaker.call.side_effect = lambda func: func()
                mock_cb.return_value = mock_breaker

                tts = TextToSpeech()
                audio, text = await tts.synthesize_with_fallback("Hello, I'm Rose.")

                assert audio is None
                assert "I'm having trouble with my voice right now" in text
                assert "Hello, I'm Rose." in text

    @pytest.mark.asyncio
    async def test_fallback_on_circuit_breaker_open(self, mock_elevenlabs_client):
        """Test fallback when circuit breaker is open."""
        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            with patch("ai_companion.modules.speech.text_to_speech.get_elevenlabs_circuit_breaker") as mock_cb:
                mock_breaker = MagicMock()
                mock_breaker.call.side_effect = CircuitBreakerError("Circuit breaker is OPEN")
                mock_cb.return_value = mock_breaker

                tts = TextToSpeech()
                audio, text = await tts.synthesize_with_fallback("Test message")

                assert audio is None
                assert "I'm having trouble with my voice right now" in text
                assert not tts.is_available()

    @pytest.mark.asyncio
    async def test_fallback_on_validation_error(self, mock_elevenlabs_client):
        """Test fallback on validation error returns original text."""
        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            tts = TextToSpeech()
            audio, text = await tts.synthesize_with_fallback("")  # Empty text

            assert audio is None
            assert text == ""  # Returns original text without error prefix

    @pytest.mark.asyncio
    async def test_successful_synthesis_returns_audio(self, mock_elevenlabs_client):
        """Test successful synthesis returns audio and text."""
        mock_elevenlabs_client.generate.return_value = iter([b"success_audio"])

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            with patch("ai_companion.modules.speech.text_to_speech.get_elevenlabs_circuit_breaker") as mock_cb:
                mock_breaker = MagicMock()
                mock_breaker.call.side_effect = lambda func: func()
                mock_cb.return_value = mock_breaker

                tts = TextToSpeech()
                audio, text = await tts.synthesize_with_fallback("Hello")

                assert audio == b"success_audio"
                assert text == "Hello"
                assert tts.is_available()

    @pytest.mark.asyncio
    async def test_fallback_never_raises_exception(self, mock_elevenlabs_client):
        """Test that fallback method never raises exceptions."""
        mock_elevenlabs_client.generate.side_effect = RuntimeError("Unexpected error")

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            with patch("ai_companion.modules.speech.text_to_speech.get_elevenlabs_circuit_breaker") as mock_cb:
                mock_breaker = MagicMock()
                mock_breaker.call.side_effect = lambda func: func()
                mock_cb.return_value = mock_breaker

                tts = TextToSpeech()
                # Should not raise exception
                audio, text = await tts.synthesize_with_fallback("Test")

                assert audio is None
                assert "I'm having trouble with my voice right now" in text


@pytest.mark.unit
class TestCircuitBreakerIntegration:
    """Test circuit breaker integration."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_open_fails_fast(self, mock_elevenlabs_client):
        """Test that open circuit breaker fails fast."""
        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            with patch("ai_companion.modules.speech.text_to_speech.get_elevenlabs_circuit_breaker") as mock_cb:
                mock_breaker = MagicMock()
                mock_breaker.call.side_effect = CircuitBreakerError("Circuit breaker is OPEN")
                mock_cb.return_value = mock_breaker

                tts = TextToSpeech()

                with pytest.raises(TextToSpeechError, match="temporarily unavailable"):
                    await tts.synthesize("Test message")

                mock_breaker.call.assert_called_once()

    @pytest.mark.asyncio
    async def test_circuit_breaker_success_path(self, mock_elevenlabs_client):
        """Test successful synthesis through circuit breaker."""
        mock_elevenlabs_client.generate.return_value = iter([b"success_audio"])

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            with patch("ai_companion.modules.speech.text_to_speech.get_elevenlabs_circuit_breaker") as mock_cb:
                mock_breaker = MagicMock()
                mock_breaker.call.side_effect = lambda func: func()
                mock_cb.return_value = mock_breaker

                tts = TextToSpeech()
                result = await tts.synthesize("Test message")

                assert result == b"success_audio"
                mock_breaker.call.assert_called_once()

    @pytest.mark.asyncio
    async def test_circuit_breaker_records_failures(self, mock_elevenlabs_client):
        """Test that circuit breaker records failures."""
        mock_elevenlabs_client.generate.side_effect = Exception("API error")

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            with patch("ai_companion.modules.speech.text_to_speech.get_elevenlabs_circuit_breaker") as mock_cb:
                mock_breaker = MagicMock()
                mock_breaker.call.side_effect = lambda func: func()
                mock_cb.return_value = mock_breaker

                tts = TextToSpeech()

                with pytest.raises(TextToSpeechError):
                    await tts.synthesize("Test message")

                mock_breaker.call.assert_called_once()


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling for various edge cases."""

    @pytest.mark.asyncio
    async def test_empty_text_error(self):
        """Test handling of empty text input."""
        tts = TextToSpeech()

        with pytest.raises(ValueError, match="Input text cannot be empty"):
            await tts.synthesize("")

    @pytest.mark.asyncio
    async def test_whitespace_only_text_error(self):
        """Test handling of whitespace-only text."""
        tts = TextToSpeech()

        with pytest.raises(ValueError, match="Input text cannot be empty"):
            await tts.synthesize("   \n\t  ")

    @pytest.mark.asyncio
    async def test_oversized_text_error(self):
        """Test handling of oversized text input."""
        tts = TextToSpeech()

        # Create text exceeding max length
        long_text = "a" * 6000  # Exceeds 5000 char limit

        with pytest.raises(ValueError, match="exceeds maximum length"):
            await tts.synthesize(long_text)

    @pytest.mark.asyncio
    async def test_empty_audio_generation_error(self, mock_elevenlabs_client):
        """Test handling of empty audio generation."""
        mock_elevenlabs_client.generate.return_value = iter([])  # Empty generator

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            with patch("ai_companion.modules.speech.text_to_speech.get_elevenlabs_circuit_breaker") as mock_cb:
                mock_breaker = MagicMock()
                mock_breaker.call.side_effect = lambda func: func()
                mock_cb.return_value = mock_breaker

                tts = TextToSpeech()

                with pytest.raises(TextToSpeechError, match="Generated audio is empty"):
                    await tts.synthesize("Test message")

    @pytest.mark.asyncio
    async def test_api_timeout_error(self, mock_elevenlabs_client):
        """Test handling of API timeout."""
        mock_elevenlabs_client.generate.side_effect = TimeoutError("API timeout")

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            with patch("ai_companion.modules.speech.text_to_speech.get_elevenlabs_circuit_breaker") as mock_cb:
                mock_breaker = MagicMock()
                mock_breaker.call.side_effect = lambda func: func()
                mock_cb.return_value = mock_breaker

                tts = TextToSpeech()

                with pytest.raises(TextToSpeechError, match="conversion failed"):
                    await tts.synthesize("Test message")

    @pytest.mark.asyncio
    async def test_network_error(self, mock_elevenlabs_client):
        """Test handling of network errors."""
        mock_elevenlabs_client.generate.side_effect = ConnectionError("Network error")

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            with patch("ai_companion.modules.speech.text_to_speech.get_elevenlabs_circuit_breaker") as mock_cb:
                mock_breaker = MagicMock()
                mock_breaker.call.side_effect = lambda func: func()
                mock_cb.return_value = mock_breaker

                tts = TextToSpeech()

                with pytest.raises(TextToSpeechError):
                    await tts.synthesize("Test message")


@pytest.mark.unit
class TestCacheWarming:
    """Test cache warming functionality."""

    @pytest.mark.asyncio
    async def test_warm_cache_with_common_phrases(self, mock_elevenlabs_client):
        """Test warming cache with common therapeutic phrases."""
        mock_elevenlabs_client.generate.return_value = iter([b"cached_audio"])

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            with patch("ai_companion.modules.speech.text_to_speech.get_elevenlabs_circuit_breaker") as mock_cb:
                mock_breaker = MagicMock()
                mock_breaker.call.side_effect = lambda func: func()
                mock_cb.return_value = mock_breaker

                tts = TextToSpeech(enable_cache=True)
                await tts.warm_cache()

                # Verify cache was populated
                assert len(tts._cache) > 0
                # Verify API was called for each common phrase
                assert mock_elevenlabs_client.generate.call_count == len(tts._common_phrases)

    @pytest.mark.asyncio
    async def test_warm_cache_skipped_when_disabled(self, mock_elevenlabs_client):
        """Test that cache warming is skipped when cache is disabled."""
        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            tts = TextToSpeech(enable_cache=False)
            await tts.warm_cache()

            # Verify no API calls were made
            mock_elevenlabs_client.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_warm_cache_continues_on_error(self, mock_elevenlabs_client):
        """Test that cache warming continues even if some phrases fail."""
        # First call fails, rest succeed
        mock_elevenlabs_client.generate.side_effect = [
            Exception("First phrase failed"),
            iter([b"audio2"]),
            iter([b"audio3"]),
            iter([b"audio4"]),
            iter([b"audio5"]),
            iter([b"audio6"]),
            iter([b"audio7"]),
            iter([b"audio8"]),
        ]

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            with patch("ai_companion.modules.speech.text_to_speech.get_elevenlabs_circuit_breaker") as mock_cb:
                mock_breaker = MagicMock()
                mock_breaker.call.side_effect = lambda func: func()
                mock_cb.return_value = mock_breaker

                tts = TextToSpeech(enable_cache=True)
                await tts.warm_cache()

                # Verify cache has entries despite one failure
                assert len(tts._cache) > 0

    @pytest.mark.asyncio
    async def test_warmed_cache_used_for_requests(self, mock_elevenlabs_client):
        """Test that warmed cache is used for subsequent requests."""
        mock_elevenlabs_client.generate.return_value = iter([b"cached_audio"])

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            with patch("ai_companion.modules.speech.text_to_speech.get_elevenlabs_circuit_breaker") as mock_cb:
                mock_breaker = MagicMock()
                mock_breaker.call.side_effect = lambda func: func()
                mock_cb.return_value = mock_breaker

                tts = TextToSpeech(enable_cache=True)
                await tts.warm_cache()

                initial_call_count = mock_elevenlabs_client.generate.call_count

                # Request a common phrase that should be cached
                common_phrase = tts._common_phrases[0]
                result = await tts.synthesize_cached(common_phrase)

                # Verify no additional API call was made (cache hit)
                assert mock_elevenlabs_client.generate.call_count == initial_call_count
                assert result == b"cached_audio"


@pytest.mark.unit
class TestClientInitialization:
    """Test ElevenLabs client initialization."""

    def test_client_lazy_initialization(self):
        """Test that ElevenLabs client is initialized lazily."""
        tts = TextToSpeech()

        # Client should not be initialized yet
        assert tts._client is None

        # Access client property
        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs") as mock_elevenlabs:
            mock_instance = MagicMock()
            mock_elevenlabs.return_value = mock_instance

            client = tts.client

            # Verify client was created
            assert client is mock_instance
            mock_elevenlabs.assert_called_once()

    def test_client_singleton_pattern(self):
        """Test that client instance is reused (singleton pattern)."""
        tts = TextToSpeech()

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs") as mock_elevenlabs:
            mock_instance = MagicMock()
            mock_elevenlabs.return_value = mock_instance

            # Access client multiple times
            client1 = tts.client
            client2 = tts.client

            # Verify same instance is returned
            assert client1 is client2
            # Verify ElevenLabs was only called once
            mock_elevenlabs.assert_called_once()

    def test_client_initialization_with_api_key(self):
        """Test that client is initialized with correct API key."""
        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs") as mock_elevenlabs:
            tts = TextToSpeech()
            _ = tts.client

            # Verify client was initialized with API key
            call_args = mock_elevenlabs.call_args
            assert "api_key" in call_args[1]


@pytest.mark.unit
class TestAvailabilityTracking:
    """Test TTS availability tracking."""

    @pytest.mark.asyncio
    async def test_availability_true_initially(self):
        """Test that TTS is marked as available initially."""
        tts = TextToSpeech()
        assert tts.is_available() is True

    @pytest.mark.asyncio
    async def test_availability_false_after_failure(self, mock_elevenlabs_client):
        """Test that TTS is marked unavailable after failure."""
        mock_elevenlabs_client.generate.side_effect = Exception("API error")

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            with patch("ai_companion.modules.speech.text_to_speech.get_elevenlabs_circuit_breaker") as mock_cb:
                mock_breaker = MagicMock()
                mock_breaker.call.side_effect = lambda func: func()
                mock_cb.return_value = mock_breaker

                tts = TextToSpeech()
                await tts.synthesize_with_fallback("Test")

                assert tts.is_available() is False

    @pytest.mark.asyncio
    async def test_availability_restored_after_success(self, mock_elevenlabs_client):
        """Test that availability is restored after successful synthesis."""
        # First call fails, second succeeds
        mock_elevenlabs_client.generate.side_effect = [
            Exception("API error"),
            iter([b"success_audio"]),
        ]

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            with patch("ai_companion.modules.speech.text_to_speech.get_elevenlabs_circuit_breaker") as mock_cb:
                mock_breaker = MagicMock()
                mock_breaker.call.side_effect = lambda func: func()
                mock_cb.return_value = mock_breaker

                tts = TextToSpeech()

                # First call fails
                await tts.synthesize_with_fallback("Test")
                assert tts.is_available() is False

                # Second call succeeds
                await tts.synthesize_with_fallback("Test")
                assert tts.is_available() is True
