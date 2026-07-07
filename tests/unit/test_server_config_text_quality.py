from __future__ import annotations

from pathlib import Path

import ai_companion.config.server_config as server_config

SERVER_CONFIG_PATH = Path(server_config.__file__)


def test_server_config_runtime_text_is_ascii() -> None:
    """Keep active API docs, errors, and log markers portable across clients."""

    text = SERVER_CONFIG_PATH.read_text(encoding="utf-8")

    assert text.isascii()


def test_user_facing_error_messages_are_plain_text() -> None:
    """HTTP error details should be readable even in plain terminals or logs."""

    messages = {
        name: value
        for name, value in vars(server_config).items()
        if name.startswith("ERROR_MSG_") and isinstance(value, str)
    }

    assert messages
    for name, message in messages.items():
        assert message.isascii(), name
        assert message == message.strip(), name
        assert len(message) >= 20, name
        assert not message.startswith(("ERROR:", "[error]", "error:")), name


def test_log_markers_are_ascii_labels() -> None:
    """Structured log marker fields should not depend on emoji rendering."""

    markers = {
        name: value
        for name, value in vars(server_config).items()
        if name.startswith("LOG_EMOJI_") and isinstance(value, str)
    }

    assert markers
    for name, marker in markers.items():
        assert marker.isascii(), name
        assert marker.isidentifier(), name
