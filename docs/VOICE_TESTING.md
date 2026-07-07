# Voice Testing

This file used to contain an older smoke-test checklist for a previous voice UI. The active voice surface is now the
React and FastAPI web app documented in:

- `tests/manual_e2e_voice_first_testing.md`
- `docs/VOICE_ARCHITECTURE.md`
- `README.md`

Use `tests/manual_e2e_voice_first_testing.md` for manual end-to-end validation. It covers the current WebSocket voice
path, HTTP fallback, interruption and barge-in, incomplete turn recovery, memory controls, crisis safety routing,
browser-console privacy, and latency notes.

Current local entry points:

```bash
python scripts/run_dev_server.py
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/api/v1/docs

Provider reminders:

- Groq is the default LLM and STT provider.
- OpenRouter is optional for LLM fallback or primary routing.
- Deepgram is optional for streaming STT on the WebSocket path.
- ElevenLabs is the backend TTS provider.
- Qdrant stores long-term memory when session memory is enabled.

Privacy and safety reminders:

- Keep `LOG_SENSITIVE_CONTENT=false` unless debugging locally with consented or synthetic data.
- Do not log raw transcripts, raw audio, provider payloads, secrets, or embedding vectors.
- Rose is AI emotional support, not a therapist, doctor, emergency service, or replacement for professional care.
- Use synthetic crisis prompts only for safety regression checks.
