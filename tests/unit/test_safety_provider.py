"""Unit tests for safety classifier provider selection."""

from unittest.mock import MagicMock, patch

import pytest

from ai_companion.modules.safety import (
    DeterministicCrisisSafetyProvider,
    SafetyClassifierProvider,
    get_safety_classifier_provider,
)
from ai_companion.settings import settings


def test_get_safety_classifier_provider_defaults_to_deterministic(monkeypatch):
    monkeypatch.setattr(settings, "SAFETY_PROVIDER", "deterministic")
    get_safety_classifier_provider.cache_clear()

    provider = get_safety_classifier_provider()

    assert isinstance(provider, DeterministicCrisisSafetyProvider)
    assert isinstance(provider, SafetyClassifierProvider)
    assert provider.name == "deterministic_crisis"

    get_safety_classifier_provider.cache_clear()


def test_get_safety_classifier_provider_accepts_local_alias(monkeypatch):
    monkeypatch.setattr(settings, "SAFETY_PROVIDER", "local")
    get_safety_classifier_provider.cache_clear()

    provider = get_safety_classifier_provider()

    assert isinstance(provider, DeterministicCrisisSafetyProvider)

    get_safety_classifier_provider.cache_clear()


def test_get_safety_classifier_provider_rejects_unknown_provider(monkeypatch):
    monkeypatch.setattr(settings, "SAFETY_PROVIDER", "unknown")
    get_safety_classifier_provider.cache_clear()

    with pytest.raises(ValueError, match="Unsupported SAFETY_PROVIDER"):
        get_safety_classifier_provider()

    get_safety_classifier_provider.cache_clear()


def test_deterministic_provider_delegates_to_crisis_assessment():
    provider = DeterministicCrisisSafetyProvider()

    assessment = provider.assess("I do not want to live.")

    assert assessment.is_crisis is True
    assert assessment.response is not None
    assert "988" in assessment.response


def test_safety_node_uses_configured_provider():
    from ai_companion.graph import nodes
    from ai_companion.modules.safety.crisis import CrisisAssessment

    fake_provider = MagicMock()
    fake_provider.assess.return_value = CrisisAssessment(
        is_crisis=True,
        is_imminent=True,
        response="Call or text 988 now.",
    )

    with patch("ai_companion.graph.nodes.get_safety_classifier_module", return_value=fake_provider):
        result = nodes.safety_node(
            {
                "messages": [MagicMock(content="help")],
                "summary": "",
                "workflow": "audio",
                "audio_buffer": b"",
                "current_activity": "",
                "apply_activity": False,
                "memory_context": "",
                "safety_risk": "",
                "safety_response": "",
            }
        )

    fake_provider.assess.assert_called_once_with("help")
    assert result == {"safety_risk": "imminent_crisis", "safety_response": "Call or text 988 now."}
