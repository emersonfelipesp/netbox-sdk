"""Executable coverage for every registered NetBox release line.

The registry guards in ``test_release_registry.py`` are *static*: they compare
the registry against file names and against the typed client's AST. They prove a
line is wired up; they do not prove it actually works.

This module is the executable half. For every line in
``SUPPORTED_NETBOX_VERSIONS`` it loads the bundled schema, indexes it, builds the
typed client, and imports the generated models module. A line that is registered
but whose artifacts are corrupt, truncated, or un-importable fails here rather
than at a user's first call.

It also holds the CI-coverage contract, so the decision "4.7 has no live-instance
job" is asserted and self-retiring instead of living only in a closed issue.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest
import yaml

from netbox_sdk.schema import SchemaIndex, load_openapi_schema
from netbox_sdk.typed_api import typed_api
from netbox_sdk.versioning import (
    DEFAULT_NETBOX_VERSION,
    SUPPORTED_NETBOX_VERSIONS,
    bundled_openapi_path,
    release_line,
)

pytestmark = pytest.mark.suite_sdk

ROOT = Path(__file__).resolve().parents[1]

# Release lines with no live-instance CI job, each with its reason. Two distinct
# causes are recorded separately on purpose: a line with no published upstream
# image *cannot* be live-tested, while a line excluded for CI cost *could* be.
# Conflating them would hide the second kind forever. The guard below fails once
# a line gains a live job, so each exception retires itself rather than quietly
# becoming permanent.
LINES_WITHOUT_LIVE_CI: dict[str, str] = {
    "4.7": (
        "no upstream image exists: ghcr.io/netbox-community/netbox publishes no "
        "tag for v4.7.0-beta1 (verified against the GHCR tag list). Nothing can "
        "be run until upstream publishes one; re-check at 4.7 GA."
    ),
    "4.3": (
        "an image exists (ghcr.io/netbox-community/netbox:v4.3.7) but the live "
        "matrix is deliberately limited to the newest stable lines for CI cost. "
        "Tracked for expansion; unlike 4.7 this gap is a choice, not a limit."
    ),
    "4.4": (
        "an image exists (ghcr.io/netbox-community/netbox:v4.4.0) but the live "
        "matrix is deliberately limited to the newest stable lines for CI cost. "
        "Tracked for expansion; unlike 4.7 this gap is a choice, not a limit. "
        "Note v4.4.10 is NOT published — pick a tag that exists when adding it."
    ),
}


def _matrix_values(job: str, key: str) -> list[str]:
    """Return one matrix axis from the tests workflow, parsed as YAML.

    Parsed rather than regexed on purpose. ``bundled-netbox-version`` contains
    ``netbox-version`` as a substring, so a pattern for one silently matched the
    other during development; and any regex over YAML also breaks on a reformat
    (indentation, block vs flow style, quoting). Reading the actual document
    removes both failure modes.

    Raises:
        AssertionError: If the job or axis is absent, so a renamed job fails
            loudly instead of skipping the check.
    """
    workflow = yaml.safe_load(_read(".github/workflows/test.yml"))
    jobs = workflow.get("jobs") or {}
    assert job in jobs, f".github/workflows/test.yml has no job {job!r}"
    matrix = ((jobs[job].get("strategy") or {}).get("matrix")) or {}
    assert key in matrix, f"job {job!r} has no matrix axis {key!r}"
    values = matrix[key]
    assert isinstance(values, list) and values, f"{job}.{key} is not a non-empty list"
    return [str(value) for value in values]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


@pytest.mark.parametrize("line", SUPPORTED_NETBOX_VERSIONS)
def test_every_registered_line_loads_and_indexes_its_bundled_schema(line: str) -> None:
    schema = load_openapi_schema(version=line)  # type: ignore[arg-type]

    assert isinstance(schema.get("paths"), dict) and schema["paths"], (
        f"bundled schema for {line} has no paths"
    )
    reported = schema.get("info", {}).get("version", "")
    assert reported.startswith(line), f"bundled schema for {line} reports info.version={reported!r}"

    index = SchemaIndex(schema)
    assert index.groups(), f"SchemaIndex for {line} produced no groups"
    # Every line must expose the core DCIM device collection; a line that indexes
    # to something unusable would otherwise pass a mere "groups are non-empty".
    assert index.resource_paths("dcim", "devices") is not None, (
        f"{line} does not resolve dcim/devices"
    )


@pytest.mark.parametrize("line", SUPPORTED_NETBOX_VERSIONS)
def test_every_registered_line_builds_a_typed_client(line: str) -> None:
    api = typed_api("https://netbox.example.com", token="t", netbox_version=line)

    suffix = line.replace(".", "_")
    assert type(api).__name__ == f"TypedApiV{suffix}"
    # Core groups must be reachable off the built client, not merely importable.
    for group in ("dcim", "ipam", "extras"):
        assert hasattr(api, group), f"typed client for {line} lacks {group}"
    assert hasattr(api.dcim, "devices")


@pytest.mark.parametrize("line", SUPPORTED_NETBOX_VERSIONS)
def test_every_registered_line_imports_its_generated_modules(line: str) -> None:
    record = release_line(line)

    models = importlib.import_module(record.models_module)
    typed = importlib.import_module(record.typed_module)

    assert hasattr(models, "Device"), f"{record.models_module} lacks Device"
    assert hasattr(typed, f"TypedApiV{record.module_suffix}")
    assert hasattr(typed, "build_api")


@pytest.mark.parametrize("line", SUPPORTED_NETBOX_VERSIONS)
def test_every_registered_line_has_a_readable_bundled_asset(line: str) -> None:
    path = bundled_openapi_path(line)  # type: ignore[arg-type]
    assert path.is_file(), f"missing bundled asset for {line}: {path}"
    assert path.stat().st_size > 0


def test_preview_lines_are_never_the_default() -> None:
    """A preview line must never become the resolved default."""
    assert release_line(DEFAULT_NETBOX_VERSION).status == "stable"


def test_ci_runs_the_version_sensitive_suite_for_every_registered_line() -> None:
    """CI must name every registered line, so a dropped line is visible.

    The full mocked suite exercises the version-sensitive tests transitively, but
    nothing in CI *named* 4.7, so a regression that removed its coverage would
    not have shown up in any job title or report.
    """
    declared = set(_matrix_values("test-bundled-release-lines", "bundled-netbox-version"))

    assert declared == set(SUPPORTED_NETBOX_VERSIONS), (
        "the bundled release-line CI matrix and the registry disagree; "
        f"workflow={sorted(declared)} registry={sorted(SUPPORTED_NETBOX_VERSIONS)}"
    )


def test_live_netbox_matrix_covers_every_line_without_a_documented_exception() -> None:
    """Every registered line is either live-tested or explicitly excepted.

    This is what makes the "4.7 has no live job" decision self-retiring: when
    upstream publishes an image and the matrix gains a 4.7 entry, the stale
    exception below fails this test and must be removed.
    """
    live_lines = {
        ".".join(str(version).lstrip("v").split(".")[:2])
        for version in _matrix_values("test-live-netbox", "netbox-version")
    }

    for line in SUPPORTED_NETBOX_VERSIONS:
        if line in live_lines:
            assert line not in LINES_WITHOUT_LIVE_CI, (
                f"{line} now has a live CI job; remove its LINES_WITHOUT_LIVE_CI "
                "exception and its no-live-coverage note from the docs"
            )
            continue
        assert line in LINES_WITHOUT_LIVE_CI, (
            f"release line {line} has neither a live CI job nor a documented "
            "exception in LINES_WITHOUT_LIVE_CI"
        )
        assert LINES_WITHOUT_LIVE_CI[line].strip(), f"{line} exception has no reason"


def test_documented_live_ci_exceptions_are_all_registered_lines() -> None:
    """A stale exception for an unregistered line must not linger."""
    unknown = set(LINES_WITHOUT_LIVE_CI) - set(SUPPORTED_NETBOX_VERSIONS)
    assert not unknown, f"LINES_WITHOUT_LIVE_CI names unregistered lines: {sorted(unknown)}"


def test_metadata_publishes_every_registered_line() -> None:
    """The published package metadata must advertise every bundled line."""
    metadata = json.loads(_read("metadata.json"))
    assert set(metadata["netbox"]) == set(SUPPORTED_NETBOX_VERSIONS), (
        f"metadata.json netbox={metadata['netbox']} registry={sorted(SUPPORTED_NETBOX_VERSIONS)}"
    )
