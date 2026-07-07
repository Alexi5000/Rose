"""Helper functions for graph utilities.

This module provides utility functions for creating and configuring
components used in the LangGraph workflow, including chat models,
speech modules, and text parsers.
"""

# Standard library
import asyncio
import logging
import re
from functools import lru_cache, wraps

# Third-party
from langchain_core.output_parsers import StrOutputParser

# Local
from ai_companion.core.exceptions import CircuitBreakerError, WorkflowError
from ai_companion.core.privacy_logging import exc_info_for_log, exception_message_for_log
from ai_companion.modules.memory.provider import MemoryProvider, get_memory_provider
from ai_companion.modules.response_quality import sanitize_voice_response
from ai_companion.modules.safety import SafetyClassifierProvider, get_safety_classifier_provider
from ai_companion.modules.speech import TTSProvider, get_tts_provider


@lru_cache(maxsize=1)
def get_text_to_speech_module() -> TTSProvider:
    """Get shared text-to-speech provider instance (singleton).

    Cached so all LangGraph node invocations share one provider instance and
    therefore one in-memory TTS cache. Without this, each audio_node call would
    create a fresh provider with an empty cache, making warm_cache() useless.

    Returns:
        TTSProvider: Configured TTS provider for audio generation
    """
    return get_tts_provider()


@lru_cache(maxsize=1)
def get_safety_classifier_module() -> SafetyClassifierProvider:
    """Get shared safety classifier provider instance."""
    return get_safety_classifier_provider()


@lru_cache(maxsize=1)
def get_memory_module() -> MemoryProvider:
    """Get shared memory provider instance."""
    return get_memory_provider()


def remove_asterisk_content(text: str) -> str:
    """Remove content between asterisks from the text.

    Args:
        text: Input text containing asterisk-wrapped content

    Returns:
        str: Text with asterisk content removed and whitespace stripped
    """
    return re.sub(r"\*.*?\*", "", text).strip()


class AsteriskRemovalParser(StrOutputParser):
    """Output parser that removes asterisk-wrapped content from LLM responses.

    This parser extends StrOutputParser to automatically clean up
    asterisk-wrapped stage directions or internal thoughts from responses.
    """

    def parse(self, text: str) -> str:
        """Parse and clean text by removing asterisk content.

        Args:
            text: Raw text from LLM response

        Returns:
            str: Cleaned text with asterisk content removed
        """
        return sanitize_voice_response(super().parse(text))


def node_error_wrapper(func):
    """Decorator for LangGraph nodes to add structured exception logging.

    This decorator logs entry/exit, catches exceptions within node functions,
    emits a stack trace only when sensitive-content logging is enabled, and
    re-raises WorkflowError or CircuitBreakerError so the upper layers have
    consistent error handling.
    """
    logger = logging.getLogger(__name__)

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        node_name = func.__name__
        logger.info("node_enter", extra={"node_name": node_name})
        try:
            result = await func(*args, **kwargs)
            logger.info("node_exit", extra={"node_name": node_name})
            return result
        except CircuitBreakerError as e:
            logger.error(
                "node_circuit_breaker_error",
                extra={
                    "node_name": node_name,
                    "error_type": type(e).__name__,
                    "error": exception_message_for_log(e),
                },
                exc_info=exc_info_for_log(),
            )
            raise
        except Exception as e:
            logger.error(
                "node_exception",
                extra={
                    "node_name": node_name,
                    "error_type": type(e).__name__,
                    "error": exception_message_for_log(e),
                },
                exc_info=exc_info_for_log(),
            )
            raise WorkflowError(f"Node {node_name} failed: {type(e).__name__}") from e

    return async_wrapper


def node_wrapper(func):
    """Compatibility wrapper to handle both sync and async node functions.

    If the decorated function is synchronous we'll execute it in a thread pool.
    """
    if asyncio.iscoroutinefunction(func):
        return node_error_wrapper(func)

    @wraps(func)
    async def sync_to_async_wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    return node_error_wrapper(sync_to_async_wrapper)
