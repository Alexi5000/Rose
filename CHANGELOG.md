<!-- Rose full repository refresh 2026-05-17 -->
# Changelog

All notable changes to Rose are documented in this file.

## v2.1.0 - Release Metadata And Public Identity Refresh

Rose v2.1.0 aligns the public About surface, package metadata, runtime version, health responses, monitoring release fallback, and documentation examples around a single release version.

| Area | What changed |
|---|---|
| Public identity | Updated stale legacy product labels to Rose or Rose Voice Companion API across source, tests, and docs. |
| Version metadata | Normalized Python package, uv lock, frontend package, OpenAPI metadata, health responses, and production env examples to `2.1.0`. |
| API documentation | Split release version from the stable `/api/v1` route namespace so docs no longer confuse app release with API route version. |
| Frontend polish | Updated the browser title from the scaffold default to `Rose`. |
| Release readiness | Added v2.1.0 release notes for GitHub release publication. |

## v2.0.0 - State-of-the-Art Rose Buildout

Rose v2.0.0 modernizes the repository as a voice-first, memory-aware AI companion built around LangGraph orchestration, multimodal routing, and clear provider boundaries. This release manually ports the useful intent of five open community pull requests while preserving the current Python, FastAPI, Chainlit, Qdrant, and React stack.

| Area | What changed |
|---|---|
| Community PR integration | Integrated the intent of PRs #43, #44, #46, #47, and #49 with contributor credit in `CONTRIBUTORS.md` and `docs/UPSTREAM_PR_INTEGRATION.md`. |
| Architecture | Added `docs/ARCHITECTURE_PATTERNS.md` to map the Ava-inspired voice flow, LangGraph graph, memory extraction, retrieval, multimodal routing, audio buffering, and provider boundaries onto Rose. |
| Safety and privacy | Reduced unsafe payload logging, added repository hygiene coverage, and kept response payloads out of production route logs. |
| Provider configuration | Updated Groq defaults away from deprecated model identifiers and strengthened settings validation. |
| Frontend foundation | Added reusable API and audio utility modules for the React voice interface. |
| Repository polish | Added governance files, release notes, contributor credits, and stricter quality targets that no longer require `.env` for format or lint checks. |

### Community acknowledgments

This release credits the contributors whose pull requests improved Rose reliability, execution hygiene, and provider compatibility.

| Contributor | Pull request | Contribution |
|---|---:|---|
| @a692570 | #49 | Removed sensitive WhatsApp response payload logging intent. |
| @rafaelgildin | #47 | Improved Chainlit execution and local development compatibility intent. |
| @ysntns | #46 | Added Chainlit generated translations ignore coverage intent. |
| @TensorCruncher | #44 | Corrected assistant-role message semantics for generated image and scenario responses intent. |
| @Shaheerabdullah1 | #43 | Updated deprecated Groq model defaults intent. |

### Verification notes

The repository hygiene pass confirmed zero em dashes, no obvious secret-like tokens, and no stale upstream identity terms in the intended source and documentation scan scope. Python tests were not executed in the host environment because `pytest` is not installed for the available Python 3.11 interpreter, while the project declares Python 3.12 tooling through `uv`.
