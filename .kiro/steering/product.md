# Product Overview

This is an AI companion application that provides conversational AI interactions through multiple interfaces (Chainlit web UI and WhatsApp). The companion uses LangGraph to orchestrate a multi-modal workflow supporting text conversations, image generation, and audio/speech interactions.

## Key Features

- Multi-modal interactions: text, image generation, and speech
- Long-term memory using Qdrant vector database
- Short-term conversation memory with automatic summarization
- Multiple deployment interfaces: web (Chainlit) and messaging (WhatsApp)
- Scheduled activities and context-aware responses
- Character-based personality system

## Architecture

The application uses a graph-based workflow (LangGraph) with nodes for:
- Memory extraction and injection
- Request routing (conversation/image/audio)
- Context injection
- Response generation
- Conversation summarization

## External Services

- Groq: LLM inference (text generation, vision, STT)
- ElevenLabs: Text-to-speech
- Together AI: Image generation (FLUX model)
- Qdrant: Vector database for long-term memory
