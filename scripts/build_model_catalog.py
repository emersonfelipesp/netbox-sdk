"""Select and normalize the Django model-build catalog shipped inside the wheel.

``django_models_builds/`` is a repository-root archive that grows with every
upstream tag ever built, including release lines this SDK no longer supports. It
sits outside every package, so it cannot ship in a distribution.

This script derives the newest non-prerelease build for each supported NetBox
release line into package data, so an installed wheel exposes the same catalog a
checkout does. Previously packaged exact builds are retained by default. Pass
``--prune`` only when an explicit compatibility decision removes those builds.

It also validates portable provenance. Current builders record paths relative to
the NetBox checkout root. Older artifacts are normalized from the checkout root
identified by ``meta.source_path``; an absolute path outside that root is rejected
instead of leaking the build machine's layout into a published artifact.

Run from the repository root:

    python scripts/build_model_catalog.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO_ROOT / "django_models_builds"
TARGET_DIR = REPO_ROOT / "netbox_sdk" / "django_models" / "model_builds"
MANIFEST = TARGET_DIR / "manifest.json"
SUFFIX = "-django-models-build.json"


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


def _load_normalized_build(path: Path) -> dict[str, object]:
    sys.path.insert(0, str(REPO_ROOT))
    from netbox_sdk.django_models.paths import normalize_build_paths  # noqa: PLC0415

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return normalize_build_paths(payload)


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _exact_tags() -> list[str]:
    tags = {path.name[: -len(SUFFIX)] for path in TARGET_DIR.glob(f"*{SUFFIX}")}
    return sorted(tags, key=lambda tag: (_parse(tag) or (), tag), reverse=True)


def _prune_unselected(selected_tags: set[str]) -> None:
    for existing in TARGET_DIR.glob(f"*{SUFFIX}"):
        tag = existing.name[: -len(SUFFIX)]
        if tag not in selected_tags:
            existing.unlink()


def main(*, prune: bool = False) -> int:
    selected = select_tags()
    if not selected:
        print("no builds matched a supported release line", file=sys.stderr)
        return 1

    normalized_builds: dict[str, dict[str, object]] = {}
    for line, tag in selected.items():
        source = SOURCE_DIR / f"{tag}{SUFFIX}"
        try:
            normalized_builds[tag] = _load_normalized_build(source)
        except (OSError, ValueError) as exc:
            print(f"cannot normalize {_display_path(source)}: {exc}", file=sys.stderr)
            return 1

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    if prune:
        _prune_unselected(set(selected.values()))

    for line, tag in selected.items():
        target = TARGET_DIR / f"{tag}{SUFFIX}"
        target.write_text(
            json.dumps(normalized_builds[tag], indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"{line}: {tag} -> {_display_path(target)} ({target.stat().st_size} bytes)")

    MANIFEST.write_text(
        json.dumps(
            {
                "description": (
                    "Newest non-prerelease Django model build per supported NetBox release "
                    "line, with previously packaged exact builds retained. Refresh with "
                    "scripts/refresh_django_model_builds.py."
                ),
                "builds": selected,
                "exact_builds": _exact_tags(),
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


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument(
        "--prune",
        action="store_true",
        help="remove packaged exact builds that are not selected release-line defaults",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    arguments = parse_args()
    raise SystemExit(main(prune=arguments.prune))
