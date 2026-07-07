from __future__ import annotations

from ai_companion.config.server_config import APP_DESCRIPTION, APP_TITLE
from ai_companion.interfaces.web.app import create_app


def test_api_metadata_uses_safe_non_clinical_positioning() -> None:
    """OpenAPI metadata should not over-claim clinical or emergency capabilities."""

    assert APP_TITLE == "Rose Voice Companion API"
    assert "emotional support companion" in APP_DESCRIPTION
    assert "crisis-safety" in APP_DESCRIPTION
    assert "memory controls" in APP_DESCRIPTION

    forbidden_phrases = [
        "grief counselor",
        "therapeutic support",
        "therapist",
        "doctor",
        "emergency service",
        "HIPAA",
        "diagnosis",
        "clinical",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in APP_DESCRIPTION


def test_fastapi_openapi_metadata_uses_safe_description() -> None:
    """The configured metadata should be the description surfaced in API docs."""

    app = create_app()

    assert app.description == APP_DESCRIPTION
    assert "emotional support companion" in app.description
    assert "grief counselor" not in app.description
