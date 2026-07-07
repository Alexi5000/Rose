# Upstream Lineage Research

Last checked: 2026-07-06

Rose is forked from the Ava WhatsApp agent course and should keep upstream lineage visible while evolving into a
voice-first emotional-support companion.

## Source Repositories

- Rose fork: https://github.com/Alexi5000/Rose
- Ava upstream: https://github.com/neural-maze/ava-whatsapp-agent-course

## Upstream Snapshot

GitHub API snapshot on 2026-07-06:

- Repository: `neural-maze/ava-whatsapp-agent-course`
- Description: "Meet Ava, the WhatsApp Agent"
- License: MIT
- Default branch: `main`
- Stars: 1664
- Forks: 420
- Open issues count: 6
- Last repository update: 2026-07-04
- Last push: 2025-10-20

## Upstream Contributors

GitHub contributors API snapshot on 2026-07-06:

| Contributor | Contributions | Profile |
| --- | ---: | --- |
| MichaelisTrofficus | 67 | https://github.com/MichaelisTrofficus |
| jesuscopado | 36 | https://github.com/jesuscopado |
| gullayeshwantkumarruler | 3 | https://github.com/gullayeshwantkumarruler |
| Excergic | 1 | https://github.com/Excergic |
| carfer13 | 1 | https://github.com/carfer13 |
| contributor | 1 | https://github.com/contributor |
| marceloacosta | 1 | https://github.com/marceloacosta |

## Open Upstream Work To Watch

Open upstream PRs on 2026-07-06:

| PR | Title | Author | Why Rose Cares |
| --- | --- | --- | --- |
| #49 | Stop logging WhatsApp response payloads | a692570 | Reinforces Rose's no raw payload/transcript logging posture. |
| #47 | fixing files for chainlit execution | rafaelgildin | Historical Chainlit compatibility only; Rose's active surface is React/FastAPI voice. |
| #46 | Add chainlit translations to gitignore | ysntns | Historical Chainlit hygiene only; keep out of active Rose runtime unless preserving lineage. |
| #44 | fix: replace HumanMessage with AIMessage for scenario_message in image_node | TensorCruncher | Watch message-type correctness if frozen image paths are revived. |
| #43 | Fix: updated deprecated Groq models in settings.py | Shaheerabdullah1 | Aligns with Groq's 2026 model deprecation guidance; Rose now defaults to GPT-OSS models. |

Open upstream issue on 2026-07-06:

- #40 "Together AI has terminated the free tier" by KishanPipariya. Rose should avoid restoring Together image flows
  as an active dependency without a current provider review.

## 2026 Provider Notes

Groq's official deprecation page says `llama-3.1-8b-instant` and `llama-3.3-70b-versatile` are scheduled for
shutdown on 2026-08-16 for free/developer-tier usage, with `openai/gpt-oss-20b` and `openai/gpt-oss-120b` as
recommended replacements.

Rose defaults now reflect that direction:

- Primary Groq LLM: `openai/gpt-oss-120b`
- Small/memory Groq LLM: `openai/gpt-oss-20b`
- Groq STT: `whisper-large-v3-turbo`
- OpenRouter fallback model: `openai/gpt-oss-120b`

## PR Policy From Upstream Research

- Treat upstream PRs as design signals, not automatic patches.
- Port only the intent that matches Rose's active architecture.
- Prefer provider-agnostic selectors over hardcoded model IDs in business logic.
- Keep privacy fixes as durable tests, especially around logs, payloads, transcripts, memory text, audio, and secrets.
- Preserve Ava credit in README and docs while making Rose's voice-first safety posture distinct.
