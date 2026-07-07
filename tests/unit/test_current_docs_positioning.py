from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
API_DOCUMENTATION = REPO_ROOT / "docs" / "API_DOCUMENTATION.md"
API_DESIGN_VERIFICATION = REPO_ROOT / "docs" / "API_DESIGN_VERIFICATION.md"
API_QUICK_REFERENCE = REPO_ROOT / "docs" / "API_QUICK_REFERENCE.md"
OPERATIONAL_DOC_INDEX = REPO_ROOT / "docs" / "OPERATIONAL_DOCUMENTATION_INDEX.md"
PROVIDER_GUIDE = REPO_ROOT / "docs" / "PROVIDERS.md"


def test_api_documentation_uses_safe_current_positioning() -> None:
    """The current API reference should not describe Rose as clinical care."""

    text = API_DOCUMENTATION.read_text(encoding="utf-8")
    normalized = " ".join(text.split())

    assert "AI emotional support" in text
    assert "not a therapist, doctor, emergency service, or clinical product" in normalized
    assert "memory privacy controls" in text
    assert "configured STT provider" in text
    assert "configured TTS provider" in text
    assert "grief counselor" not in text
    assert "therapeutic AI" not in text
    assert "Ready to begin your healing journey" not in text
    assert "Rose is ready for emotional support when you are" in text


def test_api_design_verification_no_longer_recommends_old_metadata() -> None:
    """Historical verification docs should not preserve unsafe metadata examples."""

    text = API_DESIGN_VERIFICATION.read_text(encoding="utf-8")

    assert "Voice-first AI emotional support companion" in text
    assert "not a grief counselor" in text
    assert "Voice-first AI grief counselor" not in text
    assert "Ready to begin your healing journey" not in text


def test_api_quick_reference_uses_current_session_start_copy() -> None:
    """Quick-reference examples should not drift back to healing-journey copy."""

    text = API_QUICK_REFERENCE.read_text(encoding="utf-8")

    assert "Rose is ready for emotional support when you are" in text
    assert "Ready to begin your healing journey" not in text


def test_operational_index_routes_new_engineers_to_current_architecture_docs() -> None:
    """New contributors should land on current voice/provider docs before historical architecture."""

    text = OPERATIONAL_DOC_INDEX.read_text(encoding="utf-8")

    assert "[Voice Architecture](VOICE_ARCHITECTURE.md) - Understand the current voice pipeline" in text
    assert (
        "[Provider Guide](PROVIDERS.md) - Understand active AI, speech, safety, memory, and fallback providers" in text
    )
    assert "[Upstream Lineage Research](UPSTREAM_LINEAGE_RESEARCH.md)" in text
    assert (
        "[Architecture Documentation](ARCHITECTURE.md) | Historical architecture detail and frozen lineage references"
        in text
    )
    assert "Architecture Documentation](ARCHITECTURE.md) - Understand the system" not in text


def test_provider_guide_tracks_current_fallback_and_safety_modes() -> None:
    """Provider docs should match implemented degraded TTS and safety routes."""

    text = PROVIDER_GUIDE.read_text(encoding="utf-8")

    assert "Text-only / browser speech fallback" in text
    assert "TTS_PROVIDER=text_only" in text
    assert "TTS_PROVIDER=browser_speech" in text
    assert "External imminent danger guidance" in text
    assert "without self-harm wording" in text
