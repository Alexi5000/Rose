# Implementation Plan

- [ ] 1. Update settings module for PlayAI configuration
  - Replace ELEVENLABS_API_KEY with PLAYAI_API_KEY in Settings class
  - Replace ELEVENLABS_VOICE_ID with PLAYAI_VOICE_ID in Settings class
  - Update TTS_MODEL_NAME default value to PlayAI model identifier
  - Update REQUIRED_ENV_VARS list in TextToSpeech class
  - Update field validators to validate PlayAI credentials
  - Remove or repurpose ROSE_VOICE_ID for PlayAI voice selection
  - _Requirements: 1.4, 3.1, 3.2, 3.3_

- [ ] 2. Update environment configuration files
  - Replace ElevenLabs configuration with PlayAI in .env.example
  - Update comments to reference PlayAI TTS service
  - Provide example PlayAI API key format
  - Update Rose-specific voice configuration section
  - _Requirements: 3.2, 4.2_

- [ ] 3. Implement PlayAI HTTP client in TextToSpeech class
  - Remove ElevenLabs SDK imports (elevenlabs package)
  - Add httpx import for async HTTP client
  - Replace ElevenLabs client initialization with httpx AsyncClient
  - Update client property to return httpx client instance
  - Implement PlayAI API request structure (POST to TTS endpoint)
  - Add authentication header with PlayAI API key
  - Map voice parameters (stability, similarity_boost) to PlayAI equivalents
  - Handle binary audio response from PlayAI API
  - _Requirements: 1.1, 1.3, 1.4_

- [ ] 4. Update error handling for PlayAI-specific responses
  - Handle 401/403 authentication errors with clear messages
  - Handle 429 rate limiting errors
  - Handle 400 validation errors
  - Handle 500/502/503 service errors
  - Handle network timeout and connection errors
  - Update error messages to reference PlayAI instead of ElevenLabs
  - Ensure TextToSpeechError exceptions maintain same interface
  - _Requirements: 1.3, 2.3, 3.4_

- [ ] 5. Update circuit breaker configuration
  - Create get_playai_circuit_breaker() function in resilience.py
  - Configure circuit breaker thresholds for PlayAI API
  - Update TextToSpeech class to use PlayAI circuit breaker
  - Remove or deprecate get_elevenlabs_circuit_breaker() function
  - Test circuit breaker behavior with PlayAI API failures
  - _Requirements: 1.1, 2.3_

- [ ] 6. Update cache key generation for PlayAI
  - Modify _get_cache_key() to use PlayAI voice parameters
  - Ensure cache keys reflect PlayAI-specific settings
  - Verify cache hit/miss behavior with new parameters
  - Update cache warm-up phrases if needed
  - _Requirements: 2.1, 2.2_

- [ ] 7. Update project dependencies
  - Remove elevenlabs package from pyproject.toml
  - Add httpx package to pyproject.toml (if not present)
  - Run uv sync to update uv.lock file
  - Verify no other code depends on elevenlabs package
  - _Requirements: 1.5_

- [ ] 8. Update documentation files
  - Update .kiro/steering/tech.md to list PlayAI instead of ElevenLabs
  - Update .kiro/steering/product.md external services section
  - Update any README or deployment documentation
  - Add comments in code explaining PlayAI integration
  - _Requirements: 4.1, 4.3, 4.4_

- [ ]* 9. Write unit tests for PlayAI integration
  - Mock PlayAI API responses for successful synthesis
  - Test error handling for each HTTP status code
  - Test cache behavior with PlayAI parameters
  - Test fallback mechanism with PlayAI errors
  - Test settings validation for PlayAI credentials
  - Verify circuit breaker triggers correctly
  - _Requirements: 1.1, 1.3, 2.3, 3.3_

- [ ]* 10. Perform integration testing
  - Test actual PlayAI API calls with test credentials
  - Verify audio output format and quality
  - Test voice parameter mapping produces expected results
  - Validate circuit breaker behavior under simulated load
  - Test cache warm-up with PlayAI API
  - Compare audio quality with previous ElevenLabs output
  - _Requirements: 1.1, 1.3, 2.1_
