"""STT Provider abstraction for speech-to-text backends.

This module provides:
- Protocol-based abstraction for STT providers
- Support for both batch and streaming transcription
- Groq Whisper provider implementation (batch mode)
- Factory function for provider instantiation
"""

import asyncio
import logging
from typing import AsyncIterator, Optional, Protocol, runtime_checkable

from ai_companion.core.exceptions import SpeechToTextError
from ai_companion.core.resilience import CircuitBreaker, CircuitBreakerError, get_groq_circuit_breaker
from ai_companion.settings import settings

logger = logging.getLogger(__name__)


@runtime_checkable
class STTProvider(Protocol):
    """Protocol for speech-to-text providers.
    
    All STT providers must implement this interface to ensure consistent
    behavior across different backends (Groq, Deepgram, AssemblyAI, etc.).
    """
    
    @property
    def supports_streaming(self) -> bool:
        """Whether this provider supports streaming transcription."""
        ...
    
    @property
    def name(self) -> str:
        """Human-readable provider name for logging."""
        ...
    
    async def transcribe(self, audio_data: bytes, audio_format: Optional[str] = None) -> str:
        """Transcribe audio to text (batch mode).
        
        Args:
            audio_data: Binary audio data
            audio_format: Optional audio format hint (e.g., 'wav', 'mp3')
            
        Returns:
            str: Transcribed text
            
        Raises:
            SpeechToTextError: If transcription fails
        """
        ...
    
    async def transcribe_streaming(
        self, audio_stream: AsyncIterator[bytes]
    ) -> AsyncIterator[str]:
        """Stream transcription as audio chunks arrive.
        
        Args:
            audio_stream: Async iterator of audio chunks
            
        Yields:
            str: Partial transcription results as they become available
            
        Raises:
            SpeechToTextError: If streaming transcription fails
            NotImplementedError: If provider doesn't support streaming
        """
        ...


class GroqWhisperProvider:
    """Groq Whisper STT provider (batch mode only).
    
    Uses Groq's hosted Whisper model for transcription.
    Does NOT support streaming - transcription happens after full audio is received.
    
    This is the default provider as it's already integrated and provides
    good accuracy with reasonable latency (~800ms for typical utterances).
    """
    
    SUPPORTED_FORMATS = [".wav", ".mp3", ".webm", ".m4a", ".ogg", ".flac"]
    
    def __init__(self) -> None:
        """Initialize Groq Whisper provider."""
        from groq import Groq
        self._client: Optional[Groq] = None
        self._circuit_breaker: CircuitBreaker = get_groq_circuit_breaker()
    
    @property
    def client(self):
        """Get or create Groq client instance."""
        if self._client is None:
            from groq import Groq
            self._client = Groq(api_key=settings.GROQ_API_KEY, timeout=settings.STT_TIMEOUT)
        return self._client
    
    @property
    def supports_streaming(self) -> bool:
        """Groq Whisper does not support streaming."""
        return False
    
    @property
    def name(self) -> str:
        return "Groq Whisper"
    
    def _detect_audio_format(self, audio_data: bytes) -> str:
        """Detect audio format from file header."""
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
            logger.warning("Could not detect audio format, defaulting to .wav")
            return ".wav"
    
    async def transcribe(self, audio_data: bytes, audio_format: Optional[str] = None) -> str:
        """Transcribe audio using Groq Whisper (batch mode)."""
        import os
        import tempfile
        
        if not audio_data:
            raise ValueError("Audio data cannot be empty")
        
        max_size = settings.STT_MAX_AUDIO_SIZE_MB * 1024 * 1024
        if len(audio_data) > max_size:
            raise ValueError(f"Audio file too large. Maximum size is {settings.STT_MAX_AUDIO_SIZE_MB}MB")
        
        if audio_format:
            file_ext = f".{audio_format.lstrip('.')}"
        else:
            file_ext = self._detect_audio_format(audio_data)
        
        logger.info(f"[{self.name}] Transcribing: size={len(audio_data)} bytes, format={file_ext}")
        
        last_exception = None
        for attempt in range(settings.STT_MAX_RETRIES):
            try:
                with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as temp_file:
                    temp_file.write(audio_data)
                    temp_file_path = temp_file.name
                
                try:
                    async def _call_groq_api() -> str:
                        def _sync_transcribe() -> str:
                            with open(temp_file_path, "rb") as audio_file:
                                return self.client.audio.transcriptions.create(
                                    file=audio_file,
                                    model=settings.STT_MODEL_NAME,
                                    language="en",
                                    response_format="text",
                                )
                        return await asyncio.to_thread(_sync_transcribe)
                    
                    transcription: str = await self._circuit_breaker.call_async(_call_groq_api)
                    
                    if not transcription:
                        raise SpeechToTextError("Transcription result is empty")
                    
                    logger.info(f"[{self.name}] Transcription successful: {transcription[:100]}...")
                    return transcription
                
                finally:
                    try:
                        await asyncio.to_thread(os.unlink, temp_file_path)
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to cleanup temp file: {cleanup_error}")
            
            except CircuitBreakerError as e:
                logger.error(f"[{self.name}] Circuit breaker is open: {str(e)}")
                raise SpeechToTextError("Speech-to-text service is temporarily unavailable") from e
            
            except ValueError:
                raise
            
            except Exception as e:
                last_exception = e
                logger.warning(f"[{self.name}] Attempt {attempt + 1} failed: {type(e).__name__}: {str(e)}")
                
                if attempt < settings.STT_MAX_RETRIES - 1:
                    backoff_time = min(settings.STT_INITIAL_BACKOFF * (2**attempt), settings.STT_MAX_BACKOFF)
                    await asyncio.sleep(backoff_time)
        
        error_msg = f"[{self.name}] Transcription failed after {settings.STT_MAX_RETRIES} attempts"
        raise SpeechToTextError(error_msg) from last_exception
    
    async def transcribe_streaming(
        self, audio_stream: AsyncIterator[bytes]
    ) -> AsyncIterator[str]:
        """Groq Whisper does not support streaming - collect all audio then transcribe."""
        logger.warning(f"[{self.name}] Streaming not supported, falling back to batch mode")
        
        # Collect all audio chunks
        audio_chunks = []
        async for chunk in audio_stream:
            audio_chunks.append(chunk)
        
        audio_data = b"".join(audio_chunks)
        
        # Transcribe as batch
        result = await self.transcribe(audio_data)
        yield result


def get_stt_provider() -> STTProvider:
    """Factory function to get the STT provider instance.

    Returns:
        STTProvider: Configured Groq Whisper STT provider
    """
    logger.info("Using Groq Whisper STT provider (batch mode)")
    return GroqWhisperProvider()
