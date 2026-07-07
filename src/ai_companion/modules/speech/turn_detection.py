"""Deterministic semantic turn-completion checks for voice transcripts."""

import re
from dataclasses import dataclass

CONTINUATION_PROMPT = "I'm with you. Finish that thought when you're ready."

_DANGLING_SUFFIXES = {
    "and",
    "but",
    "or",
    "so",
    "because",
    "cause",
    "when",
    "while",
    "if",
    "although",
    "though",
    "that",
    "about",
    "with",
    "for",
    "to",
    "from",
    "into",
    "like",
    "as",
}

_DANGLING_PHRASES = (
    "i feel like",
    "i felt like",
    "it feels like",
    "it felt like",
    "i am trying to",
    "i'm trying to",
    "i want to",
    "i need to",
    "i was going to",
    "what i mean is",
    "the thing is",
    "and then",
    "but then",
    "because i",
    "because it",
    "when i",
    "if i",
)

_COMPLETE_SHORT_ACKS = {
    "yes",
    "no",
    "yeah",
    "yep",
    "nope",
    "okay",
    "ok",
    "sure",
    "thanks",
    "thank you",
}


@dataclass(frozen=True)
class TurnCompletion:
    """Result of a conservative transcript completeness check."""

    is_complete: bool
    reason: str = "complete"


def assess_turn_completion(transcript: str) -> TurnCompletion:
    """Assess whether a voice transcript sounds ready for Rose to answer.

    This is intentionally conservative. It catches clear dangling fragments
    without trying to replace provider endpointing or a future learned turn
    detector.
    """

    normalized = _normalize(transcript)
    if not normalized:
        return TurnCompletion(False, "empty")

    if normalized in _COMPLETE_SHORT_ACKS:
        return TurnCompletion(True)

    if _has_unbalanced_boundary(transcript):
        return TurnCompletion(False, "unbalanced_boundary")

    if normalized.endswith(tuple(f" {phrase}" for phrase in _DANGLING_PHRASES)) or normalized in _DANGLING_PHRASES:
        return TurnCompletion(False, "dangling_phrase")

    words = normalized.split()
    if len(words) < 3:
        return TurnCompletion(False, "too_short")

    last_word = words[-1]
    if last_word in _DANGLING_SUFFIXES:
        return TurnCompletion(False, "dangling_suffix")

    if re.search(r"\b(i|we|you|they|he|she|it)\s+(am|are|is|was|were|feel|felt|want|need|try|trying)\s*$", normalized):
        return TurnCompletion(False, "unfinished_clause")

    return TurnCompletion(True)


def _normalize(text: str) -> str:
    normalized = re.sub(r"[^\w'\s]", " ", text.lower())
    return " ".join(normalized.split())


def _has_unbalanced_boundary(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False

    if stripped.count('"') % 2:
        return True

    return stripped.count("(") > stripped.count(")")
