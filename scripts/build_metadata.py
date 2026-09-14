"""Generate and verify metadata.json from in-tree sources of truth.

Reads pyproject.toml and netbox_sdk/typed_versions/ to derive:
- release: project.version
- python:  lower bound of project.requires-python, suffixed with "+"
- netbox:  ascending list parsed from typed_versions/v*.py filenames
- source:  repository, project version, informational commit, and content identity

The content identity is the SHA-256 hex digest of the UTF-8 bytes of sorted
``git ls-tree -r --full-tree`` lines, with one trailing newline per line and the
``metadata.json`` entry omitted. Generation builds the candidate tree in a
temporary index and object database after staging the current checkout with
``git add --all``. It therefore leaves the real index and Git object database
unchanged and equals the committed tree outside ``metadata.json`` when all
generated files are committed together. Recursive ``git ls-tree`` output does
not contain empty subtrees, so empty directories do not affect the identity.

Content equality authenticates the candidate tree, not its repository origin.
The metadata schema pins the declared repository name, but an external trusted
fetch or equivalent canonical-source binding must authenticate the origin.

Writes metadata.json at the repo root. Pure stdlib so it can run in any CI image.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
TYPED_VERSIONS_DIR = ROOT / "netbox_sdk" / "typed_versions"
OUTPUT = ROOT / "metadata.json"

VERSION_FILE_RE = re.compile(r"^v(\d+)_(\d+)\.py$")
PYTHON_LOWER_BOUND_RE = re.compile(r">=\s*(\d+\.\d+)")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
CONTENT_ID_RE = re.compile(r"^[0-9a-f]{64}$")
GENERATED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

CANONICAL_REPOSITORY = "emersonfelipesp/netbox-sdk"
CANONICAL_REPOSITORY_URL = f"https://github.com/{CANONICAL_REPOSITORY}"
TOP_LEVEL_FIELDS = frozenset({"release", "python", "netbox", "generated_at", "source"})
SOURCE_FIELDS = frozenset({"repo", "version", "commit", "content_id"})


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
    """Return a full informational source commit from the environment or Git."""
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

    if not COMMIT_RE.fullmatch(commit.lower()):
        raise ValueError("Metadata source commit must be a full 40-character Git SHA")
    return commit.lower()


def _run_git(
    *args: str,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=ROOT,
            capture_output=True,
            check=False,
            env=env,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Metadata provenance validation requires Git history") from exc


def _git_output(*args: str, env: Mapping[str, str] | None = None) -> str:
    result = _run_git(*args, env=env)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "Git command failed"
        raise RuntimeError(f"Metadata provenance validation failed: {detail}")
    return result.stdout.rstrip("\n")


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


def validate_source_provenance(
    commit: str,
    project_version: str,
    *,
    expected_content_id: str | None = None,
) -> None:
    """Require a resolved informational commit to match the candidate tree."""
    object_type = _git_output("cat-file", "-t", commit)
    if object_type != "commit":
        raise RuntimeError(
            f"Metadata source SHA must identify a commit object, got {object_type!r}"
        )
    source_pyproject = tomllib.loads(_git_blob_text(commit, "pyproject.toml"))
    source_version = str(source_pyproject["project"]["version"])
    if source_version != project_version:
        raise RuntimeError(
            "Metadata source commit has project version "
            f"{source_version!r}, expected {project_version!r}"
        )
    candidate_content_id = expected_content_id or content_id_for_tree()
    source_content_id = content_id_for_tree(commit)
    if source_content_id != candidate_content_id:
        raise RuntimeError(
            "Metadata source commit does not match the candidate tree outside "
            "metadata.json; commit the candidate tree first or provide an unavailable "
            "informational SHA until the commit exists"
        )


def _canonical_tree_bytes(listing: str) -> bytes:
    lines: list[str] = []
    for line in listing.splitlines():
        try:
            _entry, path = line.split("\t", 1)
        except ValueError as exc:
            raise RuntimeError("Metadata content identity found a malformed tree entry") from exc
        if path != "metadata.json":
            lines.append(line)
    return "".join(f"{line}\n" for line in sorted(lines)).encode("utf-8")


def content_id_for_tree(
    treeish: str = "HEAD",
    *,
    env: Mapping[str, str] | None = None,
) -> str:
    """Return the content identity for a Git tree, excluding metadata.json."""
    listing = _git_output(
        "-c",
        "core.quotePath=true",
        "ls-tree",
        "-r",
        "--full-tree",
        treeish,
        env=env,
    )
    return hashlib.sha256(_canonical_tree_bytes(listing)).hexdigest()


def _temporary_git_environment(temporary_root: Path) -> dict[str, str]:
    object_directory = Path(_git_output("rev-parse", "--git-path", "objects"))
    if not object_directory.is_absolute():
        object_directory = ROOT / object_directory
    temporary_objects = temporary_root / "objects"
    temporary_objects.mkdir()

    environment = os.environ.copy()
    inherited_alternates = environment.get("GIT_ALTERNATE_OBJECT_DIRECTORIES")
    alternates = [str(object_directory.resolve())]
    if inherited_alternates:
        alternates.append(inherited_alternates)
    environment.update(
        {
            "GIT_ALTERNATE_OBJECT_DIRECTORIES": os.pathsep.join(alternates),
            "GIT_INDEX_FILE": str(temporary_root / "index"),
            "GIT_OBJECT_DIRECTORY": str(temporary_objects),
        }
    )
    return environment


def content_id_for_worktree() -> str:
    """Hash a candidate tree containing every tracked and unignored checkout file."""
    with tempfile.TemporaryDirectory(prefix="netbox-sdk-metadata-") as temporary:
        environment = _temporary_git_environment(Path(temporary))
        _git_output("read-tree", "HEAD", env=environment)
        _git_output("add", "--all", "--", ".", env=environment)
        tree = _git_output("write-tree", env=environment)
        return content_id_for_tree(tree, env=environment)


def _resolved_object_type(object_id: str) -> str | None:
    result = _run_git("cat-file", "-t", object_id)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _load_project() -> dict[str, Any]:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]


def _require_exact_object(
    value: object,
    expected_fields: frozenset[str],
    path: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must be an object")
    actual_fields = set(value)
    if actual_fields != expected_fields:
        missing = ", ".join(sorted(expected_fields - actual_fields)) or "none"
        unknown = ", ".join(sorted(actual_fields - expected_fields)) or "none"
        raise RuntimeError(
            f"{path} fields must match the exact schema; missing: {missing}; unknown: {unknown}"
        )
    return cast(dict[str, Any], value)


def _canonical_repository(project: Mapping[str, Any]) -> str:
    urls = project.get("urls")
    if not isinstance(urls, dict) or urls.get("Repository") != CANONICAL_REPOSITORY_URL:
        raise RuntimeError(
            "pyproject.toml project.urls.Repository does not match the trusted canonical "
            f"repository URL {CANONICAL_REPOSITORY_URL!r}"
        )
    return CANONICAL_REPOSITORY


def _validate_generated_at(value: object) -> None:
    if not isinstance(value, str) or not GENERATED_AT_RE.fullmatch(value):
        raise RuntimeError("metadata.json generated_at must be RFC 3339 UTC (YYYY-MM-DDTHH:MM:SSZ)")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError as exc:
        raise RuntimeError(
            "metadata.json generated_at must be a valid RFC 3339 UTC timestamp"
        ) from exc


def _validate_derived_fields(
    metadata: Mapping[str, Any],
    source: Mapping[str, Any],
    project: Mapping[str, Any],
) -> None:
    project_version = str(project["version"])
    expected_python = python_lower_bound(str(project["requires-python"]))
    expected_netbox = discover_netbox_versions(TYPED_VERSIONS_DIR)
    expected_repo = _canonical_repository(project)
    if metadata["release"] != project_version or source["version"] != project_version:
        raise RuntimeError("metadata.json source version does not match the project version")
    if metadata["python"] != expected_python:
        raise RuntimeError("metadata.json python does not match project.requires-python")
    if not isinstance(metadata["netbox"], list) or metadata["netbox"] != expected_netbox:
        raise RuntimeError("metadata.json netbox does not match the typed version modules")
    if source["repo"] != expected_repo:
        raise RuntimeError("metadata.json source.repo does not match the canonical repository")
    _validate_generated_at(metadata["generated_at"])


def _validate_available_source(
    commit: str,
    project_version: str,
    expected_content_id: str,
) -> None:
    if _resolved_object_type(commit) is None:
        return
    validate_source_provenance(
        commit,
        project_version,
        expected_content_id=expected_content_id,
    )


def verify_metadata(*, use_worktree: bool = False) -> None:
    """Verify metadata against HEAD, or against the candidate checkout when requested."""
    metadata = _require_exact_object(
        json.loads(OUTPUT.read_text(encoding="utf-8")),
        TOP_LEVEL_FIELDS,
        "metadata.json",
    )
    source = _require_exact_object(metadata["source"], SOURCE_FIELDS, "metadata.json source")
    project = _load_project()
    project_version = str(project["version"])
    _validate_derived_fields(metadata, source, project)

    content_id = source["content_id"]
    if not isinstance(content_id, str) or not CONTENT_ID_RE.fullmatch(content_id):
        raise RuntimeError("metadata.json source.content_id must be lowercase SHA-256 hex")
    expected_content_id = content_id_for_worktree() if use_worktree else content_id_for_tree()
    if content_id != expected_content_id:
        raise RuntimeError("metadata.json source.content_id does not match the repository content")

    commit = source["commit"]
    if not isinstance(commit, str) or not COMMIT_RE.fullmatch(commit):
        raise RuntimeError("metadata.json source.commit must be a full Git SHA")
    _validate_available_source(commit, project_version, expected_content_id)


def generate_metadata() -> dict[str, Any]:
    project = _load_project()
    project_version = str(project["version"])
    commit = source_commit()
    content_id = content_id_for_worktree()
    _validate_available_source(commit, project_version, content_id)
    return {
        "release": project_version,
        "python": python_lower_bound(str(project["requires-python"])),
        "netbox": discover_netbox_versions(TYPED_VERSIONS_DIR),
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": {
            "repo": _canonical_repository(project),
            "version": project_version,
            "commit": commit,
            "content_id": content_id,
        },
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify",
        action="store_true",
        help="verify metadata.json against HEAD instead of regenerating it",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.verify:
        verify_metadata()
        print("metadata.json content identity is valid for HEAD")
        return 0

    metadata = generate_metadata()
    OUTPUT.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
