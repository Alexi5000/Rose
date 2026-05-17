<!-- Rose full repository refresh 2026-05-17 -->
# Rose v2.0.0 Release Notes

Rose v2.0.0 is a major repository polish and architecture-alignment release. It positions Rose as a voice-first AI companion with clear LangGraph orchestration, memory extraction and retrieval, multimodal routing, audio buffering, and provider boundaries.

## Highlights

| Theme | Release impact |
|---|---|
| Voice-first product flow | Documents and preserves the microphone-to-response loop through FastAPI, Chainlit, LangGraph, memory, and TTS boundaries. |
| LangGraph orchestration | Keeps graph nodes responsible for routing, assistant response generation, image handling, and memory updates. |
| Memory architecture | Clarifies short-term state, long-term Qdrant retrieval, summarization, and hierarchical memory organization. |
| Multimodal routing | Preserves routing across text, voice, image, and generated media flows. |
| Provider boundaries | Keeps OpenAI-compatible, Groq, ElevenLabs, Qdrant, and web interfaces isolated behind module and settings boundaries. |
| Community integration | Manually ports all five open PR intents without applying stale patches over the evolved codebase. |

## Integrated community PRs

| PR | Contributor | Integrated result |
|---:|---|---|
| #49 | @a692570 | Production route logging no longer exposes raw WhatsApp response payloads. |
| #47 | @rafaelgildin | Chainlit execution compatibility and generated artifact handling are preserved. |
| #46 | @ysntns | Chainlit translation artifacts are ignored. |
| #44 | @TensorCruncher | Assistant scenario and image responses keep assistant-role semantics. |
| #43 | @Shaheerabdullah1 | Groq defaults use current supported model names. |

## Upgrade notes

The project version is now `2.0.0`. Development workflows should prefer `uv sync --extra test` for Python tooling and `npm install` inside `frontend/` for the React interface. Quality targets no longer require an existing `.env` file.

## Known environment note

The sandbox host used for this buildout provides Python 3.11, while Rose declares Python 3.12. Full test execution should run in a Python 3.12 environment with `uv sync --extra test` before production deployment.
