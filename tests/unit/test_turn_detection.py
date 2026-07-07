"""Tests for semantic voice turn-completion heuristics."""

import pytest

from ai_companion.modules.speech.turn_detection import assess_turn_completion


@pytest.mark.parametrize(
    "transcript",
    [
        "I feel like",
        "The thing is",
        "I keep thinking about",
        "I wanted to say that",
        "When I",
        "I am trying to",
        "I'm trying to",
    ],
)
def test_assess_turn_completion_flags_dangling_fragments(transcript):
    result = assess_turn_completion(transcript)

    assert result.is_complete is False
    assert result.reason in {"dangling_phrase", "dangling_suffix", "unfinished_clause"}


@pytest.mark.parametrize(
    "transcript",
    [
        "I feel like I finally understand what happened.",
        "No.",
        "Okay",
        "I keep thinking about my dad and I miss him.",
        "When I breathe slowly, I can feel my shoulders drop.",
    ],
)
def test_assess_turn_completion_allows_complete_voice_turns(transcript):
    assert assess_turn_completion(transcript).is_complete is True


def test_assess_turn_completion_flags_unbalanced_boundaries():
    result = assess_turn_completion('I heard the words "come home')

    assert result.is_complete is False
    assert result.reason == "unbalanced_boundary"
