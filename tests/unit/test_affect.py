"""Unit tests for non-clinical affect-state tracking."""

from langchain_core.messages import HumanMessage

from ai_companion.graph.nodes import affect_tracking_node
from ai_companion.graph.state import AICompanionState
from ai_companion.modules.affect import classify_affect_state


def _state(message: str) -> AICompanionState:
    return AICompanionState(
        messages=[HumanMessage(content=message)],
        summary="",
        workflow="audio",
        audio_buffer=b"",
        current_activity="",
        apply_activity=False,
        memory_context="",
        affect_state="",
        safety_risk="",
        safety_response="",
    )


def test_classify_affect_state_detects_grief():
    affect = classify_affect_state("I miss my mother so much since she passed away.")

    assert affect.category == "grief"
    assert affect.intensity == "medium"
    assert "honor the loss" in affect.support_style


def test_classify_affect_state_detects_high_anxiety():
    affect = classify_affect_state("I'm terrified and I can't breathe!!")

    assert affect.category == "anxiety"
    assert affect.intensity == "high"
    assert "ground in the body" in affect.support_style


def test_classify_affect_state_defaults_to_steady():
    affect = classify_affect_state("I had a pretty normal morning.")

    assert affect.category == "steady"
    assert affect.intensity == "low"


def test_classify_affect_state_detects_spiritual_openness():
    affect = classify_affect_state("I keep dreaming about my grandmother. Could we make a small ritual?")

    assert affect.category == "spiritual_openness"
    assert affect.intensity == "medium"
    assert "ask consent before offering ritual" in affect.support_style


def test_affect_tracking_node_returns_prompt_hint():
    result = affect_tracking_node(_state("I feel numb and blank today."))

    assert result["affect_state"].startswith("numbness; intensity=medium")
    assert "sensory grounding" in result["affect_state"]


def test_affect_tracking_node_returns_spiritual_prompt_hint():
    result = affect_tracking_node(_state("Prayer has felt meaningful again lately."))

    assert result["affect_state"].startswith("spiritual_openness; intensity=medium")
    assert "spiritual frame with humility" in result["affect_state"]
