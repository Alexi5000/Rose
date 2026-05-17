"""Speech-to-text conversion using Groq's Whisper model.

This module provides the SpeechToText class for converting audio to text using
Groq's Whisper API. It includes automatic retry logic with exponential backoff,
circuit breaker protection, and audio format detection.

The module handles various audio formats (WAV, MP3, WebM, M4A, OGG, FLAC) and
automatically detects the format from file headers when not explicitly provided.

Key features:
- Automatic retry with exponential backoff (configurable via settings)
- Circuit breaker protection to prevent cascading failures
- Audio format auto-detection from file headers
- Async/await support with thread pool execution for sync Groq SDK
- Comprehensive error handling and logging

Module Dependencies:
- ai_companion.core.exceptions: SpeechToTextError for error handling
- ai_companion.core.resilience: Circuit breaker for Groq API calls
- ai_companion.settings: Configuration for API keys, timeouts, retry settings
- groq: Groq SDK for Whisper API access
- Standard library: asyncio, logging, os, tempfile, typing

Dependents (modules that import this):
- ai_companion.interfaces.chainlit.app: Audio message handling
- ai_companion.interfaces.whatsapp.whatsapp_response: WhatsApp audio messages
- ai_companion.interfaces.web.routes.voice: Voice API endpoint
- Test modules: tests/unit/test_speech_to_text.py

Architecture:
This module is part of the modules layer and provides speech-to-text functionality
with resilience patterns (retry + circuit breaker). It uses asyncio.to_thread() to
run the synchronous Groq SDK in a thread pool, preventing event loop blocking.

For detailed architecture documentation, see:
- docs/ARCHITECTURE.md: Retry Pattern with Exponential Backoff section
- docs/ARCHITECTURE.md: Circuit Breaker Pattern section

Design Reference:
- .kiro/specs/technical-debt-management/design.md: Test Infrastructure section

Example:
    Basic usage of speech-to-text:

    >>> stt = SpeechToText()
    >>> with open("audio.wav", "rb") as f:
    ...     audio_data = f.read()
    >>> text = await stt.transcribe(audio_data)
    >>> print(text)
    'Hello, how are you today?'
"""

import asyncio
import logging
import os
import tempfile
from typing import Optional

from groq import Groq

from ai_companion.core.exceptions import SpeechToTextError
from ai_companion.core.resilience import CircuitBreaker, CircuitBreakerError, get_groq_circuit_breaker
from ai_companion.settings import settings

logger = logging.getLogger(__name__)


class SpeechToText:
    """A class to handle speech-to-text conversion using Groq's Whisper model.

    This class provides speech-to-text transcription with automatic retry logic,
    circuit breaker protection, and audio format detection.

    Configuration is loaded from settings module for consistency across the application.
    """

    # Supported audio formats
    SUPPORTED_FORMATS = [".wav", ".mp3", ".webm", ".m4a", ".ogg", ".flac"]

    def __init__(self) -> None:
        """Initialize the SpeechToText class and validate environment variables."""
        self._client: Optional[Groq] = None
        self._circuit_breaker: CircuitBreaker = get_groq_circuit_breaker()

    @property
    def client(self) -> Groq:
        """Get or create Groq client instance using singleton pattern."""
        if self._client is None:
            self._client = Groq(api_key=settings.GROQ_API_KEY, timeout=settings.STT_TIMEOUT)
        return self._client

    def _detect_audio_format(self, audio_data: bytes) -> str:
        """Detect audio format from file header.

        Args:
            audio_data: Binary audio data

        Returns:
            str: File extension (e.g., '.wav', '.mp3')
        """
        # Check for common audio file signatures
        if audio_data[:4] == b"RIFF" and audio_data[8:12] == b"WAVE":
            return ".wav"
        elif audio_data[:3] == b"ID3" or audio_data[:2] == b"\xff\xfb" or audio_data[:2] == b"\xff\xf3":
            return ".mp3"
        elif audio_data[:4] == b"OggS":
            return ".ogg"
        elif audio_data[:4] == b"fLaC":
            return ".flac"
        elif len(audio_data) > 8 and audio_data[4:8] == b"ftyp":
            return ".m4a"
        else:
            # Default to wav if format cannot be detected
            logger.warning("Could not detect audio format, defaulting to .wav")
            return ".wav"

    async def transcribe(self, audio_data: bytes, audio_format: Optional[str] = None) -> str:
        """Convert speech to text using Groq's Whisper model with retry logic.

        Args:
            audio_data: Binary audio data
            audio_format: Optional audio format (e.g., 'wav', 'mp3'). If not provided, will be auto-detected.

        Returns:
            str: Transcribed text

        Raises:
            ValueError: If the audio file is empty or invalid
            SpeechToTextError: If the transcription fails after all retries
        """
        if not audio_data:
            raise ValueError("Audio data cannot be empty")

        # Validate audio size (configurable via settings)
        max_size = settings.STT_MAX_AUDIO_SIZE_MB * 1024 * 1024
        if len(audio_data) > max_size:
            raise ValueError(f"Audio file too large. Maximum size is {settings.STT_MAX_AUDIO_SIZE_MB}MB")

        # Determine file extension
        if audio_format:
            file_ext = f".{audio_format.lstrip('.')}"
            if file_ext not in self.SUPPORTED_FORMATS:
                logger.warning(f"Unsupported format {file_ext}, attempting anyway")
        else:
            file_ext = self._detect_audio_format(audio_data)

        logger.info(f"Transcribing audio: size={len(audio_data)} bytes, format={file_ext}")

        # Retry loop with exponential backoff (configured via settings)
        # This provides resilience against transient network errors and API rate limits
        last_exception = None
        for attempt in range(settings.STT_MAX_RETRIES):
            try:
                # Create a temporary file with appropriate extension
                # Note: We use synchronous tempfile here as it's a quick operation and
                # asyncio doesn't provide a native async alternative for NamedTemporaryFile
                with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as temp_file:
                    temp_file.write(audio_data)
                    temp_file_path = temp_file.name

                try:
                    logger.info(f"Attempt {attempt + 1}/{settings.STT_MAX_RETRIES}: Calling Groq Whisper API")

                    # Use circuit breaker for API call (async version)
                    # Note: Groq SDK is synchronous, so we use asyncio.to_thread() to run it
                    # in a thread pool, preventing event loop blocking. This is necessary
                    # because the Groq client doesn't provide native async support.
                    async def _call_groq_api() -> str:
                        # Run sync Groq API call in thread pool to avoid blocking event loop
                        # We need to open the file inside the thread to avoid file handle issues
                        def _sync_transcribe() -> str:
                            with open(temp_file_path, "rb") as audio_file:
                                return self.client.audio.transcriptions.create(  # type: ignore[return-value]  # Groq returns Transcription object with text attribute
                                    file=audio_file,
                                    model=settings.STT_MODEL_NAME,
                                    language="en",
                                    response_format="text",
                                )

                        return await asyncio.to_thread(_sync_transcribe)

                    transcription: str = await self._circuit_breaker.call_async(_call_groq_api)

                    if not transcription:
                        raise SpeechToTextError("Transcription result is empty")

                    logger.info(f"Transcription successful: {transcription[:100]}...")
                    return transcription

                finally:
                    # Clean up the temporary file asynchronously
                    try:
                        await asyncio.to_thread(os.unlink, temp_file_path)
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to cleanup temp file: {cleanup_error}")

            except CircuitBreakerError as e:
                # Circuit breaker is open - fail fast without retrying
                # This prevents wasting time on retries when the service is known to be down
                logger.error(f"Circuit breaker is open for Groq API: {str(e)}")
                raise SpeechToTextError("Speech-to-text service is temporarily unavailable") from e

            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Attempt {attempt + 1}/{settings.STT_MAX_RETRIES} failed: {type(e).__name__}: {str(e)}",
                    exc_info=attempt == settings.STT_MAX_RETRIES - 1,  # Full traceback on last attempt
                )

                # Don't retry on validation errors (they won't succeed on retry)
                if isinstance(e, ValueError):
                    raise

                # If not the last attempt, wait with exponential backoff
                # Exponential backoff formula: initial_backoff * (2 ^ attempt)
                # Example with initial=1s: 1s, 2s, 4s, 8s, 16s (capped at max_backoff)
                # This gives the service time to recover and reduces load during outages
                if attempt < settings.STT_MAX_RETRIES - 1:
                    backoff_time = min(settings.STT_INITIAL_BACKOFF * (2**attempt), settings.STT_MAX_BACKOFF)
                    logger.info(f"Retrying in {backoff_time:.1f} seconds...")
                    await asyncio.sleep(backoff_time)

        # All retries exhausted
        error_msg = f"Speech-to-text conversion failed after {settings.STT_MAX_RETRIES} attempts"
        if last_exception:
            error_msg += f": {str(last_exception)}"
        logger.error(error_msg)
        raise SpeechToTextError(error_msg) from last_exception
