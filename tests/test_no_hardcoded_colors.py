"""Tests that runtime UI files avoid hardcoded color values."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.suite_tui

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_ROOT = PROJECT_ROOT / "netbox_tui"

# Quoted hex literals in Python code indicate hardcoded runtime colors.
_PY_HEX_LITERAL = re.compile(r"""["']#[0-9A-Fa-f]{3,8}["']""")

# Named terminal colors in explicit style strings bypass theme variables.
_PY_NAMED_STYLE = re.compile(
    r"""style\s*=\s*["'][^"']*\b(red|green|blue|yellow|magenta|cyan|orange|purple|white|black)\b[^"']*["']"""
)

# Any hex color in TCSS outside theme JSON files is considered hardcoded.
_TCSS_HEX = re.compile(r"#[0-9A-Fa-f]{3,8}")
_TCSS_TOKEN = re.compile(r"\$([A-Za-z0-9_-]+)")

_RUNTIME_TCSS_ENTRYPOINTS = (
    PACKAGE_ROOT / "ui_common.tcss",
    PACKAGE_ROOT / "tui.tcss",
    PACKAGE_ROOT / "dev_tui.tcss",
    PACKAGE_ROOT / "django_model_tui.tcss",
    PACKAGE_ROOT / "logs_tui.tcss",
)
_ALLOWED_THEME_TOKENS = {
    "accent",
    "background",
    "block-hover-background",
    "boost",
    "border",
    "error",
    "footer-background",
    "footer-description-background",
    "footer-description-foreground",
    "footer-foreground",
    "footer-item-background",
    "footer-key-background",
    "footer-key-foreground",
    "foreground",
    "input-cursor-background",
    "input-cursor-foreground",
    "nb-border",
    "nb-border-subtle",
    "nb-danger-bg",
    "nb-danger-text",
    "nb-id-text",
    "nb-info-bg",
    "nb-info-text",
    "nb-key-text",
    "nb-link-text",
    "nb-logo-accent",
    "nb-logo-wordmark",
    "nb-muted-text",
    "nb-secondary-bg",
    "nb-secondary-text",
    "nb-success-bg",
    "nb-success-text",
    "nb-warning-bg",
    "nb-warning-text",
    "panel",
    "primary",
    "secondary",
    "success",
    "surface",
    "text",
    "text-muted",
    "warning",
}


def _runtime_files() -> list[Path]:
    files: list[Path] = []
    for path in PACKAGE_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts:
            continue
        if "themes" in path.parts:
            continue
        if path.suffix not in {".py", ".tcss"}:
            continue
        files.append(path)
    return sorted(files)


def test_no_hardcoded_runtime_colors() -> None:
    violations: list[str] = []

    for path in _runtime_files():
        content = path.read_text(encoding="utf-8")

        if path.suffix == ".py":
            for idx, line in enumerate(content.splitlines(), start=1):
                if _PY_HEX_LITERAL.search(line):
                    violations.append(f"{path.relative_to(PROJECT_ROOT)}:{idx}: hex literal")
                if _PY_NAMED_STYLE.search(line):
                    violations.append(f"{path.relative_to(PROJECT_ROOT)}:{idx}: named style color")
            continue

        tcss_without_comments = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
        for idx, line in enumerate(tcss_without_comments.splitlines(), start=1):
            if _TCSS_HEX.search(line):
                violations.append(f"{path.relative_to(PROJECT_ROOT)}:{idx}: hex literal in tcss")

    assert not violations, "Hardcoded runtime colors found:\n" + "\n".join(violations)


def test_runtime_tcss_tokens_are_theme_backed() -> None:
    violations: list[str] = []

    for path in _RUNTIME_TCSS_ENTRYPOINTS:
        content = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.DOTALL)
        for idx, line in enumerate(content.splitlines(), start=1):
            for token in _TCSS_TOKEN.findall(line):
                if token not in _ALLOWED_THEME_TOKENS:
                    violations.append(
                        f"{path.relative_to(PROJECT_ROOT)}:{idx}: unknown theme token ${token}"
                    )

    assert not violations, "Unsupported runtime TCSS tokens found:\n" + "\n".join(violations)
