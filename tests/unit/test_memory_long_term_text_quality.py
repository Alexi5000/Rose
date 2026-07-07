from __future__ import annotations

from pathlib import Path

LONG_TERM_MEMORY_DIR = Path(__file__).resolve().parents[2] / "src" / "ai_companion" / "modules" / "memory" / "long_term"


def test_long_term_memory_runtime_files_are_ascii() -> None:
    """Keep runtime memory logs portable across terminals and CI output."""

    offenders: list[str] = []
    for path in sorted(LONG_TERM_MEMORY_DIR.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.isascii():
                offenders.append(f"{path.relative_to(LONG_TERM_MEMORY_DIR)}:{line_number}: {line.strip()}")

    assert offenders == []
