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
