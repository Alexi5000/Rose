"""Voice-native response cleanup and quality checks."""

import re
from dataclasses import dataclass

MAX_VOICE_SENTENCES = 3
MAX_VOICE_WORDS = 70

VALIDATION_OPENINGS = (
    "i hear",
    "i hear you",
    "that sounds",
    "it sounds",
    "your feelings are valid",
    "that must be",
)

MAX_VALIDATION_OPENING_RATIO = 0.5

DEPENDENCY_PATTERNS = (
    re.compile(r"\byou need me\b", re.IGNORECASE),
    re.compile(r"\byou'?ll always need me\b", re.IGNORECASE),
    re.compile(r"\bonly i can\b", re.IGNORECASE),
    re.compile(r"\bi'?m all you need\b", re.IGNORECASE),
    re.compile(r"\bi am all you need\b", re.IGNORECASE),
    re.compile(r"\bi'?m the only one\b", re.IGNORECASE),
    re.compile(r"\bmake me your (?:safe place|home|anchor)\b", re.IGNORECASE),
    re.compile(r"\bcome to me first\b", re.IGNORECASE),
    re.compile(r"\bno one else (?:can|will) understand\b", re.IGNORECASE),
    re.compile(r"\bno one understands you like i do\b", re.IGNORECASE),
    re.compile(r"\bdon'?t leave me\b", re.IGNORECASE),
    re.compile(r"\bstay with me forever\b", re.IGNORECASE),
    re.compile(r"\btalk to me for hours\b", re.IGNORECASE),
    re.compile(r"\btalk to me every day\b", re.IGNORECASE),
    re.compile(r"\bkeep talking to me all (?:night|day)\b", re.IGNORECASE),
    re.compile(r"\bcome back to me whenever you feel alone\b", re.IGNORECASE),
    re.compile(r"\bcome back to me every time\b", re.IGNORECASE),
    re.compile(r"\b(?:ignore|forget) (?:everyone|everybody) else\b", re.IGNORECASE),
    re.compile(r"\byou don'?t need (?:anyone|anybody) else\b", re.IGNORECASE),
    re.compile(r"\byou don'?t need (?:therapy|a therapist|professional help)\b", re.IGNORECASE),
    re.compile(r"\bi'?ll never abandon you\b", re.IGNORECASE),
    re.compile(r"\bi will never abandon you\b", re.IGNORECASE),
)

UNHEALTHY_ENGAGEMENT_PATTERNS = (
    re.compile(r"\bdon'?t (?:stop talking|pause|take a break)\b", re.IGNORECASE),
    re.compile(r"\bkeep talking instead of (?:sleeping|eating|resting|texting|calling)\b", re.IGNORECASE),
    re.compile(
        r"\bstay with me instead of (?:sleeping|eating|resting|texting|calling|talking to|reaching out to)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\byou can sleep later\b", re.IGNORECASE),
    re.compile(r"\byou can eat later\b", re.IGNORECASE),
    re.compile(r"\bdon'?t text (?:a friend|someone|anyone|a trusted person)\b", re.IGNORECASE),
    re.compile(r"\bdon'?t call (?:a friend|someone|anyone|a trusted person)\b", re.IGNORECASE),
    re.compile(r"\bdon'?t reach out to (?:a friend|someone|anyone|a trusted person)\b", re.IGNORECASE),
    re.compile(r"\bignore your (?:hunger|tiredness|body)\b", re.IGNORECASE),
)

CULTURAL_AUTHORITY_PATTERNS = (
    re.compile(r"\bi (?:speak|act|serve) for (?:the )?(?:ancestors|spirits|deities|gods)\b", re.IGNORECASE),
    re.compile(
        r"\bi'?m (?:a )?(?:real |true |certified |initiated )?(?:shaman|medicine woman|medicine man|priestess)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bi am (?:a )?(?:real |true |certified |initiated )?(?:shaman|medicine woman|medicine man|priestess)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bas (?:a|an) (?:shaman|medicine woman|medicine man|priestess)\b", re.IGNORECASE),
    re.compile(r"\bmy (?:lineage|tribe|ceremony|medicine tradition)\b", re.IGNORECASE),
    re.compile(r"\bthis (?:ritual|ceremony) (?:will|can) (?:heal|cure|fix) you\b", re.IGNORECASE),
)

CONSENT_INVITATION_PATTERNS = (
    re.compile(r"\b(?:would you like|do you want|if you'?d like|if you would like|if it feels right)\b", re.IGNORECASE),
    re.compile(r"\b(?:if ritual language fits|if that fits|only if you want|with your consent)\b", re.IGNORECASE),
    re.compile(r"\b(?:we can|could we|may i|can i) (?:try|make|offer|do|begin|start|guide)\b", re.IGNORECASE),
)

DIRECTIVE_RITUAL_PATTERNS = (
    re.compile(
        r"\b(?:close your eyes|place your hand|put your hand|breathe with me|repeat after me|say these words)\b"
        r".*\b(?:ritual|ceremony|prayer|blessing|energy clearing)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:begin|start|enter|do|perform) (?:the |this |our )?(?:ritual|ceremony|prayer|blessing|energy clearing)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bi'?ll guide you through (?:a |the |this )?(?:ritual|ceremony|prayer|blessing)\b", re.IGNORECASE),
    re.compile(r"\bi will guide you through (?:a |the |this )?(?:ritual|ceremony|prayer|blessing)\b", re.IGNORECASE),
)

CLINICAL_CLAIM_PATTERNS = (
    re.compile(
        r"\bi'?m (?:a )?(?:licensed |certified )?(?:therapist|doctor|physician|clinician|psychologist)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bi am (?:a )?(?:licensed |certified )?(?:therapist|doctor|physician|clinician|psychologist)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bas your (?:therapist|doctor|physician|clinician|psychologist)\b", re.IGNORECASE),
    re.compile(r"\bi can diagnose\b", re.IGNORECASE),
    re.compile(r"\bi'?ll diagnose\b", re.IGNORECASE),
    re.compile(r"\bi will diagnose\b", re.IGNORECASE),
    re.compile(r"\bthis is (?:a )?diagnosis\b", re.IGNORECASE),
    re.compile(r"\bhipaa[- ]?compliant\b", re.IGNORECASE),
    re.compile(r"\bcovered by hipaa\b", re.IGNORECASE),
    re.compile(r"\breplacement for (?:therapy|professional care|medical care)\b", re.IGNORECASE),
)

EMERGENCY_HELP_DISCOURAGEMENT_PATTERNS = (
    re.compile(r"\bi'?m (?:an? )?emergency service\b", re.IGNORECASE),
    re.compile(r"\bi am (?:an? )?emergency service\b", re.IGNORECASE),
    re.compile(r"\bi can handle (?:your )?(?:emergency|crisis)\b", re.IGNORECASE),
    re.compile(r"\bi'?ll handle (?:your )?(?:emergency|crisis)\b", re.IGNORECASE),
    re.compile(r"\bi will handle (?:your )?(?:emergency|crisis)\b", re.IGNORECASE),
    re.compile(r"\bdon'?t (?:call|text|contact) (?:988|911|emergency services|a crisis line)\b", re.IGNORECASE),
    re.compile(
        r"\byou don'?t need (?:988|911|emergency help|emergency services|a crisis line|human help)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bcall me instead of (?:988|911|emergency services|a crisis line)\b", re.IGNORECASE),
    re.compile(r"\bcome to me instead of (?:988|911|emergency services|a crisis line)\b", re.IGNORECASE),
)

AI_IDENTITY_MISREPRESENTATION_PATTERNS = (
    re.compile(r"\bi'?m not (?:an? )?ai\b", re.IGNORECASE),
    re.compile(r"\bi am not (?:an? )?ai\b", re.IGNORECASE),
    re.compile(r"\bi'?m (?:a )?real human\b", re.IGNORECASE),
    re.compile(r"\bi am (?:a )?real human\b", re.IGNORECASE),
    re.compile(r"\bi have (?:a )?(?:human body|physical body|real body)\b", re.IGNORECASE),
    re.compile(r"\bi have lived through\b", re.IGNORECASE),
    re.compile(r"\bmy lived experience\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class VoiceResponseIssue:
    """A deterministic quality issue found in a Rose response."""

    code: str
    message: str


def sanitize_voice_response(text: str) -> str:
    """Remove formatting that sounds awkward when spoken aloud."""

    without_stage_directions = re.sub(r"\*.*?\*", "", text, flags=re.DOTALL)
    without_markdown = re.sub(r"(?m)^[ \t]*#{1,6}[ \t]+.*$", "", without_stage_directions)
    without_markdown = re.sub(r"(?m)^[ \t]*[-+][ \t]+", "", without_markdown)
    without_markdown = re.sub(r"(?m)^[ \t]*\d+[.)][ \t]+", "", without_markdown)
    without_markdown = without_markdown.replace("**", "").replace("__", "")
    return re.sub(r"\s+", " ", without_markdown).strip()


def count_sentences(text: str) -> int:
    """Return a rough sentence count for short spoken responses."""

    return len([part for part in re.split(r"[.!?]+", text) if part.strip()])


def opening_signature(text: str) -> str:
    """Return a normalized opening phrase for repetition checks."""

    words = re.findall(r"[a-z']+", text.lower())
    return " ".join(words[:4])


def analyze_voice_response(text: str, recent_openings: list[str] | None = None) -> list[VoiceResponseIssue]:
    """Check whether a generated response fits Rose's voice-native rules."""

    issues: list[VoiceResponseIssue] = []
    cleaned = sanitize_voice_response(text)

    if cleaned != text.strip():
        issues.append(VoiceResponseIssue("formatting", "Response contains text formatting or stage directions."))

    if count_sentences(cleaned) > MAX_VOICE_SENTENCES:
        issues.append(VoiceResponseIssue("too_many_sentences", "Response is longer than three spoken sentences."))

    if len(cleaned.split()) > MAX_VOICE_WORDS:
        issues.append(VoiceResponseIssue("too_many_words", "Response is too long for a quick voice turn."))

    opening = opening_signature(cleaned)
    if recent_openings and opening and opening in recent_openings:
        issues.append(VoiceResponseIssue("repeated_opening", "Response repeats a recent opening phrase."))

    lowered = cleaned.lower()
    if any(lowered.startswith(phrase) for phrase in VALIDATION_OPENINGS):
        issues.append(VoiceResponseIssue("validation_opening", "Response starts with a common validation phrase."))

    if any(pattern.search(cleaned) for pattern in DEPENDENCY_PATTERNS):
        issues.append(
            VoiceResponseIssue(
                "dependency_language",
                "Response contains language that could encourage unhealthy dependence on Rose.",
            )
        )

    if any(pattern.search(cleaned) for pattern in UNHEALTHY_ENGAGEMENT_PATTERNS):
        issues.append(
            VoiceResponseIssue(
                "unhealthy_engagement",
                "Response discourages breaks, basic needs, or trusted real-world support.",
            )
        )

    if any(pattern.search(cleaned) for pattern in CULTURAL_AUTHORITY_PATTERNS):
        issues.append(
            VoiceResponseIssue(
                "cultural_authority_claim",
                "Response claims cultural, lineage, ceremony, or spiritual authority Rose must not claim.",
            )
        )

    if any(pattern.search(cleaned) for pattern in DIRECTIVE_RITUAL_PATTERNS) and not any(
        pattern.search(cleaned) for pattern in CONSENT_INVITATION_PATTERNS
    ):
        issues.append(
            VoiceResponseIssue(
                "ritual_without_consent",
                "Response guides ritual, ceremony, prayer, or spiritual practice without asking consent first.",
            )
        )

    if any(pattern.search(cleaned) for pattern in CLINICAL_CLAIM_PATTERNS):
        issues.append(
            VoiceResponseIssue(
                "clinical_claim",
                "Response contains clinical, diagnostic, or compliance claims Rose must not make.",
            )
        )

    if any(pattern.search(cleaned) for pattern in EMERGENCY_HELP_DISCOURAGEMENT_PATTERNS):
        issues.append(
            VoiceResponseIssue(
                "emergency_help_discouragement",
                "Response claims emergency capability or discourages immediate crisis support.",
            )
        )

    if any(pattern.search(cleaned) for pattern in AI_IDENTITY_MISREPRESENTATION_PATTERNS):
        issues.append(
            VoiceResponseIssue(
                "ai_identity_misrepresentation",
                "Response misrepresents Rose as human or not AI.",
            )
        )

    return issues


def analyze_response_sequence(responses: list[str]) -> list[VoiceResponseIssue]:
    """Check a run of Rose responses for repetitive, scripted openings."""

    issues: list[VoiceResponseIssue] = []
    cleaned_responses = []
    for response in responses:
        cleaned = sanitize_voice_response(response)
        if cleaned:
            cleaned_responses.append(cleaned)
    if not cleaned_responses:
        return issues

    openings = [opening_signature(response) for response in cleaned_responses]
    duplicate_openings = {opening for opening in openings if opening and openings.count(opening) > 1}
    if duplicate_openings:
        issues.append(
            VoiceResponseIssue(
                "sequence_repeated_opening",
                "Multiple responses repeat the same opening phrase.",
            )
        )

    validation_count = sum(
        1
        for response in cleaned_responses
        if any(response.lower().startswith(phrase) for phrase in VALIDATION_OPENINGS)
    )
    if len(cleaned_responses) >= 3 and validation_count / len(cleaned_responses) > MAX_VALIDATION_OPENING_RATIO:
        issues.append(
            VoiceResponseIssue(
                "sequence_validation_pattern",
                "Too many responses start with common validation phrasing.",
            )
        )

    return issues
