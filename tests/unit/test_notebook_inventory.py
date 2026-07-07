from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "notebook_inventory.py"
SPEC = importlib.util.spec_from_file_location("notebook_inventory", SCRIPT_PATH)
notebook_inventory = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = notebook_inventory
SPEC.loader.exec_module(notebook_inventory)


def _write_notebook(path: Path, cells: list[dict[str, object]], metadata: dict[str, object] | None = None) -> None:
    path.write_text(json.dumps({"cells": cells, "metadata": metadata or {}}), encoding="utf-8")


def test_inventory_notebooks_counts_cells_and_outputs(tmp_path: Path) -> None:
    notebook = tmp_path / "notebooks" / "demo.ipynb"
    notebook.parent.mkdir()
    _write_notebook(
        notebook,
        [
            {"cell_type": "markdown", "source": ["# Demo Notebook\n", "notes"]},
            {"cell_type": "code", "source": ["print('hi')"], "outputs": [{"name": "stdout"}]},
            {"cell_type": "raw", "source": "raw notes"},
        ],
        metadata={"kernelspec": {"display_name": "Python 3"}, "language_info": {"name": "python"}},
    )

    [item] = notebook_inventory.inventory_notebooks(tmp_path, large_bytes=10_000)

    assert item.path == "notebooks/demo.ipynb"
    assert item.kernel == "Python 3"
    assert item.language == "python"
    assert item.cells == 3
    assert item.markdown_cells == 1
    assert item.code_cells == 1
    assert item.raw_cells == 1
    assert item.code_outputs == 1
    assert item.output_bytes > 0
    assert item.first_heading == "Demo Notebook"
    assert item.large is False
    assert item.large_outputs is False


def test_inventory_flags_large_notebooks(tmp_path: Path) -> None:
    notebook = tmp_path / "big.ipynb"
    _write_notebook(notebook, [{"cell_type": "markdown", "source": ["# Big\n", "x" * 200]}])

    [item] = notebook_inventory.inventory_notebooks(tmp_path, large_bytes=100)

    assert item.large is True


def test_inventory_flags_large_notebook_outputs(tmp_path: Path) -> None:
    notebook = tmp_path / "outputs.ipynb"
    _write_notebook(
        notebook,
        [
            {
                "cell_type": "code",
                "source": ["display(data)"],
                "outputs": [{"output_type": "stream", "text": "x" * 200}],
            }
        ],
    )

    [item] = notebook_inventory.inventory_notebooks(tmp_path, large_output_bytes=100)

    assert item.output_bytes >= 100
    assert item.large_outputs is True


def test_render_markdown_escapes_headings(tmp_path: Path) -> None:
    notebook = tmp_path / "demo.ipynb"
    _write_notebook(
        notebook,
        [{"cell_type": "markdown", "source": ["# A | B"]}],
        metadata={"kernelspec": {"display_name": "Python 3"}, "language_info": {"name": "python"}},
    )
    inventory = notebook_inventory.inventory_notebooks(tmp_path)

    markdown = notebook_inventory.render_markdown(inventory)

    assert "`demo.ipynb`" in markdown
    assert "Python 3" in markdown
    assert "python" in markdown
    assert "A \\| B" in markdown
