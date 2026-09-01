#!/usr/bin/env python3
"""Compare a live NetBox ``/api/status/`` report to the CI matrix pin.

The digest-pinned 4.7 preview image reports ``4.7.0``. That alias is valid
only for this exact digest. Other matrix pins still require an exact match.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PREVIEW_LIVE_PIN = "4.7.0-beta2"
PREVIEW_LIVE_DIGEST = "sha256:b4c36c2ecbb161dad6557cec9f505e7dd7af0fee23f16f937f5585f440941467"
PREVIEW_LIVE_IMAGE = f"ghcr.io/netbox-community/netbox@{PREVIEW_LIVE_DIGEST}"
PREVIEW_LIVE_STATUS = "4.7.0"


def allowed_live_status_versions(expected: str, image: str | None = None) -> frozenset[str]:
    """Return the status strings accepted for a matrix pin and selected image."""

    pin = expected.removeprefix("v")
    if pin == PREVIEW_LIVE_PIN:
        if image != PREVIEW_LIVE_IMAGE:
            return frozenset()
        return frozenset({PREVIEW_LIVE_STATUS})
    return frozenset({pin})


def live_status_matches(expected: str, reported: str, image: str | None = None) -> bool:
    """Return whether ``reported`` is valid for the pin and selected image."""

    return reported in allowed_live_status_versions(expected, image)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected", required=True)
    parser.add_argument("--status-file", type=Path, required=True)
    parser.add_argument("--image", default="")
    args = parser.parse_args(argv)
    reported = json.loads(args.status_file.read_text(encoding="utf-8")).get("netbox-version")
    expected = args.expected.removeprefix("v")
    print(f"NetBox API status: {reported} (expected {expected})")
    if not live_status_matches(args.expected, str(reported), args.image or None):
        print(
            f"Live job expected NetBox {expected}; /api/status/ reported {reported!r}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
