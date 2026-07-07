"""Unit tests for Rose's crisis safety layer."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from ai_companion.graph.edges import should_use_crisis_response
from ai_companion.graph.nodes import audio_node, safety_node
from ai_companion.graph.state import AICompanionState
from ai_companion.modules.safety import assess_crisis_risk


def _state(message: str, **overrides):
    base = {
        "messages": [HumanMessage(content=message)],
        "summary": "",
        "workflow": "audio",
        "audio_buffer": b"",
        "current_activity": "",
        "apply_activity": False,
        "memory_context": "",
        "safety_risk": "",
        "safety_response": "",
    }
    base.update(overrides)
    return AICompanionState(**base)


def test_assess_crisis_risk_detects_988_level_language():
    assessment = assess_crisis_risk("I do not want to live anymore.")

    assert assessment.is_crisis is True
    assert assessment.is_imminent is False
    assert assessment.response is not None
    assert "988" in assessment.response


def test_assess_crisis_risk_detects_imminent_language():
    assessment = assess_crisis_risk("I want to die tonight and I have a plan.")

    assert assessment.is_crisis is True
    assert assessment.is_imminent is True
    assert assessment.response is not None
    assert "emergency services" in assessment.response


@pytest.mark.parametrize(
    ("message", "is_imminent"),
    [
        ("I'm scared I might hurt myself.", False),
        ("I think I'm going to harm myself right now.", True),
        ("I want to overdose tonight.", True),
        ("I am going to cut myself tonight.", True),
        ("I want to shoot myself.", False),
        ("I keep thinking I should jump off a bridge.", False),
        ("I might jump in front of traffic today.", True),
        ("I want to slit my wrists.", False),
        ("I have the pills in my hand and I might take all my pills.", True),
        ("I can't keep myself safe tonight.", True),
        ("I'm not safe with myself right now.", True),
        ("I don't trust myself alone tonight.", True),
        ("I'm afraid of what I might do to myself.", False),
        ("I shouldn't be alone with myself right now.", True),
        ("I'm scared I might hurt myself if everyone leaves.", False),
        ("I might unalive myself when I get home.", True),
        ("I wish I were dead.", False),
        ("Everyone would be better off without me.", False),
        ("I want to go to sleep and not wake up soon.", True),
        ("I think I might end it all.", False),
        ("I won't be here tomorrow. Goodbye.", True),
    ],
)
def test_assess_crisis_risk_detects_direct_self_harm_intent(message, is_imminent):
    assessment = assess_crisis_risk(message)

    assert assessment.is_crisis is True
    assert assessment.is_imminent is is_imminent
    assert assessment.response is not None
    assert "988" in assessment.response


def test_assess_crisis_risk_ignores_non_crisis_distress():
    assessment = assess_crisis_risk("I feel sad and lonely today.")

    assert assessment.is_crisis is False
    assert assessment.response is None


@pytest.mark.parametrize(
    "message",
    [
        "I don't want to die. I want this pain to change.",
        "I'm not suicidal, I just feel overwhelmed.",
        "I'm not going to hurt myself, I just need someone to sit with me.",
        "I'm not going to self-harm, I need grounding.",
        "I volunteer in suicide prevention work.",
        "That movie about suicide really upset me.",
        "This deadline is killing me, but I am safe.",
        "I could die of embarrassment, but I'm okay.",
        "My phone is dead and I feel stranded.",
        "I am dead tired, but I am safe.",
        "I accidentally cut myself while cooking, but I'm safe.",
        "I cut myself shaving and need a bandage.",
        "I might end it with my partner, but I am safe.",
    ],
)
def test_assess_crisis_risk_recovers_from_clear_false_positive_contexts(message):
    assessment = assess_crisis_risk(message)

    assert assessment.is_crisis is False
    assert assessment.is_imminent is False
    assert assessment.response is None


def test_assess_crisis_risk_keeps_imminent_route_when_negation_is_not_enough():
    assessment = assess_crisis_risk("I'm not suicidal, but I want to die tonight.")

    assert assessment.is_crisis is True
    assert assessment.is_imminent is True
    assert assessment.response is not None
    assert "emergency services" in assessment.response


@pytest.mark.parametrize(
    "message",
    [
        "I am not safe at home and someone might hurt me.",
        "My partner threatened me and I'm afraid to go home.",
        "He hit me and I am hiding from him right now.",
    ],
)
def test_assess_crisis_risk_detects_imminent_external_danger(message):
    assessment = assess_crisis_risk(message)

    assert assessment.is_crisis is True
    assert assessment.is_imminent is True
    assert assessment.response is not None
    assert "emergency services" in assessment.response
    assert "safer public place" in assessment.response
    assert "trusted contact" in assessment.response
    assert "hurt yourself" not in assessment.response
    assert "988" not in assessment.response


def test_safety_node_sets_crisis_response():
    result = safety_node(_state("I keep thinking about suicide."))

    assert result["safety_risk"] == "crisis"
    assert "988" in result["safety_response"]


def test_safety_node_keeps_false_positive_context_on_normal_path():
    result = safety_node(_state("I'm not suicidal, I just need someone to sit with me."))

    assert result == {"safety_risk": "", "safety_response": ""}


def test_safety_routing_bypasses_memory_for_crisis():
    route = should_use_crisis_response(_state("I want to die.", safety_risk="crisis"))

    assert route == "audio_node"


def test_safety_routing_keeps_normal_memory_path():
    route = should_use_crisis_response(_state("I miss my mother."))

    assert route == "affect_tracking_node"


@pytest.mark.asyncio
async def test_audio_node_uses_safety_response_without_llm():
    text_to_speech = MagicMock()
    text_to_speech.synthesize_with_fallback = AsyncMock(return_value=(b"audio", False))

    chain = MagicMock()
    chain.ainvoke = AsyncMock(return_value=AIMessage(content="normal response"))

    with (
        patch("ai_companion.graph.nodes.get_text_to_speech_module", return_value=text_to_speech),
        patch("ai_companion.graph.nodes.get_character_response_chain", return_value=chain),
    ):
        result = await audio_node(
            _state("I want to die.", safety_response="Please call or text 988 now."),
            config={"configurable": {"thread_id": "test"}},
        )

    chain.ainvoke.assert_not_called()
    text_to_speech.synthesize_with_fallback.assert_awaited_once_with("Please call or text 988 now.")
    assert result["messages"].content == "Please call or text 988 now."
    assert result["audio_buffer"] == b"audio"
