# Voice Architecture

Rose's voice path is built around fast, interruptible turns: get from microphone to first audio quickly, keep safety and
privacy checks close to the data, and preserve a clean provider boundary so contributors can improve one layer without
rewriting the whole companion.

## WebSocket Voice Turn

```mermaid
sequenceDiagram
    participant Browser
    participant WS as FastAPI WebSocket
    participant STT as STT Provider
    participant Turn as Turn Gate
    participant Safety as Crisis Safety
    participant Graph as LangGraph Rose Brain
    participant TTS as TTS Provider

    Browser->>WS: start_listening
    Browser->>WS: audio chunks
    Browser->>WS: stop_listening
    WS->>STT: transcribe audio or stream
    STT-->>WS: partial and final transcript
    WS->>Turn: assess transcript completion
    alt Dangling fragment
        Turn-->>WS: incomplete reason
        WS-->>Browser: turn_incomplete
        WS->>TTS: continuation prompt
        TTS-->>Browser: audio chunks
    else Complete turn
        WS->>Safety: crisis routing in graph
        Safety->>Graph: safe route or crisis response route
        Graph-->>WS: streamed response deltas
        WS->>TTS: phrase chunks
        TTS-->>Browser: audio chunks
    end
    WS-->>Browser: audio_end with timings
```

## Provider Boundaries

```mermaid
flowchart LR
    VoiceRoute["Voice Routes"] --> LLM["LLM Provider\nGroq default\nOpenRouter fallback"]
    VoiceRoute --> STT["STT Provider\nGroq batch\nDeepgram streaming optional"]
    VoiceRoute --> TTS["TTS Provider\nElevenLabs streaming\nBrowser fallback"]
    VoiceRoute --> Metrics["Metrics\np50/p95 latency\nturn counters"]
    Graph["LangGraph Rose Brain"] --> Safety["Safety Provider\ndeterministic crisis checks"]
    Graph --> Memory["Memory Provider\nQdrant + session-only controls"]
    Memory --> Embeddings["Embeddings\nlocal sentence-transformer"]
```

Provider details and tradeoffs live in [PROVIDERS.md](PROVIDERS.md).

## Design Rules

- Do not send raw transcripts, memory text, or audio payloads to logs unless `LOG_SENSITIVE_CONTENT=true` is explicitly
  enabled for a local consented debugging session.
- Keep Groq as the fast default LLM/STT path and treat OpenRouter as configurable fallback or alternate primary.
- Keep turn-taking conservative. A false continuation prompt is less harmful than Rose answering a half-sentence with
  misplaced certainty.
- Stream response text into TTS in phrase chunks so Rose can start speaking before the full answer is complete.
- Preserve barge-in. Interruptions must cancel queued speech and return the browser to listening without a full page or
  session reset.
- Record latency where users feel it: mic-to-first-audio and total turn time matter more than isolated provider timings.
