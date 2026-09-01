from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from packaging.version import InvalidVersion

from scripts.release_policy import (
    is_public_pypi_version,
    validate_canonical_main_ancestry,
    validate_event_tag,
    validate_immutable_tag,
    validate_release_source,
)

pytestmark = pytest.mark.suite_sdk


@pytest.mark.parametrize("version", ["1.0", "1.0.0", "1.0.post1", "2!1.0.post2"])
def test_public_pypi_version_accepts_final_and_post_releases(version: str) -> None:
    assert is_public_pypi_version(version)


@pytest.mark.parametrize(
    "version",
    ["1.0a1", "1.0b1", "1.0rc1", "1.0.dev1", "1.0rc1.post1", "1.0+local"],
)
def test_public_pypi_version_rejects_non_public_candidates(version: str) -> None:
    assert not is_public_pypi_version(version)


def test_public_pypi_version_rejects_invalid_version() -> None:
    with pytest.raises(ValueError, match="Invalid PEP 440") as exc_info:
        is_public_pypi_version("not a version")
    assert isinstance(exc_info.value.__cause__, InvalidVersion)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        check=True,
        text=True,
    )
    return result.stdout.strip()


def _commit(repo: Path, message: str, content: str) -> str:
    marker = repo / "marker.txt"
    marker.write_text(content, encoding="utf-8")
    _git(repo, "add", "marker.txt")
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def test_release_commit_must_already_be_on_canonical_main(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Release Test")
    _git(repo, "config", "user.email", "release-test@example.invalid")
    base = _commit(repo, "base", "base")
    canonical_main = _commit(repo, "main", "main")
    _git(repo, "update-ref", "refs/remotes/origin/release-policy-main", canonical_main)

    assert validate_canonical_main_ancestry(
        candidate_ref=base,
        canonical_main_ref="refs/remotes/origin/release-policy-main",
        repo=repo,
    ) == (base, canonical_main)

    _git(repo, "switch", "--detach", base)
    topic = _commit(repo, "topic", "topic")
    with pytest.raises(RuntimeError, match="Release Git validation failed"):
        validate_canonical_main_ancestry(
            candidate_ref=topic,
            canonical_main_ref="refs/remotes/origin/release-policy-main",
            repo=repo,
        )


def test_final_release_source_must_equal_canonical_main(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Release Test")
    _git(repo, "config", "user.email", "release-test@example.invalid")
    ancestor = _commit(repo, "base", "base")
    canonical_main = _commit(repo, "main", "main")
    _git(repo, "update-ref", "refs/remotes/origin/release-policy-main", canonical_main)

    assert validate_release_source(
        event_name="push",
        candidate_ref=ancestor,
        canonical_main_ref="refs/remotes/origin/release-policy-main",
        repo=repo,
    ) == (ancestor, canonical_main)
    with pytest.raises(RuntimeError, match="must equal the explicitly fetched canonical main"):
        validate_release_source(
            event_name="release",
            candidate_ref=ancestor,
            canonical_main_ref="refs/remotes/origin/release-policy-main",
            repo=repo,
        )
    assert validate_release_source(
        event_name="release",
        candidate_ref=canonical_main,
        canonical_main_ref="refs/remotes/origin/release-policy-main",
        repo=repo,
    ) == (canonical_main, canonical_main)


def test_release_events_require_exact_project_version() -> None:
    validate_event_tag(event_name="push", ref_name="v1.0rc1", version="1.0rc1")
    validate_event_tag(event_name="release", ref_name="v1.0", version="1.0")
    validate_event_tag(event_name="release", ref_name="v1.0.post1", version="1.0.post1")
    with pytest.raises(RuntimeError, match="Tag/version mismatch"):
        validate_event_tag(event_name="push", ref_name="v1.0rc1", version="1.0")


@pytest.mark.parametrize("version", ["1.0", "1.0.post1", "1.0a1", "1.0b1", "1.0.dev1"])
def test_direct_tag_push_is_limited_to_rc_versions(version: str) -> None:
    with pytest.raises(RuntimeError, match="only for public RC versions"):
        validate_event_tag(event_name="push", ref_name=f"v{version}", version=version)


@pytest.mark.parametrize("version", ["1.0rc1", "1.0.dev1", "1.0+local"])
def test_github_release_is_limited_to_final_and_post_versions(version: str) -> None:
    with pytest.raises(RuntimeError, match="only for final or post-release versions"):
        validate_event_tag(event_name="release", ref_name=f"v{version}", version=version)


@pytest.mark.parametrize("event_name", ["workflow_dispatch", "schedule"])
def test_release_policy_rejects_unknown_event(event_name: str) -> None:
    with pytest.raises(RuntimeError, match="Unsupported release workflow event"):
        validate_event_tag(event_name=event_name, ref_name="v1.0", version="1.0")


def test_immutable_tag_requires_exact_annotated_object_and_commit(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Release Test")
    _git(repo, "config", "user.email", "release-test@example.invalid")
    commit = _commit(repo, "release", "release")
    _git(repo, "tag", "-a", "v1.0", "-m", "Release v1.0")
    tag_object = _git(repo, "rev-parse", "v1.0")
    _git(repo, "update-ref", "refs/release-policy/gitea-v1.0", tag_object)

    assert validate_immutable_tag(
        tag_ref="refs/release-policy/gitea-v1.0",
        expected_tag_object=tag_object,
        expected_commit=commit,
        repo=repo,
    ) == (tag_object, commit)

    _git(repo, "update-ref", "refs/release-policy/gitea-v1.0", commit)
    with pytest.raises(RuntimeError, match="must identify a tag object"):
        validate_immutable_tag(
            tag_ref="refs/release-policy/gitea-v1.0",
            expected_tag_object=tag_object,
            expected_commit=commit,
            repo=repo,
        )
