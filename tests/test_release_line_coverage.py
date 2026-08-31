"""Executable coverage for every registered NetBox release line.

The registry guards in ``test_release_registry.py`` are *static*: they compare
the registry against file names and against the typed client's AST. They prove a
line is wired up; they do not prove it actually works.

This module is the executable half. For every line in
``SUPPORTED_NETBOX_VERSIONS`` it loads the bundled schema, indexes it, builds the
typed client, and imports the generated models module. A line that is registered
but whose artifacts are corrupt, truncated, or un-importable fails here rather
than at a user's first call.

It also holds the CI-coverage contract, so a line without a live-instance job
must carry a documented, self-retiring exception in ``LINES_WITHOUT_LIVE_CI``.
"""

from __future__ import annotations

import importlib
import json
import re
from pathlib import Path
from typing import Literal, NamedTuple

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
class LiveCiExemption(NamedTuple):
    """Why a registered line has no live-instance CI job."""

    cause: Literal["no-upstream-image", "ci-cost"]
    reason: str


# Lines with no live-instance CI job. The two causes are represented
# STRUCTURALLY, not just described in prose, because they expire differently:
#
#   no-upstream-image — nothing can be run; valid only while the line is still a
#       preview. Once it goes stable an image exists (or should), so the
#       exemption must be reconsidered rather than silently inherited.
#   ci-cost — an image exists and the line *could* be live-tested; excluded as a
#       deliberate trade-off. This one never expires on its own.
#
# Either way, a line that gains a live job fails its own exemption below, so no
# entry can outlive its reason unnoticed.
LINES_WITHOUT_LIVE_CI: dict[str, LiveCiExemption] = {
    "4.3": LiveCiExemption(
        cause="ci-cost",
        reason=(
            "an image exists (ghcr.io/netbox-community/netbox:v4.3.7) but the "
            "live matrix is deliberately limited to the newest stable lines. "
            "Unlike 4.7 this gap is a choice, not a limit."
        ),
    ),
    "4.4": LiveCiExemption(
        cause="ci-cost",
        reason=(
            "an image exists (ghcr.io/netbox-community/netbox:v4.4.0) but the "
            "live matrix is deliberately limited to the newest stable lines. "
            "Note v4.4.10 is NOT published — pick a tag that exists when adding it."
        ),
    ),
}


def _assert_status_reports_line(app: object, line: str) -> None:
    """Assert the mock server reports ``line`` from ``/api/status/``.

    This is the only assertion that separates every release line from every
    other. Route-shape checks can only distinguish lines whose surfaces differ,
    so a mock that silently served one stable line for all of them would pass
    them.
    """
    from fastapi.testclient import TestClient

    # Deliberately not used as a context manager: that runs the app lifespan,
    # which this assertion does not need and which makes the check slow.
    client = TestClient(app)  # type: ignore[arg-type]
    response = client.get("/api/status/")
    assert response.status_code == 200, f"{line}: /api/status/ returned {response.status_code}"
    reported = response.json().get("netbox-version", "")
    assert reported.startswith(line), (
        f"mock asked for NetBox {line} reports netbox-version={reported!r}"
    )


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


@pytest.mark.parametrize("line", SUPPORTED_NETBOX_VERSIONS)
def test_every_registered_line_builds_a_mock_app(line: str) -> None:
    """The mock server must actually serve each registered line.

    The per-line CI matrix exports ``NETBOX_MOCK_VERSION``, but nothing read it
    until this test existed, so every matrix job could pass without the mock
    server ever being built for its named line.
    """
    pytest.importorskip("fastapi", reason="the mock server requires the optional `mock` extra")

    from netbox_sdk.mock.app import create_mock_app

    app = create_mock_app(version=line)  # type: ignore[arg-type]
    routes = {getattr(route, "path", "") for route in app.routes}
    assert "/api/dcim/devices/" in routes, f"mock app for {line} has no device routes"

    # Asserting only a route every line shares would be trivially true. The mock
    # builds a genuinely different surface per line, so pin a route that exists on
    # exactly one line and require the mock to track the schema on it.
    #
    # The mock deliberately serves a few routes the core OpenAPI document does not
    # describe — the netbox-branching plugin surface and the job-polling endpoint —
    # so this is not a subset assertion.
    schema_paths = set(load_openapi_schema(version=line)["paths"])  # type: ignore[arg-type]

    cooling = "/api/dcim/cooling-sources/"
    if cooling in schema_paths:
        assert cooling in routes, f"{line} bundles {cooling} but the mock does not serve it"
    else:
        assert cooling not in routes, f"{line} does not bundle {cooling} but the mock serves it"

    # The cooling route only separates the preview line from the stable ones. If
    # the mock mapped every stable request to a single line, the assertions above
    # would still pass. Ask the server which line it believes it is serving.
    _assert_status_reports_line(app, line)


@pytest.mark.parametrize("line", SUPPORTED_NETBOX_VERSIONS)
def test_mock_app_honours_the_environment_pin(monkeypatch: pytest.MonkeyPatch, line: str) -> None:
    """``NETBOX_MOCK_VERSION`` must select the served line.

    This is what makes the matrix job's env pin meaningful rather than
    decorative: in CI each job inherits its own line, and locally the
    parametrization sweeps all of them.

    Parametrized rather than looping inside one test — building a mock app is
    expensive (hundreds of routes through FastAPI model creation), and a single
    test constructing one per line exceeded the suite's 60s per-test timeout.
    """
    pytest.importorskip("fastapi", reason="the mock server requires the optional `mock` extra")

    from netbox_sdk.mock.app import create_mock_app

    monkeypatch.setenv("NETBOX_MOCK_VERSION", line)

    app = create_mock_app()

    # The env pin must select the same server as the explicit argument...
    explicit = create_mock_app(version=line)  # type: ignore[arg-type]
    assert {getattr(r, "path", "") for r in app.routes} == {
        getattr(r, "path", "") for r in explicit.routes
    }, f"env pin {line} built a different route set than the explicit argument"
    # ...and the server must report that exact line.
    _assert_status_reports_line(app, line)


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

    This is what makes a missing live job self-retiring: when the matrix gains
    an entry for a previously excepted line, the stale exception below fails
    this test and must be removed.
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
        exemption = LINES_WITHOUT_LIVE_CI[line]
        assert exemption.reason.strip(), f"{line} exemption has no reason"
        if exemption.cause == "no-upstream-image":
            # This cause is only credible while the line is a pre-release. When it
            # goes stable, an upstream image exists (or the claim is wrong either
            # way), so force an explicit decision instead of inheriting the note.
            assert release_line(line).status == "preview", (
                f"{line} is no longer a preview line, so its 'no-upstream-image' "
                "exemption is stale: either add a live CI job or re-classify the "
                "exemption with the real current reason"
            )


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


def test_every_matrix_test_input_is_routed_by_change_detection() -> None:
    """A change to a matrix-owned test must trigger the matrix that runs it.

    The ``sdk`` path filter is an explicit allowlist. The new coverage module was
    not in it, so a pull request touching only that file left both ``sdk`` and
    ``run_all`` false and skipped the very job that guards it — the guard could
    have been weakened without CI ever running it.
    """
    workflow_text = _read(".github/workflows/test.yml")
    workflow = yaml.safe_load(workflow_text)

    step = next(
        s
        for s in workflow["jobs"]["test-bundled-release-lines"]["steps"]
        if "pytest" in str(s.get("run", ""))
    )
    matrix_inputs = set(re.findall(r"(tests/test_[a-z0-9_]+\.py)", str(step["run"])))
    assert matrix_inputs, "could not parse the matrix job's test inputs"

    detect = next(
        s
        for s in workflow["jobs"]["changes"]["steps"]
        if "filters" in str((s.get("with") or {}).keys())
    )
    filters = yaml.safe_load(detect["with"]["filters"])
    routed = set(filters.get("sdk") or []) | set(filters.get("run_all") or [])

    missing = sorted(path for path in matrix_inputs if path not in routed)
    assert not missing, (
        "these matrix-owned tests are not routed by the sdk/run_all path filters, "
        f"so editing them would skip the job that runs them: {missing}"
    )


def test_matrix_job_is_triggered_by_every_package_its_checks_import() -> None:
    """The matrix must re-run when any package it exercises changes.

    Its parity step imports ``netbox_cli.runtime`` and ``netbox_mcp.service``, so
    gating the job on the SDK filter alone meant a CLI-only or MCP-only pull
    request skipped all five jobs. The routing guard above cannot see this: it
    reads the pytest file list, not the heredoc's imports or the job's condition.
    """
    workflow = yaml.safe_load(_read(".github/workflows/test.yml"))
    job = workflow["jobs"]["test-bundled-release-lines"]
    condition = str(job.get("if", ""))

    parity = next(
        (
            s
            for s in job["steps"]
            if "import" in str(s.get("run", "")) and "netbox_" in str(s.get("run", ""))
        ),
        None,
    )
    assert parity is not None, "the matrix job has no parity step to check"

    # Map an imported package to the change-detection output that must gate it.
    package_outputs = {
        "netbox_cli": "cli",
        "netbox_mcp": "mcp",
        "netbox_sdk": "sdk",
    }
    run = str(parity["run"])
    for package, output in package_outputs.items():
        if package not in run:
            continue
        assert f"needs.changes.outputs.{output}" in condition, (
            f"the matrix job imports {package} but is not gated on "
            f"needs.changes.outputs.{output}, so a {output}-only change skips it"
        )


# Extras the matrix job's own test inputs need in order to actually run rather
# than skip. `importorskip` is right for a developer running without an extra —
# the mock server genuinely is not installed then — but in CI a skip would mean
# the job reports success having asserted nothing, which is the exact shape this
# module exists to prevent.
MATRIX_REQUIRED_EXTRAS = {
    "mock": "tests/test_mock_api.py and the per-line mock assertions need fastapi",
    "cli": "the parity step imports netbox_cli.runtime",
    "mcp": "the parity step imports netbox_mcp.service",
}


def test_matrix_job_syncs_every_extra_its_checks_require() -> None:
    """The matrix job must install what its own tests need, or they skip green.

    Verified empirically while writing this: with ``fastapi`` unimportable the
    per-line mock tests report ``10 skipped`` and exit 0. Nothing else asserts
    that CI installs the ``mock`` extra, so dropping it from this job's sync
    would silently delete all per-line mock coverage — including the
    ``/api/status/`` discriminator — while the job stayed green.
    """
    workflow = yaml.safe_load(_read(".github/workflows/test.yml"))
    job = workflow["jobs"]["test-bundled-release-lines"]

    sync = next(
        (s for s in job["steps"] if "uv sync" in str(s.get("run", ""))),
        None,
    )
    assert sync is not None, "the matrix job has no `uv sync` step"
    command = str(sync["run"])

    missing = sorted(
        f"{extra} ({why})"
        for extra, why in MATRIX_REQUIRED_EXTRAS.items()
        if f"--extra {extra}" not in command
    )
    assert not missing, (
        "the matrix job does not install extras its own checks depend on, so those "
        f"checks would skip instead of running: {missing}"
    )


def test_documentation_changes_route_to_a_job_that_runs_the_docs_guard() -> None:
    """A docs-only pull request must run the docs alignment guard.

    Before this, no ``docs/`` pattern appeared in any filter, so changing
    ``docs/sdk/index.md`` matched nothing and no GitHub test job ran — the
    registry-derived inventory guard did not execute on exactly the pull requests
    that make an inventory stale.

    Gitea CI runs the full suite unconditionally on every pull request, so this
    was defence-in-depth rather than an unguarded path, but the GitHub matrices
    own the multi-Python coverage and should not silently skip.
    """
    import fnmatch

    workflow = yaml.safe_load(_read(".github/workflows/test.yml"))
    detect = next(
        (
            s
            for s in workflow["jobs"]["changes"]["steps"]
            if "filters" in str((s.get("with") or {}).keys())
        ),
        None,
    )
    assert detect is not None, "the changes job has no filters step"
    filters = yaml.safe_load(detect["with"]["filters"])

    # Representative documentation inputs that carry support inventories.
    samples = ("docs/sdk/index.md", "docs/sdk/typed.pt.md", "CERTIFICATION.md")
    for sample in samples:
        matched = [
            name
            for name, patterns in filters.items()
            if any(fnmatch.fnmatch(sample, p.replace("**", "*")) for p in patterns)
        ]
        assert matched, f"{sample} matches no change-detection filter"

        # ...and at least one matched filter must gate a job that runs the guard.
        gating = [
            job_name
            for job_name, job in workflow["jobs"].items()
            if any(f"needs.changes.outputs.{name}" in str(job.get("if", "")) for name in matched)
            and any(
                "test_docs_alignment" in str(s.get("run", ""))
                or "suite_sdk" in str(s.get("run", ""))
                for s in job.get("steps", [])
            )
        ]
        assert gating, (
            f"{sample} routes to {matched}, but no job gated on those outputs runs "
            "the documentation alignment guard"
        )
