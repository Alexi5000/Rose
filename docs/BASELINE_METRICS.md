# Rose Voice Agent Baseline Metrics

> **Document Purpose**: Track baseline performance metrics before optimization.
> **Created**: January 2026
> **Last Updated**: January 2026

## Overview

This document captures the baseline performance metrics for the Rose voice agent pipeline before implementing the optimization plan. These measurements serve as the comparison point for measuring improvement impact.

## Measurement Methodology

- **Environment**: Development environment with Docker compose
- **Network**: Local network (minimal latency)
- **Audio Input**: ~3-5 second utterances (typical user turn)
- **Metrics Source**: `PipelineTimings` instrumentation in `voice.py`

## Current Pipeline Timing Targets

| Stage | Target P50 | Target P95 | Notes |
|-------|------------|------------|-------|
| Audio Validation | <20ms | <50ms | File size and format checks |
| Speech-to-Text (STT) | <800ms | <1200ms | Groq Whisper (batch) |
| Workflow (total) | <1200ms | <1800ms | LangGraph with memory |
| ├─ Memory Retrieval | <200ms | <400ms | Qdrant vector search |
| ├─ LLM Generation | <800ms | <1200ms | Groq LLM response |
| └─ Memory Extraction | <100ms | <200ms | Background (non-blocking) |
| Text-to-Speech (TTS) | <1000ms | <1500ms | ElevenLabs synthesis |
| Audio Save | <20ms | <50ms | File I/O |
| **Total End-to-End** | **<3500ms** | **<5000ms** | User turn to first audio byte |

## Baseline Measurements (Pre-Optimization)

> **Note**: Fill in these values after running baseline tests.

### Measured P50 (Median)

| Stage | Baseline (ms) | Target (ms) | Status |
|-------|--------------|-------------|--------|
| Audio Validation | TBD | <20 | ⏳ |
| STT | TBD | <800 | ⏳ |
| Workflow | TBD | <1200 | ⏳ |
| TTS | TBD | <1000 | ⏳ |
| Audio Save | TBD | <20 | ⏳ |
| **Total** | TBD | <3500 | ⏳ |

### Measured P95

| Stage | Baseline (ms) | Target (ms) | Status |
|-------|--------------|-------------|--------|
| Audio Validation | TBD | <50 | ⏳ |
| STT | TBD | <1200 | ⏳ |
| Workflow | TBD | <1800 | ⏳ |
| TTS | TBD | <1500 | ⏳ |
| Audio Save | TBD | <50 | ⏳ |
| **Total** | TBD | <5000 | ⏳ |

## Stretch Goals (Post-Optimization)

| Metric | Current Target | Stretch Goal | Method |
|--------|---------------|--------------|--------|
| Total E2E | <3500ms | <1500ms | Streaming + parallelization |
| First Audio Byte | N/A | <500ms | Streaming TTS |
| STT First Word | N/A | <200ms | Streaming STT (Deepgram) |
| Memory Recall | >80% | >90% | Hierarchical memory |

## VAD Configuration

Current Voice Activity Detection settings (from `frontend/src/config/voice.ts`):

| Parameter | Current Value | Notes |
|-----------|--------------|-------|
| DEACTIVATION_FRAMES_REQUIRED | 30 | ~500ms silence before end |
| ACTIVATION_FRAMES_REQUIRED | 1 | Near-instant start |
| RMS_ACTIVATION_THRESHOLD | 0.002 | Sensitivity for speech detection |
| RMS_DEACTIVATION_THRESHOLD | 0.001 | Lower threshold to avoid cutoffs |

## How to Collect Metrics

1. **Enable timing metrics** (enabled by default):
   ```bash
   FEATURE_TIMING_METRICS_ENABLED=true
   ```

2. **Run the application**:
   ```bash
   docker-compose -f docker-compose.dev.yml up
   ```

3. **Make test voice interactions** and observe the `timings` field in API responses.

4. **Aggregate metrics** from logs:
   ```bash
   grep "pipeline_timings" logs/app.log | jq '.total_ms'
   ```

5. **Run benchmark suite**:
   ```bash
   pytest tests/test_performance_benchmarks.py -v -m slow
   ```

## Optimization Phases Impact Tracking

| Phase | Description | Expected Impact | Status |
|-------|-------------|-----------------|--------|
| Phase 0 | Latency Instrumentation | Baseline measurement | ✅ Implemented |
| Phase 1 | Quick Wins (VAD, TTS latency level) | -500ms to -800ms | ✅ Implemented |
| Phase 2 | Streaming TTS | -300ms to first byte | ✅ Implemented |
| Phase 3 | Parallel Memory Operations | -200ms | ✅ Implemented |
| Phase 4 | Streaming STT Abstraction | -600ms to first word | ✅ Implemented |
| Phase 5 | Hierarchical Memory | Quality improvement | ✅ Implemented |
| Phase 6 | WebSocket Streaming | -500ms overlap | ✅ Implemented |
| Phase 7 | Barge-In Support | Better UX | ✅ Implemented |
| Phase 8 | UX Polish | Demo readiness | ✅ Implemented |

## Implementation Summary (January 2026)

### Backend Changes
- `voice.py`: Added `PipelineTimings` dataclass and `timed_stage` context manager
- `text_to_speech.py`: Added `synthesize_streaming()` method with async iterator
- `speech_to_text.py`: Created abstraction in `stt_provider.py` for multiple backends
- `memory_manager.py`: Added search result caching with 60s TTL
- `vector_store.py`: Added `temporal_score` property to `Memory` class
- `hierarchical.py`: New module with 3-tier memory (working, session, long-term)
- `voice_websocket.py`: New WebSocket endpoint for real-time streaming
- `nodes.py`: Made `memory_extraction_node` fire-and-forget

### Frontend Changes
- `voice.ts` config: Reduced `DEACTIVATION_FRAMES_REQUIRED` from 30 to 15
- `shader-background-wrapper.tsx`: Added barge-in support
- `voice-status-indicator.tsx`: New component for state visibility

### Settings Changes
- `TTS_STREAMING_LATENCY_LEVEL`: 3 → 4
- `FEATURE_TIMING_METRICS_ENABLED`: New flag (default: true)
- `STT_PROVIDER`: New setting for provider selection
- `DEEPGRAM_API_KEY`: New optional setting for streaming STT

## References

- [Performance Backlog](./PERFORMANCE_BACKLOG.md)
- [Architecture](./ARCHITECTURE.md)
- [Voice Processing Code](../src/ai_companion/interfaces/web/routes/voice.py)
