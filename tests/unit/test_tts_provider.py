"""Unit tests for TTS provider selection."""

from unittest.mock import patch

import pytest

from ai_companion.core.exceptions import TextToSpeechError
from ai_companion.modules.speech import ElevenLabsTTSProvider, TextOnlyTTSProvider, TTSProvider
from ai_companion.modules.speech.tts_provider import get_tts_provider
from ai_companion.settings import settings


def test_get_tts_provider_defaults_to_elevenlabs(monkeypatch):
    monkeypatch.setattr(settings, "TTS_PROVIDER", "elevenlabs")

    provider = get_tts_provider()

    assert isinstance(provider, ElevenLabsTTSProvider)
    assert isinstance(provider, TTSProvider)
    assert provider.name == "elevenlabs_tts"


def test_get_tts_provider_accepts_metric_name_alias(monkeypatch):
    monkeypatch.setattr(settings, "TTS_PROVIDER", "elevenlabs_tts")

    provider = get_tts_provider()

    assert isinstance(provider, ElevenLabsTTSProvider)


def test_get_tts_provider_accepts_text_only_degraded_mode(monkeypatch):
    monkeypatch.setattr(settings, "TTS_PROVIDER", "text_only")

    provider = get_tts_provider()

    assert isinstance(provider, TextOnlyTTSProvider)
    assert isinstance(provider, TTSProvider)
    assert provider.name == "text_only_tts"
    assert provider.is_available() is False
    assert provider.get_cache_stats() == {"enabled": False, "size": 0, "ttl_hours": 0, "entries": []}


def test_get_tts_provider_accepts_browser_speech_alias(monkeypatch):
    monkeypatch.setattr(settings, "TTS_PROVIDER", "browser_speech")

    provider = get_tts_provider()

    assert isinstance(provider, TextOnlyTTSProvider)


@pytest.mark.asyncio
async def test_text_only_tts_provider_returns_text_fallback_without_audio():
    provider = TextOnlyTTSProvider()

    audio, text = await provider.synthesize_with_fallback("I am here with you.")

    assert audio is None
    assert text == "I am here with you."


@pytest.mark.asyncio
async def test_text_only_tts_provider_raises_for_audio_generation():
    provider = TextOnlyTTSProvider()

    with pytest.raises(TextToSpeechError, match="Server-side TTS is disabled"):
        await provider.synthesize("I am here with you.")

    with pytest.raises(TextToSpeechError, match="Server-side streaming TTS is disabled"):
        async for _chunk in provider.synthesize_streaming("I am here with you."):
            pass


def test_get_tts_provider_rejects_unknown_provider(monkeypatch):
    monkeypatch.setattr(settings, "TTS_PROVIDER", "unknown")

    with pytest.raises(ValueError, match="Unsupported TTS_PROVIDER"):
        get_tts_provider()


def test_voice_route_get_tts_uses_provider_factory():
    from ai_companion.graph.utils.helpers import get_text_to_speech_module
    from ai_companion.interfaces.web.routes import voice

    get_text_to_speech_module.cache_clear()
    fake_provider = object()

    with patch("ai_companion.graph.utils.helpers.get_tts_provider", return_value=fake_provider):
        assert voice.get_tts() is fake_provider

    get_text_to_speech_module.cache_clear()
