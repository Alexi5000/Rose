# Implementation Plan

- [x] 1. Set up test infrastructure and fixtures

  - Create test directory structure with unit/, integration/, and fixtures/ subdirectories
  - Add pytest configuration for async tests and coverage reporting
  - Create mock fixtures for Groq, ElevenLabs, and Qdrant clients
  - Create sample audio files for STT testing (WAV, MP3 formats)
  - Add pytest-asyncio, pytest-mock, pytest-cov to development dependencies
  - _Requirements: 1.1, 1.5_

- [x] 2. Implement unit tests for Memory Manager module

  - [x] 2.1 Create test_memory_manager.py with test class structure

    - Write tests for memory extraction from HumanMessage
    - Write tests for memory storage with duplicate detection
    - Write tests for relevant memory retrieval with various contexts
    - Write tests for memory formatting for prompts
    - Mock Qdrant vector store operations
    - _Requirements: 1.2_

  - [x] 2.2 Create test_vector_store.py for vector store operations

    - Write tests for storing memories in Qdrant
    - Write tests for searching memories with similarity scores
    - Write tests for finding similar memories (duplicate detection)
    - Mock Qdrant client responses
    - _Requirements: 1.2_

- [x] 3. Implement unit tests for Speech-to-Text module

  - [x] 3.1 Create test_speech_to_text_unit.py with comprehensive test coverage

    - Write tests for transcribing WAV format audio
    - Write tests for transcribing MP3 format audio
    - Write tests for audio format auto-detection
    - Write tests for retry logic with exponential backoff
    - Write tests for circuit breaker integration
    - Write tests for error handling (empty audio, oversized audio, invalid format)
    - Mock Groq client transcription calls
    - _Requirements: 1.3_

- [x] 4. Implement unit tests for Text-to-Speech module

  - [x] 4.1 Create test_text_to_speech_unit.py with caching and fallback tests

    - Write tests for basic text-to-speech synthesis
    - Write tests for caching behavior (cache hit, cache miss, cache expiration)
    - Write tests for fallback behavior when TTS fails
    - Write tests for circuit breaker integration
    - Write tests for error handling (empty text, oversized text)
    - Write tests for cache warming with common phrases
    - Mock ElevenLabs client synthesis calls
    - _Requirements: 1.4_

- [x] 5. Implement integration tests for LangGraph workflow

  - [x] 5.1 Create test_workflow_integration.py for end-to-end flows

    - Write test for complete conversation workflow (message → memory → router → response)
    - Write test for audio workflow (audio input → STT → processing → TTS → audio output)
    - Write test for memory extraction and injection in workflow
    - Write test for conversation summarization trigger
    - Write test for workflow timeout handling
    - Mock external API calls but use real LangGraph execution
    - _Requirements: 1.5_

- [x] 6. Refactor error handler decorators to eliminate duplication

  - [x] 6.1 Extract common error handling logic in error_handlers.py

    - Create shared error handling function that works for both sync and async
    - Refactor handle_api_errors to use single implementation with introspection
    - Refactor handle_workflow_errors to use single implementation
    - Refactor handle_memory_errors to use single implementation
    - Refactor handle_validation_errors to use single implementation
    - Ensure backward compatibility with existing decorator usage
    - _Requirements: 2.2, 4.2_

  - [x] 6.2 Write tests for refactored error handlers

    - Test sync function error handling
    - Test async function error handling
    - Test error logging and metrics recording
    - Test user-facing error messages
    - _Requirements: 2.2, 4.4_

- [x] 7. Refactor circuit breaker to eliminate duplication

  - [x] 7.1 Extract common state management logic in resilience.py

    - Create \_check_circuit_state() method for state checking and transitions
    - Create \_handle_success() method for successful call handling
    - Create \_handle_failure() method for failed call handling
    - Refactor call() method to use extracted methods
    - Refactor call_async() method to use extracted methods
    - Ensure backward compatibility with existing circuit breaker usage
    - _Requirements: 2.3, 2.4, 4.3_

  - [x] 7.2 Write tests for refactored circuit breaker

    - Test circuit state transitions (CLOSED → OPEN → HALF_OPEN → CLOSED)
    - Test failure counting and threshold
    - Test recovery timeout behavior
    - Test sync and async call methods
    - _Requirements: 2.3, 2.4_

- [x] 8. Add type hints to graph nodes module

  - Add return type hints to router_node function
  - Add return type hints to context_injection_node function
  - Add return type hints to conversation_node function
  - Add return type hints to image_node function
  - Add return type hints to audio_node function
  - Add return type hints to summarize_conversation_node function
  - Add return type hints to memory_extraction_node function
  - Add return type hints to memory_injection_node function
  - _Requirements: 3.2_

- [x] 9. Add type hints to memory modules

  - Add type hints to MemoryManager class methods
  - Add type hints to vector store functions
  - Add type hints to memory analysis functions
  - Create type aliases for common memory types (MemorySearchResult, etc.)
  - _Requirements: 3.3_

- [x] 10. Add type hints to speech modules

  - Add type hints to SpeechToText class methods
  - Add type hints to TextToSpeech class methods
  - Add type hints to audio processing utility functions
  - _Requirements: 3.4_

- [x] 11. Add type hints to graph utilities

  - Add type hints to get_chat_model function
  - Add type hints to get_text_to_speech_module function
  - Add type hints to get_text_to_image_module function
  - Add type hints to chain construction functions
  - Add type hints to AsteriskRemovalParser class
  - _Requirements: 3.2_

- [x] 12. Set up mypy validation

  - [x] 12.1 Add mypy configuration file (mypy.ini or pyproject.toml section)

    - Configure mypy for strict type checking
    - Set up exclusions for third-party code without type stubs
    - Configure mypy to check all Python files in src/
    - _Requirements: 3.5_

  - [x] 12.2 Run mypy and fix any type errors

    - Run mypy on entire codebase
    - Fix any type errors or inconsistencies
    - Add type: ignore comments only where absolutely necessary with explanations
    - _Requirements: 3.5_

- [x] 13. Refactor Chainlit interface module initialization

  - [x] 13.1 Replace global module instances with factory functions

    - Create get_speech_to_text() factory function
    - Create get_text_to_speech() factory function
    - Create get_image_to_text() factory function
    - Update on_message handler to use factory functions
    - Update on_audio_end handler to use factory functions
    - _Requirements: 5.1, 5.2_

  - [x] 13.2 Implement session-scoped module instances

    - Store module instances in cl.user_session
    - Initialize modules in on_chat_start handler
    - Retrieve modules from session in message handlers
    - Document module lifecycle in code comments
    - _Requirements: 5.3, 5.4, 5.5_

- [x] 14. Enhance configuration validation

  - [x] 14.1 Add range validators for numeric configuration values

    - Add validator for MEMORY_TOP_K (1-20 range)
    - Add validator for CIRCUIT_BREAKER_FAILURE_THRESHOLD (1-10 range)
    - Add validator for LLM*TEMPERATURE*\* values (0.0-1.0 range)
    - Add validator for timeout values (positive numbers)
    - _Requirements: 6.4_

  - [x] 14.2 Add cross-field validation for related settings

    - Add validator for DATABASE_URL when FEATURE_DATABASE_TYPE is postgresql
    - Add validator for WHATSAPP\_\* fields when FEATURE_WHATSAPP_ENABLED is true
    - Add validator for SENTRY_DSN when monitoring is enabled
    - Provide detailed error messages with remediation steps
    - _Requirements: 6.2, 6.3_

  - [x] 14.3 Add startup connectivity validation

    - Add optional validation for Qdrant connectivity
    - Add optional validation for database connectivity
    - Log warnings for connectivity issues without blocking startup
    - _Requirements: 6.1, 6.5_

- [x] 15. Improve async/await pattern consistency

  - [x] 15.1 Audit codebase for async pattern inconsistencies

    - Identify blocking I/O operations in async functions
    - Identify unnecessary sync-to-async conversions
    - Document findings in code review comments
    - _Requirements: 7.1, 7.2_

  - [x] 15.2 Fix async pattern issues

    - Replace blocking I/O with async equivalents where possible
    - Add proper async context managers for resource management
    - Document any necessary sync-to-async bridges with rationale
    - _Requirements: 7.3, 7.4_

  - [x] 15.3 Configure ruff for async pattern linting

    - Add async-specific ruff rules to pyproject.toml
    - Run ruff with async rules and fix any violations
    - _Requirements: 7.5_

- [x] 16. Enhance documentation and code comments

  - [x] 16.1 Add comprehensive docstrings to core modules

    - Add module-level docstrings describing module responsibilities
    - Add docstrings to all public functions with parameter descriptions
    - Add usage examples to complex functions
    - Document return types and exceptions raised
    - _Requirements: 8.1, 8.2, 8.5_

  - [x] 16.2 Add inline comments for complex logic

    - Add comments explaining circuit breaker state transitions
    - Add comments explaining retry logic and backoff calculations
    - Add comments explaining memory extraction and formatting
    - Add comments for non-obvious implementation decisions
    - _Requirements: 8.3_

  - [x] 16.3 Document architectural patterns

    - Create or update ARCHITECTURE.md with circuit breaker pattern
    - Document retry pattern with exponential backoff
    - Document module initialization patterns
    - Add references to design documents in code comments
    - _Requirements: 8.4_

- [x] 17. Validate dependency boundaries

  - [x] 17.1 Analyze module dependencies

    - Use import analysis tools to map dependencies
    - Identify circular dependencies
    - Identify interface-to-core dependencies that should be reversed
    - Document findings
    - _Requirements: 9.1, 9.5_

  - [x] 17.2 Refactor problematic dependencies

    - Break circular dependencies using dependency injection
    - Ensure core modules don't depend on interface implementations
    - Update module-level docstrings with dependency information
    - _Requirements: 9.2, 9.3, 9.4_

- [x] 18. Run full test suite and validate coverage

  - [x] 18.1 Execute all unit and integration tests

    - Run pytest with coverage reporting
    - Verify >70% overall coverage, >80% for core modules
    - Fix any failing tests
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 18.2 Generate and review coverage report

    - Identify modules below coverage targets
    - Add additional tests for uncovered code paths
    - Document any intentionally untested code with rationale
    - _Requirements: 1.1_

- [x] 19. Performance validation and optimization

  - [x] 19.1 Add performance benchmarks to test suite

    - Add benchmark for memory extraction (<500ms)
    - Add benchmark for memory retrieval (<200ms)
    - Add benchmark for STT transcription (<2s for 10s audio)
    - Add benchmark for TTS synthesis (<1s for 100 words)
    - Add benchmark for end-to-end workflow (<5s)
    - _Requirements: 10.5_

  - [x] 19.2 Identify and document performance optimization opportunities

    - Profile critical code paths

    - Identify operations that could be parallelized
    - Document performance-critical code with timing expectations
    - Create performance optimization backlog items
    - _Requirements: 10.1, 10.2, 10.3, 10.4_


- [x] 20. Final validation and documentation

  - [x] 20.1 Run mypy type checking on entire codebase

    - Verify zero mypy errors
    - Document any type: ignore comments with explanations
    - _Requirements: 3.5_

  - [x] 20.2 Run code quality tools

    - Run ruff linter and fix any violations
    - Run code duplication detector (radon or similar)
    - Verify <5% code duplication
    - _Requirements: 2.5, 7.5_

  - [x] 20.3 Update project documentation

    - Update README with testing instructions
    - Update ARCHITECTURE.md with refactored patterns
    - Create CONTRIBUTING.md with code quality standards
    - Document all new testing utilities and fixtures
    - _Requirements: 8.1, 8.2, 8.4, 8.5_

  - [x] 20.4 Create developer guide

    - Document common patterns (error handling, circuit breakers, async)
    - Provide examples of adding new features with tests
    - Document module initialization patterns
    - Include troubleshooting guide for common issues
    - _Requirements: 5.5, 8.3, 8.4_
