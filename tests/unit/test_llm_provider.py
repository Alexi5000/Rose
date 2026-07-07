"""Unit tests for LLM provider selection."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from ai_companion.modules.providers import llm
from ai_companion.settings import settings


@pytest.fixture(autouse=True)
def clear_llm_provider_cache():
    llm.get_chat_model.cache_clear()
    llm.get_structured_chat_model.cache_clear()
    yield
    llm.get_chat_model.cache_clear()
    llm.get_structured_chat_model.cache_clear()


class StructuredTestResponse(BaseModel):
    """Small schema used to verify structured provider wrapping."""

    answer: str


def test_get_chat_model_defaults_to_groq(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "groq")
    monkeypatch.setattr(settings, "LLM_FALLBACK_PROVIDER", "openrouter")
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", None)

    groq_model = MagicMock(name="groq_model")
    with patch("ai_companion.modules.providers.llm.ChatGroq", return_value=groq_model) as mock_groq:
        model = llm.get_chat_model()

    assert model is groq_model
    mock_groq.assert_called_once()
    assert mock_groq.call_args.kwargs["model_name"] == settings.TEXT_MODEL_NAME
    assert mock_groq.call_args.kwargs["max_tokens"] == 250


def test_get_chat_model_can_use_openrouter_directly(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "openrouter")
    monkeypatch.setattr(settings, "LLM_FALLBACK_PROVIDER", None)
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setattr(settings, "OPENROUTER_MODEL_NAME", "openai/gpt-4o-mini")

    openrouter_model = MagicMock(name="openrouter_model")
    with patch("ai_companion.modules.providers.llm.ChatOpenAI", return_value=openrouter_model) as mock_openrouter:
        model = llm.get_chat_model(temperature=0.4)

    assert model is openrouter_model
    mock_openrouter.assert_called_once()
    assert mock_openrouter.call_args.kwargs["api_key"] == "test-openrouter-key"
    assert mock_openrouter.call_args.kwargs["base_url"] == settings.OPENROUTER_BASE_URL
    assert mock_openrouter.call_args.kwargs["model"] == "openai/gpt-4o-mini"
    assert mock_openrouter.call_args.kwargs["temperature"] == 0.4
    assert mock_openrouter.call_args.kwargs["default_headers"]["X-OpenRouter-Title"] == settings.OPENROUTER_APP_NAME


def test_get_chat_model_adds_openrouter_fallback_when_key_exists(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "groq")
    monkeypatch.setattr(settings, "LLM_FALLBACK_PROVIDER", "openrouter")
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-openrouter-key")

    groq_model = MagicMock(name="groq_model")
    fallback_wrapped_model = MagicMock(name="fallback_wrapped_model")
    groq_model.with_fallbacks.return_value = fallback_wrapped_model
    openrouter_model = MagicMock(name="openrouter_model")

    with (
        patch("ai_companion.modules.providers.llm.ChatGroq", return_value=groq_model),
        patch("ai_companion.modules.providers.llm.ChatOpenAI", return_value=openrouter_model),
    ):
        model = llm.get_chat_model()

    assert model is fallback_wrapped_model
    groq_model.with_fallbacks.assert_called_once_with([openrouter_model])


def test_get_chat_model_accepts_task_specific_groq_model(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "groq")
    monkeypatch.setattr(settings, "LLM_FALLBACK_PROVIDER", None)

    groq_model = MagicMock(name="groq_model")
    with patch("ai_companion.modules.providers.llm.ChatGroq", return_value=groq_model) as mock_groq:
        model = llm.get_chat_model(
            temperature=settings.LLM_TEMPERATURE_MEMORY,
            model_name=settings.SMALL_TEXT_MODEL_NAME,
            max_tokens=500,
        )

    assert model is groq_model
    assert mock_groq.call_args.kwargs["model_name"] == settings.SMALL_TEXT_MODEL_NAME
    assert mock_groq.call_args.kwargs["temperature"] == settings.LLM_TEMPERATURE_MEMORY
    assert mock_groq.call_args.kwargs["max_tokens"] == 500


def test_get_structured_chat_model_wraps_fallback_after_schema_binding(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "groq")
    monkeypatch.setattr(settings, "LLM_FALLBACK_PROVIDER", "openrouter")
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-openrouter-key")

    primary_model = MagicMock(name="primary_model")
    primary_structured = MagicMock(name="primary_structured")
    primary_fallback = MagicMock(name="primary_fallback")
    primary_model.with_structured_output.return_value = primary_structured
    primary_structured.with_fallbacks.return_value = primary_fallback

    fallback_model = MagicMock(name="fallback_model")
    fallback_structured = MagicMock(name="fallback_structured")
    fallback_model.with_structured_output.return_value = fallback_structured

    with (
        patch("ai_companion.modules.providers.llm.ChatGroq", return_value=primary_model),
        patch("ai_companion.modules.providers.llm.ChatOpenAI", return_value=fallback_model),
    ):
        model = llm.get_structured_chat_model(
            StructuredTestResponse,
            temperature=0.2,
            model_name=settings.SMALL_TEXT_MODEL_NAME,
            max_tokens=400,
        )

    assert model is primary_fallback
    primary_model.with_structured_output.assert_called_once_with(StructuredTestResponse)
    fallback_model.with_structured_output.assert_called_once_with(StructuredTestResponse)
    primary_structured.with_fallbacks.assert_called_once_with([fallback_structured])


def test_openrouter_provider_requires_api_key(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "openrouter")
    monkeypatch.setattr(settings, "LLM_FALLBACK_PROVIDER", None)
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", None)

    with pytest.raises(ValueError, match="OPENROUTER_API_KEY is required"):
        llm.get_chat_model()


def test_unknown_llm_provider_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "unknown")
    monkeypatch.setattr(settings, "LLM_FALLBACK_PROVIDER", None)

    with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER"):
        llm.get_chat_model()
