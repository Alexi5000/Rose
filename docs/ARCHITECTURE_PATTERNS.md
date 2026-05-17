# Rose Architecture Patterns

Rose follows the voice-first, stateful companion architecture represented in the provided Ava reference while adapting the implementation to the current Python, LangGraph, Chainlit, React, and provider-gateway stack.

| Reference pattern | Rose implementation commitment |
|---|---|
| Voice-first entry point | The React voice interface manages microphone capture, VAD, audio buffering, transcription submission, and barge-in playback control. |
| Stateful graph orchestration | LangGraph remains the orchestration spine for routing user context, generated responses, multimodal tasks, and memory operations. |
| Memory extraction and recall | Rose keeps long-term memory and session context separated, with explicit retrieval paths before response generation. |
| Multimodal routing | Text, image, audio, and scenario workflows are documented as separate nodes with provider boundaries so each model can be swapped cleanly. |
| Activity context | Current activity and conversation state are treated as first-class context inputs rather than prompt-only side channels. |
| Audio buffer discipline | Frontend audio utilities isolate RMS, analyser, recording, playback, and fallback synthesis behavior. |
| Provider boundaries | Settings centralize Groq, ElevenLabs, OpenAI-compatible, and local runtime options without hardcoding provider secrets. |
| Human-designed repository surface | README graphics, diagrams, links, contributor credit, release notes, and quality instructions describe the same design system that the code follows. |

This document is used as a coverage checklist during repository cleanup so visual polish does not drift away from the system architecture.
