"""Text-to-speech provider abstraction.

This module keeps Rose's current ElevenLabs voice path as the default while
making TTS swappable in the same style as the LLM and STT provider layers.
"""

from __future__ import annotations

from typing import AsyncIterator, Protocol, Tuple, runtime_checkable

from ai_companion.core.exceptions import TextToSpeechError
from ai_companion.modules.speech.text_to_speech import TextToSpeech
from ai_companion.settings import settings


@runtime_checkable
class TTSProvider(Protocol):
    """Protocol for Rose text-to-speech providers."""

    name: str

    async def synthesize(self, text: str, **kwargs) -> bytes:
        """Convert text into a complete audio payload."""
        ...

    async def synthesize_streaming(self, text: str, **kwargs) -> AsyncIterator[bytes]:
        """Stream audio chunks for lower time-to-first-audio."""
        ...

    async def synthesize_cached(self, text: str, **kwargs) -> bytes:
        """Convert text into audio, reusing a provider cache when available."""
        ...

    async def synthesize_with_fallback(self, text: str, **kwargs) -> Tuple[bytes | None, str]:
        """Convert text into audio or return text-only fallback content."""
        ...

    async def warm_cache(self) -> None:
        """Warm any provider-side cache for common Rose phrases."""
        ...

    def clear_cache(self) -> None:
        """Clear provider cache."""
        ...

    def get_cache_stats(self) -> dict:
        """Return provider cache statistics."""
        ...

    def is_available(self) -> bool:
        """Return whether the provider is currently considered available."""
        ...


class ElevenLabsTTSProvider(TextToSpeech):
    """ElevenLabs-backed TTS provider for Rose's primary voice."""

    name = "elevenlabs_tts"


class TextOnlyTTSProvider:
    """Intentional degraded TTS provider that leaves audio to the browser."""

    name = "text_only_tts"

    async def synthesize(self, text: str, **kwargs) -> bytes:
        """Fail audio generation so callers use their text-only fallback path."""

        if not text.strip():
            raise ValueError("Input text cannot be empty")
        raise TextToSpeechError("Server-side TTS is disabled; use text-only or browser speech fallback")

    async def synthesize_streaming(self, text: str, **kwargs) -> AsyncIterator[bytes]:
        """Fail streaming audio generation so WebSocket clients receive audio_unavailable."""

        if not text.strip():
            raise ValueError("Input text cannot be empty")
        raise TextToSpeechError("Server-side streaming TTS is disabled; use browser speech fallback")
        yield b""

    async def synthesize_cached(self, text: str, **kwargs) -> bytes:
        """Fail cached audio generation consistently with synthesize."""

        return await self.synthesize(text, **kwargs)

    async def synthesize_with_fallback(self, text: str, **kwargs) -> Tuple[bytes | None, str]:
        """Return the original response text with no server audio."""

        if not text.strip():
            return None, text
        return None, text

    async def warm_cache(self) -> None:
        """No-op: text-only mode has no server audio cache."""

    def clear_cache(self) -> None:
        """No-op: text-only mode has no server audio cache."""

    def get_cache_stats(self) -> dict:
        """Return empty cache stats for provider-compatible health/debug views."""

        return {"enabled": False, "size": 0, "ttl_hours": 0, "entries": []}

    def is_available(self) -> bool:
        """Text fallback is always available even when server audio is disabled."""

        return False


def get_tts_provider() -> TTSProvider:
    """Create the configured TTS provider.

    Raises:
        ValueError: If ``TTS_PROVIDER`` is not supported.
    """
    provider = settings.TTS_PROVIDER.strip().lower()
    if provider in {"elevenlabs", "elevenlabs_tts"}:
        return ElevenLabsTTSProvider()
    if provider in {"text_only", "text_only_tts", "browser_speech"}:
        return TextOnlyTTSProvider()
    raise ValueError(f"Unsupported TTS_PROVIDER '{settings.TTS_PROVIDER}'")
