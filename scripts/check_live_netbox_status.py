#!/usr/bin/env python3
"""Compare a live NetBox ``/api/status/`` report to the exact CI matrix pin."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def allowed_live_status_versions(expected: str) -> frozenset[str]:
    """Return the sole status string accepted for a matrix pin."""

    return frozenset({expected.removeprefix("v")})


def live_status_matches(expected: str, reported: str) -> bool:
    """Return whether ``reported`` exactly matches the normalized pin."""

    return reported in allowed_live_status_versions(expected)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected", required=True)
    parser.add_argument("--status-file", type=Path, required=True)
    args = parser.parse_args(argv)
    reported = json.loads(args.status_file.read_text(encoding="utf-8")).get("netbox-version")
    expected = args.expected.removeprefix("v")
    print(f"NetBox API status: {reported} (expected {expected})")
    if not live_status_matches(args.expected, str(reported)):
        print(
            f"Live job expected NetBox {expected}; /api/status/ reported {reported!r}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
