"""Speech-to-text provider abstraction.

The current production provider is Groq Whisper in batch mode. This seam lets
the voice routes depend on a provider contract now, while leaving room for
streaming providers such as Deepgram or local Whisper backends later.
"""

import asyncio
import logging
from typing import Any, AsyncIterator, Callable, Optional, Protocol, runtime_checkable

from ai_companion.modules.speech.speech_to_text import SpeechToText
from ai_companion.settings import settings

logger = logging.getLogger(__name__)

GROQ_STT_PROVIDER = "groq"
DEEPGRAM_STT_PROVIDER = "deepgram"


@runtime_checkable
class STTProvider(Protocol):
    """Protocol for speech-to-text providers."""

    @property
    def supports_streaming(self) -> bool:
        """Whether this provider can emit partial transcripts while audio arrives."""
        ...

    @property
    def name(self) -> str:
        """Human-readable provider name for metrics and logs."""
        ...

    async def transcribe(self, audio_data: bytes, audio_format: Optional[str] = None) -> str:
        """Transcribe a complete audio buffer."""
        ...

    async def transcribe_streaming(self, audio_stream: AsyncIterator[bytes]) -> AsyncIterator[str]:
        """Transcribe audio chunks as they arrive."""
        ...


class GroqWhisperProvider(SpeechToText):
    """Groq Whisper provider.

    Groq Whisper is currently batch-only for this app, so streaming calls are
    collected into one audio buffer and passed through the existing transcriber.
    """

    @property
    def supports_streaming(self) -> bool:
        return False

    @property
    def name(self) -> str:
        return "groq_stt"

    async def transcribe_streaming(self, audio_stream: AsyncIterator[bytes]) -> AsyncIterator[str]:
        audio_chunks: list[bytes] = []
        async for chunk in audio_stream:
            if chunk:
                audio_chunks.append(chunk)

        result = await self.transcribe(b"".join(audio_chunks))
        yield result


class DeepgramStreamingProvider:
    """Deepgram-backed STT provider with live streaming support.

    The Deepgram SDK is optional so the default Groq installation stays lean.
    Configure `STT_PROVIDER=deepgram` only when `deepgram-sdk` is installed and
    `DEEPGRAM_API_KEY` is set.
    """

    def __init__(
        self,
        client: Any | None = None,
        client_factory: Callable[[str], Any] | None = None,
        live_options_cls: Any | None = None,
        prerecorded_options_cls: Any | None = None,
        events: Any | None = None,
    ) -> None:
        self._client = client
        self._client_factory = client_factory
        self._live_options_cls = live_options_cls
        self._prerecorded_options_cls = prerecorded_options_cls
        self._events = events

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def name(self) -> str:
        return "deepgram_stt"

    def _load_sdk(self) -> tuple[Any, Any, Any, Any]:
        if self._live_options_cls and self._prerecorded_options_cls and self._events:
            return self._client_factory, self._live_options_cls, self._prerecorded_options_cls, self._events

        try:
            from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents, PrerecordedOptions
        except ImportError as exc:
            raise ValueError(
                "STT_PROVIDER=deepgram requires the optional Deepgram SDK. "
                "Install with `uv sync --extra streaming-stt` or `pip install deepgram-sdk`."
            ) from exc

        return DeepgramClient, LiveOptions, PrerecordedOptions, LiveTranscriptionEvents

    @property
    def client(self) -> Any:
        if self._client is None:
            if not settings.DEEPGRAM_API_KEY:
                raise ValueError("DEEPGRAM_API_KEY is required when STT_PROVIDER=deepgram")
            client_factory, _, _, _ = self._load_sdk()
            self._client = client_factory(settings.DEEPGRAM_API_KEY)
        return self._client

    async def transcribe(self, audio_data: bytes, audio_format: Optional[str] = None) -> str:
        """Transcribe a complete audio buffer through Deepgram prerecorded STT."""
        _, _, prerecorded_options_cls, _ = self._load_sdk()
        options = prerecorded_options_cls(
            model=settings.DEEPGRAM_MODEL_NAME,
            language=settings.DEEPGRAM_LANGUAGE,
            smart_format=True,
        )
        source = {
            "buffer": audio_data,
            "mimetype": audio_format or settings.DEEPGRAM_AUDIO_MIMETYPE,
        }

        listen = self.client.listen
        if hasattr(listen, "rest"):
            response = listen.rest.v("1").transcribe_file(source, options)
        else:
            response = listen.v1.media.transcribe_file(request=audio_data, model=settings.DEEPGRAM_MODEL_NAME)

        return _extract_deepgram_transcript(response)

    async def transcribe_streaming(self, audio_stream: AsyncIterator[bytes]) -> AsyncIterator[str]:
        """Stream audio chunks to Deepgram and yield partial/final transcripts."""
        _, live_options_cls, _, events = self._load_sdk()
        transcript_queue: asyncio.Queue[str | None] = asyncio.Queue()

        connection = self.client.listen.websocket.v("1")

        def handle_transcript(result: Any, **_: Any) -> None:
            transcript = _extract_deepgram_transcript(result)
            if transcript:
                transcript_queue.put_nowait(transcript)

        transcript_event = getattr(events, "Transcript", "Transcript")
        connection.on(transcript_event, handle_transcript)
        connection.start(
            live_options_cls(
                model=settings.DEEPGRAM_MODEL_NAME,
                language=settings.DEEPGRAM_LANGUAGE,
                interim_results=True,
                endpointing=settings.DEEPGRAM_ENDPOINTING_MS,
                utterance_end_ms=settings.DEEPGRAM_UTTERANCE_END_MS,
                smart_format=True,
            )
        )

        async def send_audio() -> None:
            try:
                async for chunk in audio_stream:
                    if chunk:
                        connection.send(chunk)
            finally:
                connection.finish()
                transcript_queue.put_nowait(None)

        sender = asyncio.create_task(send_audio())
        try:
            while True:
                transcript = await transcript_queue.get()
                if transcript is None:
                    break
                yield transcript
        finally:
            await sender


def _extract_deepgram_transcript(response: Any) -> str:
    """Extract the best transcript from common Deepgram SDK response shapes."""
    try:
        return response.channel.alternatives[0].transcript.strip()
    except (AttributeError, IndexError, TypeError):
        pass

    try:
        return response.results.channels[0].alternatives[0].transcript.strip()
    except (AttributeError, IndexError, TypeError):
        pass

    if isinstance(response, dict):
        try:
            return response["results"]["channels"][0]["alternatives"][0]["transcript"].strip()
        except (KeyError, IndexError, TypeError):
            return ""

    return ""


def _normalize_provider(provider: str | None) -> str:
    normalized = (provider or GROQ_STT_PROVIDER).strip().lower()
    return normalized or GROQ_STT_PROVIDER


def get_stt_provider() -> STTProvider:
    """Return the configured STT provider."""
    provider = _normalize_provider(settings.STT_PROVIDER)
    if provider == GROQ_STT_PROVIDER:
        logger.info("Using Groq Whisper STT provider", supports_streaming=False)
        return GroqWhisperProvider()
    if provider in {DEEPGRAM_STT_PROVIDER, "deepgram_streaming"}:
        logger.info("Using Deepgram streaming STT provider", supports_streaming=True)
        return DeepgramStreamingProvider()

    raise ValueError(f"Unsupported STT_PROVIDER '{provider}'. Supported providers: groq, deepgram")
