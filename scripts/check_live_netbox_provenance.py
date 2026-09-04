#!/usr/bin/env python3
"""Fail closed unless a live-CI source commit or OCI digest matches its reviewed pin."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def source_commit_matches(expected: str, actual: str) -> bool:
    """Return whether both values are full lowercase SHA-1s and match exactly."""
    return bool(_SHA1_RE.fullmatch(expected) and _SHA1_RE.fullmatch(actual) and expected == actual)


def image_digest_matches(expected: str, repo_digests: list[str]) -> bool:
    """Return whether an inspected RepoDigest contains the exact reviewed digest."""
    if not _SHA256_RE.fullmatch(expected):
        return False
    actual = {
        reference.rsplit("@", 1)[1]
        for reference in repo_digests
        if isinstance(reference, str) and "@" in reference
    }
    return expected in actual


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-commit")
    parser.add_argument("--actual-commit")
    parser.add_argument("--expected-image-digest")
    parser.add_argument("--repo-digests-file", type=Path)
    args = parser.parse_args(argv)

    checked = False
    if args.expected_commit is not None or args.actual_commit is not None:
        checked = True
        if not source_commit_matches(args.expected_commit or "", args.actual_commit or ""):
            print(
                f"Source commit mismatch: expected {args.expected_commit!r}, "
                f"got {args.actual_commit!r}",
                file=sys.stderr,
            )
            return 1
        print(f"Verified source commit {args.actual_commit}")

    if args.expected_image_digest is not None or args.repo_digests_file is not None:
        checked = True
        if args.repo_digests_file is None or not args.repo_digests_file.is_file():
            print("Docker RepoDigests evidence file is missing", file=sys.stderr)
            return 1
        try:
            repo_digests = json.loads(args.repo_digests_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Cannot parse Docker RepoDigests evidence: {exc}", file=sys.stderr)
            return 1
        if not isinstance(repo_digests, list) or not image_digest_matches(
            args.expected_image_digest or "", repo_digests
        ):
            print(
                f"Image digest mismatch: expected {args.expected_image_digest!r}, "
                f"got {repo_digests!r}",
                file=sys.stderr,
            )
            return 1
        print(f"Verified image digest {args.expected_image_digest}")

    if not checked:
        print("No provenance property was supplied for verification", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
