# Async Pattern Fixes Summary

## Overview
This document summarizes the async/await pattern improvements made to the AI Companion codebase to eliminate blocking I/O operations and ensure consistent async patterns throughout.

## Changes Made

### 1. Fixed Blocking Sleep Operations
**File**: `src/ai_companion/modules/speech/speech_to_text.py`
- **Issue**: Used `time.sleep()` in async function, blocking the event loop
- **Fix**: Replaced with `await asyncio.sleep()` for non-blocking sleep
- **Impact**: Prevents event loop blocking during retry backoff

### 2. Fixed Circuit Breaker Usage in Async Functions
**Files**: 
- `src/ai_companion/modules/speech/speech_to_text.py`
- `src/ai_companion/modules/speech/text_to_speech.py`

- **Issue**: Used synchronous `circuit_breaker.call()` in async functions
- **Fix**: Changed to `await circuit_breaker.call_async()` with proper async wrappers
- **Rationale**: Groq and ElevenLabs SDKs are synchronous, so we use `asyncio.to_thread()` to run them in a thread pool
- **Impact**: Prevents event loop blocking during API calls

### 3. Fixed File I/O Operations
**Files**:
- `src/ai_companion/interfaces/chainlit/app.py`
- `src/ai_companion/interfaces/whatsapp/whatsapp_response.py`
- `src/ai_companion/modules/image/image_to_text.py`
- `src/ai_companion/modules/image/text_to_image.py`
- `src/ai_companion/graph/nodes.py`

- **Issue**: Used synchronous `open()` and `os.makedirs()` in async functions
- **Fix**: Replaced with `aiofiles` for async file operations and `asyncio.to_thread()` for directory creation
- **Impact**: Prevents event loop blocking during file I/O

### 4. Fixed Temporary File Operations
**File**: `src/ai_companion/modules/speech/speech_to_text.py`
- **Issue**: Multiple synchronous file operations in async function
- **Fix**: Moved file operations into thread pool using `asyncio.to_thread()`
- **Rationale**: `tempfile.NamedTemporaryFile` doesn't have an async equivalent, so we use thread pool
- **Impact**: Minimizes event loop blocking

### 5. Fixed API Calls in Async Functions
**Files**:
- `src/ai_companion/modules/image/image_to_text.py`
- `src/ai_companion/modules/image/text_to_image.py`

- **Issue**: Synchronous Groq and Together API calls in async functions
- **Fix**: Wrapped API calls with `asyncio.to_thread()` to run in thread pool
- **Rationale**: These SDKs don't provide native async support
- **Impact**: Prevents event loop blocking during API calls

### 6. Added Async Linting Rules
**File**: `pyproject.toml`
- **Change**: Added `ASYNC` rule set to ruff configuration
- **Purpose**: Automatically detect blocking operations in async functions
- **Rules**: Catches `time.sleep()`, `open()`, and other blocking calls in async contexts

### 7. Added aiofiles Dependency
**File**: `pyproject.toml`
- **Change**: Added `aiofiles>=23.1.0,<24.0.0` to dependencies
- **Purpose**: Enable async file I/O operations
- **Note**: Version constraint matches Chainlit's requirements

## Documentation Added

### Sync-to-Async Bridges
All sync-to-async conversions are now documented with comments explaining:
- Why the bridge is necessary (SDK doesn't provide async support)
- How it works (using `asyncio.to_thread()`)
- What it prevents (event loop blocking)

### Examples:
```python
# Note: Groq SDK is synchronous, so we use asyncio.to_thread() to run it
# in a thread pool, preventing event loop blocking. This is necessary
# because the Groq client doesn't provide native async support.
async def _call_groq_api() -> str:
    return await asyncio.to_thread(...)
```

## Verification

### Ruff Async Checks
All async pattern checks now pass:
```bash
uv tool run ruff check src/ --select ASYNC
# Result: All checks passed!
```

### Test Coverage
The existing test suite continues to pass with these changes, confirming backward compatibility.

## Benefits

1. **No Event Loop Blocking**: All blocking operations now run in thread pools or use async equivalents
2. **Better Concurrency**: Multiple requests can be processed concurrently without blocking
3. **Improved Performance**: Async operations allow better resource utilization
4. **Automatic Detection**: Ruff will catch future async pattern violations
5. **Clear Documentation**: All sync-to-async bridges are documented with rationale

## Future Improvements

1. **Monitor SDK Updates**: Watch for async versions of Groq, ElevenLabs, and Together SDKs
2. **Connection Pooling**: Consider implementing connection pooling for HTTP clients
3. **Async Memory Operations**: Evaluate if memory operations would benefit from being async

## Requirements Addressed

- **7.1**: ✅ Identified blocking I/O operations in async functions
- **7.2**: ✅ Identified unnecessary sync-to-async conversions
- **7.3**: ✅ Replaced blocking I/O with async equivalents
- **7.4**: ✅ Added proper async context managers and documented bridges
- **7.5**: ✅ Configured ruff for async pattern linting
