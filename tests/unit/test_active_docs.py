from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT_README = REPO_ROOT / "README.md"
ENV_EXAMPLE = REPO_ROOT / ".env.example"
MANUAL_VOICE_GUIDE = REPO_ROOT / "tests" / "manual_e2e_voice_first_testing.md"
FRONTEND_README = REPO_ROOT / "frontend" / "README.md"
VOICE_TESTING_DOC = REPO_ROOT / "docs" / "VOICE_TESTING.md"
DEVELOPER_GUIDE = REPO_ROOT / "docs" / "DEVELOPER_GUIDE.md"


def test_manual_voice_guide_tracks_current_web_app_surface() -> None:
    """The active manual voice guide should not drift back to archived UI flows."""

    text = MANUAL_VOICE_GUIDE.read_text(encoding="utf-8")

    assert "React and FastAPI web app" in text
    assert "http://localhost:3000" in text
    assert "/api/v1/voice/ws" in text
    assert "Chainlit application running locally" not in text
    assert "uv run chainlit" not in text
    assert "Upload an image" not in text


def test_frontend_readme_uses_current_safe_product_language() -> None:
    """The active frontend README should match current runtime and safety posture."""

    text = FRONTEND_README.read_text(encoding="utf-8")

    assert "React 19" in text
    assert "WebSocket audio transport" in text
    assert "not a therapist, doctor, emergency service, or clinical product" in text
    assert "grief counselor" not in text
    assert "React 18" not in text
    assert "â" not in text


def test_root_readme_uses_current_safe_product_language() -> None:
    """The root README should present Rose honestly and avoid stale or garbled docs."""

    text = ROOT_README.read_text(encoding="utf-8")
    normalized = " ".join(text.split())

    assert "AI emotional support" in text
    assert "not a therapist, doctor, emergency service, or replacement for professional care" in normalized
    assert "OpenRouter" in text
    assert "Deepgram" in text
    assert "text-only/browser speech degraded modes" in text
    assert "Imminent external danger" in text
    assert "trusted-contact" in text
    assert "cp .env.example .env" in text
    assert "neural-maze/ava-whatsapp-agent-course" in text
    assert "grief counselor" not in text
    assert "Chainlit application running locally" not in text
    assert "â" not in text
    assert "├" not in text
    assert "└" not in text


def test_env_example_tracks_active_provider_configuration() -> None:
    """The env template should expose active providers without containing real secrets."""

    text = ENV_EXAMPLE.read_text(encoding="utf-8")

    required_keys = [
        "GROQ_API_KEY",
        "ELEVENLABS_API_KEY",
        "ELEVENLABS_VOICE_ID",
        "QDRANT_URL",
        "LLM_PROVIDER",
        "LLM_FALLBACK_PROVIDER",
        "OPENROUTER_API_KEY",
        "OPENROUTER_BASE_URL",
        "OPENROUTER_MODEL_NAME",
        "STT_PROVIDER",
        "DEEPGRAM_API_KEY",
        "TTS_PROVIDER",
        "DEEPGRAM_ENDPOINTING_MS",
        "DEEPGRAM_UTTERANCE_END_MS",
        "EMBEDDING_PROVIDER",
        "MEMORY_PROVIDER",
        "SAFETY_PROVIDER",
        "LOG_SENSITIVE_CONTENT",
    ]

    for key in required_keys:
        assert f"{key}=" in text, key

    assert "sk-" not in text.lower()
    assert "gsk_" not in text.lower()
    assert "copy to .env" in text.lower()


def test_developer_guide_tracks_active_source_tree() -> None:
    """The contributor guide should describe current active surfaces, not frozen lineage."""

    text = DEVELOPER_GUIDE.read_text(encoding="utf-8")

    assert "React/FastAPI voice surface" in text
    assert "interfaces/web/" in text
    assert "modules/providers/" in text
    assert "modules/safety/" in text
    assert "WebSocket Session State" in text
    assert "/api/v1/voice/ws" in text
    assert "Chainlit chat interface" not in text
    assert "import chainlit" not in text
    assert "Image generation (frozen)" not in text
    assert "Ã¢" not in text
    assert "â”" not in text


def test_voice_testing_doc_points_to_current_manual_guide() -> None:
    """The legacy voice-testing filename should not preserve stale provider or UI flows."""

    text = VOICE_TESTING_DOC.read_text(encoding="utf-8")

    assert "tests/manual_e2e_voice_first_testing.md" in text
    assert "React and FastAPI web app" in text
    assert "http://localhost:3000" in text
    assert "OpenRouter" in text
    assert "Deepgram" in text
    assert "LOG_SENSITIVE_CONTENT=false" in text
    assert "ANTHROPIC_API_KEY" not in text
    assert "Claude" not in text
    assert 'Transcription: "Hello Rose' not in text
    assert "You said:" not in text
    assert "â" not in text
