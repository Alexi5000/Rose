"""Helper functions for graph utilities.

This module provides utility functions for creating and configuring
components used in the LangGraph workflow, including chat models,
speech modules, and text parsers.
"""

import re
from typing import Optional

from langchain_core.output_parsers import StrOutputParser
import asyncio
import logging
from functools import wraps

from ai_companion.core.exceptions import WorkflowError, CircuitBreakerError
from langchain_groq import ChatGroq

from ai_companion.modules.image.image_to_text import ImageToText
from ai_companion.modules.image.text_to_image import TextToImage
from ai_companion.modules.speech import TextToSpeech
from ai_companion.settings import settings


def get_chat_model(temperature: Optional[float] = None) -> ChatGroq:
    """Get ChatGroq model with retry and timeout configuration.

    Args:
        temperature: Model temperature for response generation (0.0-1.0).
                    Defaults to settings.LLM_TEMPERATURE_DEFAULT if not provided.

    Returns:
        ChatGroq: Configured chat model with retry logic and timeout
    """
    temp: float = temperature if temperature is not None else settings.LLM_TEMPERATURE_DEFAULT
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model_name=settings.TEXT_MODEL_NAME,
        temperature=temp,
        timeout=settings.LLM_TIMEOUT_SECONDS,
        max_retries=settings.LLM_MAX_RETRIES,
    )


def get_text_to_speech_module() -> TextToSpeech:
    """Get TextToSpeech module instance.

    Returns:
        TextToSpeech: Configured TTS module for audio generation
    """
    return TextToSpeech()


def get_text_to_image_module() -> TextToImage:
    """Get TextToImage module instance.

    Returns:
        TextToImage: Configured image generation module
    """
    return TextToImage()


def get_image_to_text_module() -> ImageToText:
    """Get ImageToText module instance.

    Returns:
        ImageToText: Configured image analysis module
    """
    return ImageToText()


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
        return remove_asterisk_content(super().parse(text))


def node_error_wrapper(func):
    """Decorator for LangGraph nodes to add structured exception logging.

    This decorator logs entry/exit, catches exceptions within node functions,
    emits a full stack trace, and re-raises WorkflowError or CircuitBreakerError
    so the upper layers have consistent error handling.
    """
    logger = logging.getLogger(__name__)

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        node_name = func.__name__
        logger.info(f"➡️ Entering node: {node_name}")
        try:
            result = await func(*args, **kwargs)
            logger.info(f"✅ Exiting node: {node_name}")
            return result
        except CircuitBreakerError:
            logger.exception(f"⚡ Circuit breaker error in node {node_name}")
            raise
        except Exception as e:
            logger.exception(f"❌ Exception in node {node_name}: {type(e).__name__}: {str(e)}")
            raise WorkflowError(f"Node {node_name} failed: {type(e).__name__}: {str(e)}") from e

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

