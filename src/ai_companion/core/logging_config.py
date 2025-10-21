"""Structured logging configuration for Rose the Healer Shaman."""

import logging
import os
import sys

import structlog


def configure_logging() -> None:
    """Configure structured logging with JSON output for production.
    
    This sets up structlog with processors for:
    - Timestamp in ISO format
    - Log level
    - Logger name
    - Exception info
    - JSON rendering for production or console rendering for development
    
    Log level can be controlled via LOG_LEVEL environment variable.
    """
    # Get log level from environment (default to INFO)
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    # Determine if we're in production (use JSON) or development (use console)
    use_json = os.getenv("LOG_FORMAT", "json").lower() == "json"
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    
    # Configure structlog processors
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Add appropriate renderer based on environment
    if use_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Log configuration
    logger = structlog.get_logger(__name__)
    logger.info(
        "logging_configured",
        log_level=log_level_str,
        format="json" if use_json else "console",
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)
