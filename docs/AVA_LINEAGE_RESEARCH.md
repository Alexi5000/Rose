# Ava Lineage Research

Last reviewed: July 6, 2026.

This note records the upstream Ava evidence used for Rose architecture decisions. It is intentionally separate from
planning artifacts so implementation PRs can cite research without editing `.planning/`.

## Upstream Repository

Original project: [neural-maze/ava-whatsapp-agent-course](https://github.com/neural-maze/ava-whatsapp-agent-course).

Live GitHub/API findings refreshed on July 6, 2026:

- Repository description: "Meet Ava, the WhatsApp Agent."
- Public repo, MIT license, default branch `main`.
- Created December 17, 2024; last pushed October 20, 2025; metadata updated July 4, 2026.
- 1,664 stars, 420 forks, 23 subscribers, 6 open issues/PRs.
- Language mix by bytes: Python 66,058; Jupyter Notebook 26,950; Batchfile 2,883; PowerShell 2,868; Dockerfile 1,068; Makefile 804.
- Upstream README frames Ava as a course project for WhatsApp, LangGraph, Qdrant memory, Groq, Whisper, ElevenLabs,
  Chainlit, Cloud Run, and WhatsApp API integration.

Local git evidence from `upstream/main`:

- 95 tracked files.
- Latest local upstream commit: `338fd68` (`Create run.bat`, June 29, 2025).
- Local history has 110 commits and the dominant author aliases are Miguel/MichaelisTrofficus and Jesus Copado.

## Contributors And Adjacent Repos

GitHub contributors API returned:

| Contributor | GitHub | Contributions | Notes |
| --- | --- | ---: | --- |
| MichaelisTrofficus | https://github.com/MichaelisTrofficus | 67 | Ava co-builder; README credits Miguel Otero Pedrido and The Neural Maze. |
| Jesus Copado | https://github.com/jesuscopado | 36 | Ava co-builder; adjacent voice-agent repos are directly relevant. |
| gullayeshwantkumarruler | https://github.com/gullayeshwantkumarruler | 3 | Added Windows run helpers and getting-started docs. |
| Excergic | https://github.com/Excergic | 1 | ElevenLabs TTS update. |
| carfer13 | https://github.com/carfer13 | 1 | Virtualenv setup clarification. |
| contributor | https://github.com/contributor | 1 | Docker build fix. |
| marceloacosta | https://github.com/marceloacosta | 1 | Intel Mac PyTorch/NumPy compatibility fix. |

Adjacent contributor repos worth respecting:

- Jesus Copado has public realtime voice projects including
  [samantha-os1-openai-realtime](https://github.com/jesuscopado/samantha-os1-openai-realtime),
  [local-voice-ai-agent](https://github.com/jesuscopado/local-voice-ai-agent), and
  [fastrtc-groq-voice-agent](https://github.com/jesuscopado/fastrtc-groq-voice-agent).
- MichaelisTrofficus has Python/ML repos including
  [hampel_filter](https://github.com/MichaelisTrofficus/hampel_filter) and public forks of agent/ML infrastructure.

Practical implication for Rose: keep PRs small, provider-oriented, documented, and testable. The original builder
ecosystem values course clarity, reproducible setup, and practical voice-agent demos.

## Upstream PR Signal

The open upstream PR list refreshed through the GitHub API included:

| PR | Signal for Rose |
| --- | --- |
| [#49 Stop logging WhatsApp response payloads](https://github.com/neural-maze/ava-whatsapp-agent-course/pull/49) | Privacy direction: redact raw payloads, transcripts, memory text, and exception text by default. |
| [#47 fixing files for chainlit execution](https://github.com/neural-maze/ava-whatsapp-agent-course/pull/47) | Treat Chainlit docs/code as lineage unless Rose actively supports that surface again. |
| [#46 Add chainlit translations to gitignore](https://github.com/neural-maze/ava-whatsapp-agent-course/pull/46) | Keep generated/local artifacts out of PRs. |
| [#44 fix: replace HumanMessage with AIMessage for scenario_message in image_node](https://github.com/neural-maze/ava-whatsapp-agent-course/pull/44) | Preserve LangGraph message-type correctness when porting graph ideas. |
| [#43 Fix: updated deprecated Groq models in settings.py](https://github.com/neural-maze/ava-whatsapp-agent-course/pull/43) | Keep provider model names configurable and reviewed for deprecations. |

Do not copy or credit an open PR as merged behavior. Use it as live ecosystem signal only after checking state.

## Notebook Inventory

Rose currently carries two Ava notebooks:

| Notebook | Size | Kernel | Language | Cells | Markdown | Code | Outputs | Output bytes | Heading | Large | Large outputs |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| `notebooks/character_card.ipynb` | 20244 | .venv | python | 13 | 6 | 7 | 2 | 433 | Understanding Ava's character card | no | no |
| `notebooks/router.ipynb` | 6677 | .venv | python | 13 | 8 | 5 | 3 | 434 | How does the router node work? | no | no |

Use:

```bash
python scripts/notebook_inventory.py --markdown
```

For future large notebooks, reviewers should inspect inventory first, then open targeted cells. Avoid committing
execution outputs unless the notebook is explicitly meant to preserve them. Use `--fail-on-large` for size gates and
`--fail-on-large-output` when a PR should reject embedded outputs.

## 2026 Voice-Agent Pattern Check

Current official docs and ecosystem references point to two valid architectures:

- Live speech-to-speech sessions for natural low-latency voice, barge-in, turn taking, and realtime tool use.
  OpenAI's voice-agent docs recommend live audio for agents that need immediate conversation and interruptions, with
  WebRTC as the usual browser path.
- Chained STT -> LLM -> TTS pipelines when the app needs stronger control over transcript handling, deterministic
  safety gates, durable text, and existing text-agent reuse.

July 2026 refresh:

- OpenAI's May 2026 voice model announcement positions GPT-Realtime-2 for harder realtime conversations,
  GPT-Realtime-Translate for live multilingual speech, and GPT-Realtime-Whisper for streaming STT. This supports a
  future live-session provider, but does not remove Rose's need for explicit safety and memory gates.
- LiveKit's current turn-taking docs emphasize VAD plus endpointing, semantic turn completion, preemptive generation,
  background voice cancellation, and speech scheduling. Its July 2026 Turn Detector v1 announcement is especially
  relevant because it fuses acoustic and semantic cues before final transcript availability.
- The upstream Ava PR list still shows provider deprecation and logging hygiene work as active community concerns.

Rose is currently a cascaded/chained voice agent. That is still the right base for a healing companion because safety,
memory consent, transcript cleanup, and privacy redaction need explicit checkpoints. The next state-of-art move is not
to abandon the chain, but to make it feel live:

- stream partial STT into a conservative turn gate;
- stream LLM text into sentence or phrase TTS chunks;
- preserve reliable barge-in and cancellation;
- record mic-to-first-audio and total turn latency;
- keep a future WebRTC/live-session provider path isolated behind provider boundaries.

Sources:

- OpenAI Voice agents guide: https://developers.openai.com/api/docs/guides/voice-agents
- OpenAI Realtime and audio guide: https://developers.openai.com/api/docs/guides/realtime
- OpenAI voice model announcement: https://openai.com/index/advancing-voice-intelligence-with-new-models-in-the-api/
- LiveKit Agents docs: https://docs.livekit.io/agents/
- LiveKit turns overview: https://docs.livekit.io/agents/logic/turns/
- LiveKit Turn Detector v1 announcement: https://livekit.com/blog/solving-end-of-turn-detection
- Pipecat introduction: https://docs.pipecat.ai/overview/introduction

## Build Rules From The Research

- Preserve Ava lineage clearly, but do not keep WhatsApp/Chainlit/image-generation docs presented as active Rose
  features unless the code path is active.
- Keep Groq and ElevenLabs defaults because they are part of Ava's teaching lineage and Rose's current working setup.
- Keep OpenRouter as LLM fallback or alternate primary provider; do not turn it into a hidden dependency.
- Treat realtime voice as an optional provider/transport lane rather than a rewrite of the safety-first cascaded path.
- Make notebook additions reviewable through inventory and size/output checks.
- Keep privacy fixes high priority; upstream PR activity shows payload logging is a shared concern.
