# Performance Optimization Backlog

This document tracks performance optimization tasks identified through profiling and analysis. Tasks are prioritized based on impact and effort.

## Priority Matrix

```
High Impact, Low Effort (Quick Wins)
├── PERF-001: TTS Cache Warming
├── PERF-002: Memory Search Result Caching
└── PERF-003: Audio Format Optimization

High Impact, High Effort (Strategic)
├── PERF-004: Streaming Audio Synthesis
├── PERF-005: LLM Response Streaming
└── PERF-006: Parallel Node Execution

Medium Impact, Medium Effort (Incremental)
├── PERF-007: Parallel Memory Operations
├── PERF-008: Batch Memory Extraction
└── PERF-009: Conditional Node Skipping

Low Impact, Low Effort (Nice to Have)
└── PERF-010: Adaptive Circuit Breaker Thresholds
```

---

## Quick Wins (High Impact, Low Effort)

### PERF-001: TTS Cache Warming
**Status:** Not Started  
**Priority:** High  
**Impact:** High (eliminates cold-start latency)  
**Effort:** Low (1-2 days)  
**Owner:** Unassigned

**Description:**
Preemptively warm the TTS cache with common therapeutic phrases during application startup or idle time.

**Implementation:**
```python
async def warm_cache_background(self):
    """Warm cache in background without blocking startup."""
    await asyncio.sleep(5)  # Wait for app to be ready
    for phrase in self._common_phrases:
        try:
            await self.synthesize_cached(phrase)
        except Exception as e:
            logger.warning(f"Failed to warm cache for phrase: {e}")
```

**Success Criteria:**
- [ ] Cache warming runs in background
- [ ] Does not block application startup
- [ ] Covers top 20 most common phrases
- [ ] Cache hit rate >80% for first-time users

**Dependencies:** None

---

### PERF-002: Memory Search Result Caching
**Status:** Not Started  
**Priority:** High  
**Impact:** Medium (reduces vector search calls)  
**Effort:** Low (2-3 days)  
**Owner:** Unassigned

**Description:**
Cache memory search results for identical or similar queries within a session to reduce redundant vector searches.

**Implementation:**
```python
class MemoryManager:
    def __init__(self):
        self._search_cache: Dict[str, Tuple[List[str], float]] = {}
        self._cache_ttl = 300  # 5 minutes
    
    def get_relevant_memories(self, context: str) -> List[str]:
        cache_key = hashlib.md5(context.encode()).hexdigest()
        if cache_key in self._search_cache:
            results, timestamp = self._search_cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return results
        # ... perform search and cache
```

**Success Criteria:**
- [ ] Cache hit rate >50% for repeated contexts
- [ ] Cache invalidation works correctly
- [ ] Memory usage stays within bounds
- [ ] No stale results returned

**Dependencies:** None

---

### PERF-003: Audio Format Optimization
**Status:** Not Started  
**Priority:** Medium  
**Impact:** Low (reduces bandwidth)  
**Effort:** Low (1 day)  
**Owner:** Unassigned

**Description:**
Use Opus audio format instead of MP3 for better compression and quality.

**Implementation:**
```python
# Configure ElevenLabs to use Opus
audio_bytes = await self.synthesize(
    text=text,
    output_format="opus"  # Smaller file size, better quality
)
```

**Success Criteria:**
- [ ] Audio file size reduced by 20-30%
- [ ] Audio quality maintained or improved
- [ ] Compatible with all clients
- [ ] No increase in processing time

**Dependencies:** ElevenLabs API support for Opus

---

## Strategic Initiatives (High Impact, High Effort)

### PERF-004: Streaming Audio Synthesis
**Status:** Not Started  
**Priority:** High  
**Impact:** High (reduces perceived latency)  
**Effort:** High (2-3 weeks)  
**Owner:** Unassigned

**Description:**
Stream TTS audio chunks as they're generated instead of waiting for complete synthesis.

**Implementation:**
```python
async def synthesize_streaming(self, text: str) -> AsyncIterator[bytes]:
    """Stream audio chunks as they're generated."""
    async for chunk in self.client.generate(text=text, stream=True):
        yield chunk
```

**Success Criteria:**
- [ ] First audio chunk arrives within 200ms
- [ ] Smooth playback without buffering
- [ ] Fallback to non-streaming for errors
- [ ] Compatible with Chainlit interface

**Dependencies:**
- ElevenLabs streaming API support
- Chainlit streaming audio support

---

### PERF-005: LLM Response Streaming
**Status:** Not Started  
**Priority:** High  
**Impact:** High (reduces perceived latency)  
**Effort:** High (2-3 weeks)  
**Owner:** Unassigned

**Description:**
Stream LLM responses token-by-token instead of waiting for complete response.

**Implementation:**
```python
async def conversation_node_streaming(state: AICompanionState):
    """Stream LLM response as it's generated."""
    async for chunk in llm.astream(state["messages"]):
        yield {"messages": [chunk]}
```

**Success Criteria:**
- [ ] First token arrives within 500ms
- [ ] Smooth streaming without stuttering
- [ ] Memory extraction still works
- [ ] Compatible with all interfaces

**Dependencies:**
- LangGraph streaming support
- Groq streaming API

---

### PERF-006: Parallel Node Execution
**Status:** Not Started  
**Priority:** High  
**Impact:** High (reduces workflow time)  
**Effort:** High (3-4 weeks)  
**Owner:** Unassigned

**Description:**
Execute independent workflow nodes in parallel to reduce total execution time.

**Implementation:**
```python
# Define parallel execution groups
graph.add_node("parallel_group", [
    "memory_retrieval",
    "context_preparation",
    "user_profile_lookup"
])
```

**Success Criteria:**
- [ ] 30-50% reduction in workflow time
- [ ] No race conditions
- [ ] Proper error handling
- [ ] Maintains state consistency

**Dependencies:**
- LangGraph parallel execution support
- Careful analysis of node dependencies

---

## Incremental Improvements (Medium Impact, Medium Effort)

### PERF-007: Parallel Memory Operations
**Status:** Not Started  
**Priority:** Medium  
**Impact:** Medium (reduces workflow time)  
**Effort:** Medium (1-2 weeks)  
**Owner:** Unassigned

**Description:**
Execute memory extraction and retrieval in parallel during workflow execution.

**Implementation:**
```python
retrieval_task = asyncio.create_task(
    asyncio.to_thread(memory_manager.get_relevant_memories, context)
)
extraction_task = asyncio.create_task(
    memory_manager.extract_and_store_memories(message)
)
memories, _ = await asyncio.gather(retrieval_task, extraction_task)
```

**Success Criteria:**
- [ ] 20-30% reduction in memory operation time
- [ ] No race conditions
- [ ] Proper error handling
- [ ] Maintains data consistency

**Dependencies:** None

---

### PERF-008: Batch Memory Extraction
**Status:** Not Started  
**Priority:** Medium  
**Impact:** High (for multi-turn conversations)  
**Effort:** Medium (1-2 weeks)  
**Owner:** Unassigned

**Description:**
Extract memories from multiple messages in a single LLM call.

**Implementation:**
```python
async def extract_and_store_memories_batch(
    self,
    messages: List[BaseMessage]
) -> None:
    """Extract memories from multiple messages in batch."""
    # Combine messages into single prompt
    combined_content = "\n".join([msg.content for msg in messages])
    # Single LLM call for all messages
    analysis = await self.llm.ainvoke(combined_content)
    # Store all extracted memories
```

**Success Criteria:**
- [ ] 30-40% reduction in LLM API calls
- [ ] Maintains extraction quality
- [ ] Handles large batches efficiently
- [ ] Proper error handling

**Dependencies:** None

---

### PERF-009: Conditional Node Skipping
**Status:** Not Started  
**Priority:** Medium  
**Impact:** Medium (for simple queries)  
**Effort:** Medium (1-2 weeks)  
**Owner:** Unassigned

**Description:**
Skip expensive workflow nodes when not needed based on query analysis.

**Implementation:**
```python
def should_extract_memory(state: AICompanionState) -> bool:
    """Determine if memory extraction is needed."""
    message = state["messages"][-1].content
    # Skip for simple greetings
    if len(message.split()) < 5:
        return False
    # Skip for questions
    if message.strip().endswith("?"):
        return False
    return True
```

**Success Criteria:**
- [ ] 40-60% reduction in time for simple queries
- [ ] No false negatives (missing important memories)
- [ ] Configurable skip rules
- [ ] Proper logging of skipped operations

**Dependencies:** None

---

## Nice to Have (Low Impact, Low Effort)

### PERF-010: Adaptive Circuit Breaker Thresholds
**Status:** Not Started  
**Priority:** Low  
**Impact:** Low (better resilience)  
**Effort:** Medium (1 week)  
**Owner:** Unassigned

**Description:**
Automatically adjust circuit breaker failure thresholds based on historical performance.

**Implementation:**
```python
class AdaptiveCircuitBreaker(CircuitBreaker):
    def adjust_threshold(self):
        """Adjust threshold based on recent performance."""
        success_rate = self._successes / (self._successes + self._failures)
        if success_rate > 0.95:
            self.failure_threshold = min(self.failure_threshold + 1, 10)
        elif success_rate < 0.80:
            self.failure_threshold = max(self.failure_threshold - 1, 3)
```

**Success Criteria:**
- [ ] Thresholds adapt to service reliability
- [ ] No unnecessary circuit opens
- [ ] Proper logging of adjustments
- [ ] Configurable adaptation parameters

**Dependencies:** None

---

## Completed Tasks

_No completed tasks yet_

---

## Metrics and Monitoring

### Key Performance Indicators (KPIs)

1. **Latency Metrics:**
   - P50, P95, P99 response times
   - Time to first byte (TTFB)
   - End-to-end workflow time

2. **Throughput Metrics:**
   - Requests per second
   - Concurrent users supported
   - Queue depth

3. **Resource Metrics:**
   - CPU utilization
   - Memory usage
   - Network bandwidth

4. **Cache Metrics:**
   - TTS cache hit rate
   - Memory search cache hit rate
   - Cache size and eviction rate

### Performance Targets

| Metric | Current | Target | Stretch Goal |
|--------|---------|--------|--------------|
| Memory extraction | <500ms | <300ms | <200ms |
| Memory retrieval | <200ms | <100ms | <50ms |
| STT transcription | <2s | <1.5s | <1s |
| TTS synthesis | <1s | <500ms | <300ms |
| End-to-end workflow | <5s | <3s | <2s |
| TTS cache hit rate | N/A | >80% | >90% |

---

## Review Schedule

- **Weekly:** Review progress on active tasks
- **Monthly:** Prioritize new tasks from backlog
- **Quarterly:** Review overall performance trends and adjust targets

---

## Notes

- All performance improvements should be validated with benchmarks
- Monitor for regressions in CI/CD pipeline
- Document any breaking changes or API modifications
- Consider user experience impact for all optimizations
