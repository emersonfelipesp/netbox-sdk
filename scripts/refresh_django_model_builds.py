"""Prepare a reviewed Django model-build archive refresh from local inputs.

This command performs no downloads. Supply either a directory extracted from a
GitHub Actions artifact or an existing local NetBox checkout and exact release
tag. The command normalizes the tracked archive, regenerates the bundled catalog,
and prints ``git status`` for review in a Gitea pull request.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from netbox_sdk.django_models.paths import normalize_build_paths
from netbox_sdk.django_models.store import DjangoModelStore

REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_DIR = REPO_ROOT / "django_models_builds"
BUILD_SUFFIX = "-django-models-build.json"
TAG_RE = re.compile(r"^v[0-9][0-9A-Za-z.-]*$")


def _load_build(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return normalize_build_paths(payload)


def _write_build(payload: dict[str, Any], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _git_commit(checkout: Path, revision: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "--verify", f"{revision}^{{commit}}"],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        raise ValueError(f"cannot resolve {revision!r} in the local NetBox checkout")
    return result.stdout.strip()


def _verify_checkout_tag(checkout: Path, tag: str) -> None:
    tagged_commit = _git_commit(checkout, tag)
    head_commit = _git_commit(checkout, "HEAD")
    if tagged_commit != head_commit:
        raise ValueError(
            f"local NetBox checkout HEAD {head_commit} does not match {tag} at {tagged_commit}"
        )


def _verify_checkout_clean(checkout: Path) -> None:
    result = subprocess.run(
        ["git", "-C", str(checkout), "status", "--porcelain", "--untracked-files=all"],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        raise ValueError("cannot inspect the local NetBox checkout status")
    if result.stdout:
        raise ValueError(
            "local NetBox checkout has modified tracked or untracked files; "
            "refusing to archive them under an official release tag"
        )


def import_artifacts(artifact_dir: Path, archive_dir: Path = ARCHIVE_DIR) -> list[Path]:
    """Normalize artifact JSON files into the tracked archive."""
    if not artifact_dir.is_dir():
        raise ValueError(f"artifact directory does not exist: {artifact_dir}")
    sources = sorted(artifact_dir.rglob(f"*{BUILD_SUFFIX}"))
    if not sources:
        raise ValueError(f"no *{BUILD_SUFFIX} files found under {artifact_dir}")

    normalized: dict[str, dict[str, Any]] = {}
    for source in sources:
        if source.is_symlink():
            raise ValueError(f"artifact build must not be a symbolic link: {source}")
        tag = source.name[: -len(BUILD_SUFFIX)]
        if not TAG_RE.fullmatch(tag):
            raise ValueError(f"artifact build has an invalid NetBox release tag: {source.name}")
        if source.name in normalized:
            raise ValueError(f"duplicate artifact build filename: {source.name}")
        normalized[source.name] = _load_build(source)

    destinations: list[Path] = []
    for name, payload in normalized.items():
        destination = archive_dir / name
        _write_build(payload, destination)
        destinations.append(destination)
    return destinations


def build_local(netbox_checkout: Path, tag: str, archive_dir: Path = ARCHIVE_DIR) -> Path:
    """Build one artifact from an existing local NetBox checkout."""
    if not TAG_RE.fullmatch(tag):
        raise ValueError(f"invalid NetBox release tag: {tag!r}")
    checkout = netbox_checkout.resolve()
    netbox_root = checkout / "netbox"
    if not netbox_root.is_dir():
        raise ValueError(f"NetBox checkout must contain a netbox/ directory: {checkout}")
    _verify_checkout_tag(checkout, tag)
    _verify_checkout_clean(checkout)

    temp_root = REPO_ROOT / ".tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="django-model-refresh-", dir=temp_root) as raw_temp:
        temporary_build = Path(raw_temp) / f"{tag}{BUILD_SUFFIX}"
        payload = DjangoModelStore(cache_path=temporary_build).build(netbox_root)
        destination = archive_dir / temporary_build.name
        _write_build(normalize_build_paths(payload), destination)
    return destination


def _run_repository_command(args: list[str]) -> None:
    result = subprocess.run(args, cwd=REPO_ROOT, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"command failed with exit code {result.returncode}: {' '.join(args)}")


def regenerate_catalog_and_show_status() -> None:
    """Regenerate package data and print the exact Git status."""
    _run_repository_command([sys.executable, str(REPO_ROOT / "scripts" / "build_model_catalog.py")])
    print("Review this exact git status before opening the Gitea pull request:", flush=True)
    _run_repository_command(["git", "status"])


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--artifact-dir",
        type=Path,
        help="local directory produced by gh run download",
    )
    source.add_argument(
        "--netbox-checkout",
        type=Path,
        help="existing local NetBox checkout containing netbox/",
    )
    parser.add_argument("--tag", help="exact v-prefixed tag required with --netbox-checkout")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.artifact_dir is not None:
            if args.tag is not None:
                raise ValueError("--tag is only valid with --netbox-checkout")
            imported = import_artifacts(args.artifact_dir)
            for path in imported:
                print(f"Imported {path.relative_to(REPO_ROOT)}")
        else:
            if args.tag is None:
                raise ValueError("--tag is required with --netbox-checkout")
            built = build_local(args.netbox_checkout, args.tag)
            print(f"Built {built.relative_to(REPO_ROOT)}")
        regenerate_catalog_and_show_status()
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Django model-build refresh failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
