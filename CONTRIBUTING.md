# Contributing to Rose

Thank you for improving Rose. This project values careful changes that preserve the voice-first experience, LangGraph orchestration, memory retrieval, multimodal routing, and provider boundaries.

## Development setup

| Step | Command | Purpose |
|---:|---|---|
| 1 | `cp .env.example .env` | Create local configuration from the example file. |
| 2 | `uv sync --extra test` | Install Python 3.12 dependencies and test tooling. |
| 3 | `make setup-dev` | Create local memory and generated artifact directories. |
| 4 | `cd frontend && npm install` | Install React frontend dependencies. |
| 5 | `make format-check && make lint-check` | Run formatting and lint checks before opening a PR. |

## Pull request guidelines

Keep pull requests focused, explain the user-visible behavior change, and call out any impact on memory, audio, provider configuration, or logging. If a change touches provider payloads, transcripts, or memory records, include a privacy note in the PR description.

## Architecture guidelines

| Boundary | Expected pattern |
|---|---|
| Voice interface | Keep recording, buffering, upload, transcription, graph invocation, and TTS response handling explicit. |
| LangGraph | Add graph behavior through nodes and routing functions rather than mixing orchestration into web routes. |
| Memory | Keep extraction, retrieval, summarization, and long-term storage paths modular and testable. |
| Providers | Keep OpenAI-compatible, Groq, ElevenLabs, Qdrant, and PostgreSQL concerns behind settings or provider modules. |
| Frontend | Reuse shared API and audio utilities instead of duplicating voice-session logic across components. |

## Documentation expectations

Documentation should be clear, linked, and current. Avoid em dashes in repository files. When adding major capabilities, update the README, architecture documentation, and release notes together.
