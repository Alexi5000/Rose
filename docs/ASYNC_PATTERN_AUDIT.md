# Async Pattern Audit Report

## Overview
This document identifies async/await pattern inconsistencies in the AI Companion codebase, including blocking I/O operations in async functions and unnecessary sync-to-async conversions.

## Findings

### 1. Blocking I/O in Async Functions

#### 1.1 File Operations in `graph/nodes.py`
**Location**: `src/ai_companion/graph/nodes.py:119-120`
**Issue**: Synchronous file operations in async function `image_node()`
```python
async def image_node(state: AICompanionState, config: RunnableConfig) -> dict[str, AIMessage | str]:
    # ...
    os.makedirs("generated_images", exist_ok=True)  # Blocking I/O
    img_path = f"generated_images/image_{str(uuid4())}.png"
    await text_to_image_module.generate_image(scenario.image_prompt, img_path)
```
**Impact**: Blocks event loop during directory creation
**Recommendation**: Use `aiofiles` or `asyncio.to_thread()` for file operations

#### 1.2 File Operations in `interfaces/chainlit/app.py`
**Location**: `src/ai_companion/interfaces/chainlit/app.py:107-109`
**Issue**: Synchronous file reading in async function `on_message()`
```python
async def on_message(message: cl.Message):
    # ...
    with open(elem.path, "rb") as f:  # Blocking I/O
        image_bytes = f.read()
```
**Impact**: Blocks event loop during image file reading
**Recommendation**: Use `aiofiles` for async file reading

#### 1.3 File Operations in `whatsapp/whatsapp_response.py`
**Location**: `src/ai_companion/interfaces/whatsapp/whatsapp_response.py:133`
**Issue**: Synchronous file reading in async function `whatsapp_handler()`
```python
async def whatsapp_handler(request: Request) -> Response:
    # ...
    with open(image_path, "rb") as f:  # Blocking I/O
        image_data = f.read()
```
**Impact**: Blocks event loop during image file reading
**Recommendation**: Use `aiofiles` for async file reading

#### 1.4 Synchronous Sleep in `speech_to_text.py`
**Location**: `src/ai_companion/modules/speech/speech_to_text.py:127`
**Issue**: Using `time.sleep()` instead of `asyncio.sleep()` in async context
```python
async def transcribe(self, audio_data: bytes, audio_format: Optional[str] = None) -> str:
    # ...
    time.sleep(backoff_time)  # Blocking sleep in async function
```
**Impact**: Blocks entire event loop during retry backoff
**Recommendation**: Use `await asyncio.sleep(backoff_time)`

#### 1.5 Temporary File Operations in `speech_to_text.py`
**Location**: `src/ai_companion/modules/speech/speech_to_text.py:88-106`
**Issue**: Synchronous file operations in async function
```python
async def transcribe(self, audio_data: bytes, audio_format: Optional[str] = None) -> str:
    # ...
    with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as temp_file:  # Blocking I/O
        temp_file.write(audio_data)
        temp_file_path = temp_file.name
    
    with open(temp_file_path, "rb") as audio_file:  # Blocking I/O
        # ...
    
    os.unlink(temp_file_path)  # Blocking I/O
```
**Impact**: Multiple blocking I/O operations in async function
**Recommendation**: Use `aiofiles` and `asyncio.to_thread()` for file operations

### 2. Sync-to-Async Conversions

#### 2.1 Circuit Breaker Sync Wrapper in Async Context
**Location**: `src/ai_companion/modules/speech/speech_to_text.py:97-102`
**Issue**: Using synchronous circuit breaker `call()` method in async function
```python
async def transcribe(self, audio_data: bytes, audio_format: Optional[str] = None) -> str:
    # ...
    def _call_groq_api() -> str:
        return self.client.audio.transcriptions.create(...)
    
    transcription: str = self._circuit_breaker.call(_call_groq_api)  # Sync call in async function
```
**Impact**: Blocks event loop during API call
**Recommendation**: Use `self._circuit_breaker.call_async()` instead

#### 2.2 Circuit Breaker Sync Wrapper in TTS
**Location**: `src/ai_companion/modules/speech/text_to_speech.py:88-97`
**Issue**: Using synchronous circuit breaker `call()` method in async function
```python
async def synthesize(self, text: str, ...) -> bytes:
    # ...
    def _call_elevenlabs_api() -> bytes:
        audio_generator = self.client.generate(...)
        return b"".join(audio_generator)
    
    audio_bytes: bytes = self._circuit_breaker.call(_call_elevenlabs_api)  # Sync call in async function
```
**Impact**: Blocks event loop during API call
**Recommendation**: Use `self._circuit_breaker.call_async()` instead

#### 2.3 Synchronous Memory Operations in Async Context
**Location**: `src/ai_companion/graph/nodes.py:248-256`
**Issue**: Calling synchronous methods in async function `memory_injection_node()`
```python
def memory_injection_node(state: AICompanionState) -> dict[str, str]:
    memory_manager = get_memory_manager()
    recent_context = " ".join([m.content for m in state["messages"][-3:]])
    memories = memory_manager.get_relevant_memories(recent_context)  # Sync call
    memory_context = memory_manager.format_memories_for_prompt(memories)  # Sync call
    return {"memory_context": memory_context}
```
**Impact**: This is actually a sync function, but it's called from async graph execution
**Recommendation**: Make this function async and update memory manager methods to be async

### 3. Missing Async Context Managers

#### 3.1 HTTP Client Context Management
**Location**: Multiple locations in `whatsapp/whatsapp_response.py`
**Issue**: Creating new `httpx.AsyncClient()` for each request instead of reusing
```python
async with httpx.AsyncClient() as client:
    # Single request
```
**Impact**: Connection overhead for each request
**Recommendation**: Use a module-level client with proper lifecycle management

### 4. Proper Async Patterns (Good Examples)

#### 4.1 Async Context Manager Usage
**Location**: `src/ai_companion/interfaces/chainlit/app.py:125`
```python
async with AsyncSqliteSaver.from_conn_string(settings.SHORT_TERM_MEMORY_DB_PATH) as short_term_memory:
    graph = graph_builder.compile(checkpointer=short_term_memory)
```
**Status**: ✅ Correct async pattern

#### 4.2 Async Timeout Usage
**Location**: `src/ai_companion/interfaces/chainlit/app.py:129`
```python
async with asyncio.timeout(settings.WORKFLOW_TIMEOUT_SECONDS):
    async for chunk in graph.astream(...):
        # Process chunks
```
**Status**: ✅ Correct async pattern

#### 4.3 Async HTTP Requests
**Location**: `src/ai_companion/interfaces/whatsapp/whatsapp_response.py:152-156`
```python
async with httpx.AsyncClient() as client:
    metadata_response = await client.get(media_metadata_url, headers=headers)
    metadata_response.raise_for_status()
```
**Status**: ✅ Correct async pattern

## Summary

### Critical Issues (High Priority)
1. **Blocking sleep in async function** - `time.sleep()` in `speech_to_text.py`
2. **Sync circuit breaker calls in async functions** - Both STT and TTS modules
3. **Blocking file I/O in async functions** - Multiple locations

### Medium Priority
4. **Temporary file operations** - Could be optimized with async I/O
5. **HTTP client reuse** - Connection pooling optimization

### Low Priority
6. **Memory operations** - Currently sync, but may not need to be async

## Recommendations

### Immediate Actions
1. Replace `time.sleep()` with `asyncio.sleep()` in retry logic
2. Use `call_async()` instead of `call()` for circuit breaker in async functions
3. Use `aiofiles` or `asyncio.to_thread()` for file operations in async functions

### Future Improvements
1. Consider making memory operations async if they become a bottleneck
2. Implement connection pooling for HTTP clients
3. Add async linting rules to prevent future regressions

## Requirements Addressed
- **7.1**: Identified blocking I/O operations in async functions
- **7.2**: Identified unnecessary sync-to-async conversions
- **7.3**: Documented findings with specific locations and recommendations
