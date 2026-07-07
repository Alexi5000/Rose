"""Lightweight affect-state detection for voice response shaping.

This module is deliberately deterministic. It is not a diagnosis or clinical
classifier; it gives Rose a compact conversational hint so she can choose a
fitting stance without another LLM call on the hot path.
"""

from dataclasses import dataclass
from typing import Literal

AffectCategory = Literal[
    "grief",
    "anxiety",
    "anger",
    "loneliness",
    "numbness",
    "spiritual_openness",
    "tender",
    "steady",
]
Intensity = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class AffectState:
    """Detected conversational affect for the latest user turn."""

    category: AffectCategory
    intensity: Intensity
    support_style: str

    def format_for_prompt(self) -> str:
        """Return a compact prompt hint for Rose."""

        return f"{self.category}; intensity={self.intensity}; stance={self.support_style}"


KEYWORDS: dict[AffectCategory, tuple[str, ...]] = {
    "grief": ("grief", "grieving", "miss my", "passed away", "died", "lost my", "loss"),
    "anxiety": ("anxious", "anxiety", "panic", "overwhelmed", "scared", "afraid", "worried", "terrified"),
    "anger": ("angry", "furious", "rage", "resent", "betrayed", "mad at"),
    "loneliness": ("lonely", "alone", "isolated", "no one", "empty house"),
    "numbness": ("numb", "nothing", "shut down", "can't feel", "blank"),
    "spiritual_openness": (
        "ritual",
        "ceremony",
        "prayer",
        "spiritual",
        "sacred",
        "ancestor",
        "ancestors",
        "dream",
        "meaning",
        "sign from",
    ),
    "tender": ("sad", "hurt", "heavy", "tired", "ashamed", "guilty"),
    "steady": (),
}

HIGH_INTENSITY_MARKERS = (
    "can't breathe",
    "falling apart",
    "unbearable",
    "desperate",
    "terrified",
    "can't stop crying",
)

MEDIUM_INTENSITY_MARKERS = ("really", "so ", "very", "a lot", "all day", "again")

SUPPORT_STYLE: dict[AffectCategory, str] = {
    "grief": "slow down, honor the loss, do not rush toward fixing",
    "anxiety": "ground in the body, reduce future-tripping, offer one small next breath",
    "anger": "validate the boundary, keep the tone steady, invite what needs protecting",
    "loneliness": "offer warmth and companionship, ask one specific connective question",
    "numbness": "use gentle sensory grounding, avoid forcing emotion",
    "spiritual_openness": "follow the user's spiritual frame with humility, ask consent before offering ritual",
    "tender": "be soft and specific, reflect the tender feeling without over-validating",
    "steady": "stay warm and curious, follow the user's lead",
}


def classify_affect_state(text: str) -> AffectState:
    """Classify the latest user turn into a conversational affect hint."""

    normalized = text.lower()
    category: AffectCategory = "steady"
    for candidate, keywords in KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            category = candidate
            break

    intensity: Intensity = "low"
    if any(marker in normalized for marker in HIGH_INTENSITY_MARKERS) or normalized.count("!") >= 2:
        intensity = "high"
    elif category != "steady" or any(marker in normalized for marker in MEDIUM_INTENSITY_MARKERS):
        intensity = "medium"

    return AffectState(
        category=category,
        intensity=intensity,
        support_style=SUPPORT_STYLE[category],
    )
