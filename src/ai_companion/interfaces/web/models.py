"""Shared Pydantic models for API requests and responses."""

from typing import Any, Dict, Optional

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standardized error response model.
    
    Attributes:
        error: Machine-readable error code (e.g., 'validation_error', 'service_unavailable')
        message: Human-readable error message
        request_id: Unique request identifier for tracing (if available)
        details: Additional error context or validation details
    """

    error: str
    message: str
    request_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error": "validation_error",
                    "message": "Audio file too large. Maximum size is 10MB",
                    "request_id": "550e8400-e29b-41d4-a716-446655440000",
                    "details": {
                        "field": "audio",
                        "max_size_mb": 10,
                        "received_size_mb": 15.2
                    }
                },
                {
                    "error": "service_unavailable",
                    "message": "I'm having trouble connecting to my services right now. Please try again in a moment.",
                    "request_id": "550e8400-e29b-41d4-a716-446655440001"
                }
            ]
        }
    }
