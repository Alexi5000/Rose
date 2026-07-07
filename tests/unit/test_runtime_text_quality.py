from __future__ import annotations

import ast
from pathlib import Path

import pytest

from ai_companion.core.exceptions import CircuitBreakerError, WorkflowError
from ai_companion.core.privacy_logging import REDACTED_TEXT
from ai_companion.graph.utils.helpers import node_wrapper
from ai_companion.settings import settings

REPO_ROOT = Path(__file__).resolve().parents[2]

ACTIVE_RUNTIME_FILES = [
    REPO_ROOT / "src" / "ai_companion" / "settings.py",
    REPO_ROOT / "src" / "ai_companion" / "interfaces" / "web" / "app.py",
    REPO_ROOT / "src" / "ai_companion" / "interfaces" / "web" / "routes" / "health.py",
    REPO_ROOT / "src" / "ai_companion" / "interfaces" / "web" / "routes" / "session.py",
    REPO_ROOT / "src" / "ai_companion" / "interfaces" / "web" / "routes" / "voice.py",
    REPO_ROOT / "src" / "ai_companion" / "interfaces" / "web" / "routes" / "voice_websocket.py",
    REPO_ROOT / "src" / "ai_companion" / "graph" / "nodes.py",
    REPO_ROOT / "src" / "ai_companion" / "graph" / "utils" / "chains.py",
    REPO_ROOT / "src" / "ai_companion" / "graph" / "utils" / "helpers.py",
    REPO_ROOT / "src" / "ai_companion" / "modules" / "memory" / "long_term" / "memory_manager.py",
]


def test_active_runtime_files_are_ascii_and_use_marker_fields() -> None:
    """Active runtime logs and docstrings should render cleanly in plain terminals."""

    for path in ACTIVE_RUNTIME_FILES:
        text = path.read_text(encoding="utf-8")

        assert text.isascii(), path
        assert "emoji=" not in text, path
        assert "therapeutic" not in text, path
        assert "therapeutic AI" not in text, path
        assert "healing session" not in text, path
        assert "grief counselor" not in text, path


def test_active_runtime_files_do_not_print_payloads() -> None:
    """Runtime paths should use structured logging, not print payloads or headers."""

    allowed_print_functions = {
        (REPO_ROOT / "src" / "ai_companion" / "settings.py", "load_settings"),
    }

    for path in ACTIVE_RUNTIME_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        parents: dict[ast.AST, ast.AST] = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                parents[child] = parent

        print_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print"
        ]

        disallowed_lines = []
        for node in print_calls:
            current: ast.AST | None = node
            function_name = ""
            while current is not None:
                if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    function_name = current.name
                    break
                current = parents.get(current)

            if (path, function_name) not in allowed_print_functions:
                disallowed_lines.append(node.lineno)

        assert disallowed_lines == [], f"{path} has print calls on lines {disallowed_lines}"


@pytest.mark.asyncio
async def test_node_wrapper_redacts_exception_text_by_default(monkeypatch, caplog) -> None:
    """Generic graph wrapper failures should not leak provider-echoed text."""

    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)

    @node_wrapper
    async def failing_node():
        raise RuntimeError("provider echoed private grief transcript")

    with caplog.at_level("ERROR", logger="ai_companion.graph.utils.helpers"):
        with pytest.raises(WorkflowError) as exc_info:
            await failing_node()

    assert "provider echoed" not in str(exc_info.value)
    assert "private grief" not in caplog.text

    node_records = [record for record in caplog.records if record.message == "node_exception"]
    assert node_records
    assert getattr(node_records[0], "error") == REDACTED_TEXT
    assert getattr(node_records[0], "error_type") == "RuntimeError"


@pytest.mark.asyncio
async def test_node_wrapper_redacts_circuit_breaker_exception_text(monkeypatch, caplog) -> None:
    """Circuit breaker wrapper logs should not include provider/user text by default."""

    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)

    @node_wrapper
    async def failing_node():
        raise CircuitBreakerError("provider echoed private grief transcript")

    with caplog.at_level("ERROR", logger="ai_companion.graph.utils.helpers"):
        with pytest.raises(CircuitBreakerError):
            await failing_node()

    assert "private grief" not in caplog.text

    node_records = [record for record in caplog.records if record.message == "node_circuit_breaker_error"]
    assert node_records
    assert getattr(node_records[0], "error") == REDACTED_TEXT
    assert getattr(node_records[0], "error_type") == "CircuitBreakerError"
