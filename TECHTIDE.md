# TechTide Backstory

## What is Rose?

Rose is a voice-first AI emotional support companion that runs as a browser voice loop (React frontend, FastAPI WebSocket backend). She supports grounding, reflective conversation, and continuity across sessions, with deterministic crisis-safety routing. The upstream WhatsApp interface is a frozen feature in this fork (see `src/ai_companion/settings.py`).

## Tech Stack

- **LLM:** Groq (low-latency inference for real-time conversation)
- **Agent Orchestration:** LangGraph (stateful multi-step workflows, tool routing, memory management)
- **Voice Synthesis:** ElevenLabs server-side text to speech, with text-only and browser-speech degraded modes
- **Interface:** Browser microphone and WebSocket audio turns (the WhatsApp Business API webhook from upstream Ava is frozen, not active)
- **Memory:** Qdrant-backed long-term memory with session-only, export, and forget controls

## Why TechTide Uses Rose

TechTide uses Rose as a reference implementation for voice-first AI companions in healthcare-adjacent verticals. The architecture demonstrates how to build safety-bounded, empathetic voice agents that keep memory under the person's control.

Key patterns extracted from Rose and applied across TechTide projects:

- Voice-first UX over text-first (ElevenLabs integration patterns)
- Persistent memory and personality continuity (LangGraph state management)
- Low-latency inference for conversational feel (Groq routing)
- Provider fallbacks and degraded modes (Groq to OpenRouter, ElevenLabs to text-only)
- Agent orchestration with a deterministic safety layer ahead of generation (LangGraph)

## Fork History

This repository was forked from `neural-maze/ava-whatsapp-agent-course` on 2025-10-20. As of 2026-10-20 the fork is 11 commits ahead of and 0 behind upstream `main` (405 files changed). The fork-only work is:

- Browser voice loop (React frontend, FastAPI WebSocket route, turn detection, interruption handling)
- Deterministic crisis-safety routing and response-quality checks
- Qdrant long-term memory with session-only, export, and forget controls
- Provider interfaces with fallbacks (Groq, OpenRouter, Deepgram, ElevenLabs)
- Administrator credentials on memory and monitoring routes (2026-10-20 security pass)

See the README `Upstream` section for the commit-level list.
