# Rose full repository refresh 2026-05-17
"""Repository hygiene checks ported from upstream PR intent.

These tests preserve the security and message-role intent of the referenced
contributor pull requests while adapting them to Rose's current stack.
"""

from __future__ import annotations

import ast
import io
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "ai_companion"


def _python_files() -> list[Path]:
    return sorted(path for path in SRC.rglob("*.py") if path.is_file())


def test_production_source_does_not_use_raw_print_logging() -> None:
    """Production code must not print payloads, headers, or tokens directly."""

    offenders: list[str] = []
    for path in _python_files():
        source = path.read_text(encoding="utf-8")
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
        for index, token in enumerate(tokens[:-1]):
            next_token = tokens[index + 1]
            if token.type == tokenize.NAME and token.string == "print" and next_token.string == "(":
                offenders.append(f"{path.relative_to(ROOT)}:{token.start[0]}")

    assert offenders == []


def test_graph_generated_responses_use_assistant_message_role() -> None:
    """Graph-generated responses should be AIMessage objects, never user messages."""

    nodes_path = SRC / "graph" / "nodes.py"
    tree = ast.parse(nodes_path.read_text(encoding="utf-8"), filename=str(nodes_path))
    function_returns: dict[str, list[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            calls: list[str] = []
            for child in ast.walk(node):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                    if child.func.id in {"AIMessage", "HumanMessage"}:
                        calls.append(child.func.id)
            function_returns[node.name] = calls

    for graph_node in {"conversation_node", "audio_node"}:
        assert "AIMessage" in function_returns.get(graph_node, [])

    assert "HumanMessage" not in function_returns.get("conversation_node", [])
    assert "HumanMessage" not in function_returns.get("audio_node", [])
