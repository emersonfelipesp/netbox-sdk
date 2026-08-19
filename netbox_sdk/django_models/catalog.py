"""One source of truth for Django model-build catalogs, in a checkout or a wheel.

Three things used to be true at once, and together they meant an installed wheel
advertised no builds at all:

* the archive lives at ``django_models_builds/`` in the repository root, outside
  every package, so it was never included in a distribution;
* the SDK fetcher resolved that root by walking up from its own module, which is
  correct in a checkout and points into ``site-packages``' parent — where nothing
  exists, and which is generally unwritable — in an installation;
* the TUI walked up one level too far, so it discovered zero builds *even in a
  checkout*.

This module replaces all three paths with one service over two clearly separated
stores:

* **bundled** — the deliberately supported subset shipped as package data and read
  through :mod:`importlib.resources`, so it works from a wheel, a zipimport, or a
  checkout without caring which;
* **downloaded** — a user-writable XDG location, so generating a build never tries
  to write into a read-only ``site-packages``.

A downloaded build shadows a bundled one of the same tag: it is the more specific
artifact, and it is what the user explicitly asked to generate.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from importlib import resources
from pathlib import Path
from typing import Any

CATALOG_PACKAGE = "netbox_sdk.django_models.model_builds"
BUILD_SUFFIX = "-django-models-build.json"
MANIFEST_NAME = "manifest.json"


def _version_key(tag: str) -> tuple[object, ...]:
    """Sort tags by numeric version, keeping prereleases below their release."""
    body = tag.removeprefix("v")
    head, _, tail = body.partition("-")
    parts: list[object] = []
    for chunk in head.split("."):
        parts.append(int(chunk) if chunk.isdigit() else chunk)
    # A bare release must sort ABOVE its own prereleases, so absence of a suffix
    # has to compare greater than any suffix rather than as an empty string.
    return (tuple(parts), tail == "", tail)


def user_builds_dir() -> Path:
    """Return the writable directory for generated/downloaded builds.

    Honors ``XDG_DATA_HOME``; falls back to the XDG-specified default rather than
    writing next to the installed package, which may be read-only.
    """
    override = os.environ.get("NETBOX_SDK_MODEL_BUILDS_DIR")
    if override:
        return Path(override).expanduser()
    base = os.environ.get("XDG_DATA_HOME")
    root = Path(base).expanduser() if base else Path.home() / ".local" / "share"
    return root / "netbox-sdk" / "django-model-builds"


def _bundled_files() -> Iterator[Any]:
    try:
        root = resources.files(CATALOG_PACKAGE)
    except (ModuleNotFoundError, FileNotFoundError):
        return
    try:
        entries = list(root.iterdir())
    except (FileNotFoundError, NotADirectoryError, OSError):
        return
    for entry in entries:
        if entry.name.endswith(BUILD_SUFFIX):
            yield entry


def bundled_tags() -> list[str]:
    """Tags shipped inside the distribution, newest first."""
    tags = [entry.name[: -len(BUILD_SUFFIX)] for entry in _bundled_files()]
    return sorted(set(tags), key=_version_key, reverse=True)


def downloaded_tags() -> list[str]:
    """Tags present in the user-writable store, newest first."""
    directory = user_builds_dir()
    if not directory.is_dir():
        return []
    tags = [
        path.name[: -len(BUILD_SUFFIX)]
        for path in directory.glob(f"*{BUILD_SUFFIX}")
        if path.is_file()
    ]
    return sorted(set(tags), key=_version_key, reverse=True)


def available_tags() -> list[str]:
    """Every reachable tag, deduplicated and ordered newest first.

    Deterministic regardless of which store a tag came from, so the SDK and the
    TUI cannot disagree about ordering.
    """
    return sorted(set(bundled_tags()) | set(downloaded_tags()), key=_version_key, reverse=True)


def build_exists(tag: str) -> bool:
    return tag in available_tags()


def build_path(tag: str) -> Path | None:
    """Filesystem path for ``tag`` when one exists on disk.

    Returns ``None`` for a bundled build that is not extractable to a real path
    (a zipimported distribution). Use :func:`load_build` to read content; this is
    only for messages that need to name a location.
    """
    candidate = user_builds_dir() / f"{tag}{BUILD_SUFFIX}"
    if candidate.is_file():
        return candidate
    for entry in _bundled_files():
        if entry.name == f"{tag}{BUILD_SUFFIX}":
            try:
                return Path(str(entry))
            except (TypeError, ValueError):  # pragma: no cover - exotic loaders
                return None
    return None


def load_build(tag: str) -> dict[str, Any]:
    """Load a build by exact tag. A downloaded build shadows a bundled one."""
    candidate = user_builds_dir() / f"{tag}{BUILD_SUFFIX}"
    if candidate.is_file():
        return json.loads(candidate.read_text(encoding="utf-8"))
    for entry in _bundled_files():
        if entry.name == f"{tag}{BUILD_SUFFIX}":
            return json.loads(entry.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"no Django model build for tag {tag!r}")


def supported_manifest() -> dict[str, str]:
    """The declared ``{release line: tag}`` map shipped with the bundled catalog."""
    try:
        raw = (resources.files(CATALOG_PACKAGE) / MANIFEST_NAME).read_text(encoding="utf-8")
    except (ModuleNotFoundError, FileNotFoundError, OSError):
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    builds = payload.get("builds")
    return dict(builds) if isinstance(builds, dict) else {}
