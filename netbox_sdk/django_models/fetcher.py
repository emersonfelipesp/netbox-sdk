"""GitHub release fetcher — look up, clone, and build NetBox model graphs.

All online operations are transparent: the user is told *why* and *where*
(what URL) before any network call is made.

Usage::

    tag = find_github_release_tag("4.2")         # → "v4.2.1"
    graph = clone_and_build("v4.2.1", output_path)  # clones, parses, saves
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

from netbox_sdk.django_models import catalog
from netbox_sdk.django_models.store import DjangoModelStore

_RELEASES_URL = "https://api.github.com/repos/netbox-community/netbox/releases"
_NETBOX_REPO_URL = "https://github.com/netbox-community/netbox.git"

# Builds come from the shared catalog service (imported above): a read-only
# bundled set shipped as package data, plus a user-writable store. Resolving a
# repository-root path from this module worked only in a checkout — in an
# installation it pointed outside the package, where the catalog is absent and
# the location is generally unwritable.


# ── Helpers ────────────────────────────────────────────────────────────────


def _print(msg: str) -> None:
    """Print a message to the user (always visible, not suppressed by spinners)."""
    print(msg)


def _fetch_json(url: str) -> Any:
    """GET a JSON body from *url* with a User-Agent header."""
    req = urllib.request.Request(url, headers={"User-Agent": "nbx-cli"})  # noqa: S310
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        return json.loads(resp.read())


# ── Public API ─────────────────────────────────────────────────────────────


def find_github_release_tag(api_version: str) -> str | None:
    """Look up the matching release tag on GitHub for an API version.

    Args:
        api_version: ``"4.2"`` from the ``API-Version`` response header.

    Returns:
        ``"v4.2.1"`` (exact tag) or ``None`` if no matching release exists.
    """
    _print(f"  Looking up NetBox release for API version {api_version} ...")
    _print(f"  GET {_RELEASES_URL}")

    releases = _fetch_json(_RELEASES_URL)
    if not isinstance(releases, list):
        _print("  Unexpected response from GitHub API.")
        return None

    # Build tag → version mapping (e.g. "v4.2.1" → VersionInfo)
    candidates: list[tuple[str, str]] = []
    for release in releases:
        tag = release.get("tag_name", "")
        if not tag.startswith("v"):
            continue
        candidates.append((tag, release.get("published_at", "")))

    # Sort by published date descending (newest first)
    candidates.sort(key=lambda x: x[1], reverse=True)

    # Match: v4.2. starts with v4.2.
    prefix = f"v{api_version}."
    for tag, _ in candidates:
        if tag.startswith(prefix):
            _print(f"  Found release: {tag}")
            return tag

    # Fallback: major-only match (v4. matches v4.0.0)
    major = api_version.split(".")[0]
    major_prefix = f"v{major}."
    for tag, _ in candidates:
        if tag.startswith(major_prefix):
            _print(f"  Found release (major match): {tag}")
            return tag

    _print(f"  No release found matching API version {api_version}.")
    return None


def builds_dir() -> Path:
    """Return the writable directory new builds are generated into.

    This is the user-writable store, never the installed package: writing beside
    ``site-packages`` fails on a read-only installation.
    """
    return catalog.user_builds_dir()


def available_build_tags() -> list[str]:
    """List every reachable build tag, bundled and downloaded, newest first."""
    return catalog.available_tags()


def build_exists(tag: str) -> bool:
    """Check whether *tag* is reachable from either store."""
    return catalog.build_exists(tag)


def _match_tag(api_version: str, tags: list[str]) -> str | None:
    """Find the best build tag matching an API-Version value.

    ``api_version`` is e.g. ``"4.2"``; tags are e.g. ``["v4.5.5", "v4.2.1"]``.
    """
    prefix = f"v{api_version}."
    for t in tags:
        if t.startswith(prefix):
            return t
    major = api_version.split(".")[0]
    major_prefix = f"v{major}."
    for t in tags:
        if t.startswith(major_prefix):
            return t
    return None


def clone_and_build(
    tag: str,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Clone NetBox at *tag*, build the model graph, and save to *output_path*.

    Args:
        tag: Release tag like ``"v4.2.1"``.
        output_path: Where to write the JSON. Defaults to
            ``django_models_builds/{tag}-django-models-build.json``.

    Returns:
        The built graph dict.
    """
    if output_path is None:
        output_path = catalog.user_builds_dir() / f"{tag}-django-models-build.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Clone ─────────────────────────────────────────────────────────────
    clone_dir = Path(tempfile.mkdtemp(prefix=f"netbox-{tag}-"))
    _print("\n  Cloning NetBox source (this may take a moment) ...")
    _print(f"  git clone --depth 1 --branch {tag} {_NETBOX_REPO_URL}")
    _print(f"  Target: {clone_dir}")

    try:
        result = subprocess.run(  # noqa: S603
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                tag,
                _NETBOX_REPO_URL,
                str(clone_dir),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"git clone failed (exit {result.returncode}): {result.stderr.strip()}"
            )

        netbox_root = clone_dir / "netbox"
        if not netbox_root.is_dir():
            raise RuntimeError(f"Expected {netbox_root} after clone but it does not exist.")

        # ── Build ─────────────────────────────────────────────────────────
        _print(f"  Scanning {netbox_root} ...")
        graph = DjangoModelStore(cache_path=output_path).build(netbox_root)
        stats = graph["stats"]

        _print(
            f"  Built {stats['total_models']} models, "
            f"{stats['total_edges']} edges "
            f"({stats['cross_app_edges']} cross-app) "
            f"across {len(stats['apps'])} apps."
        )
        _print(f"  Saved: {output_path}\n")

        return graph

    finally:
        _print(f"  Cleaning up {clone_dir} ...")
        shutil.rmtree(clone_dir, ignore_errors=True)


def fetch_and_build(
    api_version: str,
    *,
    confirm: bool = True,
) -> dict[str, Any] | None:
    """High-level: detect version, look up release, clone, build.

    Args:
        api_version: ``"4.2"`` from the ``API-Version`` header.
        confirm: If ``True``, ask the user before cloning.

    Returns:
        The built graph dict, or ``None`` if the user declined or no release found.
    """
    import typer  # noqa: PLC0415

    tag = find_github_release_tag(api_version)
    if tag is None:
        return None

    if build_exists(tag):
        located = catalog.build_path(tag)
        _print(f"  Build already exists: {located if located is not None else tag}")
        return None

    output_path = catalog.user_builds_dir() / f"{tag}-django-models-build.json"
    _print(f"\n  This will clone {_NETBOX_REPO_URL} (tag {tag})")
    _print(f"  and build the Django model graph → {output_path}")

    if confirm:
        if not typer.confirm("  Proceed?"):
            _print("  Aborted.")
            return None

    return clone_and_build(tag, output_path=output_path)
