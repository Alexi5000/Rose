# TechTide Backstory

## What is Rose?

Rose is an AI wellness companion that communicates via WhatsApp. She provides empathetic, voice-first interactions for users seeking daily mental wellness support, guided breathing exercises, journaling prompts, and conversational check-ins.

## Tech Stack

- **LLM:** Groq (low-latency inference for real-time conversation)
- **Agent Orchestration:** LangGraph (stateful multi-step workflows, tool routing, memory management)
- **Voice Synthesis:** ElevenLabs (natural-sounding voice notes sent as WhatsApp audio messages)
- **Messaging:** WhatsApp Business API via webhook integration
- **Memory:** Persistent conversation memory with personality continuity across sessions

## Why TechTide Uses Rose

TechTide uses Rose as a reference implementation for voice-first AI companions in healthcare-adjacent verticals. The architecture demonstrates how to build compliant, empathetic AI agents that maintain long-term user relationships through familiar messaging channels.

Key patterns extracted from Rose and applied across TechTide projects:

- Voice-first UX over text-first (ElevenLabs integration patterns)
- Persistent memory and personality continuity (LangGraph state management)
- Low-latency inference for conversational feel (Groq routing)
- Webhook-driven messaging integration (WhatsApp Business API)
- Agent orchestration for multi-step wellness workflows

## Fork History

This repository was originally forked from `neural-maze/ava-whatsapp-agent-course` but has diverged heavily with 186 local commits of custom development. The fork now represents an effectively independent project with:

- Custom personality system and tone calibration
- Persistent memory architecture for long-term user relationships
- Voice synthesis pipeline with emotion-aware prosody
- Wellness-specific tool integrations (breathing timers, mood tracking, journaling)
- Production-hardened webhook handling and error recovery
