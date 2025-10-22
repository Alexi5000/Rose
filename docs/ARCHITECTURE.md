# Architecture Documentation: Rose the Healer Shaman

This document provides comprehensive architecture diagrams and explanations for the Rose application.

## Table of Contents

- [System Overview](#system-overview)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [Deployment Architecture](#deployment-architecture)
- [Memory System Architecture](#memory-system-architecture)
- [API Architecture](#api-architecture)
- [Security Architecture](#security-architecture)

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interfaces                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │  Web Interface   │  │  Voice Interface │  │  WhatsApp     │ │
│  │  (Chainlit)      │  │  (FastAPI)       │  │  (Frozen)     │ │
│  └────────┬─────────┘  └────────┬─────────┘  └───────┬───────┘ │
└───────────┼────────────────────┼────────────────────┼──────────┘
            │                    │                    │
            └────────────────────┼────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│                      Application Layer                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              LangGraph Workflow Engine                    │  │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────────────┐ │  │
│  │  │ Memory │→ │ Router │→ │Context │→ │    Response    │ │  │
│  │  │Extract │  │        │  │Inject  │  │   Generation   │ │  │
│  │  └────────┘  └────────┘  └────────┘  └────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

            │                    │                    │
┌───────────▼────────────────────▼────────────────────▼───────────┐
│                      Service Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Speech     │  │    Memory    │  │      Character       │  │
│  │   Module     │  │    Module    │  │      Module          │  │
│  │  - STT       │  │  - Short-term│  │  - Prompts           │  │
│  │  - TTS       │  │  - Long-term │  │  - Personality       │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
            │                    │                    │
┌───────────▼────────────────────▼────────────────────▼───────────┐
│                    External Services                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │    Groq      │  │  ElevenLabs  │  │      Qdrant          │  │
│  │  - LLM       │  │  - TTS       │  │  - Vector DB         │  │
│  │  - STT       │  │              │  │  - Long-term Memory  │  │
│  │  - Vision    │  │              │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
            │                    │                    │
┌───────────▼────────────────────▼────────────────────▼───────────┐
│                    Data Persistence                              │
│  ┌──────────────────────────────┐  ┌──────────────────────────┐│
│  │      SQLite Database         │  │   Temporary Storage      ││
│  │  - Conversation State        │  │   - Audio Files          ││
│  │  - Session Checkpoints       │  │   - Generated Images     ││
│  └──────────────────────────────┘  └──────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Frontend**:
- React 18 with TypeScript
- Vite for build tooling
- Framer Motion for animations
- Web Audio API for voice recording

**Backend**:
- FastAPI for REST API
- Chainlit for web interface
- LangGraph for workflow orchestration
- LangChain for LLM integration

**AI Services**:
- Groq: LLM (llama-3.3-70b), STT (whisper), Vision
- ElevenLabs: TTS (eleven_flash_v2_5)
- Together AI: Image generation (FLUX.1-schnell)

**Data Storage**:
- SQLite: Short-term memory and checkpoints
- Qdrant: Long-term vector memory
- File system: Temporary audio and images

**Infrastructure**:
- Docker for containerization
- Railway for deployment
- uv for Python package management

---

## Component Architecture

### LangGraph Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph State Machine                       │
│                                                                  │
│  START                                                           │
│    │                                                             │
│    ▼                                                             │
│  ┌──────────────────┐                                           │
│  │ Memory Extraction│  Extract relevant memories from input     │
│  └────────┬─────────┘                                           │
│           │                                                      │
│           ▼                                                      │
│  ┌──────────────────┐                                           │
│  │     Router       │  Determine workflow type:                 │
│  │                  │  - conversation                           │
│  │                  │  - image                                  │
│  │                  │  - audio                                  │
│  └────────┬─────────┘                                           │
│           │                                                      │
│     ┌─────┴─────┬──────────────┐                               │
│     │           │              │                                │
│     ▼           ▼              ▼                                │
│  ┌──────┐  ┌────────┐  ┌──────────┐                            │
│  │ Text │  │ Image  │  │  Audio   │                            │
│  │ Flow │  │  Flow  │  │   Flow   │                            │
│  └───┬──┘  └───┬────┘  └────┬─────┘                            │
│      │         │            │                                   │
│      └─────────┴────────────┘                                   │
│                 │                                                │
│                 ▼                                                │
│  ┌──────────────────────┐                                       │
│  │  Context Injection   │  Inject memories and context          │
│  └──────────┬───────────┘                                       │
│             │                                                    │
│             ▼                                                    │
│  ┌──────────────────────┐                                       │
│  │ Response Generation  │  Generate response using LLM          │
│  └──────────┬───────────┘                                       │
│             │                                                    │
│             ▼                                                    │
│  ┌──────────────────────┐                                       │
│  │  Memory Injection    │  Store new memories                   │
│  └──────────┬───────────┘                                       │
│             │                                                    │
│             ▼                                                    │
│  ┌──────────────────────┐                                       │
│  │   Summarization      │  Summarize if threshold reached       │
│  └──────────┬───────────┘                                       │
│             │                                                    │
│             ▼                                                    │
│           END                                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Module Structure

```
src/ai_companion/
│
├── core/                    # Core utilities
│   ├── exceptions.py        # Custom exceptions
│   ├── prompts.py           # System prompts
│   ├── resilience.py        # Circuit breakers
│   ├── backup.py            # Backup system
│   └── session_cleanup.py   # Session management
│
├── graph/                   # LangGraph workflow
│   ├── graph.py             # Graph construction
│   ├── state.py             # State schema
│   ├── nodes.py             # Node implementations
│   └── edges.py             # Conditional edges
│
├── modules/                 # Feature modules
│   ├── speech/
│   │   ├── speech_to_text.py
│   │   └── text_to_speech.py
│   ├── memory/
│   │   ├── short_term_memory.py
│   │   └── long_term_memory.py
│   └── image/
│       └── image_generation.py
│
└── interfaces/              # User interfaces
    ├── web/                 # FastAPI voice interface
    │   ├── app.py
    │   ├── routes/
    │   ├── middleware.py
    │   └── models.py
    ├── chainlit/            # Chainlit chat interface
    │   └── app.py
    └── whatsapp/            # WhatsApp (frozen)
        └── webhook_endpoint.py
```

---

## Data Flow

### Voice Processing Flow

```
1. User Input (Frontend)
   │
   ▼
2. Audio Recording (Web Audio API)
   │
   ▼
3. POST /api/voice/process
   │
   ▼
4. Audio Validation (size, format)
   │
   ▼
5. Speech-to-Text (Groq Whisper)
   │
   ▼
6. LangGraph Workflow
   │
   ├─► Memory Extraction (Qdrant)
   │
   ├─► Router (determine type)
   │
   ├─► Context Injection
   │
   ├─► Response Generation (Groq LLM)
   │
   ├─► Memory Injection (Qdrant)
   │
   └─► Summarization (if needed)
   │
   ▼
7. Text-to-Speech (ElevenLabs)
   │
   ▼
8. Audio File Storage (/tmp)
   │
   ▼
9. Response to Frontend
   │
   ▼
10. Audio Playback (Frontend)
```

### Memory Flow

```
User Message
    │
    ▼
┌─────────────────────┐
│ Short-Term Memory   │  Store in SQLite
│ (Conversation State)│  - Last N messages
└──────────┬──────────┘  - Session context
           │
           ▼
┌─────────────────────┐
│ Memory Extraction   │  Identify important info
│                     │  - Facts about user
└──────────┬──────────┘  - Preferences
           │             - Emotional state
           ▼
┌─────────────────────┐
│ Long-Term Memory    │  Store in Qdrant
│ (Vector Database)   │  - Embedded memories
└──────────┬──────────┘  - Semantic search
           │
           ▼
┌─────────────────────┐
│ Memory Retrieval    │  Retrieve relevant memories
│                     │  - Top K similar
└──────────┬──────────┘  - Context injection
           │
           ▼
┌─────────────────────┐
│ Response Generation │  Use memories in prompt
│                     │  - Personalized response
└─────────────────────┘  - Contextual awareness
```

---

## Deployment Architecture

### Railway Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                         Railway Platform                         │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Build Process                            │ │
│  │  1. Install Python dependencies (uv sync)                  │ │
│  │  2. Build React frontend (npm run build)                   │ │
│  │  3. Create Docker image                                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   Runtime Container                         │ │
│  │                                                             │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │  FastAPI Application (Port 8080)                     │ │ │
│  │  │  - Serves React frontend (/)                         │ │ │
│  │  │  - Serves API endpoints (/api/*)                     │ │ │
│  │  │  - Health checks (/api/health)                       │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                                                             │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │  Persistent Volume (/app/data)                       │ │ │
│  │  │  - SQLite database (memory.db)                       │ │ │
│  │  │  - Backups directory                                 │ │ │
│  │  │  - Temporary audio files                             │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                                                             │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │  Background Jobs                                     │ │ │
│  │  │  - Audio cleanup (hourly)                            │ │ │
│  │  │  - Session cleanup (daily)                           │ │ │
│  │  │  - Database backup (daily)                           │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   External Connections                      │ │
│  │  - Groq API (LLM, STT)                                     │ │
│  │  - ElevenLabs API (TTS)                                    │ │
│  │  - Qdrant Cloud (Vector DB)                               │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Resource Allocation

```
┌─────────────────────────────────────────────────────────────────┐
│                      Resource Limits                             │
│                                                                  │
│  Memory: 512MB - 8GB (Railway)                                  │
│  ├─ Application: ~200-400MB baseline                            │
│  ├─ LangGraph State: ~50-100MB                                  │
│  ├─ Audio Processing: ~50MB per request                         │
│  └─ Buffer: ~100MB                                              │
│                                                                  │
│  CPU: Shared (Railway)                                          │
│  ├─ STT Processing: High CPU                                    │
│  ├─ Vector Search: Medium CPU                                   │
│  └─ API Requests: Low CPU                                       │
│                                                                  │
│  Disk: 1GB+ Persistent Volume                                   │
│  ├─ SQLite Database: ~10-100MB                                  │
│  ├─ Backups: ~50-500MB                                          │
│  └─ Temporary Files: ~100-500MB                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Memory System Architecture

### Two-Tier Memory System

```
┌─────────────────────────────────────────────────────────────────┐
│                    Short-Term Memory (SQLite)                    │
│                                                                  │
│  Purpose: Conversation state and recent context                 │
│  Storage: /app/data/memory.db                                   │
│  Retention: Current session + recent sessions                   │
│                                                                  │
│  Schema:                                                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Checkpoints Table                                          │ │
│  │ - thread_id (session identifier)                           │ │
│  │ - checkpoint_id (state version)                            │ │
│  │ - parent_checkpoint_id (previous state)                    │ │
│  │ - checkpoint (serialized state)                            │ │
│  │ - metadata (timestamps, etc.)                              │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Operations:                                                     │
│  - Save state after each workflow step                          │
│  - Load state when resuming conversation                        │
│  - Cleanup old sessions (7+ days)                               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   Long-Term Memory (Qdrant)                      │
│                                                                  │
│  Purpose: Semantic memory and user knowledge                    │
│  Storage: Qdrant Cloud                                          │
│  Retention: Permanent (until manually deleted)                  │
│                                                                  │
│  Collection Structure:                                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Vectors                                                    │ │
│  │ - Embedding: 384-dimensional (sentence-transformers)      │ │
│  │ - Payload:                                                 │ │
│  │   - text: Original memory text                            │ │
│  │   - session_id: Associated session                        │ │
│  │   - timestamp: When created                               │ │
│  │   - memory_type: fact/preference/emotion                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Operations:                                                     │
│  - Extract memories from conversations                          │
│  - Embed memories using sentence-transformers                   │
│  - Store vectors in Qdrant                                      │
│  - Retrieve top-K similar memories (K=3)                        │
│  - Inject retrieved memories into context                       │
└─────────────────────────────────────────────────────────────────┘

Memory Lifecycle:
1. User sends message
2. Store in short-term (SQLite checkpoint)
3. Extract important information
4. Embed and store in long-term (Qdrant)
5. On next message, retrieve relevant memories
6. Inject into LLM context
7. Generate personalized response
```

---

## API Architecture

### REST API Endpoints

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Routes                               │
│                                                                  │
│  Health & Status                                                 │
│  ├─ GET  /api/health          Health check with service status  │
│  └─ GET  /                    Serve React frontend              │
│                                                                  │
│  Session Management                                              │
│  └─ POST /api/session/start   Create new conversation session   │
│                                                                  │
│  Voice Processing                                                │
│  ├─ POST /api/voice/process   Process voice input               │
│  └─ GET  /api/voice/audio/:id Retrieve generated audio          │
│                                                                  │
│  Static Files                                                    │
│  └─ GET  /assets/*            Frontend assets (JS, CSS, images) │
└─────────────────────────────────────────────────────────────────┘
```

### Request/Response Flow

```
POST /api/voice/process
│
├─ Request:
│  ├─ Headers:
│  │  └─ Content-Type: multipart/form-data
│  └─ Body:
│     ├─ audio: <audio file>
│     └─ session_id: <uuid>
│
├─ Processing:
│  ├─ 1. Validate audio (size, format)
│  ├─ 2. Save to temporary storage
│  ├─ 3. Speech-to-text (Groq)
│  ├─ 4. LangGraph workflow
│  ├─ 5. Text-to-speech (ElevenLabs)
│  └─ 6. Save audio response
│
└─ Response:
   ├─ Status: 200 OK
   └─ Body:
      ├─ text: "Response text"
      ├─ audio_url: "/api/voice/audio/<id>"
      ├─ session_id: "<uuid>"
      └─ duration_ms: 2500
```

### Middleware Stack

```
Request
  │
  ▼
┌─────────────────────┐
│ CORS Middleware     │  Allow frontend origins
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Request ID          │  Add unique request ID
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Rate Limiting       │  10 requests/minute per IP
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Security Headers    │  CSP, HSTS, X-Frame-Options
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Logging             │  Structured JSON logs
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Route Handler       │  Process request
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Error Handler       │  Catch and format errors
└──────────┬──────────┘
           ▼
        Response
```

---

## Security Architecture

### Security Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                      Security Architecture                       │
│                                                                  │
│  Layer 1: Network Security                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ - HTTPS/TLS encryption (Railway automatic)                │ │
│  │ - CORS restrictions (environment-based)                    │ │
│  │ - Rate limiting (10 req/min per IP)                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Layer 2: Application Security                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ - Input validation (Pydantic models)                       │ │
│  │ - Audio size limits (10MB)                                 │ │
│  │ - File type validation                                     │ │
│  │ - Request size limits                                      │ │
│  │ - Security headers (CSP, HSTS, X-Frame-Options)           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Layer 3: Data Security                                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ - Environment variable encryption (Railway)                │ │
│  │ - API key rotation procedures                              │ │
│  │ - Temporary file cleanup                                   │ │
│  │ - Secure file permissions                                  │ │
│  │ - Database backups                                         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Layer 4: External Service Security                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ - Circuit breakers (prevent cascading failures)           │ │
│  │ - Retry with exponential backoff                           │ │
│  │ - Timeout configuration                                    │ │
│  │ - Error message sanitization                               │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Authentication Flow (Future)

```
Currently: No authentication (public access)

Future Implementation:
┌─────────────────────┐
│ User Login          │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ JWT Token Generation│
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Token in Header     │  Authorization: Bearer <token>
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Token Validation    │  Verify signature and expiry
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ User Context        │  Extract user ID from token
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Request Processing  │  Associate with user
└─────────────────────┘
```

---

## Resilience Architecture

### Circuit Breaker Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                    Circuit Breaker States                        │
│                                                                  │
│  CLOSED (Normal Operation)                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ - All requests pass through                                │ │
│  │ - Track failure count                                      │ │
│  │ - If failures > threshold (5): Open circuit                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                          │                                       │
│                          ▼ (5 failures)                          │
│  OPEN (Failing Fast)                                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ - Reject requests immediately                              │ │
│  │ - Return fallback response                                 │ │
│  │ - Wait for recovery timeout (60s)                          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                          │                                       │
│                          ▼ (after 60s)                           │
│  HALF-OPEN (Testing)                                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ - Allow limited requests                                   │ │
│  │ - If success: Close circuit                                │ │
│  │ - If failure: Open circuit again                           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                          │                                       │
│                          ▼ (success)                             │
│                      CLOSED                                      │
└─────────────────────────────────────────────────────────────────┘

Applied to:
- Groq API calls (LLM, STT)
- ElevenLabs API calls (TTS)
- Qdrant operations (vector search)
```

### Retry Strategy

```
Request to External Service
  │
  ▼
┌─────────────────────┐
│ Attempt 1           │
└──────────┬──────────┘
           │
    Success? ──Yes──> Return Result
           │
          No
           ▼
┌─────────────────────┐
│ Wait 1 second       │  Exponential backoff
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Attempt 2           │
└──────────┬──────────┘
           │
    Success? ──Yes──> Return Result
           │
          No
           ▼
┌─────────────────────┐
│ Wait 2 seconds      │  Exponential backoff
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Attempt 3           │
└──────────┬──────────┘
           │
    Success? ──Yes──> Return Result
           │
          No
           ▼
┌─────────────────────┐
│ Return Error        │  Circuit breaker may open
└─────────────────────┘
```

---

## Monitoring Architecture

### Observability Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                      Logging Architecture                        │
│                                                                  │
│  Application Logs                                                │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Structured JSON Logs                                       │ │
│  │ {                                                          │ │
│  │   "timestamp": "2024-01-15T10:30:00Z",                    │ │
│  │   "level": "INFO",                                         │ │
│  │   "request_id": "abc-123",                                │ │
│  │   "session_id": "xyz-789",                                │ │
│  │   "message": "Voice processing completed",                │ │
│  │   "duration_ms": 2500,                                    │ │
│  │   "groq_duration_ms": 800,                                │ │
│  │   "tts_duration_ms": 1200                                 │ │
│  │ }                                                          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Log Levels                                                      │
│  ├─ DEBUG: Detailed diagnostic information                      │
│  ├─ INFO: General informational messages                        │
│  ├─ WARNING: Warning messages (non-critical)                    │
│  ├─ ERROR: Error messages (handled)                             │
│  └─ CRITICAL: Critical errors (unhandled)                       │
│                                                                  │
│  Log Destinations                                                │
│  ├─ stdout/stderr (captured by Railway)                         │
│  ├─ Railway dashboard (real-time)                               │
│  └─ External log aggregation (optional: Logtail, Papertrail)   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Metrics Architecture                        │
│                                                                  │
│  Application Metrics                                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Request Metrics                                            │ │
│  │ - Total requests                                           │ │
│  │ - Requests per endpoint                                    │ │
│  │ - Response times (P50, P95, P99)                          │ │
│  │ - Error rate                                               │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Resource Metrics                                           │ │
│  │ - Memory usage                                             │ │
│  │ - CPU usage                                                │ │
│  │ - Disk usage                                               │ │
│  │ - Active sessions                                          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ External Service Metrics                                   │ │
│  │ - Groq API latency                                         │ │
│  │ - ElevenLabs API latency                                   │ │
│  │ - Qdrant query latency                                     │ │
│  │ - Circuit breaker status                                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Metrics Collection                                              │
│  ├─ Railway built-in metrics                                    │
│  ├─ Application logs (parsed for metrics)                       │
│  └─ External monitoring (optional: Prometheus, Datadog)         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Alerting Architecture                       │
│                                                                  │
│  Alert Triggers                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Critical Alerts (P0)                                       │ │
│  │ - Service down (health check fails)                        │ │
│  │ - Error rate > 10%                                         │ │
│  │ - Memory usage > 90%                                       │ │
│  │ - All circuit breakers open                                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Warning Alerts (P1)                                        │ │
│  │ - Error rate > 5%                                          │ │
│  │ - Response time P95 > 10s                                  │ │
│  │ - Memory usage > 80%                                       │ │
│  │ - Disk usage > 80%                                         │ │
│  │ - Circuit breaker open                                     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Alert Channels                                                  │
│  ├─ Email notifications                                          │
│  ├─ Slack/Teams integration                                      │
│  ├─ PagerDuty (for on-call)                                     │
│  └─ SMS (critical only)                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Scaling Architecture

### Vertical Scaling (Current)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Single Instance Deployment                    │
│                                                                  │
│  Railway Instance                                                │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ FastAPI Application                                        │ │
│  │ - Handles all requests                                     │ │
│  │ - SQLite for state                                         │ │
│  │ - Local file storage                                       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Scaling Strategy:                                               │
│  - Increase memory allocation (512MB → 8GB)                     │
│  - Railway auto-scales CPU                                      │
│  - Limited by single instance constraints                       │
│                                                                  │
│  Capacity: ~50-100 concurrent users                             │
└─────────────────────────────────────────────────────────────────┘
```

### Horizontal Scaling (Future)

```
┌─────────────────────────────────────────────────────────────────┐
│                   Multi-Instance Deployment                      │
│                                                                  │
│  Load Balancer                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ - Distribute requests                                      │ │
│  │ - Health check instances                                   │ │
│  │ - Session affinity (sticky sessions)                       │ │
│  └──────────┬─────────────────────────────────┬───────────────┘ │
│             │                                 │                  │
│  ┌──────────▼──────────┐         ┌──────────▼──────────┐       │
│  │ Instance 1          │         │ Instance 2          │       │
│  │ - FastAPI App       │         │ - FastAPI App       │       │
│  └─────────────────────┘         └─────────────────────┘       │
│             │                                 │                  │
│             └─────────────┬───────────────────┘                  │
│                           │                                      │
│  ┌────────────────────────▼────────────────────────────────────┐│
│  │ Shared PostgreSQL Database                                  ││
│  │ - Replace SQLite for multi-instance support                 ││
│  │ - Shared conversation state                                 ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  Requirements for Horizontal Scaling:                            │
│  - PostgreSQL checkpointer (replace SQLite)                     │
│  - Shared file storage (S3 or similar)                          │
│  - Session affinity or stateless design                         │
│  - Distributed caching (Redis)                                  │
│                                                                  │
│  Capacity: 500+ concurrent users                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Performance Characteristics

### Response Time Breakdown

```
Total Response Time: ~3-5 seconds (typical)

┌─────────────────────────────────────────────────────────────────┐
│                    Response Time Components                      │
│                                                                  │
│  Audio Upload          │████                    │ ~200ms         │
│  Speech-to-Text (Groq) │████████████████        │ ~800ms         │
│  Memory Retrieval      │████                    │ ~200ms         │
│  LLM Generation (Groq) │████████████████████    │ ~1000ms        │
│  Text-to-Speech (EL)   │████████████████████████│ ~1200ms        │
│  Audio Download        │████                    │ ~200ms         │
│                                                                  │
│  Total: ~3600ms (3.6 seconds)                                   │
└─────────────────────────────────────────────────────────────────┘

Optimization Opportunities:
- TTS caching: Reduce repeated responses
- Streaming responses: Start audio playback earlier
- Parallel processing: Overlap operations where possible
```

### Throughput Characteristics

```
Single Instance Capacity:

Concurrent Users: 50-100
- Limited by memory and external API rate limits
- Each user session: ~50MB memory
- Total memory: 512MB-8GB available

Requests per Minute: ~100-200
- Rate limited to 10 req/min per IP
- Multiple users can make concurrent requests
- External API limits may apply

Database Operations:
- SQLite: ~1000 reads/sec, ~100 writes/sec
- Qdrant: ~100 vector searches/sec
- Sufficient for single instance deployment
```

---

## Architectural Patterns

### Circuit Breaker Pattern

The application implements the Circuit Breaker pattern to protect against cascading failures when external services become unavailable. This pattern is critical for maintaining system stability and providing graceful degradation.

#### Implementation

Circuit breakers are implemented in `src/ai_companion/core/resilience.py` and applied to all external service calls:

```python
from ai_companion.core.resilience import CircuitBreaker

# Create circuit breaker instance
breaker = CircuitBreaker(
    failure_threshold=5,      # Open after 5 failures
    recovery_timeout=60,      # Wait 60s before retry
    expected_exception=Exception,
    name="ServiceName"
)

# Use with sync functions
result = breaker.call(external_api_function, *args, **kwargs)

# Use with async functions
result = await breaker.call_async(async_external_api_function, *args, **kwargs)
```

#### State Machine

```
┌─────────────────────────────────────────────────────────────────┐
│                    Circuit Breaker States                        │
│                                                                  │
│  CLOSED (Normal Operation)                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ • All requests pass through to external service            │ │
│  │ • Track failure count for each request                     │ │
│  │ • If failures >= threshold (5): Transition to OPEN         │ │
│  │ • Reset failure count on successful request                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                          │                                       │
│                          ▼ (5 consecutive failures)              │
│                                                                  │
│  OPEN (Failing Fast)                                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ • Reject all requests immediately (fail fast)              │ │
│  │ • Raise CircuitBreakerError without calling service        │ │
│  │ • Record last_failure_time                                 │ │
│  │ • Wait for recovery_timeout (60s)                          │ │
│  │ • Prevents overwhelming failing service                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                          │                                       │
│                          ▼ (after 60 seconds)                    │
│                                                                  │
│  HALF_OPEN (Testing Recovery)                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ • Allow ONE test request through                           │ │
│  │ • If success: Transition to CLOSED (service recovered)     │ │
│  │ • If failure: Transition back to OPEN (still failing)      │ │
│  │ • Reset recovery timer on failure                          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                          │                                       │
│                          ▼ (test request succeeds)               │
│                                                                  │
│                      CLOSED                                      │
│                  (Resume Normal Operation)                       │
└─────────────────────────────────────────────────────────────────┘
```

#### Service-Specific Circuit Breakers

The application maintains separate circuit breaker instances for each external service:

```python
# Groq API (LLM, STT, Vision)
groq_breaker = get_groq_circuit_breaker()
# Configuration: 5 failures, 60s recovery

# ElevenLabs API (TTS)
elevenlabs_breaker = get_elevenlabs_circuit_breaker()
# Configuration: 5 failures, 60s recovery

# Qdrant API (Vector Database)
qdrant_breaker = get_qdrant_circuit_breaker()
# Configuration: 5 failures, 60s recovery
```

This separation ensures that failure in one service doesn't affect others. For example, if Groq's STT service fails, the circuit breaker for ElevenLabs TTS remains operational.

#### Benefits

1. **Fast Failure**: When a service is down, requests fail immediately instead of waiting for timeouts
2. **Service Recovery**: Gives failing services time to recover without being overwhelmed
3. **Cascading Failure Prevention**: Prevents failures from propagating through the system
4. **Resource Conservation**: Avoids wasting resources on requests that will fail
5. **User Experience**: Provides faster error responses instead of long timeouts

#### Monitoring

Circuit breaker state changes are logged with structured logging:

```python
logger.info(f"{self.name}: Attempting recovery (HALF_OPEN)")
logger.error(f"{self.name}: Circuit breaker OPENED after {count} failures")
logger.info(f"{self.name}: Recovery successful, closing circuit")
```

These logs enable monitoring and alerting on circuit breaker state transitions.

---

### Retry Pattern with Exponential Backoff

The application implements retry logic with exponential backoff for transient failures in external API calls. This pattern is particularly important for speech-to-text operations where network issues or temporary service unavailability can occur.

#### Implementation

Retry logic is implemented in `src/ai_companion/modules/speech/speech_to_text.py`:

```python
# Retry configuration (from settings)
STT_MAX_RETRIES = 3
STT_INITIAL_BACKOFF = 1.0  # seconds
STT_MAX_BACKOFF = 10.0     # seconds

# Retry loop
for attempt in range(STT_MAX_RETRIES):
    try:
        result = await external_api_call()
        return result  # Success - exit loop
    except CircuitBreakerError:
        # Circuit breaker open - fail fast without retry
        raise
    except ValueError:
        # Validation error - don't retry
        raise
    except Exception as e:
        if attempt < STT_MAX_RETRIES - 1:
            # Calculate backoff time: initial * (2 ^ attempt)
            backoff_time = min(
                STT_INITIAL_BACKOFF * (2 ** attempt),
                STT_MAX_BACKOFF
            )
            await asyncio.sleep(backoff_time)
        else:
            # Last attempt failed - raise exception
            raise
```

#### Backoff Calculation

The exponential backoff formula provides increasing delays between retries:

```
Backoff Time = min(INITIAL_BACKOFF * (2 ^ attempt), MAX_BACKOFF)

Example with INITIAL_BACKOFF=1s, MAX_BACKOFF=10s:
- Attempt 1 fails: Wait 1s  (1 * 2^0 = 1s)
- Attempt 2 fails: Wait 2s  (1 * 2^1 = 2s)
- Attempt 3 fails: Wait 4s  (1 * 2^2 = 4s)
- Attempt 4 fails: Wait 8s  (1 * 2^3 = 8s)
- Attempt 5 fails: Wait 10s (1 * 2^4 = 16s, capped at 10s)
```

#### Retry Decision Logic

```
┌─────────────────────────────────────────────────────────────────┐
│                    Retry Decision Flow                           │
│                                                                  │
│  API Call Fails                                                  │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────────┐                                        │
│  │ CircuitBreakerError?│──Yes──> Fail Fast (don't retry)        │
│  └──────────┬──────────┘                                        │
│             No                                                   │
│             ▼                                                    │
│  ┌─────────────────────┐                                        │
│  │ ValidationError?    │──Yes──> Fail Fast (don't retry)        │
│  └──────────┬──────────┘                                        │
│             No                                                   │
│             ▼                                                    │
│  ┌─────────────────────┐                                        │
│  │ Last attempt?       │──Yes──> Raise Exception                │
│  └──────────┬──────────┘                                        │
│             No                                                   │
│             ▼                                                    │
│  ┌─────────────────────┐                                        │
│  │ Calculate backoff   │                                        │
│  │ Wait (exponential)  │                                        │
│  └──────────┬──────────┘                                        │
│             │                                                    │
│             ▼                                                    │
│       Retry Request                                              │
└─────────────────────────────────────────────────────────────────┘
```

#### Benefits

1. **Transient Failure Recovery**: Automatically recovers from temporary network issues
2. **Service Load Reduction**: Exponential backoff reduces load on recovering services
3. **Rate Limit Handling**: Increasing delays help avoid hitting rate limits
4. **User Experience**: Transparent retry improves success rate without user intervention
5. **Resource Efficiency**: Capped backoff prevents excessive waiting

#### Integration with Circuit Breaker

The retry pattern works in conjunction with circuit breakers:

1. **Circuit Breaker Check First**: Before each retry, circuit breaker state is checked
2. **Fail Fast on Open Circuit**: If circuit is open, skip retries and fail immediately
3. **Circuit Opens on Repeated Failures**: Multiple retry failures contribute to circuit breaker threshold
4. **Coordinated Recovery**: Circuit breaker recovery timeout aligns with retry backoff

This integration prevents wasting resources on retries when a service is known to be down.

---

### Module Initialization Patterns

The application uses several patterns for module initialization to ensure efficient resource usage and proper lifecycle management.

#### Singleton Pattern for Stateful Resources

Stateful resources like vector stores and circuit breakers use the singleton pattern to ensure only one instance exists:

```python
# Vector Store Singleton (using class-level state)
class VectorStore:
    _instance: Optional["VectorStore"] = None
    _initialized: bool = False
    
    def __new__(cls) -> "VectorStore":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        if not self._initialized:
            # Initialize Qdrant client, embedding model
            self.client = QdrantClient(...)
            self.model = SentenceTransformer(...)
            VectorStore._initialized = True

# Usage
store1 = VectorStore()
store2 = VectorStore()
assert store1 is store2  # Same instance
```

Benefits:
- **Connection Pooling**: Single Qdrant client maintains connection pool
- **Memory Efficiency**: Embedding model loaded once
- **State Consistency**: All operations use same instance

#### Factory Functions with LRU Cache

Factory functions with `@lru_cache` provide lazy initialization and caching:

```python
from functools import lru_cache

@lru_cache
def get_vector_store() -> VectorStore:
    """Get or create the VectorStore singleton instance."""
    return VectorStore()

@lru_cache
def get_memory_manager() -> MemoryManager:
    """Get or create the MemoryManager instance."""
    return MemoryManager()
```

Benefits:
- **Lazy Initialization**: Resources created only when first needed
- **Import-Time Safety**: No initialization during module import
- **Testability**: Can clear cache in tests for fresh instances

#### Lazy Initialization for Circuit Breakers

Circuit breakers use lazy initialization to avoid requiring settings at import time:

```python
# Global circuit breaker instances (lazy initialization)
_groq_circuit_breaker: Optional[CircuitBreaker] = None

def get_groq_circuit_breaker() -> CircuitBreaker:
    """Get the global Groq circuit breaker instance."""
    global _groq_circuit_breaker
    if _groq_circuit_breaker is None:
        from ai_companion.settings import settings
        _groq_circuit_breaker = CircuitBreaker(
            failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
            name="GroqAPI"
        )
    return _groq_circuit_breaker
```

Benefits:
- **Settings Dependency**: Settings loaded only when needed
- **Module Import Order**: No circular dependency issues
- **Global State**: Single circuit breaker per service across application

#### Property-Based Lazy Initialization

Client instances use property-based lazy initialization:

```python
class SpeechToText:
    def __init__(self) -> None:
        self._client: Optional[Groq] = None
        self._circuit_breaker: CircuitBreaker = get_groq_circuit_breaker()
    
    @property
    def client(self) -> Groq:
        """Get or create Groq client instance using singleton pattern."""
        if self._client is None:
            self._client = Groq(
                api_key=settings.GROQ_API_KEY,
                timeout=settings.STT_TIMEOUT
            )
        return self._client
```

Benefits:
- **Deferred Initialization**: Client created only when first used
- **Instance-Level Caching**: Each instance maintains its own client
- **Clean Interface**: Transparent to callers (looks like regular attribute)

#### Session-Scoped Instances (Chainlit)

For Chainlit interface, modules can be scoped to user sessions:

```python
@cl.on_chat_start
async def on_chat_start():
    """Initialize session-scoped module instances."""
    cl.user_session.set("speech_to_text", SpeechToText())
    cl.user_session.set("text_to_speech", TextToSpeech())
    cl.user_session.set("memory_manager", get_memory_manager())

@cl.on_message
async def on_message(message: cl.Message):
    """Use session-scoped instances."""
    stt = cl.user_session.get("speech_to_text")
    tts = cl.user_session.get("text_to_speech")
    # Use instances...
```

Benefits:
- **Session Isolation**: Each user has independent module instances
- **State Management**: Session-specific state (e.g., TTS cache)
- **Resource Cleanup**: Instances cleaned up when session ends

#### Initialization Pattern Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                  Module Initialization Patterns                  │
│                                                                  │
│  Pattern              │ Use Case              │ Example          │
│  ────────────────────────────────────────────────────────────── │
│  Singleton            │ Stateful resources    │ VectorStore      │
│  Factory + LRU Cache  │ Lazy initialization   │ get_vector_store │
│  Lazy Global          │ Circuit breakers      │ get_groq_cb      │
│  Property Lazy        │ Client instances      │ SpeechToText     │
│  Session-Scoped       │ User-specific state   │ Chainlit modules │
└─────────────────────────────────────────────────────────────────┘
```

#### Best Practices

1. **Avoid Global Instances**: Use factory functions instead of module-level instances
2. **Lazy Initialization**: Defer resource creation until first use
3. **Singleton for Connections**: Use singleton pattern for database/API connections
4. **Session Scope for State**: Use session-scoped instances for user-specific state
5. **Document Lifecycle**: Add docstrings explaining initialization and cleanup

#### References

- Circuit Breaker Implementation: `src/ai_companion/core/resilience.py`
- Retry Logic: `src/ai_companion/modules/speech/speech_to_text.py`
- Vector Store Singleton: `src/ai_companion/modules/memory/long_term/vector_store.py`
- Memory Manager Factory: `src/ai_companion/modules/memory/long_term/memory_manager.py`
- Chainlit Session Management: `src/ai_companion/interfaces/chainlit/app.py`

---

## Related Documentation

- [Operations Runbook](OPERATIONS_RUNBOOK.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Data Persistence Guide](DATA_PERSISTENCE.md)
- [Security Documentation](SECURITY.md)
- [Monitoring and Observability](MONITORING_AND_OBSERVABILITY.md)

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2024-01-15 | 1.0 | Initial architecture documentation |


---

## Refactored Patterns and Best Practices

### Error Handling Pattern

The application uses a unified error handling pattern that works for both synchronous and asynchronous functions using function introspection.

**Implementation**:

```python
def handle_api_errors(service_name: str, fallback_message: Optional[str] = None):
    """Unified error handler decorator for both sync and async functions."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{service_name} error: {e}")
                metrics.record_error(service_name, type(e).__name__)
                return fallback_message or f"Error in {service_name}"

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{service_name} error: {e}")
                metrics.record_error(service_name, type(e).__name__)
                return fallback_message or f"Error in {service_name}"

        # Single decision point based on function type
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator
```

**Benefits**:
- Eliminates code duplication (50% reduction in error handler code)
- Single source of truth for error handling logic
- Consistent error logging and metrics across all services
- Automatic detection of sync vs async functions

**Usage**:

```python
@handle_api_errors("groq_stt", fallback_message="Could not transcribe audio")
async def transcribe_audio(audio_data: bytes) -> str:
    # Implementation
    pass

@handle_api_errors("memory_retrieval")
def get_relevant_memories(context: str) -> List[str]:
    # Implementation
    pass
```

### Circuit Breaker Pattern

The circuit breaker pattern protects against cascading failures by preventing calls to failing services.

**State Machine**:

```
┌─────────┐
│ CLOSED  │ ◄──────────────────────────┐
│ (Normal)│                            │
└────┬────┘                            │
     │ Failures >= Threshold           │
     │                                 │ Success in HALF_OPEN
     ▼                                 │
┌─────────┐                       ┌────┴────┐
│  OPEN   │ ──────────────────►  │HALF_OPEN│
│(Blocked)│   After timeout       │(Testing)│
└─────────┘                       └─────────┘
```

**Refactored Implementation**:

```python
class CircuitBreaker:
    """Circuit breaker with extracted common state management logic."""

    def _check_circuit_state(self) -> None:
        """Common logic for checking and transitioning circuit state."""
        if self._state == "OPEN" and self._should_attempt_reset():
            self._state = "HALF_OPEN"
            logger.info(f"Circuit breaker {self.name} entering HALF_OPEN state")
        elif self._state == "OPEN":
            raise CircuitBreakerError(f"Circuit breaker {self.name} is OPEN")

    def _handle_success(self) -> None:
        """Common logic for successful calls."""
        if self._state == "HALF_OPEN":
            self._state = "CLOSED"
            self._failure_count = 0
            logger.info(f"Circuit breaker {self.name} recovered to CLOSED")

    def _handle_failure(self, exception: Exception) -> None:
        """Common logic for failed calls."""
        self._failure_count += 1
        if self._failure_count >= self.failure_threshold:
            self._state = "OPEN"
            self._last_failure_time = time.time()
            logger.warning(f"Circuit breaker {self.name} opened after {self._failure_count} failures")

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute function with circuit breaker protection (sync)."""
        self._check_circuit_state()
        try:
            result = func(*args, **kwargs)
            self._handle_success()
            return result
        except self.expected_exception as e:
            self._handle_failure(e)
            raise

    async def call_async(self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
        """Execute function with circuit breaker protection (async)."""
        self._check_circuit_state()
        try:
            result = await func(*args, **kwargs)
            self._handle_success()
            return result
        except self.expected_exception as e:
            self._handle_failure(e)
            raise
```

**Benefits**:
- Eliminates duplicated state management logic (33% code reduction)
- Easier to add new features (e.g., metrics, notifications)
- Consistent behavior between sync and async paths
- Clear separation of concerns

**Usage**:

```python
# Create circuit breaker for external service
groq_breaker = CircuitBreaker(
    name="groq_api",
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=GroqAPIError
)

# Use with sync function
result = groq_breaker.call(groq_client.transcribe, audio_data)

# Use with async function
result = await groq_breaker.call_async(groq_client.transcribe_async, audio_data)
```

### Module Initialization Pattern

The application uses factory functions and session-scoped instances to manage module lifecycle efficiently.

**Pattern**:

```python
# Factory function for singleton-like behavior
def get_speech_to_text() -> SpeechToText:
    """Get or create SpeechToText instance."""
    if not hasattr(get_speech_to_text, '_instance'):
        get_speech_to_text._instance = SpeechToText()
    return get_speech_to_text._instance

# Session-scoped instances in Chainlit
@cl.on_chat_start
async def on_chat_start():
    """Initialize session-scoped module instances."""
    cl.user_session.set("speech_to_text", SpeechToText())
    cl.user_session.set("text_to_speech", TextToSpeech())
    cl.user_session.set("memory_manager", MemoryManager())

@cl.on_message
async def on_message(message: cl.Message):
    """Retrieve modules from session."""
    stt = cl.user_session.get("speech_to_text")
    tts = cl.user_session.get("text_to_speech")
    # Use modules...
```

**Benefits**:
- Eliminates global state
- Better testability (can inject mocks)
- Clear lifecycle management
- Resource efficiency (reuse within session)

### Async/Await Pattern Consistency

The application follows consistent async/await patterns throughout:

**Rules**:
1. Use `async def` for functions that perform I/O operations
2. Always `await` async function calls
3. Use `asyncio.gather()` for parallel operations
4. Use `aiofiles` for file I/O in async contexts
5. Document any sync-to-async bridges with rationale

**Example**:

```python
# Good: Async function with async I/O
async def process_audio(audio_path: str) -> str:
    async with aiofiles.open(audio_path, 'rb') as f:
        audio_data = await f.read()
    return await transcribe_audio(audio_data)

# Good: Parallel operations
async def process_multiple_audios(audio_paths: List[str]) -> List[str]:
    tasks = [process_audio(path) for path in audio_paths]
    return await asyncio.gather(*tasks)

# Bad: Blocking I/O in async function
async def process_audio_bad(audio_path: str) -> str:
    with open(audio_path, 'rb') as f:  # Blocks event loop!
        audio_data = f.read()
    return await transcribe_audio(audio_data)
```

### Type Safety Pattern

The application uses comprehensive type hints with mypy validation:

**Standards**:
- All public functions have complete type annotations
- Use `Optional[T]` or `T | None` for nullable types
- Use `TypedDict` for structured dictionaries
- Use `Literal` for string enums
- Document complex types with type aliases

**Example**:

```python
from typing import TypedDict, Literal, Optional

# Type aliases for clarity
WorkflowType = Literal["conversation", "audio", "image"]
MemorySearchResult = List[Memory]

# Structured dictionary types
class MemoryMetadata(TypedDict):
    id: str
    timestamp: str
    topic: Optional[str]

# Complete function annotations
async def search_memories(
    query: str,
    k: int = 5,
    metadata_filter: Optional[MemoryMetadata] = None
) -> MemorySearchResult:
    """Search for similar memories with type-safe interface."""
    # Implementation
    pass
```

### Testing Pattern

The application follows a comprehensive testing strategy:

**Test Organization**:
```
tests/
├── unit/                    # Unit tests for individual modules
│   ├── test_memory_manager.py
│   ├── test_speech_to_text.py
│   └── test_error_handlers.py
├── integration/             # End-to-end workflow tests
│   └── test_workflow_integration.py
├── fixtures/                # Shared test fixtures
│   ├── audio_samples.py
│   └── mock_responses.py
└── conftest.py             # Pytest configuration
```

**Test Patterns**:

```python
# Unit test with mocking
@pytest.mark.asyncio
async def test_memory_extraction(mock_groq_client):
    """Test memory extraction from user message."""
    with patch("ai_companion.modules.memory.get_vector_store") as mock_vs:
        manager = MemoryManager()
        message = HumanMessage(content="My name is Sarah")

        await manager.extract_and_store_memory(message)

        # Verify LLM was called for analysis
        mock_groq_client.analyze.assert_called_once()
        # Verify memory was stored
        mock_vs.return_value.store_memory.assert_called_once()

# Integration test with real workflow
@pytest.mark.asyncio
async def test_complete_conversation_workflow(mock_external_services):
    """Test end-to-end conversation flow."""
    initial_state = {
        "messages": [HumanMessage(content="I'm feeling anxious")],
        "workflow_type": "conversation"
    }

    graph = create_workflow_graph().compile()
    result = await graph.ainvoke(initial_state)

    # Verify workflow completed successfully
    assert "messages" in result
    assert len(result["messages"]) > 1
    assert isinstance(result["messages"][-1], AIMessage)
```

**Test Coverage Goals**:
- Core modules: >80% coverage
- Utility modules: >70% coverage
- Integration tests: Cover all critical workflows

### Configuration Management Pattern

The application uses Pydantic for centralized configuration with validation:

**Pattern**:

```python
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with validation."""

    # API Keys
    GROQ_API_KEY: str = Field(..., description="Groq API key")
    ELEVENLABS_API_KEY: str = Field(..., description="ElevenLabs API key")

    # Memory settings with validation
    MEMORY_TOP_K: int = Field(default=5, ge=1, le=20)

    @field_validator("MEMORY_TOP_K")
    @classmethod
    def validate_memory_top_k(cls, v: int) -> int:
        """Validate memory retrieval count."""
        if v < 1 or v > 20:
            raise ValueError("MEMORY_TOP_K must be between 1 and 20")
        return v

    @model_validator(mode='after')
    def validate_database_config(self) -> 'Settings':
        """Cross-field validation for database settings."""
        if self.FEATURE_DATABASE_TYPE == "postgresql" and not self.DATABASE_URL:
            raise ValueError(
                "DATABASE_URL is required when FEATURE_DATABASE_TYPE is 'postgresql'"
            )
        return self

    class Config:
        env_file = ".env"
        case_sensitive = True
```

**Benefits**:
- Type-safe configuration
- Automatic validation at startup
- Clear error messages for misconfiguration
- Environment variable support
- IDE autocomplete for settings

---

## Architecture Decision Records

### ADR-001: Unified Error Handling

**Status**: Accepted

**Context**: Error handling was duplicated across sync and async functions, leading to maintenance burden.

**Decision**: Use function introspection to create a single error handler decorator that works for both sync and async functions.

**Consequences**:
- ✅ 50% reduction in error handling code
- ✅ Single source of truth for error logic
- ✅ Easier to maintain and extend
- ⚠️ Slightly more complex decorator implementation

### ADR-002: Circuit Breaker State Management

**Status**: Accepted

**Context**: Circuit breaker had duplicated state management logic between sync and async methods.

**Decision**: Extract common state management into private methods shared by both sync and async call methods.

**Consequences**:
- ✅ 33% reduction in circuit breaker code
- ✅ Consistent behavior across sync/async
- ✅ Easier to add new features
- ⚠️ Requires careful testing of state transitions

### ADR-003: Session-Scoped Module Instances

**Status**: Accepted

**Context**: Global module instances created tight coupling and made testing difficult.

**Decision**: Use factory functions and session-scoped instances for module lifecycle management.

**Consequences**:
- ✅ Better testability
- ✅ Clearer lifecycle management
- ✅ Reduced global state
- ⚠️ Requires explicit instance retrieval

### ADR-004: Comprehensive Type Hints

**Status**: In Progress

**Context**: Missing type hints made code harder to understand and maintain.

**Decision**: Add complete type annotations to all public functions and validate with mypy.

**Consequences**:
- ✅ Better IDE support
- ✅ Catch errors at development time
- ✅ Self-documenting code
- ⚠️ 57 type errors remaining (mostly third-party library issues)

---

## Performance Considerations

### Benchmarks

Critical operations have performance benchmarks:

- **Memory Extraction**: <500ms per message
- **Memory Retrieval**: <200ms for top-K search
- **STT Transcription**: <2s for 10s audio
- **TTS Synthesis**: <1s for 100 words
- **End-to-End Workflow**: <5s for typical conversation

### Optimization Strategies

1. **Caching**: TTS responses cached to reduce API calls
2. **Parallel Operations**: Use `asyncio.gather()` for independent operations
3. **Circuit Breakers**: Prevent wasted calls to failing services
4. **Connection Pooling**: Reuse HTTP connections to external services
5. **Lazy Loading**: Initialize expensive resources only when needed

---

## Monitoring and Observability

### Metrics

The application tracks key metrics:

- **Request Metrics**: Count, latency, errors per endpoint
- **Service Metrics**: API call success/failure rates
- **Circuit Breaker Metrics**: State transitions, failure counts
- **Memory Metrics**: Storage operations, search latency
- **System Metrics**: CPU, memory, disk usage

### Logging

Structured logging with different levels:

- **ERROR**: Service failures, exceptions
- **WARNING**: Circuit breaker state changes, retries
- **INFO**: Request processing, workflow execution
- **DEBUG**: Detailed execution traces

### Health Checks

Multiple health check endpoints:

- `/api/health` - Overall system health
- `/api/health/groq` - Groq API connectivity
- `/api/health/elevenlabs` - ElevenLabs API connectivity
- `/api/health/qdrant` - Qdrant vector database connectivity

---

## Security Architecture

### API Key Management

- All API keys stored in environment variables
- Never logged or exposed in error messages
- Validated at startup before service initialization

### Input Validation

- All user inputs validated with Pydantic models
- Audio file size limits enforced
- Text length limits for LLM inputs

### Rate Limiting

- Per-IP rate limiting on API endpoints
- Configurable limits per endpoint
- Graceful degradation under load

### Error Handling

- User-facing errors never expose internal details
- Stack traces logged but not returned to users
- Consistent error response format

---

## Future Architecture Improvements

### Planned Enhancements

1. **Distributed Tracing**: Add OpenTelemetry for request tracing
2. **Caching Layer**: Redis for distributed caching
3. **Message Queue**: Add queue for async processing
4. **Multi-tenancy**: Support multiple users with isolation
5. **Horizontal Scaling**: Support multiple application instances

### Scalability Considerations

- **Stateless Design**: Application can scale horizontally
- **External State**: All state in databases (SQLite, Qdrant)
- **Load Balancing**: Ready for load balancer deployment
- **Session Affinity**: Required for WebSocket connections

---

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Async Python Best Practices](https://docs.python.org/3/library/asyncio.html)
