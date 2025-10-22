"""Custom exceptions for AI Companion application.

This module defines the exception hierarchy for the application,
providing clear error types for different failure scenarios.
"""


class AICompanionError(Exception):
    """Base exception for all AI Companion errors."""

    pass


class ExternalAPIError(AICompanionError):
    """Base exception for external API errors (Groq, ElevenLabs, Qdrant, etc.)."""

    pass


class CircuitBreakerError(ExternalAPIError):
    """Exception raised when circuit breaker is open.

    This indicates that a service has failed repeatedly and the circuit breaker
    has opened to prevent cascading failures. The service will be retried after
    the recovery timeout period.
    """

    pass


class SpeechToTextError(ExternalAPIError):
    """Exception raised when speech-to-text conversion fails.

    This typically indicates issues with:
    - Groq Whisper API connectivity
    - Invalid audio format or corrupted audio data
    - Audio file size exceeding limits
    """

    pass


class TextToSpeechError(ExternalAPIError):
    """Exception raised when text-to-speech conversion fails.

    This typically indicates issues with:
    - ElevenLabs API connectivity
    - Invalid text input or length limits
    - Voice ID configuration errors
    """

    pass


class TextToImageError(ExternalAPIError):
    """Exception raised when text-to-image generation fails.

    This typically indicates issues with:
    - Together AI API connectivity
    - Invalid prompt or generation parameters
    - Image generation timeout or quota limits
    """

    pass


class ImageToTextError(ExternalAPIError):
    """Exception raised when image-to-text conversion fails.

    This typically indicates issues with:
    - Groq Vision API connectivity
    - Invalid image format or corrupted image data
    - Image size exceeding limits
    """

    pass


class MemoryError(AICompanionError):
    """Exception raised when memory operations fail.

    This typically indicates issues with:
    - Qdrant vector database connectivity
    - SQLite checkpointer errors
    - Memory extraction or retrieval failures
    """

    pass


class WorkflowError(AICompanionError):
    """Exception raised when LangGraph workflow execution fails.

    This typically indicates issues with:
    - Workflow timeout
    - Node execution failures
    - State management errors
    """

    pass
