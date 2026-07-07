"""Crisis-risk detection and response helpers."""

from dataclasses import dataclass

HIGH_RISK_PHRASES = (
    "kill myself",
    "end my life",
    "end it all",
    "take my life",
    "suicide",
    "suicidal",
    "unalive myself",
    "un-alive myself",
    "hurt myself",
    "harm myself",
    "self-harm",
    "self harm",
    "cut myself",
    "cutting myself",
    "shoot myself",
    "hang myself",
    "slit my wrists",
    "jump off a bridge",
    "jump from a bridge",
    "jump in front of traffic",
    "jump in front of a train",
    "overdose",
    "take all my pills",
    "i want to die",
    "want to die",
    "i wish i was dead",
    "i wish i were dead",
    "wish i was dead",
    "wish i were dead",
    "better off dead",
    "i would be better off dead",
    "everyone would be better off without me",
    "go to sleep and not wake up",
    "not wake up",
    "don't want to live",
    "do not want to live",
    "no reason to live",
    "can't stay safe",
    "cannot stay safe",
    "can't keep myself safe",
    "cannot keep myself safe",
    "not safe with myself",
    "don't trust myself alone",
    "do not trust myself alone",
    "can't trust myself alone",
    "cannot trust myself alone",
    "shouldn't be alone with myself",
    "should not be alone with myself",
    "afraid of what i might do to myself",
    "scared of what i might do to myself",
    "afraid i might hurt myself",
    "scared i might hurt myself",
    "won't be here tomorrow",
    "will not be here tomorrow",
)

IMMINENT_DANGER_PHRASES = (
    "i am not safe at home",
    "i'm not safe at home",
    "not safe at home",
    "someone is going to hurt me",
    "someone might hurt me",
    "someone threatened me",
    "they threatened me",
    "he threatened me",
    "she threatened me",
    "my partner threatened me",
    "my partner hit me",
    "he hit me",
    "she hit me",
    "they hit me",
    "i am hiding from him",
    "i'm hiding from him",
    "i am hiding from her",
    "i'm hiding from her",
    "afraid to go home",
    "scared to go home",
)

IMMINENT_RISK_PHRASES = (
    "right now",
    "tonight",
    "today",
    "tomorrow",
    "soon",
    "after this call",
    "after this conversation",
    "when i get home",
    "i have a plan",
    "i have the pills",
    "i have a gun",
    "pills in my hand",
    "gun in my hand",
    "goodbye note",
    "goodbye",
)

NEGATED_SELF_HARM_PHRASES = (
    "i don't want to die",
    "i do not want to die",
    "i don't want to kill myself",
    "i do not want to kill myself",
    "i am not suicidal",
    "i'm not suicidal",
    "not suicidal",
    "not going to kill myself",
    "not going to hurt myself",
    "not going to harm myself",
    "not going to self-harm",
    "not going to self harm",
    "not going to cut myself",
    "not going to shoot myself",
)

REFERENCE_CONTEXT_PHRASES = (
    "suicide prevention",
    "suicide awareness",
    "suicide hotline",
    "988 lifeline",
    "crisis lifeline",
    "movie about suicide",
    "book about suicide",
    "article about suicide",
    "song about suicide",
    "quote about suicide",
)

IDIOMATIC_DISTRESS_PHRASES = (
    "deadline is killing me",
    "this job is killing me",
    "my feet are killing me",
    "dying of embarrassment",
    "died of embarrassment",
    "i could die of embarrassment",
    "i'm dead tired",
    "i am dead tired",
    "my phone is dead",
    "my battery is dead",
    "accidentally cut myself",
    "cut myself shaving",
    "cut myself cooking",
    "cut myself while cooking",
    "cut myself chopping",
)


@dataclass(frozen=True)
class CrisisAssessment:
    """Result of a crisis-risk assessment."""

    is_crisis: bool
    is_imminent: bool
    response: str | None = None


def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)


def _is_clear_false_positive_context(text: str) -> bool:
    """Return True when high-risk words appear in clearly non-crisis context."""
    if _contains_any(text, REFERENCE_CONTEXT_PHRASES):
        return True
    if _contains_any(text, IDIOMATIC_DISTRESS_PHRASES):
        return True
    return _contains_any(text, NEGATED_SELF_HARM_PHRASES) and not _contains_any(text, IMMINENT_RISK_PHRASES)


def _imminent_danger_response() -> str:
    """Return a non-clinical response for immediate external danger."""

    return (
        "I'm really glad you told me. If you are in immediate danger, call emergency services now if you can, "
        "or move toward a safer public place. Reach one real person nearby or a trusted contact, and keep this "
        "simple: your safety comes before continuing this conversation."
    )


def assess_crisis_risk(text: str) -> CrisisAssessment:
    """Assess whether user text needs a crisis response before LLM generation."""
    normalized = " ".join(text.lower().split())
    if not normalized:
        return CrisisAssessment(is_crisis=False, is_imminent=False)

    if _contains_any(normalized, IMMINENT_DANGER_PHRASES):
        return CrisisAssessment(
            is_crisis=True,
            is_imminent=True,
            response=_imminent_danger_response(),
        )

    is_crisis = _contains_any(normalized, HIGH_RISK_PHRASES)
    if not is_crisis:
        return CrisisAssessment(is_crisis=False, is_imminent=False)
    if _is_clear_false_positive_context(normalized):
        return CrisisAssessment(is_crisis=False, is_imminent=False)

    is_imminent = _contains_any(normalized, IMMINENT_RISK_PHRASES)
    if is_imminent:
        response = (
            "I'm really glad you said this out loud. If you might hurt yourself soon, call or text 988 now, "
            "or call emergency services. If you can, move away from anything you could use to hurt yourself "
            "and reach one real person nearby while I stay with you."
        )
    else:
        response = (
            "I'm really glad you told me. You deserve real human support with this, not just me in your ear. "
            "If you are in the U.S., call or text 988 for the Suicide and Crisis Lifeline; if you are elsewhere, "
            "contact local emergency services or a trusted person who can be with you now."
        )

    return CrisisAssessment(is_crisis=True, is_imminent=is_imminent, response=response)
