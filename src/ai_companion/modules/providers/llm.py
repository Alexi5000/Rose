"""LLM provider factory with Groq default and OpenRouter fallback support."""

from functools import lru_cache
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from ai_companion.settings import settings

GROQ_PROVIDER = "groq"
OPENROUTER_PROVIDER = "openrouter"


def _normalise_provider(provider: str | None) -> str | None:
    """Normalize provider names from env vars."""
    if provider is None:
        return None
    normalized = provider.strip().lower()
    return normalized or None


def _build_groq_model(temperature: float, model_name: str | None = None, max_tokens: int = 250) -> ChatGroq:
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model_name=model_name or settings.TEXT_MODEL_NAME,
        temperature=temperature,
        timeout=settings.LLM_TIMEOUT_SECONDS,
        max_retries=settings.LLM_MAX_RETRIES,
        max_tokens=max_tokens,
    )


def _build_openrouter_model(temperature: float, max_tokens: int = 250) -> ChatOpenAI:
    if not settings.OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is required when using the OpenRouter LLM provider")

    return ChatOpenAI(
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
        model=settings.OPENROUTER_MODEL_NAME,
        temperature=temperature,
        timeout=settings.LLM_TIMEOUT_SECONDS,
        max_retries=settings.LLM_MAX_RETRIES,
        max_tokens=max_tokens,
        default_headers={
            "HTTP-Referer": "https://github.com/Alexi5000/Rose",
            "X-OpenRouter-Title": settings.OPENROUTER_APP_NAME,
        },
    )


def _build_provider(
    provider: str,
    temperature: float,
    model_name: str | None = None,
    max_tokens: int = 250,
) -> BaseChatModel:
    if provider == GROQ_PROVIDER:
        return _build_groq_model(temperature, model_name=model_name, max_tokens=max_tokens)
    if provider == OPENROUTER_PROVIDER:
        return _build_openrouter_model(temperature, max_tokens=max_tokens)
    raise ValueError(f"Unsupported LLM_PROVIDER '{provider}'. Supported providers: groq, openrouter")


def _configured_providers() -> tuple[str, str | None]:
    primary_provider = _normalise_provider(settings.LLM_PROVIDER) or GROQ_PROVIDER
    fallback_provider = _normalise_provider(settings.LLM_FALLBACK_PROVIDER)
    return primary_provider, fallback_provider


def _should_add_fallback(primary_provider: str, fallback_provider: str | None) -> bool:
    return bool(fallback_provider and fallback_provider != primary_provider and settings.OPENROUTER_API_KEY)


@lru_cache(maxsize=16)
def get_chat_model(
    temperature: Optional[float] = None,
    model_name: str | None = None,
    max_tokens: int = 250,
) -> BaseChatModel | Runnable:
    """Build the configured chat model.

    Groq remains the default low-latency provider. When an OpenRouter key is
    configured, Rose can either run directly through OpenRouter or use it as a
    LangChain fallback behind Groq.
    """
    temp: float = temperature if temperature is not None else settings.LLM_TEMPERATURE_DEFAULT
    primary_provider, fallback_provider = _configured_providers()

    primary = _build_provider(primary_provider, temp, model_name=model_name, max_tokens=max_tokens)
    if _should_add_fallback(primary_provider, fallback_provider):
        fallback = _build_provider(fallback_provider or "", temp, max_tokens=max_tokens)
        return primary.with_fallbacks([fallback])

    return primary


@lru_cache(maxsize=16)
def get_structured_chat_model(
    schema: type[BaseModel],
    temperature: Optional[float] = None,
    model_name: str | None = None,
    max_tokens: int = 500,
) -> Runnable:
    """Build the configured chat model with Pydantic structured output.

    Structured models bind the schema before fallback wrapping so primary and
    fallback providers return the same object shape.
    """
    temp: float = temperature if temperature is not None else settings.LLM_TEMPERATURE_DEFAULT
    primary_provider, fallback_provider = _configured_providers()

    primary = _build_provider(
        primary_provider,
        temp,
        model_name=model_name,
        max_tokens=max_tokens,
    ).with_structured_output(schema)
    if _should_add_fallback(primary_provider, fallback_provider):
        fallback = _build_provider(fallback_provider or "", temp, max_tokens=max_tokens).with_structured_output(schema)
        return primary.with_fallbacks([fallback])

    return primary
