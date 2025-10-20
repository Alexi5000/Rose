import re

from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

from ai_companion.modules.image.image_to_text import ImageToText
from ai_companion.modules.image.text_to_image import TextToImage
from ai_companion.modules.speech import TextToSpeech
from ai_companion.settings import settings


def get_chat_model(temperature: float = 0.7):
    """Get ChatGroq model with retry and timeout configuration.

    Args:
        temperature: Model temperature for response generation

    Returns:
        ChatGroq: Configured chat model with retry logic
    """
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model_name=settings.TEXT_MODEL_NAME,
        temperature=temperature,
        timeout=30.0,  # 30 second timeout for LLM calls
        max_retries=3,  # Built-in retry mechanism
    )


def get_text_to_speech_module():
    return TextToSpeech()


def get_text_to_image_module():
    return TextToImage()


def get_image_to_text_module():
    return ImageToText()


def remove_asterisk_content(text: str) -> str:
    """Remove content between asterisks from the text."""
    return re.sub(r"\*.*?\*", "", text).strip()


class AsteriskRemovalParser(StrOutputParser):
    def parse(self, text):
        return remove_asterisk_content(super().parse(text))
