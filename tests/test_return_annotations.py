from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.suite_sdk


def test_all_non_test_python_functions_have_return_annotations() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    excluded_parts = {
        ".venv",
        "venv",
        "tests",
        "examples",
        "site",
        "build",
        "dist",
        "models",
        "typed_versions",
    }
    missing: list[str] = []

    for path in repo_root.rglob("*.py"):
        if any(part in excluded_parts for part in path.parts):
            continue
        if "site-packages" in path.parts:
            continue
        if any(part.startswith(".venv") for part in path.parts):
            continue
        module = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(module):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.returns is None:
                missing.append(f"{path.relative_to(repo_root)}:{node.lineno}:{node.name}")

    assert missing == []
