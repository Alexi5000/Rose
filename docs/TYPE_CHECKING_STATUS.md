# Type Checking Status

## Overview

This document tracks the current state of type checking in the AI Companion codebase using mypy. It documents known type errors, type: ignore comments, and the rationale for each.

**Last Updated**: 2025-10-22  
**Mypy Version**: 1.13.0  
**Python Version**: 3.12+

## Summary

- **Total Errors**: 57 errors across 16 files
- **Files with Errors**: 16
- **Total Files Checked**: 52

## Configuration

Type checking is configured in `pyproject.toml` with the following key settings:

- `no_implicit_optional = true` - Requires explicit Optional[] for None defaults
- `disallow_incomplete_defs = true` - Functions must have complete type annotations
- `check_untyped_defs = true` - Check function bodies even without annotations
- Tests, notebooks, and scripts are excluded from type checking

## Known Issues by Category

### 1. Third-Party Library Type Incompatibilities

Many errors stem from incompatibilities between our code and third-party library type stubs, particularly LangChain/LangGraph.

#### ChatGroq API Key Type Mismatch
**Files Affected**: 
- `src/ai_companion/modules/image/text_to_image.py`
- `src/ai_companion/modules/memory/long_term/memory_manager.py`
- `src/ai_companion/graph/utils/helpers.py`

**Error**: `Argument "api_key" to "ChatGroq" has incompatible type "str"; expected "SecretStr | None"`

**Rationale**: The Groq library expects `SecretStr` type from pydantic, but our settings provide plain strings. This is a runtime-safe mismatch as the library accepts strings at runtime.

**Resolution Strategy**: Add `# type: ignore[arg-type]` with comment explaining the runtime safety.

#### ChatGroq Missing stop_sequences Argument
**Files Affected**:
- `src/ai_companion/modules/image/text_to_image.py`

**Error**: `Missing named argument "stop_sequences" for "ChatGroq"`

**Rationale**: The type stub for ChatGroq may be outdated or incorrect. The argument is optional at runtime.

**Resolution Strategy**: Add `# type: ignore[call-arg]` with comment explaining optional nature.

#### LangChain Chain Return Types
**Files Affected**:
- `src/ai_companion/modules/image/text_to_image.py`
- `src/ai_companion/graph/utils/chains.py`

**Error**: Return type mismatches for chain invocations

**Rationale**: LangChain's dynamic chain composition makes precise typing difficult. The actual runtime types are correct.

**Resolution Strategy**: Add `# type: ignore[return-value]` or `# type: ignore[union-attr]` with explanation.

### 2. Function Signature Issues

#### Circuit Breaker *args/**kwargs
**File**: `src/ai_companion/core/resilience.py`

**Error**: `Function is missing a type annotation for one or more arguments`

**Lines**: 164, 189 (call and call_async methods)

**Rationale**: The circuit breaker needs to accept arbitrary function signatures. Using `*args: Any, **kwargs: Any` would be more explicit.

**Resolution**: Update signature to `def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:`

#### Missing Return Type Annotations
**Files Affected**:
- `src/ai_companion/core/backup.py` (line 64)
- `src/ai_companion/interfaces/web/routes/voice.py` (line 301)
- `src/ai_companion/interfaces/web/app.py` (lines 40, 131, 206, 224)
- `src/ai_companion/interfaces/chainlit/app.py` (lines 129, 219)

**Rationale**: These functions need explicit return type annotations for complete type safety.

**Resolution**: Add appropriate return type annotations (None, Response, etc.)

### 3. Path Type Issues

#### Backup Module Path Handling
**File**: `src/ai_companion/core/backup.py`

**Error**: Incompatible types between str and Path

**Lines**: 40, 42, 132, 135, 136

**Rationale**: The code converts string paths to Path objects but the type annotations don't reflect this.

**Resolution**: Update type annotations to use `str | Path` or convert at function entry.

### 4. Optional/None Default Issues

#### Implicit Optional
**Files Affected**:
- `src/ai_companion/modules/image/text_to_image.py` (line 95)
- `src/ai_companion/interfaces/whatsapp/whatsapp_response.py` (line 231)

**Error**: `PEP 484 prohibits implicit Optional`

**Rationale**: With `no_implicit_optional = true`, None defaults must use `Optional[T]` or `T | None`.

**Resolution**: Change `chat_history: list = None` to `chat_history: list | None = None`

### 5. State and Message Type Issues

#### LangGraph State Type Mismatches
**Files Affected**:
- `src/ai_companion/graph/nodes.py` (lines 115, 258, 259, 297)
- `src/ai_companion/graph/edges.py` (line 16)

**Error**: Dict entry type mismatches, incompatible return types

**Rationale**: LangGraph's state typing is complex and the actual runtime types may differ from static analysis.

**Resolution**: Review state schema and add appropriate type casts or ignores.

#### Message Content Type
**Files Affected**:
- `src/ai_companion/modules/memory/long_term/memory_manager.py` (line 166)
- `src/ai_companion/interfaces/chainlit/app.py` (lines 174-177)

**Error**: `message.content` has type `str | list[str | dict[Any, Any]]` but string expected

**Rationale**: LangChain messages can have complex content types, but we typically handle strings.

**Resolution**: Add type guards or assertions to narrow the type.

### 6. Health Check Type Issues

**File**: `src/ai_companion/interfaces/web/routes/health.py`

**Error**: Variable reuse with incompatible types (Groq vs QdrantClient vs ElevenLabs)

**Lines**: 106, 108, 111, 121

**Rationale**: The `client` variable is reused for different client types in different health checks.

**Resolution**: Use different variable names for each client type.

### 7. Comparison with None

**File**: `src/ai_companion/modules/memory/long_term/vector_store.py`

**Error**: `Unsupported operand types for <= ("float" and "None")`

**Line**: 179

**Rationale**: `results[0].score` can be None, needs null check before comparison.

**Resolution**: Add explicit None check: `if results and results[0].score is not None and results[0].score >= ...`

## Type Ignore Comments

### Current Usage

No `# type: ignore` comments are currently in the codebase. All errors are unresolved.

### Recommended Additions

For errors that cannot be easily fixed due to third-party library limitations:

```python
# Example for ChatGroq api_key
llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,  # type: ignore[arg-type]  # Runtime accepts str despite SecretStr type hint
    model=settings.LLM_MODEL_NAME,
)
```

## Action Items

### High Priority (Core Functionality)

1. ✅ Fix circuit breaker function signatures (resilience.py)
2. ✅ Fix Path type issues in backup.py
3. ✅ Fix implicit Optional issues
4. ✅ Fix health check variable reuse
5. ✅ Fix vector store None comparison

### Medium Priority (Type Safety)

6. Add return type annotations to all functions
7. Fix LangGraph state type mismatches
8. Add type guards for message content

### Low Priority (Third-Party)

9. Add type: ignore comments for ChatGroq API key issues
10. Add type: ignore comments for LangChain chain return types
11. Document all type: ignore comments in this file

## Testing Strategy

Type checking is run as part of the development workflow:

```bash
# Run mypy on source code
uv run mypy src/

# Run mypy with verbose output
uv run mypy src/ --verbose

# Run mypy and show error context
uv run mypy src/ --show-error-context
```

## Future Improvements

1. **Gradual Typing**: Enable stricter mypy settings as type coverage improves
2. **Custom Type Stubs**: Create custom type stubs for libraries with poor typing
3. **Type Testing**: Add tests that verify type correctness using mypy's test framework
4. **CI Integration**: Add mypy to CI pipeline with error threshold
5. **Type Coverage Metrics**: Track type coverage percentage over time

## References

- [Mypy Documentation](https://mypy.readthedocs.io/)
- [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/)
- [PEP 526 - Syntax for Variable Annotations](https://www.python.org/dev/peps/pep-0526/)
- [LangChain Type Hints](https://python.langchain.com/docs/guides/development/typing/)
