from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_ROOT = PROJECT_ROOT / "netbox_cli"

# Quoted hex literals in Python code indicate hardcoded runtime colors.
_PY_HEX_LITERAL = re.compile(r"""["']#[0-9A-Fa-f]{3,8}["']""")

# Named terminal colors in explicit style strings bypass theme variables.
_PY_NAMED_STYLE = re.compile(
    r"""style\s*=\s*["'][^"']*\b(red|green|blue|yellow|magenta|cyan|orange|purple|white|black)\b[^"']*["']"""
)

# Any hex color in TCSS outside theme JSON files is considered hardcoded.
_TCSS_HEX = re.compile(r"#[0-9A-Fa-f]{3,8}")


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
                    violations.append(
                        f"{path.relative_to(PROJECT_ROOT)}:{idx}: hex literal"
                    )
                if _PY_NAMED_STYLE.search(line):
                    violations.append(
                        f"{path.relative_to(PROJECT_ROOT)}:{idx}: named style color"
                    )
            continue

        tcss_without_comments = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
        for idx, line in enumerate(tcss_without_comments.splitlines(), start=1):
            if _TCSS_HEX.search(line):
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{idx}: hex literal in tcss"
                )

    assert not violations, "Hardcoded runtime colors found:\n" + "\n".join(violations)
