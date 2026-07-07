"""Regression tests for Rose's prompt guardrails."""

from ai_companion.core.prompts import (
    CHARACTER_CARD_PROMPT,
    CHARACTER_PROMPT_MODULES,
    MEMORY_ANALYSIS_PROMPT,
    get_session_arc_hint,
)


def _normalized(text: str) -> str:
    return " ".join(text.lower().split())


def test_character_prompt_keeps_ai_and_care_boundaries():
    prompt = _normalized(CHARACTER_CARD_PROMPT)

    assert "honest that you are ai" in prompt
    assert "not a therapist" in prompt
    assert "not a therapist, doctor, emergency service" in prompt
    assert "do not diagnose" in prompt
    assert "hipaa" in prompt
    assert "never create manipulative dependency" in prompt


def test_character_prompt_keeps_healthy_engagement_boundaries():
    healthy_engagement = _normalized(CHARACTER_PROMPT_MODULES["healthy_engagement"])

    assert "never tries to keep someone talking for rose's sake" in healthy_engagement
    assert "support long conversations only when they feel useful" in healthy_engagement
    assert "normalize pausing" in healthy_engagement
    assert "texting a trusted person" in healthy_engagement
    assert "rose is their only anchor" in healthy_engagement


def test_character_prompt_keeps_cultural_humility_for_spiritual_framing():
    cultural_humility = _normalized(CHARACTER_PROMPT_MODULES["cultural_humility"])
    rituals = _normalized(CHARACTER_PROMPT_MODULES["rituals_and_exercises"])

    assert "do not claim to represent a culture" in cultural_humility
    assert "lineage" in cultural_humility
    assert "unless the person invited that frame" in cultural_humility
    assert "ask consent" in _normalized(CHARACTER_CARD_PROMPT)
    assert "do not make grand spiritual claims" in rituals
    assert "medical care" in rituals


def test_session_arc_moves_to_grounding_for_high_intensity_affect():
    hint = get_session_arc_hint(message_count=8, affect_state="anger; intensity=high")

    assert hint.startswith("grounding;")
    assert "body-based anchor" in hint


def test_session_arc_moves_to_closure_for_long_sessions():
    hint = get_session_arc_hint(message_count=22, affect_state="loneliness; intensity=low")

    assert hint.startswith("closure;")
    assert "leave steadier" in hint


def test_memory_analysis_prompt_keeps_support_companion_framing():
    prompt = _normalized(MEMORY_ANALYSIS_PROMPT)

    assert "consent-worthy emotional-support context" in prompt
    assert "grounded future conversations" in prompt
    assert "healing or reflection goals" in prompt
    assert "therapeutic context" not in prompt
    assert "healing journey" not in prompt


def test_memory_analysis_prompt_preserves_sensitive_memory_taxonomy():
    prompt = _normalized(MEMORY_ANALYSIS_PROMPT)

    assert "memory_type as one of" in prompt
    assert "support_system" in prompt
    assert "health_note" in prompt
    assert "cultural_preference" in prompt
    assert "sensitivity to sensitive" in prompt
