"""Inventory Jupyter notebooks without loading them in a browser."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

DEFAULT_LARGE_NOTEBOOK_BYTES = 1_000_000
DEFAULT_LARGE_OUTPUT_BYTES = 250_000


@dataclass(frozen=True)
class NotebookInventory:
    path: str
    bytes: int
    kernel: str
    language: str
    cells: int
    markdown_cells: int
    code_cells: int
    raw_cells: int
    code_outputs: int
    output_bytes: int
    first_heading: str
    large: bool
    large_outputs: bool


def _cell_source(cell: dict[str, Any]) -> str:
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(str(part) for part in source)
    return str(source)


def _first_heading(cells: Iterable[dict[str, Any]]) -> str:
    for cell in cells:
        if cell.get("cell_type") != "markdown":
            continue
        for line in _cell_source(cell).splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip()
    return ""


def _metadata_value(data: dict[str, Any], *keys: str) -> str:
    value: Any = data.get("metadata", {})
    for key in keys:
        if not isinstance(value, dict):
            return ""
        value = value.get(key, "")
    return str(value or "")


def inventory_notebook(path: Path, *, root: Path, large_bytes: int, large_output_bytes: int) -> NotebookInventory:
    data = json.loads(path.read_text(encoding="utf-8"))
    cells = data.get("cells", [])

    markdown_cells = 0
    code_cells = 0
    raw_cells = 0
    code_outputs = 0
    output_bytes = 0

    for cell in cells:
        cell_type = cell.get("cell_type")
        if cell_type == "markdown":
            markdown_cells += 1
        elif cell_type == "code":
            code_cells += 1
            outputs = cell.get("outputs", []) or []
            code_outputs += len(outputs)
            output_bytes += len(json.dumps(outputs, ensure_ascii=True))
        else:
            raw_cells += 1

    size = path.stat().st_size
    return NotebookInventory(
        path=path.relative_to(root).as_posix(),
        bytes=size,
        kernel=_metadata_value(data, "kernelspec", "display_name"),
        language=_metadata_value(data, "language_info", "name"),
        cells=len(cells),
        markdown_cells=markdown_cells,
        code_cells=code_cells,
        raw_cells=raw_cells,
        code_outputs=code_outputs,
        output_bytes=output_bytes,
        first_heading=_first_heading(cells),
        large=size >= large_bytes,
        large_outputs=output_bytes >= large_output_bytes,
    )


def inventory_notebooks(
    root: Path,
    *,
    large_bytes: int = DEFAULT_LARGE_NOTEBOOK_BYTES,
    large_output_bytes: int = DEFAULT_LARGE_OUTPUT_BYTES,
) -> list[NotebookInventory]:
    root = root.resolve()
    notebooks = sorted(
        path
        for path in root.rglob("*.ipynb")
        if ".git" not in path.parts and ".venv" not in path.parts and "node_modules" not in path.parts
    )
    return [
        inventory_notebook(path, root=root, large_bytes=large_bytes, large_output_bytes=large_output_bytes)
        for path in notebooks
    ]


def render_markdown(inventory: list[NotebookInventory]) -> str:
    lines = [
        "| Notebook | Size | Kernel | Language | Cells | Markdown | Code | Outputs | Output bytes | Heading | Large | Large outputs |",
        "| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for item in inventory:
        heading = item.first_heading.replace("|", "\\|")
        lines.append(
            f"| `{item.path}` | {item.bytes} | {item.kernel} | {item.language} | {item.cells} | "
            f"{item.markdown_cells} | {item.code_cells} | {item.code_outputs} | {item.output_bytes} | "
            f"{heading} | {'yes' if item.large else 'no'} | {'yes' if item.large_outputs else 'no'} |"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize notebooks for review and research.")
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    parser.add_argument(
        "--large-bytes",
        type=int,
        default=DEFAULT_LARGE_NOTEBOOK_BYTES,
        help="Mark notebooks at or above this byte size as large.",
    )
    parser.add_argument(
        "--large-output-bytes",
        type=int,
        default=DEFAULT_LARGE_OUTPUT_BYTES,
        help="Mark notebooks with embedded outputs at or above this byte size.",
    )
    parser.add_argument("--markdown", action="store_true", help="Print a markdown table instead of JSON.")
    parser.add_argument("--fail-on-large", action="store_true", help="Exit nonzero if any notebook is marked large.")
    parser.add_argument(
        "--fail-on-large-output",
        action="store_true",
        help="Exit nonzero if any notebook has large embedded outputs.",
    )
    args = parser.parse_args()

    inventory = inventory_notebooks(
        Path(args.root),
        large_bytes=args.large_bytes,
        large_output_bytes=args.large_output_bytes,
    )
    if args.markdown:
        print(render_markdown(inventory))
    else:
        print(json.dumps([asdict(item) for item in inventory], indent=2))

    if args.fail_on_large and any(item.large for item in inventory):
        return 1
    if args.fail_on_large_output and any(item.large_outputs for item in inventory):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
