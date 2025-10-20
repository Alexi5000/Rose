import hashlib
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

from elevenlabs import ElevenLabs, Voice, VoiceSettings

from ai_companion.core.exceptions import TextToSpeechError
from ai_companion.settings import settings

logger = logging.getLogger(__name__)


class TextToSpeech:
    """A class to handle text-to-speech conversion using ElevenLabs with Rose's therapeutic voice."""

    # Required environment variables
    REQUIRED_ENV_VARS = ["ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID"]

    def __init__(self, enable_cache: bool = True, cache_ttl_hours: int = 24):
        """Initialize the TextToSpeech class and validate environment variables.

        Args:
            enable_cache: Whether to enable caching of TTS responses
            cache_ttl_hours: Time-to-live for cached responses in hours
        """
        self._validate_env_vars()
        self._client: Optional[ElevenLabs] = None
        self._tts_available = True  # Track TTS availability for fallback logic

        # Cache configuration
        self._cache_enabled = enable_cache
        self._cache_ttl = timedelta(hours=cache_ttl_hours)
        self._cache: dict[str, tuple[bytes, datetime]] = {}  # {cache_key: (audio_bytes, timestamp)}

        # Common therapeutic phrases to pre-cache (can be expanded)
        self._common_phrases = [
            "Hello, I'm Rose. How are you feeling today?",
            "I'm here to listen and support you.",
            "Take your time. There's no rush.",
            "That sounds really difficult. Thank you for sharing.",
            "How does that make you feel?",
            "You're doing great by being here and opening up.",
            "Let's take a deep breath together.",
            "I hear you, and your feelings are valid.",
        ]

    def _validate_env_vars(self) -> None:
        """Validate that all required environment variables are set."""
        missing_vars = [var for var in self.REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    @property
    def client(self) -> ElevenLabs:
        """Get or create ElevenLabs client instance using singleton pattern."""
        if self._client is None:
            self._client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        return self._client

    async def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        stability: Optional[float] = None,
        similarity_boost: Optional[float] = None,
    ) -> bytes:
        """Convert text to speech using ElevenLabs with Rose's therapeutic voice profile.

        Args:
            text: Text to convert to speech
            voice_id: Optional voice ID to override default (useful for Rose-specific voice)
            stability: Voice stability (0.0-1.0). Higher = more consistent. Default: 0.75 for Rose's calming voice
            similarity_boost: Similarity boost (0.0-1.0). Default: 0.5 for natural variation

        Returns:
            bytes: Audio data in MP3 format

        Raises:
            ValueError: If the input text is empty or too long
            TextToSpeechError: If the text-to-speech conversion fails
        """
        if not text.strip():
            raise ValueError("Input text cannot be empty")

        if len(text) > 5000:  # ElevenLabs typical limit
            raise ValueError("Input text exceeds maximum length of 5000 characters")

        # Use Rose-specific voice if configured, otherwise use default
        selected_voice_id = voice_id or settings.ROSE_VOICE_ID or settings.ELEVENLABS_VOICE_ID

        # Rose's therapeutic voice settings: high stability for calming, grounding effect
        # Slightly slower speech rate is achieved through voice selection, not API parameters
        voice_stability = stability if stability is not None else 0.75  # High stability for consistent, calming tone
        voice_similarity = similarity_boost if similarity_boost is not None else 0.5  # Medium for natural variation

        logger.info(
            f"Synthesizing speech for Rose: {len(text)} chars, "
            f"voice_id={selected_voice_id}, stability={voice_stability}, similarity={voice_similarity}"
        )

        try:
            audio_generator = self.client.generate(
                text=text,
                voice=Voice(
                    voice_id=selected_voice_id,
                    settings=VoiceSettings(
                        stability=voice_stability,
                        similarity_boost=voice_similarity,
                    ),
                ),
                model=settings.TTS_MODEL_NAME,
            )

            # Convert generator to bytes
            audio_bytes = b"".join(audio_generator)
            if not audio_bytes:
                raise TextToSpeechError("Generated audio is empty")

            logger.info(f"Successfully generated {len(audio_bytes)} bytes of audio for Rose")
            return audio_bytes

        except ValueError:
            # Re-raise validation errors
            logger.error(f"TTS validation error: {text[:50]}...")
            raise
        except Exception as e:
            logger.error(f"TTS conversion failed: {type(e).__name__}: {str(e)}", exc_info=True)
            raise TextToSpeechError(f"Text-to-speech conversion failed: {str(e)}") from e

    async def synthesize_with_fallback(
        self,
        text: str,
        voice_id: Optional[str] = None,
        stability: Optional[float] = None,
        similarity_boost: Optional[float] = None,
    ) -> tuple[Optional[bytes], str]:
        """Convert text to speech with graceful fallback to text-only response.

        This method handles TTS failures gracefully and provides a text-only fallback
        when audio generation is unavailable, ensuring Rose can always respond to users.

        Args:
            text: Text to convert to speech
            voice_id: Optional voice ID to override default
            stability: Voice stability (0.0-1.0)
            similarity_boost: Similarity boost (0.0-1.0)

        Returns:
            tuple: (audio_bytes or None, text_response)
                - audio_bytes: Audio data if successful, None if fallback to text-only
                - text_response: Original text or error-prefixed text for fallback

        Note:
            This method never raises exceptions - it always returns a usable response.
        """
        try:
            audio_bytes = await self.synthesize(
                text=text, voice_id=voice_id, stability=stability, similarity_boost=similarity_boost
            )
            self._tts_available = True  # Reset availability flag on success
            return audio_bytes, text

        except TextToSpeechError as e:
            # TTS service error - log and fall back to text
            logger.error(f"TTS service error, falling back to text-only: {str(e)}")
            self._tts_available = False
            fallback_message = f"I'm having trouble with my voice right now, but I'm here: {text}"
            return None, fallback_message

        except ValueError as e:
            # Validation error (empty text, too long, etc.) - log and return text
            logger.warning(f"TTS validation error: {str(e)}")
            return None, text

        except Exception as e:
            # Unexpected error - log and fall back gracefully
            logger.error(f"Unexpected TTS error: {type(e).__name__}: {str(e)}", exc_info=True)
            self._tts_available = False
            fallback_message = f"I'm having trouble with my voice right now, but I'm here: {text}"
            return None, fallback_message

    def is_available(self) -> bool:
        """Check if TTS service is currently available.

        Returns:
            bool: True if TTS is available, False if recent failures suggest unavailability
        """
        return self._tts_available

    def _get_cache_key(self, text: str, voice_id: Optional[str], stability: float, similarity: float) -> str:
        """Generate a cache key for the given TTS parameters.

        Args:
            text: Text to synthesize
            voice_id: Voice ID used
            stability: Stability setting
            similarity: Similarity boost setting

        Returns:
            str: SHA256 hash of the parameters
        """
        selected_voice_id = voice_id or settings.ROSE_VOICE_ID or settings.ELEVENLABS_VOICE_ID
        cache_input = f"{text}|{selected_voice_id}|{stability}|{similarity}|{settings.TTS_MODEL_NAME}"
        return hashlib.sha256(cache_input.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[bytes]:
        """Retrieve audio from cache if available and not expired.

        Args:
            cache_key: Cache key to lookup

        Returns:
            Optional[bytes]: Cached audio bytes or None if not found/expired
        """
        if not self._cache_enabled:
            return None

        if cache_key in self._cache:
            audio_bytes, timestamp = self._cache[cache_key]
            if datetime.now() - timestamp < self._cache_ttl:
                logger.info(f"Cache hit for key: {cache_key[:16]}...")
                return audio_bytes
            else:
                # Expired - remove from cache
                logger.debug(f"Cache expired for key: {cache_key[:16]}...")
                del self._cache[cache_key]

        return None

    def _add_to_cache(self, cache_key: str, audio_bytes: bytes) -> None:
        """Add audio to cache with current timestamp.

        Args:
            cache_key: Cache key
            audio_bytes: Audio data to cache
        """
        if self._cache_enabled:
            self._cache[cache_key] = (audio_bytes, datetime.now())
            logger.debug(f"Cached audio for key: {cache_key[:16]}... ({len(audio_bytes)} bytes)")

    async def synthesize_cached(
        self,
        text: str,
        voice_id: Optional[str] = None,
        stability: Optional[float] = None,
        similarity_boost: Optional[float] = None,
    ) -> bytes:
        """Convert text to speech with caching support.

        This method checks the cache before generating new audio, improving performance
        and reducing API costs for common therapeutic phrases.

        Args:
            text: Text to convert to speech
            voice_id: Optional voice ID to override default
            stability: Voice stability (0.0-1.0)
            similarity_boost: Similarity boost (0.0-1.0)

        Returns:
            bytes: Audio data in MP3 format

        Raises:
            ValueError: If the input text is empty or too long
            TextToSpeechError: If the text-to-speech conversion fails
        """
        # Use default values for cache key generation
        voice_stability = stability if stability is not None else 0.75
        voice_similarity = similarity_boost if similarity_boost is not None else 0.5

        # Generate cache key
        cache_key = self._get_cache_key(text, voice_id, voice_stability, voice_similarity)

        # Check cache first
        cached_audio = self._get_from_cache(cache_key)
        if cached_audio is not None:
            return cached_audio

        # Cache miss - generate new audio
        audio_bytes = await self.synthesize(
            text=text, voice_id=voice_id, stability=stability, similarity_boost=similarity_boost
        )

        # Add to cache
        self._add_to_cache(cache_key, audio_bytes)

        return audio_bytes

    async def warm_cache(self) -> None:
        """Pre-generate and cache common therapeutic phrases.

        This method should be called during application startup to improve
        response times for common Rose greetings and responses.
        """
        if not self._cache_enabled:
            logger.info("Cache is disabled, skipping warm-up")
            return

        logger.info(f"Warming TTS cache with {len(self._common_phrases)} common phrases...")

        for phrase in self._common_phrases:
            try:
                await self.synthesize_cached(phrase)
                logger.debug(f"Cached phrase: {phrase[:50]}...")
            except Exception as e:
                logger.warning(f"Failed to cache phrase '{phrase[:50]}...': {str(e)}")

        logger.info(f"Cache warm-up complete. Cached {len(self._cache)} phrases.")

    def clear_cache(self) -> None:
        """Clear all cached TTS responses."""
        cache_size = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared TTS cache ({cache_size} entries)")

    def get_cache_stats(self) -> dict:
        """Get statistics about the TTS cache.

        Returns:
            dict: Cache statistics including size, enabled status, and TTL
        """
        return {
            "enabled": self._cache_enabled,
            "size": len(self._cache),
            "ttl_hours": self._cache_ttl.total_seconds() / 3600,
            "entries": [
                {"key": key[:16] + "...", "timestamp": timestamp.isoformat(), "size_bytes": len(audio)}
                for key, (audio, timestamp) in self._cache.items()
            ],
        }
