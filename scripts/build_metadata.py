"""Generate metadata.json from in-tree sources of truth.

Reads pyproject.toml and netbox_sdk/typed_versions/ to derive:
- release: project.version
- python:  lower bound of project.requires-python, suffixed with "+"
- netbox:  ascending list parsed from typed_versions/v*.py filenames
- source:  repository plus a required full commit from the environment or Git

Writes metadata.json at the repo root. Pure stdlib so it can run in any CI image.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
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
COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}$")


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


def source_commit() -> str:
    """Return an explicit, validated commit for metadata provenance."""
    commit = os.environ.get("SOURCE_COMMIT") or os.environ.get("GITHUB_SHA")
    if not commit:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--verify", "HEAD^{commit}"],
                cwd=ROOT,
                capture_output=True,
                check=False,
                text=True,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                "Metadata generation requires SOURCE_COMMIT, GITHUB_SHA, or Git history"
            ) from exc
        if result.returncode != 0:
            raise RuntimeError(
                "Metadata generation could not resolve source commit; set SOURCE_COMMIT"
            )
        commit = result.stdout.strip()

    if not COMMIT_RE.fullmatch(commit):
        raise ValueError("Metadata source commit must be a full 40-character Git SHA")
    return commit.lower()


def _git_output(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            capture_output=True,
            check=False,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Metadata provenance validation requires Git history") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "Git command failed"
        raise RuntimeError(f"Metadata provenance validation failed: {detail}")
    return result.stdout.strip()


def _git_blob_text(commit: str, path: str) -> str:
    """Read one committed file through its tree entry and blob object."""
    entry = _git_output("ls-tree", commit, "--", path)
    lines = entry.splitlines()
    if len(lines) != 1:
        raise RuntimeError(
            f"Metadata provenance expected one Git tree entry for {path!r}, found {len(lines)}"
        )
    try:
        metadata, recorded_path = lines[0].split("\t", 1)
        _mode, object_type, object_id = metadata.split()
    except ValueError as exc:
        raise RuntimeError(
            f"Metadata provenance found a malformed tree entry for {path!r}"
        ) from exc
    if object_type != "blob" or recorded_path != path:
        raise RuntimeError(f"Metadata provenance did not resolve {path!r} to the expected blob")
    return _git_output("cat-file", "blob", object_id)


def validate_source_provenance(commit: str, project_version: str) -> None:
    """Require provenance for the candidate tree or its metadata-only parent."""
    object_type = _git_output("cat-file", "-t", commit)
    if object_type != "commit":
        raise RuntimeError(
            f"Metadata source SHA must identify a commit object, got {object_type!r}"
        )
    _git_output("merge-base", "--is-ancestor", commit, "HEAD")
    source_pyproject = tomllib.loads(_git_blob_text(commit, "pyproject.toml"))
    source_version = str(source_pyproject["project"]["version"])
    if source_version != project_version:
        raise RuntimeError(
            "Metadata source commit has project version "
            f"{source_version!r}, expected {project_version!r}; commit the integration first, "
            "then regenerate metadata in a follow-up commit"
        )
    changed_paths = _git_output(
        "diff",
        "--name-only",
        commit,
        "HEAD",
        "--",
        ".",
        ":(exclude)metadata.json",
    )
    if changed_paths:
        changed = ", ".join(changed_paths.splitlines()[:5])
        raise RuntimeError(
            "Metadata source commit does not match the candidate tree outside "
            f"metadata.json: {changed}"
        )


def main() -> int:
    pyproject = tomllib.loads(PYPROJECT.read_text())
    project = pyproject["project"]

    commit = source_commit()
    validate_source_provenance(commit, str(project["version"]))

    metadata = {
        "release": project["version"],
        "python": python_lower_bound(project["requires-python"]),
        "netbox": discover_netbox_versions(TYPED_VERSIONS_DIR),
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": {
            "repo": os.environ.get("GITHUB_REPOSITORY", "emersonfelipesp/netbox-sdk"),
            "commit": commit,
        },
    }

    OUTPUT.write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
