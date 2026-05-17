<!-- Rose full repository refresh 2026-05-17 -->
# Security Policy

Rose is a voice-first AI companion that may process sensitive conversational, audio, and memory data. Security reports should be handled privately and with care.

## Supported versions

| Version | Support status |
|---|---|
| 2.x | Supported for security fixes and responsible disclosure review. |
| 1.x and earlier | Best-effort review only. |

## Reporting a vulnerability

Please do not open a public issue for a suspected vulnerability. Instead, contact the repository owner privately through GitHub or use GitHub security advisories if enabled for the repository.

A useful report includes the affected component, reproduction steps, expected impact, and any relevant logs with secrets removed. Please never include API keys, user audio, private transcripts, or raw memory exports in public channels.

## Security principles

| Principle | Rose expectation |
|---|---|
| Least exposure | Logs should avoid raw provider payloads, headers, transcripts, and memory records unless explicitly redacted. |
| Secret isolation | Provider keys belong in environment variables or deployment secret stores, never in source control. |
| Provider boundaries | OpenAI-compatible, Groq, ElevenLabs, Qdrant, PostgreSQL, Chainlit, and web interfaces should remain isolated behind settings and module boundaries. |
| Memory care | Stored memories should be treated as sensitive user data and reviewed with data retention requirements before production use. |

## Dependency and deployment hygiene

Run Python dependency checks in the project Python 3.12 environment and rebuild frontend dependencies from lockfiles where available. Before deployment, verify that `.env` values are configured only in the deployment platform and that generated Chainlit files, local memory folders, and audio artifacts are ignored.
