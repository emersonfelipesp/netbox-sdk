"""Validate release identity, canonical-main ancestry, and PyPI eligibility."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

from packaging.version import InvalidVersion, Version

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"


@dataclass(frozen=True)
class ReleaseContext:
    package_name: str
    version: str
    publish_pypi: bool


def is_public_pypi_version(value: str) -> bool:
    """Return whether a PEP 440 version may be published to the default index."""
    try:
        version = Version(value)
    except InvalidVersion as exc:
        raise ValueError(f"Invalid PEP 440 project version: {value!r}") from exc
    return not version.is_prerelease and not version.is_devrelease and version.local is None


def release_context(*, expected_package: str, pyproject: Path = PYPROJECT) -> ReleaseContext:
    """Load and validate the project identity used by release workflows."""
    project = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]
    package_name = str(project["name"])
    version = str(project["version"])
    if package_name != expected_package:
        raise RuntimeError(f"Expected project name {expected_package!r}, got {package_name!r}")
    return ReleaseContext(
        package_name=package_name,
        version=version,
        publish_pypi=is_public_pypi_version(version),
    )


def _git_output(repo: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo,
            capture_output=True,
            check=False,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Release validation requires Git history") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "Git command failed"
        raise RuntimeError(f"Release Git validation failed: {detail}")
    return result.stdout.strip()


def validate_canonical_main_ancestry(
    *,
    candidate_ref: str,
    canonical_main_ref: str,
    repo: Path = ROOT,
) -> tuple[str, str]:
    """Require the release candidate commit to already exist on canonical main."""
    candidate = _git_output(repo, "rev-parse", "--verify", f"{candidate_ref}^{{commit}}")
    canonical_main = _git_output(
        repo,
        "rev-parse",
        "--verify",
        f"{canonical_main_ref}^{{commit}}",
    )
    _git_output(repo, "merge-base", "--is-ancestor", candidate, canonical_main)
    return candidate, canonical_main


def validate_immutable_tag(
    *,
    tag_ref: str,
    expected_tag_object: str,
    expected_commit: str,
    repo: Path = ROOT,
) -> tuple[str, str]:
    """Require canonical Gitea to retain the exact published tag object."""
    object_type = _git_output(repo, "cat-file", "-t", tag_ref)
    if object_type != "tag":
        raise RuntimeError(f"Immutable release ref must identify a tag object, got {object_type!r}")
    tag_object = _git_output(repo, "rev-parse", "--verify", tag_ref)
    if tag_object != expected_tag_object:
        raise RuntimeError(
            f"Immutable release tag object mismatch: got {tag_object}, "
            f"expected {expected_tag_object}"
        )
    peeled_commit = _git_output(repo, "rev-parse", "--verify", f"{tag_ref}^{{commit}}")
    if peeled_commit != expected_commit:
        raise RuntimeError(
            f"Immutable release tag commit mismatch: got {peeled_commit}, expected {expected_commit}"
        )
    return tag_object, peeled_commit


def validate_event_tag(*, event_name: str, ref_name: str, version: str) -> None:
    """Authorize RC tag pushes and official final/post release events."""
    if event_name not in {"push", "release"}:
        raise RuntimeError(f"Unsupported release workflow event: {event_name!r}")
    if ref_name != f"v{version}":
        raise RuntimeError(f"Tag/version mismatch: tag={ref_name!r}, version={version!r}")
    parsed = Version(version)
    if event_name == "push":
        if (
            parsed.pre is None
            or parsed.pre[0] != "rc"
            or parsed.is_devrelease
            or parsed.local is not None
        ):
            raise RuntimeError("Direct tag pushes are authorized only for public RC versions")
        return
    if not is_public_pypi_version(version):
        raise RuntimeError(
            "GitHub Release publication is authorized only for final or post-release versions"
        )


def _write_actions_outputs(context: ReleaseContext) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with Path(output_path).open("a", encoding="utf-8") as stream:
        stream.write(f"package_name={context.package_name}\n")
        stream.write(f"version={context.version}\n")
        stream.write(f"publish_pypi={'true' if context.publish_pypi else 'false'}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-package", required=True)
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--ref-name", required=True)
    parser.add_argument("--candidate-ref", default="HEAD")
    parser.add_argument("--canonical-main-ref", required=True)
    parser.add_argument("--immutable-tag-ref", required=True)
    parser.add_argument("--immutable-tag-object", required=True)
    parser.add_argument("--immutable-tag-commit", required=True)
    args = parser.parse_args()

    context = release_context(expected_package=args.expected_package)
    validate_event_tag(
        event_name=args.event_name,
        ref_name=args.ref_name,
        version=context.version,
    )
    candidate, canonical_main = validate_canonical_main_ancestry(
        candidate_ref=args.candidate_ref,
        canonical_main_ref=args.canonical_main_ref,
    )
    tag_object, tag_commit = validate_immutable_tag(
        tag_ref=args.immutable_tag_ref,
        expected_tag_object=args.immutable_tag_object,
        expected_commit=args.immutable_tag_commit,
    )
    _write_actions_outputs(context)
    print(
        f"release policy passed: candidate={candidate}, canonical_main={canonical_main}, "
        f"immutable_tag={tag_object}, immutable_tag_commit={tag_commit}, "
        f"publish_pypi={context.publish_pypi}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
