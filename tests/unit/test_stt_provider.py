"""Unit tests for STT provider selection."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_companion.modules.speech import STTProvider
from ai_companion.modules.speech.stt_provider import DeepgramStreamingProvider, GroqWhisperProvider, get_stt_provider
from ai_companion.settings import settings


def test_get_stt_provider_defaults_to_groq(monkeypatch):
    monkeypatch.setattr(settings, "STT_PROVIDER", "groq")

    provider = get_stt_provider()

    assert isinstance(provider, GroqWhisperProvider)
    assert isinstance(provider, STTProvider)
    assert provider.name == "groq_stt"
    assert provider.supports_streaming is False


def test_get_stt_provider_rejects_unknown_provider(monkeypatch):
    monkeypatch.setattr(settings, "STT_PROVIDER", "unknown")

    with pytest.raises(ValueError, match="Unsupported STT_PROVIDER"):
        get_stt_provider()


def test_get_stt_provider_can_select_deepgram(monkeypatch):
    monkeypatch.setattr(settings, "STT_PROVIDER", "deepgram")

    provider = get_stt_provider()

    assert isinstance(provider, DeepgramStreamingProvider)
    assert isinstance(provider, STTProvider)
    assert provider.name == "deepgram_stt"
    assert provider.supports_streaming is True


def test_deepgram_provider_requires_api_key(monkeypatch):
    monkeypatch.setattr(settings, "DEEPGRAM_API_KEY", None)
    provider = DeepgramStreamingProvider(
        client_factory=MagicMock(),
        live_options_cls=MagicMock(),
        prerecorded_options_cls=MagicMock(),
        events=MagicMock(),
    )

    with pytest.raises(ValueError, match="DEEPGRAM_API_KEY is required"):
        _ = provider.client


def test_deepgram_provider_reports_missing_sdk(monkeypatch):
    monkeypatch.setattr(settings, "DEEPGRAM_API_KEY", "test-key")
    provider = DeepgramStreamingProvider()

    with patch.dict("sys.modules", {"deepgram": None}):
        with pytest.raises(ValueError, match="optional Deepgram SDK"):
            _ = provider.client


@pytest.mark.asyncio
async def test_groq_streaming_fallback_collects_chunks():
    provider = GroqWhisperProvider()
    provider.transcribe = AsyncMock(return_value="hello from buffered audio")

    async def chunks():
        yield b"webm"
        yield b""
        yield b"-audio"

    results = []
    async for transcript in provider.transcribe_streaming(chunks()):
        results.append(transcript)

    assert results == ["hello from buffered audio"]
    provider.transcribe.assert_awaited_once_with(b"webm-audio")


def test_groq_provider_keeps_browser_webm_detection():
    provider = GroqWhisperProvider()

    assert provider._detect_audio_format(b"\x1a\x45\xdf\xa3" + b"\x00" * 100) == ".webm"


@pytest.mark.asyncio
async def test_deepgram_batch_transcribe_uses_prerecorded_api(monkeypatch):
    monkeypatch.setattr(settings, "DEEPGRAM_MODEL_NAME", "nova-3")
    monkeypatch.setattr(settings, "DEEPGRAM_LANGUAGE", "en-US")
    monkeypatch.setattr(settings, "DEEPGRAM_ENDPOINTING_MS", 300)
    monkeypatch.setattr(settings, "DEEPGRAM_UTTERANCE_END_MS", 1000)
    monkeypatch.setattr(settings, "DEEPGRAM_AUDIO_MIMETYPE", "audio/webm")

    response = {"results": {"channels": [{"alternatives": [{"transcript": " a clear transcript "}]}]}}
    rest = MagicMock()
    rest.v.return_value.transcribe_file.return_value = response
    client = SimpleNamespace(listen=SimpleNamespace(rest=rest))
    options_cls = MagicMock(return_value="options")

    provider = DeepgramStreamingProvider(
        client=client,
        live_options_cls=MagicMock(),
        prerecorded_options_cls=options_cls,
        events=MagicMock(),
    )

    assert await provider.transcribe(b"audio", audio_format="audio/webm") == "a clear transcript"
    rest.v.assert_called_once_with("1")
    rest.v.return_value.transcribe_file.assert_called_once_with(
        {"buffer": b"audio", "mimetype": "audio/webm"},
        "options",
    )
    options_cls.assert_called_once_with(model="nova-3", language="en-US", smart_format=True)


@pytest.mark.asyncio
async def test_deepgram_streaming_yields_transcripts(monkeypatch):
    monkeypatch.setattr(settings, "DEEPGRAM_MODEL_NAME", "nova-3")
    monkeypatch.setattr(settings, "DEEPGRAM_LANGUAGE", "en-US")

    class FakeEvents:
        Transcript = "Transcript"

    class FakeLiveOptions:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeConnection:
        def __init__(self):
            self.callback = None
            self.started_with = None
            self.sent = []
            self.finished = False

        def on(self, event, callback):
            assert event == "Transcript"
            self.callback = callback

        def start(self, options):
            self.started_with = options

        def send(self, chunk):
            self.sent.append(chunk)
            self.callback(
                SimpleNamespace(
                    channel=SimpleNamespace(alternatives=[SimpleNamespace(transcript=f"heard {chunk.decode()}")])
                )
            )

        def finish(self):
            self.finished = True

    connection = FakeConnection()
    client = SimpleNamespace(listen=SimpleNamespace(websocket=SimpleNamespace(v=lambda version: connection)))
    provider = DeepgramStreamingProvider(
        client=client,
        live_options_cls=FakeLiveOptions,
        prerecorded_options_cls=MagicMock(),
        events=FakeEvents,
    )

    async def chunks():
        yield b"one"
        yield b""
        yield b"two"

    transcripts = []
    async for transcript in provider.transcribe_streaming(chunks()):
        transcripts.append(transcript)

    assert transcripts == ["heard one", "heard two"]
    assert connection.sent == [b"one", b"two"]
    assert connection.finished is True
    assert connection.started_with.kwargs == {
        "model": "nova-3",
        "language": "en-US",
        "interim_results": True,
        "endpointing": 300,
        "utterance_end_ms": 1000,
        "smart_format": True,
    }


def test_voice_route_get_stt_uses_provider_factory():
    from ai_companion.interfaces.web.routes import voice

    voice.get_stt.cache_clear()
    fake_provider = object()

    with patch("ai_companion.interfaces.web.routes.voice.get_stt_provider", return_value=fake_provider):
        assert voice.get_stt() is fake_provider

    voice.get_stt.cache_clear()
