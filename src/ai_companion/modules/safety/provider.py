"""Safety classification provider abstraction."""

from __future__ import annotations

from functools import lru_cache
from typing import Protocol, runtime_checkable

from ai_companion.modules.safety.crisis import CrisisAssessment, assess_crisis_risk
from ai_companion.settings import settings


@runtime_checkable
class SafetyClassifierProvider(Protocol):
    """Protocol for safety classification providers."""

    name: str

    def assess(self, text: str) -> CrisisAssessment:
        """Assess text for crisis/safety risk before normal generation."""
        ...


class DeterministicCrisisSafetyProvider:
    """Deterministic phrase-based crisis classifier.

    This is intentionally conservative and dependency-free. It is the default
    provider so Rose can always apply the 988 crisis path even when LLM services
    are down.
    """

    name = "deterministic_crisis"

    def assess(self, text: str) -> CrisisAssessment:
        """Assess text using Rose's deterministic crisis-risk rules."""
        return assess_crisis_risk(text)


def create_safety_classifier_provider() -> SafetyClassifierProvider:
    """Create the configured safety classifier provider."""
    provider = settings.SAFETY_PROVIDER.strip().lower()
    if provider in {"deterministic", "deterministic_crisis", "local"}:
        return DeterministicCrisisSafetyProvider()
    raise ValueError(f"Unsupported SAFETY_PROVIDER '{settings.SAFETY_PROVIDER}'")


@lru_cache(maxsize=1)
def get_safety_classifier_provider() -> SafetyClassifierProvider:
    """Return the shared safety classifier provider."""
    return create_safety_classifier_provider()
