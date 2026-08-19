"""Select and normalize the Django model-build catalog shipped inside the wheel.

``django_models_builds/`` is a repository-root archive that grows with every
upstream tag ever built, including release lines this SDK no longer supports. It
sits outside every package, so it cannot ship in a distribution.

This script derives the *deliberately supported* subset — the newest non-prerelease
build for each supported NetBox release line — into package data, so an installed
wheel exposes the same catalog a checkout does. Selecting a subset is what keeps
the wheel from carrying ~9.5 MB of history for lines the SDK cannot talk to.

It also relativizes provenance. Builds are generated from a throwaway clone, so
every ``file_path`` recorded an absolute ``/tmp/netbox-<tag>/...`` path that says
nothing to a consumer and leaks the build machine's layout into a published
artifact.

Run from the repository root:

    python scripts/build_model_catalog.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO_ROOT / "django_models_builds"
TARGET_DIR = REPO_ROOT / "netbox_sdk" / "django_models" / "model_builds"
MANIFEST = TARGET_DIR / "manifest.json"
SUFFIX = "-django-models-build.json"

_TMP_PREFIX = re.compile(r"^/tmp/netbox-[^/]+/")


def _parse(tag: str) -> tuple[int, ...] | None:
    """Return a sortable version tuple, or None for a prerelease/unparsable tag."""
    body = tag.removeprefix("v")
    if not re.fullmatch(r"\d+(\.\d+)*", body):
        return None  # beta/rc builds never represent a line
    return tuple(int(part) for part in body.split("."))


def _supported_lines() -> tuple[str, ...]:
    sys.path.insert(0, str(REPO_ROOT))
    from netbox_sdk.versioning import SUPPORTED_NETBOX_VERSIONS

    return tuple(SUPPORTED_NETBOX_VERSIONS)


def select_tags() -> dict[str, str]:
    """Newest non-prerelease build per supported line, as ``{line: tag}``."""
    newest: dict[str, tuple[tuple[int, ...], str]] = {}
    for path in SOURCE_DIR.glob(f"*{SUFFIX}"):
        tag = path.name[: -len(SUFFIX)]
        version = _parse(tag)
        if version is None or len(version) < 2:
            continue
        line = f"{version[0]}.{version[1]}"
        if line not in _supported_lines():
            continue
        current = newest.get(line)
        if current is None or version > current[0]:
            newest[line] = (version, tag)
    return {line: tag for line, (_version, tag) in sorted(newest.items())}


def relativize(payload: object) -> object:
    """Rewrite absolute build-machine paths to repository-relative ones."""
    if isinstance(payload, dict):
        return {key: relativize(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [relativize(item) for item in payload]
    if isinstance(payload, str):
        return _TMP_PREFIX.sub("", payload)
    return payload


def main() -> int:
    selected = select_tags()
    if not selected:
        print("no builds matched a supported release line", file=sys.stderr)
        return 1

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    for stale in TARGET_DIR.glob(f"*{SUFFIX}"):
        stale.unlink()

    for line, tag in selected.items():
        payload = json.loads((SOURCE_DIR / f"{tag}{SUFFIX}").read_text(encoding="utf-8"))
        target = TARGET_DIR / f"{tag}{SUFFIX}"
        target.write_text(
            json.dumps(relativize(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"{line}: {tag} -> {target.relative_to(REPO_ROOT)} ({target.stat().st_size} bytes)")

    MANIFEST.write_text(
        json.dumps(
            {
                "description": (
                    "Newest non-prerelease Django model build per supported NetBox "
                    "release line. Regenerate with scripts/build_model_catalog.py."
                ),
                "builds": selected,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    missing = [line for line in _supported_lines() if line not in selected]
    if missing:
        print(f"note: no build available for supported line(s): {', '.join(sorted(missing))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
