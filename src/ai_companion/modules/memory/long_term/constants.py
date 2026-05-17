# Rose full repository refresh 2026-05-17
"""Memory system constants and configuration values.

This module defines all magic numbers and configuration constants for the
long-term memory system. Following Uncle Bob's Clean Code principles, we
avoid magic numbers and make all values explicit with clear documentation.

Constants are organized by category:
- Collection Configuration: Database and collection settings
- Search Configuration: Similarity and retrieval parameters
- Model Configuration: Embedding model specifications
- Isolation Configuration: Multi-user data isolation settings

All constants include comments explaining their purpose and impact.
"""

# ==============================================================================
# COLLECTION CONFIGURATION
# ==============================================================================

QDRANT_COLLECTION_NAME = "long_term_memory"
"""Name of the Qdrant collection for storing memories.

This collection stores semantic embeddings of user memories for retrieval.
Single collection design ensures simplicity and avoids multi-collection
coordination complexity (YAGNI principle).
"""

# ==============================================================================
# SEARCH AND SIMILARITY CONFIGURATION
# ==============================================================================

DUPLICATE_DETECTION_SIMILARITY_THRESHOLD = 0.90
"""Cosine similarity threshold for detecting duplicate memories (0.0-1.0).

How this works:
- 1.0 = Identical embeddings (exact duplicates)
- 0.9 = Very similar (prevents near-duplicates)
- 0.8 = Similar but different enough to keep separate
- 0.7 = Related but distinct memories

Current value (0.90) means:
✅ "User loves coffee" and "User prefers coffee" -> Duplicate (don't store)
❌ "User loves coffee" and "User drinks tea sometimes" -> Different (store both)

Impact:
- Higher values -> More duplicates stored (memory bloat)
- Lower values -> Fewer memories stored (information loss)

Recommendation: 0.85-0.95 for most use cases
"""

DEFAULT_MEMORY_SEARCH_LIMIT = 5
"""Default number of memories to retrieve in semantic search (k parameter).

This is the max number of memories returned when no specific limit is requested.
Used internally by vector_store.search_memories() default behavior.

Why 5?
- Provides good context without overwhelming the prompt
- Balances relevance (top results) vs. diversity (more results)
- Fits within typical LLM context windows efficiently

Can be overridden per query. The MemoryManager uses MEMORY_TOP_K from settings
for actual retrieval (currently 3), which is the user-facing configuration.
"""

MEMORY_CONTEXT_RETRIEVAL_LIMIT = 3
"""Number of memories to inject into LLM context (from settings.MEMORY_TOP_K).

This is the number shown to the LLM during conversation. Separate from
DEFAULT_MEMORY_SEARCH_LIMIT to allow different search vs. usage limits.

Why 3?
- Keeps context concise and focused
- Prevents context pollution with less-relevant memories
- Reduces token usage and improves response time
- Based on testing with 70B parameter LLMs

Impact of changing:
- Higher -> More context, higher cost, potentially less focused responses
- Lower -> Less context, may miss important information

Recommendation: 2-5 for most conversational use cases
"""

# ==============================================================================
# MODEL CONFIGURATION
# ==============================================================================

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
"""Sentence transformer model for generating embeddings.

Model specs:
- Dimensions: 384 (compact, efficient)
- Performance: ~14K tokens/sec on CPU
- Quality: Excellent for semantic similarity tasks
- Size: ~80MB (fast download and loading)

Why this model?
✅ Great balance of speed, size, and accuracy
✅ No GPU required (CPU-friendly for Docker deployments)
✅ Well-tested for semantic search applications
✅ Widely used and maintained by Hugging Face

Alternatives considered:
- all-mpnet-base-v2: Better accuracy, 768 dims, slower (overkill for this use case)
- all-MiniLM-L12-v2: Slightly better, but 2x slower (diminishing returns)
- text-embedding-ada-002: OpenAI, requires API calls, cost overhead (YAGNI)

Change impact:
⚠️ Changing this model INVALIDATES all existing embeddings
⚠️ Requires full re-indexing of memory collection
⚠️ Different dimension size requires collection recreation
"""

EMBEDDING_VECTOR_DIMENSIONS = 384
"""Dimension size of the embedding vectors.

Must match the output dimensions of EMBEDDING_MODEL_NAME.
Used to configure Qdrant collection schema on creation.

Do NOT change this value unless changing the embedding model.
"""

# ==============================================================================
# USER ISOLATION CONFIGURATION
# ==============================================================================

ENABLE_SESSION_ISOLATION = False
"""Enable session-based isolation for multi-user deployments.

When enabled:
✅ Each user's memories are tagged with session_id
✅ Search queries filter by session_id (no cross-user leaks)
✅ Data privacy is enforced at the database level

When disabled:
⚠️ All memories are global (ONLY safe for single-user deployments)
⚠️ Multi-user scenarios WILL leak data between users

Current: False (single-user demo mode - Rose remembers everything across sessions)
Recommendation: Set to True for multi-user deployments
"""

SESSION_ID_METADATA_KEY = "session_id"
"""Metadata key name for storing session identifiers.

Used to tag memories with their originating session/user.
Must be consistent across storage and retrieval operations.

Example memory metadata:
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-01-15T14:30:00",
    "session_id": "user_123",  # <- This key
    "memory_type": "fact"
}
"""

DEFAULT_SESSION_ID = "default_user"
"""Fallback session ID when none is provided.

Used in single-user deployments or during migration from non-isolated system.
If you see this in production logs with ENABLE_SESSION_ISOLATION=True,
it means session_id is not being passed correctly from the application layer.

⚠️ Warning: Multiple users using DEFAULT_SESSION_ID will share memories
"""

# ==============================================================================
# MEMORY METADATA SCHEMA
# ==============================================================================

REQUIRED_METADATA_KEYS = ["id", "timestamp"]
"""Metadata keys that must be present in every stored memory.

These fields are validated before storage:
- id: Unique identifier (UUID v4)
- timestamp: ISO 8601 datetime string

Optional fields (recommended but not required):
- session_id: User/session identifier (required if ENABLE_SESSION_ISOLATION=True)
- memory_type: Classification (fact, preference, emotion, goal)
- importance: Numeric score 0.0-1.0
- source: Where the memory came from (chat, import, etc.)
"""

# ==============================================================================
# HEALTH CHECK AND MONITORING
# ==============================================================================

HEALTH_CHECK_TIMEOUT_SECONDS = 5
"""Timeout for Qdrant health checks during startup validation.

Quick timeout ensures fast failure detection without blocking startup.
Circuit breaker will handle retries for transient failures.

Values:
- Too low (<2s): False negatives from slow networks
- Too high (>10s): Slow startup, poor user experience
"""

COLLECTION_INITIALIZATION_RETRY_ATTEMPTS = 3
"""Number of times to retry collection creation on startup failure.

Handles transient failures during Docker container startup race conditions:
- Qdrant container not ready yet
- Network not fully initialized
- Resource constraints during multi-container startup

Retry backoff: 1s, 2s, 4s (exponential)
Total wait time: ~7 seconds max
"""

# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================

LOG_MEMORY_SEARCH_SCORES = True
"""Enable detailed logging of memory search similarity scores.

When enabled, logs each retrieved memory with its similarity score:
🔍 Memory: 'User enjoys hiking' (score: 0.92)
🔍 Memory: 'User prefers mountains over beach' (score: 0.87)

Useful for:
✅ Debugging retrieval relevance
✅ Tuning DUPLICATE_DETECTION_SIMILARITY_THRESHOLD
✅ Understanding semantic search behavior

Disable in production to reduce log volume.
"""

LOG_DUPLICATE_DETECTION = True
"""Log when duplicate memories are detected and skipped.

When enabled, logs:
♻️ Duplicate detected: 'User loves coffee' (similarity: 0.94 >= 0.90)

Useful for:
✅ Verifying deduplication is working
✅ Tuning similarity threshold
✅ Debugging why memories aren't being stored

Disable in production if log volume is a concern.
"""

LOG_CIRCUIT_BREAKER_EVENTS = True
"""Log circuit breaker state changes (CLOSED -> OPEN -> HALF_OPEN).

When enabled, logs:
⚡ Circuit breaker OPEN: Qdrant (10 failures)
⚡ Circuit breaker HALF_OPEN: Qdrant (testing recovery)
✅ Circuit breaker CLOSED: Qdrant (recovered)

Critical for:
✅ Detecting service outages
✅ Monitoring system health
✅ Alerting on degraded performance

Recommendation: Always keep enabled
"""
