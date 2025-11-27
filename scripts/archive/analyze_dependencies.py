#!/usr/bin/env python3
"""
Dependency analysis script for AI Companion application.

This script analyzes import statements across the codebase to:
1. Map module dependencies
2. Identify circular dependencies
3. Identify interface-to-core dependencies that should be reversed
4. Generate a dependency report
"""

import ast
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple


class DependencyAnalyzer:
    """Analyzes Python module dependencies."""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.module_files: Dict[str, Path] = {}

    def analyze(self) -> None:
        """Analyze all Python files in the project."""
        src_path = self.root_path / "src" / "ai_companion"

        if not src_path.exists():
            print(f"Error: Source path {src_path} does not exist")
            return

        # Collect all Python files
        for py_file in src_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            module_name = self._get_module_name(py_file)
            self.module_files[module_name] = py_file

            # Parse imports
            imports = self._extract_imports(py_file)
            self.dependencies[module_name] = imports

    def _get_module_name(self, file_path: Path) -> str:
        """Convert file path to module name."""
        relative = file_path.relative_to(self.root_path / "src")
        parts = list(relative.parts)

        # Remove .py extension
        if parts[-1].endswith(".py"):
            parts[-1] = parts[-1][:-3]

        return ".".join(parts)

    def _extract_imports(self, file_path: Path) -> Set[str]:
        """Extract import statements from a Python file."""
        imports = set()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith("ai_companion"):
                            imports.add(alias.name)

                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith("ai_companion"):
                        imports.add(node.module)

        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}")

        return imports

    def find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependencies using DFS."""
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(module: str, path: List[str]) -> None:
            visited.add(module)
            rec_stack.add(module)
            path.append(module)

            for dep in self.dependencies.get(module, set()):
                # Only consider dependencies within our codebase
                if dep not in self.module_files:
                    continue

                if dep not in visited:
                    dfs(dep, path.copy())
                elif dep in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(dep)
                    cycle = path[cycle_start:] + [dep]
                    if cycle not in cycles:
                        cycles.append(cycle)

            rec_stack.remove(module)

        for module in self.dependencies:
            if module not in visited:
                dfs(module, [])

        return cycles

    def find_interface_to_core_dependencies(self) -> List[Tuple[str, str]]:
        """Find dependencies from interface modules to core modules."""
        problematic = []

        for module, deps in self.dependencies.items():
            # Check if this is an interface module
            if "interfaces" in module:
                for dep in deps:
                    # Check if it depends on core modules
                    if "core" in dep or "modules" in dep:
                        problematic.append((module, dep))

        return problematic

    def categorize_modules(self) -> Dict[str, List[str]]:
        """Categorize modules by their layer."""
        categories = {"core": [], "modules": [], "graph": [], "interfaces": [], "other": []}

        for module in self.module_files:
            if "core" in module:
                categories["core"].append(module)
            elif "modules" in module:
                categories["modules"].append(module)
            elif "graph" in module:
                categories["graph"].append(module)
            elif "interfaces" in module:
                categories["interfaces"].append(module)
            else:
                categories["other"].append(module)

        return categories

    def generate_report(self) -> str:
        """Generate a comprehensive dependency report."""
        report = []
        report.append("=" * 80)
        report.append("DEPENDENCY ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")

        # Module categories
        categories = self.categorize_modules()
        report.append("MODULE CATEGORIES")
        report.append("-" * 80)
        for category, modules in categories.items():
            report.append(f"\n{category.upper()} ({len(modules)} modules):")
            for module in sorted(modules):
                report.append(f"  - {module}")
        report.append("")

        # Circular dependencies
        report.append("CIRCULAR DEPENDENCIES")
        report.append("-" * 80)
        cycles = self.find_circular_dependencies()
        if cycles:
            report.append(f"Found {len(cycles)} circular dependency chain(s):\n")
            for i, cycle in enumerate(cycles, 1):
                report.append(f"{i}. Cycle:")
                for j, module in enumerate(cycle):
                    if j < len(cycle) - 1:
                        report.append(f"   {module}")
                        report.append("     ↓")
                    else:
                        report.append(f"   {module}")
                report.append("")
        else:
            report.append("✓ No circular dependencies found!")
        report.append("")

        # Interface-to-core dependencies
        report.append("INTERFACE-TO-CORE DEPENDENCIES")
        report.append("-" * 80)
        report.append("(These may indicate architectural issues)\n")

        interface_deps = self.find_interface_to_core_dependencies()
        if interface_deps:
            report.append(f"Found {len(interface_deps)} interface-to-core dependency(ies):\n")
            for interface, core in interface_deps:
                report.append(f"  {interface}")
                report.append(f"    → {core}")
                report.append("")
        else:
            report.append("✓ No problematic interface-to-core dependencies found!")
        report.append("")

        # Dependency matrix by category
        report.append("DEPENDENCY MATRIX BY CATEGORY")
        report.append("-" * 80)
        report.append("Shows which categories depend on which:\n")

        category_deps = defaultdict(lambda: defaultdict(int))
        for module, deps in self.dependencies.items():
            module_cat = self._get_category(module)
            for dep in deps:
                if dep in self.module_files:
                    dep_cat = self._get_category(dep)
                    if module_cat != dep_cat:
                        category_deps[module_cat][dep_cat] += 1

        for from_cat in ["interfaces", "graph", "modules", "core"]:
            if from_cat in category_deps:
                report.append(f"{from_cat.upper()} depends on:")
                for to_cat, count in sorted(category_deps[from_cat].items()):
                    report.append(f"  - {to_cat}: {count} dependencies")
                report.append("")

        # Detailed module dependencies
        report.append("DETAILED MODULE DEPENDENCIES")
        report.append("-" * 80)
        for module in sorted(self.module_files.keys()):
            deps = self.dependencies.get(module, set())
            internal_deps = [d for d in deps if d in self.module_files]

            if internal_deps:
                report.append(f"\n{module}:")
                for dep in sorted(internal_deps):
                    report.append(f"  → {dep}")

        report.append("")
        report.append("=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)

        return "\n".join(report)

    def _get_category(self, module: str) -> str:
        """Get the category of a module."""
        if "core" in module:
            return "core"
        elif "modules" in module:
            return "modules"
        elif "graph" in module:
            return "graph"
        elif "interfaces" in module:
            return "interfaces"
        return "other"


def main():
    """Main entry point."""
    analyzer = DependencyAnalyzer(".")
    analyzer.analyze()

    report = analyzer.generate_report()
    print(report)

    # Save report to file
    output_file = Path("docs/DEPENDENCY_ANALYSIS.md")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Dependency Analysis Report\n\n")
        f.write("Generated by `scripts/analyze_dependencies.py`\n\n")
        f.write("```\n")
        f.write(report)
        f.write("\n```\n")

    print(f"\n\nReport saved to: {output_file}")


if __name__ == "__main__":
    main()
