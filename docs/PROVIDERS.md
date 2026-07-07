# Provider Guide

Rose uses explicit provider boundaries so speed, privacy, and reliability can improve without spreading provider
conditionals through the app.

## Current Provider Matrix

| Layer | Default | Optional | Status |
| --- | --- | --- | --- |
| LLM | Groq | OpenRouter | Implemented |
| STT | Groq Whisper batch | Deepgram streaming | Implemented |
| TTS | ElevenLabs | Text-only / browser speech fallback | Implemented |
| Embeddings | Local sentence-transformer | None yet | Implemented |
| Safety | Deterministic local crisis classifier | None yet | Implemented |
| Memory | Qdrant long-term memory | Session-only mode | Implemented |

## LLM

Groq remains the default low-latency LLM provider. OpenRouter is supported through the OpenAI-compatible
`ChatOpenAI` path and can be either:

- Fallback behind Groq: `LLM_PROVIDER=groq`, `LLM_FALLBACK_PROVIDER=openrouter`, `OPENROUTER_API_KEY=...`
- Primary provider: `LLM_PROVIDER=openrouter`, `OPENROUTER_API_KEY=...`

OpenRouter documents an OpenAI-compatible API at `https://openrouter.ai/api/v1` and recommends attribution headers
such as `HTTP-Referer` and `X-OpenRouter-Title`. Rose sends both headers when OpenRouter is configured.

Reference:

- https://openrouter.ai/docs/quickstart
- https://openrouter.ai/docs/api/reference/overview

## Speech To Text

### Groq Whisper

Groq Whisper is Rose's default STT path. It is batch-oriented in this app: browser audio chunks are collected into a
turn buffer and transcribed as a complete audio buffer.

Use when:

- You want the simplest default setup.
- You already have Groq configured for LLM calls.
- You can tolerate buffered-turn transcription.

### Deepgram

Deepgram is Rose's optional streaming STT provider. Configure:

```bash
uv sync --extra streaming-stt
STT_PROVIDER=deepgram
DEEPGRAM_API_KEY="..."
```

Deepgram's current docs position Flux for conversational voice-agent STT and Nova-3 for streaming transcription and
batch transcription. Rose's current implementation is provider-ready for Deepgram streaming and uses configurable
`DEEPGRAM_MODEL_NAME`, so model selection can be tuned without changing route code.

Use when:

- Mic-to-first-audio latency matters more than minimal provider setup.
- You want partial transcripts during the turn.
- You are evaluating voice-agent style turn-taking.

Reference:

- https://developers.deepgram.com/home
- https://developers.deepgram.com/docs/models-languages-overview
- https://developers.deepgram.com/docs/flux/quickstart

### Turn Taking

Rose has a deterministic transcript-completion gate after STT and before normal response generation. It catches clear
dangling fragments such as "I feel like" or "the thing is" and asks for a continuation instead of sending the fragment
to the LLM. Treat this as a conservative safety rail, not a replacement for provider endpointing. Deepgram Flux,
Deepgram Nova-3, or a future local streaming STT provider should feed partial/final transcript events into the same
route-level turn policy.

### Local STT Candidates

Local STT is not implemented yet. The two strongest open-source candidates are:

- `faster-whisper`: a CTranslate2 Whisper implementation focused on faster, lower-memory inference.
- `whisper.cpp`: a C/C++ Whisper implementation with broad CPU/GPU support and a streaming example.

Suggested implementation path:

1. Add `STT_PROVIDER=faster_whisper` behind the existing `STTProvider` protocol.
2. Start with batch local transcription to preserve behavior.
3. Add streaming only after measuring partial transcript stability and CPU/GPU load.
4. Keep Groq as the default and Deepgram as the cloud streaming option.
5. Add tests for missing model files, unsupported local provider names, and no-network operation.

Reference:

- https://github.com/SYSTRAN/faster-whisper
- https://github.com/ggml-org/whisper.cpp
- https://github.com/ggml-org/whisper.cpp/blob/master/examples/stream/stream.cpp

## Text To Speech

ElevenLabs is Rose's default server-side TTS provider and supports streaming output through the current `TTSProvider`
interface. For local development or outages, `TTS_PROVIDER=text_only` or `TTS_PROVIDER=browser_speech` intentionally
disables server audio so HTTP responses return text-only and WebSocket turns emit `audio_unavailable`; the frontend can
then use browser speech synthesis as a degraded fallback.

Provider rules:

- Keep ElevenLabs as the default voice path.
- Keep text-only/browser-speech mode explicit; do not silently pretend server audio exists.
- Do not block the whole turn when TTS fails; return text and continue the session.
- Preserve barge-in and interruption behavior.
- Keep TTS logs redacted by default.

## Embeddings And Memory

Rose uses local sentence-transformer embeddings and Qdrant-backed long-term memory. Embeddings are sensitive data:

- Do not log raw memory text or vector payloads by default.
- Keep memory export sanitized.
- Preserve session-only, export, and forget controls.
- Add deletion and session-isolation tests for memory changes.

## Safety

Rose's safety layer is deliberately local and deterministic by default. It must remain available even when LLM
providers fail. Provider changes must not bypass:

- Crisis assessment before normal generation.
- U.S. 988 guidance for crisis and direct self-harm intent language.
- Imminent-risk escalation to immediate human help.
- External imminent danger guidance to emergency services, safer public places, and trusted contacts without self-harm wording.
- False-positive recovery for negated, prevention, and reference contexts.
- Safety eval transcript regressions in `tests/fixtures/safety_eval_transcripts.json`.

## Adding A Provider

Use this checklist before opening a provider PR:

- The provider is behind an existing protocol or a new protocol with a small surface area.
- Settings have explicit names, defaults, and validation.
- `.env.example`, README, and this guide are updated.
- Existing providers still pass tests.
- Missing credentials fail with actionable messages.
- Unsupported provider names fail fast.
- Logs do not leak transcripts, prompts, memory text, vectors, audio, or secrets.
- Focused tests cover selection, fallback, and failure behavior.
- Voice metrics still include `p50` and `p95` histograms where latency is affected.
