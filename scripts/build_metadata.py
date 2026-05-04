"""Generate metadata.json from in-tree sources of truth.

Reads pyproject.toml and netbox_sdk/typed_versions/ to derive:
- release: project.version
- python:  lower bound of project.requires-python, suffixed with "+"
- netbox:  ascending list parsed from typed_versions/v*.py filenames

Writes metadata.json at the repo root. Pure stdlib so it can run in any CI image.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tomllib
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
TYPED_VERSIONS_DIR = ROOT / "netbox_sdk" / "typed_versions"
OUTPUT = ROOT / "metadata.json"

VERSION_FILE_RE = re.compile(r"^v(\d+)_(\d+)\.py$")
PYTHON_LOWER_BOUND_RE = re.compile(r">=\s*(\d+\.\d+)")


def python_lower_bound(requires_python: str) -> str:
    match = PYTHON_LOWER_BOUND_RE.search(requires_python)
    if not match:
        raise ValueError(f"Cannot parse lower bound from requires-python={requires_python!r}")
    return f"{match.group(1)}+"


def discover_netbox_versions(directory: Path) -> list[str]:
    versions: list[tuple[int, int]] = []
    for entry in directory.iterdir():
        match = VERSION_FILE_RE.match(entry.name)
        if match:
            versions.append((int(match.group(1)), int(match.group(2))))
    if not versions:
        raise RuntimeError(f"No vMAJOR_MINOR.py files found under {directory}")
    versions.sort()
    return [f"{major}.{minor}" for major, minor in versions]


def main() -> int:
    pyproject = tomllib.loads(PYPROJECT.read_text())
    project = pyproject["project"]

    metadata = {
        "release": project["version"],
        "python": python_lower_bound(project["requires-python"]),
        "netbox": discover_netbox_versions(TYPED_VERSIONS_DIR),
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": {
            "repo": os.environ.get("GITHUB_REPOSITORY", "emersonfelipesp/netbox-sdk"),
            "commit": os.environ.get("GITHUB_SHA", ""),
        },
    }

    OUTPUT.write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
