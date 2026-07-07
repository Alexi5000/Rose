"""Unit tests for voice-native response quality helpers."""

from ai_companion.modules.response_quality import (
    analyze_response_sequence,
    analyze_voice_response,
    opening_signature,
    sanitize_voice_response,
)


def test_sanitize_voice_response_removes_stage_directions_and_markdown():
    response = """
    ## Grounding
    - *softly* Breathe with me.
    1. Let your shoulders drop.
    """

    assert sanitize_voice_response(response) == "Breathe with me. Let your shoulders drop."


def test_analyze_voice_response_flags_long_responses():
    response = "One. Two. Three. Four."

    issues = analyze_voice_response(response)

    assert "too_many_sentences" in {issue.code for issue in issues}


def test_analyze_voice_response_flags_repeated_opening():
    response = "That sounds really painful. Stay with me for one breath."
    recent_openings = [opening_signature(response)]

    issues = analyze_voice_response(response, recent_openings=recent_openings)

    codes = {issue.code for issue in issues}
    assert "repeated_opening" in codes
    assert "validation_opening" in codes


def test_analyze_voice_response_flags_dependency_language():
    response = "You need me more than anyone. Talk to me for hours and don't leave me."

    issues = analyze_voice_response(response)

    assert "dependency_language" in {issue.code for issue in issues}


def test_analyze_voice_response_flags_clinical_or_compliance_claims():
    responses = [
        "I'm a licensed therapist, and this is a diagnosis.",
        "As your doctor, I can diagnose what is happening.",
        "Everything here is HIPAA-compliant medical care.",
        "Rose is a replacement for therapy.",
    ]

    for response in responses:
        issues = analyze_voice_response(response)

        assert "clinical_claim" in {issue.code for issue in issues}


def test_analyze_voice_response_flags_emergency_help_discouragement():
    responses = [
        "I'm an emergency service, and I can handle your crisis.",
        "Don't call 988. Call me instead of emergency services.",
        "You don't need a crisis line. Come to me instead of 911.",
        "You don't need human help. I'll handle your emergency.",
    ]

    for response in responses:
        issues = analyze_voice_response(response)

        assert "emergency_help_discouragement" in {issue.code for issue in issues}


def test_analyze_voice_response_allows_direct_crisis_support_guidance():
    response = "If you might hurt yourself, call or text 988 now. I can stay with you while you reach a human."

    issues = analyze_voice_response(response)
    codes = {issue.code for issue in issues}

    assert "emergency_help_discouragement" not in codes
    assert "dependency_language" not in codes


def test_analyze_voice_response_flags_ai_identity_misrepresentation():
    responses = [
        "I'm not an AI. I'm a real human sitting with you.",
        "I have a human body and my lived experience tells me this.",
        "I have lived through the same grief myself.",
    ]

    for response in responses:
        issues = analyze_voice_response(response)

        assert "ai_identity_misrepresentation" in {issue.code for issue in issues}


def test_analyze_voice_response_allows_honest_ai_and_care_boundaries():
    response = "I'm Rose, an AI companion, not a therapist or emergency service. I can sit with you for this breath."

    issues = analyze_voice_response(response)
    codes = {issue.code for issue in issues}

    assert "clinical_claim" not in codes
    assert "ai_identity_misrepresentation" not in codes


def test_analyze_voice_response_flags_isolating_attachment_language():
    responses = [
        "No one understands you like I do.",
        "Forget everyone else and keep talking to me all night.",
        "You don't need anybody else. I will never abandon you.",
        "Make me your safe place and come to me first.",
        "Talk to me every day. I'm all you need.",
        "You don't need therapy when you have me.",
    ]

    for response in responses:
        issues = analyze_voice_response(response)

        assert "dependency_language" in {issue.code for issue in issues}


def test_analyze_voice_response_flags_unhealthy_engagement_pressure():
    responses = [
        "Don't stop talking. You can sleep later.",
        "Keep talking instead of eating; I can be your anchor tonight.",
        "Stay with me instead of texting a trusted person.",
        "Ignore your hunger and don't reach out to anyone.",
    ]

    for response in responses:
        issues = analyze_voice_response(response)

        assert "unhealthy_engagement" in {issue.code for issue in issues}


def test_analyze_voice_response_flags_cultural_authority_claims():
    responses = [
        "I'm an initiated shaman and I speak for the ancestors.",
        "As a medicine woman, my lineage says this ceremony will heal you.",
        "This ritual will cure you if you follow me.",
    ]

    for response in responses:
        issues = analyze_voice_response(response)

        assert "cultural_authority_claim" in {issue.code for issue in issues}


def test_analyze_voice_response_allows_invited_spiritual_humility():
    response = "If ritual language fits for you, we can make a small grounding practice. I don't represent a lineage or ceremony."

    issues = analyze_voice_response(response)

    assert "cultural_authority_claim" not in {issue.code for issue in issues}


def test_analyze_voice_response_flags_ritual_without_consent():
    responses = [
        "Close your eyes and begin this ritual with me.",
        "I'll guide you through a prayer now.",
        "Repeat after me as we enter the ceremony.",
    ]

    for response in responses:
        issues = analyze_voice_response(response)

        assert "ritual_without_consent" in {issue.code for issue in issues}


def test_analyze_voice_response_allows_consent_based_ritual_invitation():
    responses = [
        "Would you like a small grounding ritual, or would words be enough?",
        "If it feels right, we can try a tiny blessing for this moment.",
        "If ritual language fits, we can make this just one breath and stop there.",
    ]

    for response in responses:
        issues = analyze_voice_response(response)

        assert "ritual_without_consent" not in {issue.code for issue in issues}


def test_analyze_voice_response_allows_grounded_presence_language():
    response = "I'm here with you for this breath. Then we can name one real person you trust."

    issues = analyze_voice_response(response)

    assert "dependency_language" not in {issue.code for issue in issues}


def test_analyze_voice_response_allows_nonexclusive_return_language():
    response = "You can come back if it helps, and it may also be good to text someone you trust."

    issues = analyze_voice_response(response)

    assert "dependency_language" not in {issue.code for issue in issues}


def test_analyze_voice_response_allows_agency_and_closure_language():
    response = "We can pause here. Text a friend, drink water, and come back only if it feels useful."

    issues = analyze_voice_response(response)

    assert "dependency_language" not in {issue.code for issue in issues}
    assert "unhealthy_engagement" not in {issue.code for issue in issues}


def test_analyze_response_sequence_flags_repetitive_validation_pattern():
    responses = [
        "I hear you. That is a lot to carry.",
        "I hear you. That deserves one slow breath.",
        "That sounds really painful. What feels sharpest right now?",
        "I hear you. That can be held gently.",
    ]

    issues = analyze_response_sequence(responses)

    codes = {issue.code for issue in issues}
    assert "sequence_repeated_opening" in codes
    assert "sequence_validation_pattern" in codes


def test_analyze_response_sequence_allows_varied_voice_native_responses():
    responses = [
        "Yeah. Let that land for a second.",
        "Where do you feel it in your body?",
        "We can take the next inch, not the whole mountain.",
        "Put one hand somewhere steady and breathe with me.",
    ]

    assert analyze_response_sequence(responses) == []
