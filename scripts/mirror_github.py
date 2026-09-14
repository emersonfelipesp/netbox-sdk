"""Push a prepared canonical checkout to GitHub without overwriting changes."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

HISTORICAL_GITHUB_TIP = "d0b46101d3d91d6755b6a419e9095577b66a443d"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REMOTE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
BRANCH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")


class MirrorError(RuntimeError):
    """Raised when the mirror cannot advance without overwriting remote state."""


def _git(repository: Path, *args: str, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repository), *args],
        capture_output=capture,
        check=False,
        text=True,
    )


def _checked_git_output(repository: Path, *args: str) -> str:
    result = _git(repository, *args, capture=True)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "Git command failed"
        raise MirrorError(detail)
    return result.stdout.strip()


def _validate_ref_inputs(remote: str, branch: str, historical_tip: str) -> None:
    if not REMOTE_RE.fullmatch(remote):
        raise MirrorError(f"invalid Git remote name: {remote!r}")
    if not BRANCH_RE.fullmatch(branch) or ".." in branch or branch.endswith("/"):
        raise MirrorError(f"invalid Git branch name: {branch!r}")
    if not SHA_RE.fullmatch(historical_tip):
        raise MirrorError("historical GitHub tip must be a full lowercase Git SHA")


def _push(repository: Path, remote: str, refspec: str, *options: str) -> bool:
    result = _git(repository, "push", *options, remote, refspec)
    return result.returncode == 0


def mirror(
    repository: Path,
    *,
    remote: str = "github",
    branch: str = "main",
    historical_tip: str = HISTORICAL_GITHUB_TIP,
) -> None:
    """Mirror ``HEAD`` after one observation of the destination branch."""
    _validate_ref_inputs(remote, branch, historical_tip)
    repository = repository.resolve()
    if not repository.is_dir():
        raise MirrorError(f"mirror repository does not exist: {repository}")

    remote_ref = f"refs/remotes/{remote}/{branch}"
    destination_ref = f"refs/heads/{branch}"
    fetch = _git(
        repository,
        "fetch",
        "--no-tags",
        remote,
        f"+{destination_ref}:{remote_ref}",
    )
    if fetch.returncode != 0:
        raise MirrorError("GitHub main fetch failed; refusing to push an unobserved destination")
    observed_tip = _checked_git_output(repository, "rev-parse", f"{remote_ref}^{{commit}}")
    refspec = f"HEAD:{destination_ref}"

    if observed_tip == historical_tip:
        lease = f"--force-with-lease={destination_ref}:{historical_tip}"
        if _push(repository, remote, refspec, lease):
            print(f"Replaced the reviewed historical GitHub tip {historical_tip}.")
            return
        raise MirrorError(
            "The one-time GitHub migration lease was rejected; refusing to refresh "
            "the lease or overwrite a concurrent update."
        )

    ancestry = _git(repository, "merge-base", "--is-ancestor", observed_tip, "HEAD")
    if ancestry.returncode == 1:
        raise MirrorError("GitHub main has diverged from canonical main; refusing to overwrite it.")
    if ancestry.returncode != 0:
        raise MirrorError("Could not validate GitHub main ancestry; refusing to push.")
    lease = f"--force-with-lease={destination_ref}:{observed_tip}"
    if _push(repository, remote, refspec, lease):
        print(f"Fast-forwarded GitHub {branch} from {observed_tip}.")
        return
    raise MirrorError(
        "The GitHub fast-forward was rejected; refusing to retry against a refreshed remote tip."
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--remote", default="github")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--historical-tip", default=HISTORICAL_GITHUB_TIP)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        mirror(
            args.repository,
            remote=args.remote,
            branch=args.branch,
            historical_tip=args.historical_tip,
        )
    except (MirrorError, OSError) as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
