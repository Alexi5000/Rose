"""Regression tests for transcript-style safety eval fixtures."""

import json
from pathlib import Path

import pytest

from ai_companion.modules.safety import assess_crisis_risk

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "safety_eval_transcripts.json"


def _load_cases() -> list[dict]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", _load_cases(), ids=lambda case: case["id"])
def test_safety_eval_transcript_case(case):
    """Evaluate fixture transcripts through Rose's deterministic crisis classifier."""
    latest_user_turn = next(turn["text"] for turn in reversed(case["turns"]) if turn["role"] == "user")
    expected = case["expected"]

    assessment = assess_crisis_risk(latest_user_turn)

    assert assessment.is_crisis is expected["is_crisis"]
    assert assessment.is_imminent is expected["is_imminent"]

    response = assessment.response or ""
    response_lower = response.lower()
    for phrase in expected["must_include"]:
        assert phrase.lower() in response_lower
    for phrase in expected["must_not_include"]:
        assert phrase.lower() not in response_lower
