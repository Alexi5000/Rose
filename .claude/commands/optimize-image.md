# Optimize Docker Image Size

Remove 2.5GB CUDA/PyTorch dependencies to reduce image from ~3GB to ~300MB (90% reduction).

## Problem Overview

**Current State:**
- Docker image: ~3GB
- Root cause: `sentence-transformers==3.3.1` dependency
- Pulls in: torch, CUDA libraries, triton, nvidia-* packages
- Total CUDA bloat: ~2.5GB

**Why We Have It:**
- Used for local embeddings in `src/ai_companion/modules/memory/long_term/vector_store.py`
- Line 57: `from sentence_transformers import SentenceTransformer`
- Line 95: `EMBEDDING_MODEL = "all-MiniLM-L6-v2"`

**Impact:**
- Slower deployments
- Higher storage costs
- Unnecessary complexity (we already use Groq API for everything else)

## Optimization Strategy

### Option 1: Switch to Groq Embeddings (Recommended)

Groq may support embeddings - need to verify.

**Pros:**
- Use existing Groq API integration
- No additional API costs if included
- Consistent with current architecture

**Cons:**
- Need to verify Groq supports embeddings
- May need to switch if not available

### Option 2: Switch to OpenAI Embeddings

Use OpenAI's text-embedding-3-small model.

**Pros:**
- Well-documented and reliable
- Excellent embedding quality
- Lightweight API call

**Cons:**
- Additional API key needed
- Small cost per embedding (~$0.00002 per 1K tokens)

### Option 3: Use Voyage AI or Cohere Embeddings

Alternative embedding providers.

**Pros:**
- May be cheaper than OpenAI
- Good quality embeddings

**Cons:**
- Additional API integration
- Another API key to manage

## Implementation Steps

### Step 1: Research Embedding Options

```bash
# Check if Groq supports embeddings
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY" | \
  jq '.data[] | select(.id | contains("embed"))'

# If no results, Groq doesn't support embeddings yet
```

### Step 2: Choose Embedding Provider

**If Groq doesn't support embeddings, use OpenAI:**

1. Add to `.env`:
   ```bash
   OPENAI_API_KEY=sk-your-key-here
   ```

2. Add to `pyproject.toml` dependencies:
   ```toml
   "openai==1.58.1",  # Already have this for compatibility
   ```

3. Remove from `pyproject.toml`:
   ```toml
   "sentence-transformers==3.3.1",  # DELETE THIS LINE
   ```

### Step 3: Update Vector Store Code

**File**: `src/ai_companion/modules/memory/long_term/vector_store.py`

**Before** (lines 51-62):
```python
try:
    from qdrant_client import QdrantClient, models
    from qdrant_client.http import models as rest
    from sentence_transformers import SentenceTransformer  # ← REMOVE THIS

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logger.warning("⚠️ qdrant-client or sentence-transformers not available")
```

**After**:
```python
try:
    from qdrant_client import QdrantClient, models
    from qdrant_client.http import models as rest
    from openai import OpenAI  # ← ADD THIS

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logger.warning("⚠️ qdrant-client or openai not available")
```

**Before** (lines 90-101):
```python
# Embedding model configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # ← REMOVE THIS
EMBEDDING_DIM = 384  # Dimension for all-MiniLM-L6-v2

# Initialize embedding model lazily
_embedding_model: Optional[SentenceTransformer] = None  # ← CHANGE THIS
```

**After**:
```python
# Embedding model configuration
EMBEDDING_MODEL = "text-embedding-3-small"  # OpenAI model
EMBEDDING_DIM = 1536  # Dimension for text-embedding-3-small

# Initialize OpenAI client lazily
_openai_client: Optional[OpenAI] = None
```

**Before** (lines 103-112):
```python
def get_embedding_model() -> SentenceTransformer:
    """Get or initialize the embedding model."""
    global _embedding_model
    if _embedding_model is None:
        logger.info("embedding_model_initialization", model=EMBEDDING_MODEL)
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info("✅ embedding_model_loaded", model=EMBEDDING_MODEL, dim=EMBEDDING_DIM)
    return _embedding_model
```

**After**:
```python
def get_embedding_model() -> OpenAI:
    """Get or initialize the OpenAI client for embeddings."""
    global _openai_client
    if _openai_client is None:
        from ai_companion.settings import settings
        logger.info("🔌 openai_client_initialization")
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("✅ openai_client_initialized", model=EMBEDDING_MODEL)
    return _openai_client
```

**Before** (lines 250-260):
```python
def _generate_embedding(self, text: str) -> List[float]:
    """Generate embedding for text."""
    try:
        model = get_embedding_model()
        embedding = model.encode(text, show_progress_bar=False)
        return embedding.tolist()
    except Exception as e:
        logger.error("❌ embedding_generation_failed", error=str(e), exc_info=True)
        raise
```

**After**:
```python
def _generate_embedding(self, text: str) -> List[float]:
    """Generate embedding for text using OpenAI API."""
    try:
        client = get_embedding_model()
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        embedding = response.data[0].embedding
        logger.info("✅ embedding_generated", length=len(embedding))
        return embedding
    except Exception as e:
        logger.error("❌ embedding_generation_failed", error=str(e), exc_info=True)
        raise
```

### Step 4: Update Settings

**File**: `src/ai_companion/settings.py`

Add OPENAI_API_KEY to settings:

```python
class Settings(BaseSettings):
    # ... existing fields ...

    # OpenAI API (for embeddings)
    OPENAI_API_KEY: str = Field(
        ...,
        description="OpenAI API key for text embeddings"
    )
```

### Step 5: Update Dependencies

```bash
# Remove sentence-transformers and its CUDA deps
# This is done by editing pyproject.toml

# Regenerate lock file
uv lock

# Verify torch is removed from dependencies
uv tree | grep -i torch
# Should be empty
```

### Step 6: Rebuild Docker Image

```bash
# Clean rebuild
docker-compose down
docker rmi rose-rose:latest
docker-compose build rose

# Monitor build - should be MUCH faster
# Expected: 1-2 minutes (vs 7-11 minutes before)
```

### Step 7: Verify Image Size

```bash
# Check new image size
docker images rose-rose:latest

# Expected output:
# REPOSITORY   TAG      SIZE
# rose-rose    latest   ~300MB  ← Down from 3GB!
```

### Step 8: Test Embeddings Work

```bash
# Start containers
docker-compose up -d

# Create test session and use voice
# Verify memories are still stored in Qdrant

# Check logs for embedding generation
docker-compose logs rose | grep "embedding_generated"
```

## Verification Checklist

```
□ Groq embedding support checked
□ OpenAI API key added to .env
□ sentence-transformers removed from pyproject.toml
□ vector_store.py updated to use OpenAI
□ settings.py updated with OPENAI_API_KEY
□ Docker image rebuilt
□ Image size verified (~300MB)
□ Build time reduced (1-2 min)
□ Voice interaction still works
□ Memories stored in Qdrant
□ Embedding generation logged
□ No CUDA warnings in logs
```

## Expected Results

### Before Optimization:
```
Docker Image Size: 2.98 GB
Build Time: 7-11 minutes
CUDA Libraries: ~2.5 GB
- torch==2.5.1 (864 MB)
- nvidia-cudnn-cu12 (634 MB)
- nvidia-cublas-cu12 (346 MB)
- nvidia-nccl-cu12 (179 MB)
- nvidia-cufft-cu12 (201 MB)
- triton (199 MB)
- nvidia-cusolver-cu12 (122 MB)
- + 15 more CUDA packages
```

### After Optimization:
```
Docker Image Size: ~300 MB (90% reduction!)
Build Time: 1-2 minutes (80% faster!)
Embedding: OpenAI API (text-embedding-3-small)
Cost: ~$0.00002 per 1K tokens
```

## Cost Analysis

**Embedding Costs** (OpenAI text-embedding-3-small):
- Cost: $0.00002 per 1,000 tokens
- Average message: ~100 tokens
- Cost per embedding: $0.000002 (negligible!)
- 1,000 conversations: $0.002 (less than a penny!)

**Savings:**
- Faster deployments: Save developer time
- Lower storage costs: 2.7GB less per instance
- Faster cold starts: 90% less to download

## Rollback Plan

If issues occur:

```bash
# Restore sentence-transformers
# 1. Re-add to pyproject.toml:
#    "sentence-transformers==3.3.1",

# 2. Restore vector_store.py from git:
git checkout HEAD -- src/ai_companion/modules/memory/long_term/vector_store.py

# 3. Rebuild:
docker-compose build rose
```

## Documentation Updates

After optimization, update:
1. `DEPLOYMENT_STATUS.md` - Remove "CUDA Bloat" issue
2. `README.md` - Update image size specs
3. `.env.example` - Add OPENAI_API_KEY
4. `CLAUDE.md` - Update architecture docs

## Success Criteria

✅ Docker image < 500MB
✅ Build time < 3 minutes
✅ Voice interaction still works
✅ Memories stored and retrieved correctly
✅ No CUDA libraries in dependencies
✅ Embedding generation logged successfully
