"""Shared NetBox release-line and schema-resolution policy tests."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pytest

from netbox_sdk import schema_resolution
from netbox_sdk.schema import SchemaIndex
from netbox_sdk.versioning import (
    SUPPORTED_NETBOX_VERSIONS,
    UnsupportedNetBoxVersionError,
    bundled_openapi_path,
    version_module_suffix,
)

pytestmark = pytest.mark.suite_sdk

_VERSION_ENV_VARS = (
    "NETBOX_SDK_NETBOX_VERSION",
    "NETBOX_API_VERSION",
    "NETBOX_VERSION",
)

# A release line this SDK will never bundle. A plausible future line could turn
# this negative test into a positive one while proving nothing about unsupported
# version handling.
UNSUPPORTED_LINE = "3.9"


class _RecordCollector(logging.Handler):
    """Collect records straight off a logger, bypassing propagation."""

    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@contextmanager
def capture_sdk_logs(logger_name: str) -> Iterator[list[logging.LogRecord]]:
    """Capture records from ``logger_name`` regardless of propagation state.

    ``netbox_sdk.logging_runtime.setup_logging()`` sets ``propagate = False`` on
    the ``netbox_sdk`` namespace, so pytest's root-attached ``caplog`` silently
    sees nothing once any earlier test has initialised logging. Attaching to the
    target logger directly makes this assertion order-independent.
    """
    logger = logging.getLogger(logger_name)
    handler = _RecordCollector()
    previous_level = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    try:
        yield handler.records
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)


@contextmanager
def _isolated_bundled_index_cache() -> Iterator[None]:
    """Discard every cached document created inside a test-controlled scope."""
    schema_resolution._clear_bundled_index_cache()
    try:
        yield
    finally:
        schema_resolution._clear_bundled_index_cache()


@pytest.fixture(autouse=True)
def _isolated_resolution_state(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    with _isolated_bundled_index_cache():
        monkeypatch.setattr(schema_resolution.sys, "argv", ["pytest"])
        for name in _VERSION_ENV_VARS:
            monkeypatch.delenv(name, raising=False)
        yield


@pytest.fixture()
def bundled_loader(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    loaded: list[str] = []

    def _load(*, version: str) -> dict[str, Any]:
        loaded.append(version)
        return {
            "_release_line": version,
            "paths": {
                f"/api/{version}/objects/": {
                    "get": {"operationId": f"objects_{version}", "summary": version}
                }
            },
        }

    monkeypatch.setattr(schema_resolution.schema_module, "load_openapi_schema", _load)
    return loaded


def test_resolution_state_discards_a_document_loaded_through_a_test_double(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A patched loader must not leave its partial document for a later test."""
    partial = {
        "_source": "test-double",
        "paths": {"/api/test/widgets/": {"get": {"summary": "partial"}}},
    }

    with monkeypatch.context() as loader_patch:
        loader_patch.setattr(
            schema_resolution.schema_module,
            "load_openapi_schema",
            lambda **_kwargs: partial,
        )
        with _isolated_bundled_index_cache():
            loaded = schema_resolution.bundled_index("4.7")
            assert loaded.schema["_source"] == "test-double"

    restored = schema_resolution.bundled_index("4.7")
    assert restored.schema["info"]["version"] == "4.7.0"
    assert "/api/dcim/cooling-sources/" in restored.schema["paths"]


class _FakeClient:
    def __init__(
        self,
        version: str,
        *,
        openapi_schema: dict[str, Any] | None = None,
        version_error: Exception | None = None,
        openapi_error: Exception | None = None,
        status_document: Any = None,
        status_error: Exception | None = None,
    ) -> None:
        self.status_document = status_document
        self.status_error = status_error
        self.status_calls = 0
        self.version = version
        self.openapi_schema = openapi_schema
        self.version_error = version_error
        self.openapi_error = openapi_error
        self.version_calls = 0
        self.openapi_calls = 0

    async def status(self) -> Any:
        self.status_calls += 1
        if self.status_error is not None:
            raise self.status_error
        return self.status_document

    async def get_version(self) -> str:
        self.version_calls += 1
        if self.version_error is not None:
            raise self.version_error
        return self.version

    async def openapi(self) -> dict[str, Any]:
        self.openapi_calls += 1
        if self.openapi_error is not None:
            raise self.openapi_error
        if self.openapi_schema is None:
            raise AssertionError("test client has no live OpenAPI document")
        return self.openapi_schema


def test_requested_version_cli_precedes_environment() -> None:
    assert (
        schema_resolution.requested_netbox_version(
            ["--netbox-version", "4.5"],
            {"NETBOX_SDK_NETBOX_VERSION": "4.4"},
        )
        == "4.5"
    )
    assert (
        schema_resolution.requested_netbox_version(
            ["--api-version=v4.4"],
            {"NETBOX_SDK_NETBOX_VERSION": "4.3"},
        )
        == "4.4"
    )


def test_unsupported_line_constant_is_genuinely_unsupported() -> None:
    # Guards the negative tests below: if UNSUPPORTED_LINE ever became a real
    # bundled line, those tests would pass for the wrong reason.
    assert UNSUPPORTED_LINE not in SUPPORTED_NETBOX_VERSIONS


def test_requested_version_strict_and_lenient_invalid_handling() -> None:
    with pytest.raises(UnsupportedNetBoxVersionError, match="Supported release lines"):
        schema_resolution.requested_netbox_version(
            ["--netbox-version", UNSUPPORTED_LINE],
            env={},
            strict=True,
        )

    with capture_sdk_logs("netbox_sdk.schema_resolution") as records:
        selected = schema_resolution.requested_netbox_version(
            env={"NETBOX_SDK_NETBOX_VERSION": UNSUPPORTED_LINE}
        )

    assert selected is None
    warnings = [record for record in records if record.levelno == logging.WARNING]
    assert warnings, "lenient path must warn about the ignored override"
    assert (
        warnings[-1].getMessage()
        == f"ignoring unsupported requested NetBox version '{UNSUPPORTED_LINE}'"
    )
    assert getattr(warnings[-1], "nbx_event", None) == "schema_version_override_invalid"


def test_bundled_index_is_process_cached_and_clone_isolated(bundled_loader: list[str]) -> None:
    first = schema_resolution.bundled_index("4.5")
    changed = first.add_discovered_resource(
        group="plugins",
        resource="example/widgets",
        list_path="/api/plugins/example/widgets/",
    )
    second = schema_resolution.bundled_index("4.5")

    assert changed is True
    assert first is not second
    assert first.schema is second.schema
    assert first.resource_paths("plugins", "example/widgets") is not None
    assert second.resource_paths("plugins", "example/widgets") is None
    assert bundled_loader == ["4.5"]


async def test_explicit_line_precedes_connected_detection(bundled_loader: list[str]) -> None:
    client = _FakeClient("4.5.9")

    index = await schema_resolution.resolve_index(client, line="4.4")

    assert index.schema["_release_line"] == "4.4"
    assert client.version_calls == 0
    assert client.openapi_calls == 0
    assert bundled_loader == ["4.4"]


async def test_environment_pin_precedes_connected_detection(
    monkeypatch: pytest.MonkeyPatch,
    bundled_loader: list[str],
) -> None:
    monkeypatch.setenv("NETBOX_API_VERSION", "4.3")
    client = _FakeClient("4.6.6")

    index = await schema_resolution.resolve_index(client, use_ambient_pin=True)

    assert index.schema["_release_line"] == "4.3"
    assert client.version_calls == 0
    assert client.openapi_calls == 0
    assert bundled_loader == ["4.3"]


async def test_explicit_line_beats_process_pin(
    monkeypatch: pytest.MonkeyPatch,
    bundled_loader: list[str],
) -> None:
    monkeypatch.setenv("NETBOX_API_VERSION", "4.3")
    client = _FakeClient("4.6.6")

    index = await schema_resolution.resolve_index(client, line="4.4", use_ambient_pin=True)

    assert index.schema["_release_line"] == "4.4"
    assert bundled_loader == ["4.4"]


async def test_detected_supported_line_uses_matching_bundle(bundled_loader: list[str]) -> None:
    client = _FakeClient("4.5.10")

    with capture_sdk_logs("netbox_sdk.schema_resolution") as records:
        index = await schema_resolution.resolve_index(client)

    assert index.schema["_release_line"] == "4.5"
    assert client.version_calls == 1
    assert client.openapi_calls == 0
    assert bundled_loader == ["4.5"]
    bundled_events = [
        record
        for record in records
        if getattr(record, "nbx_event", None) == "schema_version_bundled"
    ]
    assert len(bundled_events) == 1
    assert bundled_events[0].getMessage() == "loading bundled schema for NetBox 4.5"
    assert bundled_events[0].version == "4.5"


async def test_unsupported_connected_line_uses_live_schema(bundled_loader: list[str]) -> None:
    live_schema = {
        "_source": "live",
        "paths": {
            "/api/new/widgets/": {
                "get": {"operationId": "new_widgets_list", "summary": "List widgets"}
            }
        },
    }
    client = _FakeClient("5.0.1", openapi_schema=live_schema)

    with capture_sdk_logs("netbox_sdk.schema_resolution") as records:
        index = await schema_resolution.resolve_index(client)

    assert index.schema is live_schema
    assert index.resource_paths("new", "widgets") is not None
    assert client.version_calls == 1
    assert client.openapi_calls == 1
    assert bundled_loader == []
    dynamic_events = [
        record
        for record in records
        if getattr(record, "nbx_event", None) == "schema_version_dynamic_fetch"
    ]
    assert len(dynamic_events) == 1
    assert dynamic_events[0].getMessage() == (
        "NetBox 5.0.1 is not a bundled release line; fetching schema dynamically"
    )
    assert dynamic_events[0].version == "5.0.1"


@pytest.mark.parametrize(
    (
        "client",
        "expected_version_calls",
        "expected_openapi_calls",
        "expected_event",
        "expected_message",
    ),
    [
        (
            _FakeClient("5.0.1", openapi_error=RuntimeError("schema unavailable")),
            1,
            1,
            "schema_version_detection_failed",
            "schema version detection failed (schema unavailable); using default bundled schema",
        ),
        (
            _FakeClient("", version_error=RuntimeError("connection refused")),
            1,
            0,
            "schema_version_detection_failed",
            "schema version detection failed (connection refused); using default bundled schema",
        ),
        (
            _FakeClient("5.0.1", openapi_schema={"detail": "not openapi"}),
            1,
            1,
            "schema_runtime_invalid_document",
            "connected schema response did not contain OpenAPI paths; using default bundled schema",
        ),
    ],
)
async def test_connected_resolution_failures_fall_back_when_opted_in(
    client: _FakeClient,
    expected_version_calls: int,
    expected_openapi_calls: int,
    expected_event: str,
    expected_message: str,
    bundled_loader: list[str],
) -> None:
    with capture_sdk_logs("netbox_sdk.schema_resolution") as records:
        index = await schema_resolution.resolve_index(client, fall_back_on_error=True)

    assert index.schema["_release_line"] == "4.7"
    assert client.version_calls == expected_version_calls
    assert client.openapi_calls == expected_openapi_calls
    assert bundled_loader == ["4.7"]
    matching = [
        record for record in records if getattr(record, "nbx_event", None) == expected_event
    ]
    assert len(matching) == 1
    assert matching[0].getMessage() == expected_message


async def test_ambient_pin_is_ignored_unless_opted_in(
    monkeypatch: pytest.MonkeyPatch,
    bundled_loader: list[str],
) -> None:
    """A library caller must not inherit the host process's argv/env.

    ``nbx`` opts in; ``fetch_schema_for_client`` and the MCP server do not, so an
    unrelated host-application flag can never silently repoint their schema.
    """
    monkeypatch.setenv("NETBOX_API_VERSION", "4.3")
    monkeypatch.setattr(schema_resolution.sys, "argv", ["host-app", "--api-version", "4.4"])
    client = _FakeClient("4.5.10")

    index = await schema_resolution.resolve_index(client)

    assert index.schema["_release_line"] == "4.5"
    assert client.version_calls == 1
    assert bundled_loader == ["4.5"]


@pytest.mark.parametrize(
    "make_client",
    [
        lambda: _FakeClient("5.0.1", openapi_error=RuntimeError("schema unavailable")),
        lambda: _FakeClient("", version_error=RuntimeError("connection refused")),
    ],
)
async def test_connected_resolution_errors_propagate_by_default(
    make_client: Any,
    bundled_loader: list[str],
) -> None:
    """A caller that cannot reach its instance must see the error.

    Silently substituting the default bundled contract would let a surface serve
    a schema that does not describe the server it is actually talking to.
    """
    client = make_client()

    with pytest.raises(RuntimeError):
        await schema_resolution.resolve_index(client)

    assert bundled_loader == []


@pytest.mark.parametrize(
    ("status_document", "status_error"),
    [
        (None, RuntimeError("status endpoint blocked")),
        (None, ValueError("not JSON")),
        ("<html>not a status document</html>", None),
        ({"no-version-key": True}, None),
        ({"netbox-version": ""}, None),
    ],
)
async def test_status_probe_is_best_effort_and_falls_back_to_get_version(
    status_document: Any,
    status_error: Exception | None,
    bundled_loader: list[str],
) -> None:
    """A blocked or malformed /api/status/ must not break release detection.

    Reading the status document is an enrichment over the root API-Version
    probe. If it escapes as an error, an instance with a restricted status
    endpoint either fails resolution outright or is silently handed the default
    bundled contract while actually running another line.
    """
    client = _FakeClient("4.5.10", status_document=status_document, status_error=status_error)

    index = await schema_resolution.resolve_index(client)

    assert index.schema["_release_line"] == "4.5"
    assert client.status_calls == 1
    assert client.version_calls == 1
    assert bundled_loader == ["4.5"]


async def test_status_probe_does_not_swallow_cancellation(bundled_loader: list[str]) -> None:
    """Best-effort must not mean "eats cancellation".

    ``_version_from_status`` catches ``Exception`` so a broken status endpoint
    degrades gracefully. ``asyncio.CancelledError`` derives from
    ``BaseException``, so it must still propagate — swallowing it would turn a
    cancelled request into a silently completed one that resolves an index
    nobody is waiting for.
    """
    client = _FakeClient("4.5.10", status_error=asyncio.CancelledError())

    with pytest.raises(asyncio.CancelledError):
        await schema_resolution.resolve_index(client)

    assert client.status_calls == 1
    assert client.version_calls == 0
    assert bundled_loader == []


async def test_status_document_is_preferred_when_usable(bundled_loader: list[str]) -> None:
    client = _FakeClient(
        "4.6.6",  # the header would say 4.6; the status document is authoritative
        status_document={"netbox-version": "4.4.12"},
    )

    index = await schema_resolution.resolve_index(client)

    assert index.schema["_release_line"] == "4.4"
    assert client.status_calls == 1
    assert client.version_calls == 0
    assert bundled_loader == ["4.4"]


async def test_partial_pin_sources_do_not_leak_the_other_process_global(
    monkeypatch: pytest.MonkeyPatch,
    bundled_loader: list[str],
) -> None:
    """Supplying one pin source must not implicitly consult the other.

    resolve_index(client, argv=[]) previously still read os.environ, and the
    symmetric env-only call still read sys.argv, so a caller that explicitly
    passed an empty source could be repointed by the other one anyway.
    """
    monkeypatch.setenv("NETBOX_API_VERSION", "4.3")
    monkeypatch.setattr(schema_resolution.sys, "argv", ["host-app", "--api-version", "4.4"])
    detected = "4.5"

    argv_only = await schema_resolution.resolve_index(_FakeClient("4.5.10"), argv=[])
    assert argv_only.schema["_release_line"] == detected

    env_only = await schema_resolution.resolve_index(_FakeClient("4.5.10"), env={})
    assert env_only.schema["_release_line"] == detected

    # ...while an explicitly supplied source is still honoured.
    explicit = await schema_resolution.resolve_index(
        _FakeClient("4.5.10"), argv=["--netbox-version", "4.3"], env={}
    )
    assert explicit.schema["_release_line"] == "4.3"


def test_public_version_helpers_stay_permissive_for_unregistered_strings() -> None:
    """``bundled_openapi_path``/``version_module_suffix`` must not start raising.

    Before the registry existed both helpers computed their result from the
    string for any input. Indexing the registry instead raises ``KeyError`` for an
    unregistered runtime value - a silent backward-compatibility break for public
    helpers, including callers preparing paths for a line that is not bundled yet.
    """
    unregistered = "9.9"
    assert unregistered not in SUPPORTED_NETBOX_VERSIONS

    assert version_module_suffix(unregistered) == "9_9"  # type: ignore[arg-type]
    assert (
        bundled_openapi_path(unregistered).name  # type: ignore[arg-type]
        == "netbox-openapi-9.9.json"
    )

    # Registered lines still resolve through their registry record.
    assert version_module_suffix("4.5") == "4_5"
    assert bundled_openapi_path("4.5").name == "netbox-openapi-4.5.json"
    assert bundled_openapi_path("4.5").is_file()


async def test_invalid_live_document_raises_by_default(bundled_loader: list[str]) -> None:
    """A successful HTTP response carrying a non-OpenAPI body must not fail open.

    A 403 envelope, an HTML interstitial, or an error JSON from ``/api/schema/``
    is a 200-with-garbage, not a transport failure. Substituting the default
    bundled contract would make a surface answer confidently for a server it
    cannot describe - exactly what ``fall_back_on_error=False`` promises not to do.
    """
    client = _FakeClient("5.0.1", openapi_schema={"detail": "Authentication credentials..."})

    with pytest.raises(schema_resolution.InvalidLiveSchemaError):
        await schema_resolution.resolve_index(client)

    assert client.openapi_calls == 1
    assert bundled_loader == []


async def test_invalid_live_document_falls_back_only_when_requested(
    bundled_loader: list[str],
) -> None:
    client = _FakeClient("5.0.1", openapi_schema={"detail": "not openapi"})

    index = await schema_resolution.resolve_index(client, fall_back_on_error=True)

    assert index.schema["_release_line"] == "4.7"
    assert bundled_loader == ["4.7"]


async def test_prefer_live_false_uses_default_without_detection(bundled_loader: list[str]) -> None:
    client = _FakeClient("4.5.10")

    index = await schema_resolution.resolve_index(client, prefer_live=False)

    assert index.schema["_release_line"] == "4.7"
    assert client.version_calls == 0
    assert client.openapi_calls == 0
    assert bundled_loader == ["4.7"]


async def test_detect_release_line_maps_supported_and_unsupported_versions() -> None:
    assert await schema_resolution.detect_release_line(_FakeClient("4.4.12")) == "4.4"
    assert await schema_resolution.detect_release_line(_FakeClient("5.0.0")) is None


async def test_detect_release_line_prefers_the_status_document() -> None:
    class _StatusClient:
        def __init__(self) -> None:
            self.status_calls = 0

        async def status(self) -> dict[str, str]:
            self.status_calls += 1
            return {"netbox-version": "4.5.10"}

        async def get_version(self) -> str:
            pytest.fail("a valid status document must avoid the legacy version probe")

    client = _StatusClient()

    assert await schema_resolution.detect_release_line(client) == "4.5"
    assert client.status_calls == 1


async def test_resolution_preserves_bundled_and_dynamic_log_messages(
    bundled_loader: list[str],
) -> None:
    with capture_sdk_logs("netbox_sdk.schema_resolution") as records:
        await schema_resolution.resolve_index(_FakeClient("4.5.10"))
        await schema_resolution.resolve_index(
            _FakeClient(UNSUPPORTED_LINE, openapi_schema={"paths": {}})
        )

    observed = [
        (getattr(record, "nbx_event", None), record.getMessage())
        for record in records
        if getattr(record, "nbx_event", None) is not None
    ]
    assert observed == [
        ("schema_version_bundled", "loading bundled schema for NetBox 4.5"),
        (
            "schema_version_dynamic_fetch",
            f"NetBox {UNSUPPORTED_LINE} is not a bundled release line; fetching schema dynamically",
        ),
    ]
    assert bundled_loader == ["4.5"]


def test_bundled_index_returns_schema_index(bundled_loader: list[str]) -> None:
    assert isinstance(schema_resolution.bundled_index(), SchemaIndex)
    assert bundled_loader == ["4.7"]
