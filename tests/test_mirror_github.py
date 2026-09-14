"""Executable state-matrix tests for the canonical Gitea-to-GitHub mirror."""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.mirror_github import HISTORICAL_GITHUB_TIP

pytestmark = pytest.mark.suite_sdk

REPO_ROOT = Path(__file__).resolve().parent.parent
MIRROR_SCRIPT = REPO_ROOT / "scripts" / "mirror_github.py"
HISTORICAL_PARENT = "f0e12e629d2d42295dcffc6bfce30c711a8f23fb"
HISTORICAL_TREE = "bcd4b767c2a921881056a4d159ae9deea9fd320a"
HISTORICAL_METADATA_BLOB = "a894f90986cf8cf1bb6f4c7370c5a33aab6ca69f"
HISTORICAL_METADATA = """{
  "release": "0.0.13",
  "python": "3.11+",
  "netbox": [
    "4.3",
    "4.4",
    "4.5",
    "4.6",
    "4.7"
  ],
  "generated_at": "2026-09-08T21:17:07Z",
  "source": {
    "repo": "emersonfelipesp/netbox-sdk",
    "commit": "f0e12e629d2d42295dcffc6bfce30c711a8f23fb"
  }
}
"""
HISTORICAL_COMMIT = """tree bcd4b767c2a921881056a4d159ae9deea9fd320a
parent f0e12e629d2d42295dcffc6bfce30c711a8f23fb
author github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> 1788902235 -0300
committer github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> 1788902235 -0300

chore: refresh metadata provenance
"""


def _git(
    repository: Path,
    *args: str,
    input_text: str | None = None,
) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *args],
        capture_output=True,
        check=False,
        input=input_text,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _commit(repository: Path, name: str, content: str, message: str) -> str:
    (repository / name).write_text(content, encoding="utf-8")
    _git(repository, "add", "--", name)
    _git(repository, "commit", "--quiet", "-m", message)
    return _git(repository, "rev-parse", "HEAD^{commit}")


def _repositories(tmp_path: Path) -> tuple[Path, Path, str, str]:
    canonical = tmp_path / "canonical"
    github = tmp_path / "github.git"
    canonical.mkdir()
    _git(canonical, "init", "--quiet", "--initial-branch=main")
    _git(canonical, "config", "user.name", "Mirror Test")
    _git(canonical, "config", "user.email", "mirror@example.invalid")
    _commit(canonical, "root.txt", "root\n", "root")
    base = _commit(canonical, "state.txt", "base\n", "base")
    _git(tmp_path, "init", "--quiet", "--bare", "--initial-branch=main", str(github))
    _git(canonical, "remote", "add", "github", str(github))
    _git(canonical, "push", "--quiet", "github", f"{base}:refs/heads/main")
    tip = _commit(canonical, "state.txt", "canonical\n", "canonical")
    return canonical, github, base, tip


def _sibling_commit(repository: Path, parent: str, message: str) -> str:
    tree = _git(repository, "rev-parse", "HEAD^{tree}")
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_AUTHOR_NAME": "Mirror Test",
            "GIT_AUTHOR_EMAIL": "mirror@example.invalid",
            "GIT_COMMITTER_NAME": "Mirror Test",
            "GIT_COMMITTER_EMAIL": "mirror@example.invalid",
        }
    )
    result = subprocess.run(
        ["git", "-C", str(repository), "commit-tree", tree, "-p", parent],
        capture_output=True,
        check=False,
        env=environment,
        input=f"{message}\n",
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _write_git_object(repository: Path, object_type: str, content: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), "hash-object", "-t", object_type, "-w", "--stdin"],
        capture_output=True,
        check=False,
        input=content,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _historical_repositories(tmp_path: Path) -> tuple[Path, Path, str]:
    canonical = tmp_path / "canonical"
    github = tmp_path / "github.git"
    _git(tmp_path, "clone", "--quiet", "--no-local", str(REPO_ROOT), str(canonical))
    _git(canonical, "config", "user.name", "Mirror Test")
    _git(canonical, "config", "user.email", "mirror@example.invalid")
    canonical_tip = _git(canonical, "rev-parse", "HEAD^{commit}")

    metadata_blob = _write_git_object(canonical, "blob", HISTORICAL_METADATA)
    assert metadata_blob == HISTORICAL_METADATA_BLOB
    _git(canonical, "read-tree", HISTORICAL_PARENT)
    _git(
        canonical,
        "update-index",
        "--add",
        "--cacheinfo",
        f"100644,{metadata_blob},metadata.json",
    )
    assert _git(canonical, "write-tree") == HISTORICAL_TREE
    assert _write_git_object(canonical, "commit", HISTORICAL_COMMIT) == HISTORICAL_GITHUB_TIP

    _git(tmp_path, "init", "--quiet", "--bare", "--initial-branch=main", str(github))
    _git(canonical, "remote", "add", "github", str(github))
    _git(
        canonical,
        "push",
        "--quiet",
        "github",
        f"{HISTORICAL_GITHUB_TIP}:refs/heads/main",
    )
    return canonical, github, canonical_tip


def _run_mirror(
    repository: Path, *, historical_tip: str | None = None
) -> subprocess.CompletedProcess[str]:
    args = [sys.executable, str(MIRROR_SCRIPT), "--repository", str(repository)]
    if historical_tip is not None:
        args.extend(["--historical-tip", historical_tip])
    return subprocess.run(
        args,
        capture_output=True,
        check=False,
        text=True,
    )


def _remote_tip(github: Path) -> str:
    return _git(github, "rev-parse", "refs/heads/main^{commit}")


def _install_concurrent_update_hook(
    repository: Path,
    github: Path,
    concurrent_tip: str,
    marker: Path,
) -> None:
    hook = repository / ".git" / "hooks" / "pre-push"
    hook.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\n' called >> {shlex.quote(str(marker))}\n"
        f"git --git-dir={shlex.quote(str(github))} update-ref "
        f"refs/heads/main {concurrent_tip}\n",
        encoding="utf-8",
    )
    hook.chmod(0o755)


def test_historical_tip_is_pinned_to_the_reviewed_mirror_only_commit() -> None:
    assert HISTORICAL_GITHUB_TIP == "d0b46101d3d91d6755b6a419e9095577b66a443d"


def test_tip_equal_to_the_historical_commit_uses_the_one_time_lease(
    tmp_path: Path,
) -> None:
    canonical, github, canonical_tip = _historical_repositories(tmp_path)

    result = _run_mirror(canonical)

    assert result.returncode == 0, result.stderr
    assert _remote_tip(github) == canonical_tip
    assert f"Replaced the reviewed historical GitHub tip {HISTORICAL_GITHUB_TIP}." in result.stdout


def test_older_ancestor_tip_fast_forwards(tmp_path: Path) -> None:
    canonical, github, _base, canonical_tip = _repositories(tmp_path)

    result = _run_mirror(canonical)

    assert result.returncode == 0, result.stderr
    assert _remote_tip(github) == canonical_tip
    assert "Fast-forwarded GitHub main" in result.stdout


def test_divergent_tip_fails_without_a_push(tmp_path: Path) -> None:
    canonical, github, base, _canonical_tip = _repositories(tmp_path)
    divergent_tip = _sibling_commit(canonical, base, "divergent")
    _git(
        canonical,
        "push",
        "--quiet",
        "--force",
        "github",
        f"{divergent_tip}:refs/heads/main",
    )

    result = _run_mirror(canonical)

    assert result.returncode == 1
    assert _remote_tip(github) == divergent_tip
    assert "GitHub main has diverged from canonical main; refusing to overwrite it." in (
        result.stderr
    )


def test_concurrent_migration_update_rejects_the_original_lease_without_retry(
    tmp_path: Path,
) -> None:
    canonical, github, _canonical_tip = _historical_repositories(tmp_path)
    concurrent_tip = _sibling_commit(canonical, HISTORICAL_PARENT, "concurrent migration")
    _git(
        canonical,
        "push",
        "--quiet",
        "github",
        f"{concurrent_tip}:refs/heads/concurrent",
    )
    marker = tmp_path / "migration-pushes"
    _install_concurrent_update_hook(canonical, github, concurrent_tip, marker)

    result = _run_mirror(canonical)

    assert result.returncode == 1
    assert _remote_tip(github) == concurrent_tip
    assert marker.read_text(encoding="utf-8").splitlines() == ["called"]
    assert "migration lease was rejected; refusing to refresh the lease" in result.stderr


def test_concurrent_fast_forward_rejection_does_not_retry(tmp_path: Path) -> None:
    canonical, github, base, _canonical_tip = _repositories(tmp_path)
    concurrent_tip = _sibling_commit(canonical, base, "concurrent fast-forward")
    _git(
        canonical,
        "push",
        "--quiet",
        "github",
        f"{concurrent_tip}:refs/heads/concurrent",
    )
    marker = tmp_path / "fast-forward-pushes"
    _install_concurrent_update_hook(canonical, github, concurrent_tip, marker)

    result = _run_mirror(canonical)

    assert result.returncode == 1
    assert _remote_tip(github) == concurrent_tip
    assert marker.read_text(encoding="utf-8").splitlines() == ["called"]
    assert "fast-forward was rejected; refusing to retry" in result.stderr


def test_concurrent_rewind_rejects_the_observed_lease_without_retry(tmp_path: Path) -> None:
    canonical, github, observed_tip, _canonical_tip = _repositories(tmp_path)
    rewound_tip = _git(canonical, "rev-parse", f"{observed_tip}^")
    marker = tmp_path / "rewind-pushes"
    _install_concurrent_update_hook(canonical, github, rewound_tip, marker)

    result = _run_mirror(canonical)

    assert result.returncode == 1
    assert _remote_tip(github) == rewound_tip
    assert marker.read_text(encoding="utf-8").splitlines() == ["called"]
    assert "fast-forward was rejected; refusing to retry" in result.stderr
