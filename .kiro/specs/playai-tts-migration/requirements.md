# Requirements Document

## Introduction

This specification defines the requirements for migrating the AI companion's text-to-speech functionality from ElevenLabs to PlayAI TTS service. The migration will maintain existing TTS capabilities while switching to the PlayAI provider, ensuring seamless voice synthesis for user interactions across all interfaces (Chainlit and WhatsApp).

## Glossary

- **TTS System**: The text-to-speech module responsible for converting text responses into audio output
- **PlayAI Service**: The third-party API service that provides text-to-speech synthesis capabilities
- **Audio Module**: The `src/ai_companion/modules/speech/` directory containing TTS implementation
- **Settings Module**: The `src/ai_companion/settings.py` file managing application configuration
- **Groq Service**: The LLM provider already integrated for text generation and other AI tasks

## Requirements

### Requirement 1

**User Story:** As a developer, I want to replace ElevenLabs TTS with PlayAI TTS, so that the application uses the new voice synthesis provider

#### Acceptance Criteria

1. THE TTS System SHALL use PlayAI API endpoints for all text-to-speech conversion requests
2. THE Settings Module SHALL include PlayAI API key configuration instead of ElevenLabs credentials
3. THE Audio Module SHALL implement PlayAI-specific request formatting and response handling
4. WHEN a text-to-speech request is made, THE TTS System SHALL authenticate using the PlayAI API key
5. THE TTS System SHALL remove all ElevenLabs-specific code and dependencies

### Requirement 2

**User Story:** As a developer, I want to maintain backward compatibility with existing TTS interfaces, so that no changes are required in other parts of the application

#### Acceptance Criteria

1. THE Audio Module SHALL maintain the same function signatures for TTS operations
2. THE TTS System SHALL return audio data in the same format as the previous implementation
3. WHEN the graph workflow calls TTS functions, THE Audio Module SHALL process requests without requiring workflow modifications
4. THE TTS System SHALL handle errors in a manner consistent with the existing error handling patterns

### Requirement 3

**User Story:** As a system administrator, I want clear environment configuration for PlayAI, so that I can easily set up and deploy the application

#### Acceptance Criteria

1. THE Settings Module SHALL define a PLAYAI_API_KEY environment variable
2. THE Settings Module SHALL define a PLAYAI_VOICE_ID environment variable for voice selection
3. THE Settings Module SHALL validate that PlayAI credentials are present at application startup
4. THE TTS System SHALL provide clear error messages when PlayAI credentials are missing or invalid
5. THE Settings Module SHALL remove ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID environment variables

### Requirement 4

**User Story:** As a developer, I want updated documentation, so that the migration to PlayAI is clearly documented

#### Acceptance Criteria

1. THE project documentation SHALL reflect PlayAI as the TTS provider in all relevant files
2. THE `.env.example` file SHALL include PlayAI environment variable templates
3. THE technology stack documentation SHALL list PlayAI instead of ElevenLabs
4. THE Settings Module SHALL include comments explaining PlayAI configuration options
