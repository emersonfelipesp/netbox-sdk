"""An unpinned MCP server must dispatch against the instance it is connected to.

The server used to store the *default* bundled index at construction and use it
for every tool call except those explicitly asking for ``live=true``. A server
talking to a 4.5 instance — or, now that 4.7 is registered as a preview line, a
4.7 instance while the default stays 4.6 — therefore dispatched default reads
*and any enabled mutations* against the wrong contract.

Every other surface already resolved the connected line: the CLI does it through
``_get_runtime_index()`` and hands the result to the TUI. Only MCP did not.
"""

from __future__ import annotations

from typing import Any

import pytest

from netbox_mcp.service import NetBoxMCPService
from netbox_sdk.client import ApiResponse
from netbox_sdk.config import Config
from netbox_sdk.schema_resolution import InvalidLiveSchemaError, bundled_index
from netbox_sdk.versioning import DEFAULT_NETBOX_VERSION

pytestmark = pytest.mark.suite_mcp


class _Client:
    """A client that reports a NetBox version and counts detection calls."""

    def __init__(
        self, version: str = "4.5.0", *, responses: list[ApiResponse] | None = None
    ) -> None:
        self.version = version
        self.responses = responses or [ApiResponse(status=200, text='{"ok": true}', headers={})]
        self.calls: list[dict[str, Any]] = []
        self.version_calls = 0
        self.closed = 0

    async def get_version(self) -> str:
        self.version_calls += 1
        return self.version

    async def openapi(self) -> dict[str, Any]:
        raise AssertionError("a supported release line must use the bundled schema")

    async def request(self, method: str, path: str, **kwargs: Any) -> ApiResponse:
        self.calls.append({"method": method, "path": path, **kwargs})
        return self.responses.pop(0)

    async def close(self) -> None:
        self.closed += 1


def _service(client: _Client, **kwargs: Any) -> NetBoxMCPService:
    """Build an **unpinned** server — no ``index=`` and no ``pinned_line=``."""
    return NetBoxMCPService(
        client_factory=lambda _config: client,  # type: ignore[arg-type, return-value]
        config_loader=lambda: Config(base_url="https://netbox.example.com"),
        **kwargs,
    )


def test_construction_performs_no_detection() -> None:
    """A server must still be constructible while NetBox is unreachable."""
    client = _Client()

    service = _service(client)

    assert client.version_calls == 0
    assert service.index is not None


@pytest.mark.parametrize(
    "reported",
    [
        pytest.param("4.5.10", id="4.5-below-default"),
        pytest.param("4.7.0", id="4.7-preview-above-default"),
    ],
)
async def test_unpinned_reads_dispatch_against_the_connected_line(reported: str) -> None:
    """Covers both directions past the default, which is 4.6."""
    client = _Client(reported)
    service = _service(client)

    resolved = await service._dispatch_index(None)

    expected = ".".join(reported.split(".")[:2])
    assert expected != DEFAULT_NETBOX_VERSION, "this test is only meaningful off the default line"
    # Identity of the cached document is the exact oracle: bundled_index() shares
    # one parsed document per release line, so this cannot pass by coincidence
    # and does not hard-code a patch version that a bundle refresh would move.
    assert resolved.schema is bundled_index(expected).schema, (
        f"dispatch did not use the connected {expected} contract"
    )
    assert resolved.schema is not bundled_index(DEFAULT_NETBOX_VERSION).schema


async def test_unpinned_mutations_dispatch_against_the_connected_line() -> None:
    """The dangerous half: a write against a mis-detected contract."""
    client = _Client("4.5.10")
    service = _service(client, allow_mutations=True)

    await service.create(group="dcim", resource="devices", payload={"name": "d1"})

    assert client.version_calls == 1, "a mutation must settle the contract before dispatching"
    assert client.calls[0]["method"] == "POST"


async def test_connected_resolution_happens_at_most_once_per_service() -> None:
    client = _Client(
        "4.5.10",
        responses=[ApiResponse(status=200, text="[]", headers={}) for _ in range(3)],
    )
    service = _service(client)

    for _ in range(3):
        await service.list(group="dcim", resource="devices")

    assert client.version_calls == 1, f"detected {client.version_calls} times, expected once"


async def test_detection_failure_fails_the_call_instead_of_using_the_default_bundle() -> None:
    """Fail closed. Answering from the default bundle is the defect, not the fallback."""

    class _Unreachable(_Client):
        async def get_version(self) -> str:
            self.version_calls += 1
            raise ConnectionError("netbox unreachable")

    client = _Unreachable()
    service = _service(client)

    with pytest.raises(ConnectionError):
        await service.list(group="dcim", resource="devices")


async def test_unusable_live_document_fails_the_call() -> None:
    """A 403 body or HTML interstitial is a *successful* response carrying junk."""

    class _Junk(_Client):
        async def get_version(self) -> str:
            self.version_calls += 1
            return "9.9.0"  # unsupported -> forces a live fetch

        async def openapi(self) -> dict[str, Any]:
            return {"detail": "Authentication credentials were not provided."}

    client = _Junk()
    service = _service(client)

    with pytest.raises(InvalidLiveSchemaError):
        await service.list(group="dcim", resource="devices")


async def test_a_failed_detection_is_not_cached_as_a_contract() -> None:
    """A transient outage must not poison the server for its whole lifetime."""
    recovered = ApiResponse(status=200, text="[]", headers={})

    class _Flaky(_Client):
        def __init__(self) -> None:
            super().__init__("4.5.10", responses=[recovered])
            self.fail_next = True

        async def get_version(self) -> str:
            self.version_calls += 1
            if self.fail_next:
                self.fail_next = False
                raise ConnectionError("transient")
            return self.version

    client = _Flaky()
    service = _service(client)

    with pytest.raises(ConnectionError):
        await service.list(group="dcim", resource="devices")

    await service.list(group="dcim", resource="devices")
    assert client.version_calls == 2


async def test_dry_run_constructs_no_client_and_detects_nothing() -> None:
    """A preview must stay local; acquiring a connection to preview is the bug."""

    def _explode(_config: Any) -> Any:
        raise AssertionError("a dry run must not construct a client")

    service = NetBoxMCPService(
        client_factory=_explode,  # type: ignore[arg-type]
        config_loader=lambda: Config(base_url="https://netbox.example.com"),
    )

    preview = await service.create(
        group="dcim", resource="devices", payload={"name": "d1"}, dry_run=True
    )

    assert preview["dry_run"] is True
    assert preview["method"] == "POST"


async def test_dry_run_is_still_local_when_mutations_are_denied() -> None:
    """The gate ordering must not turn a denied preview into network I/O."""

    def _explode(_config: Any) -> Any:
        raise AssertionError("a dry run must not construct a client")

    service = NetBoxMCPService(
        client_factory=_explode,  # type: ignore[arg-type]
        config_loader=lambda: Config(base_url="https://netbox.example.com"),
        allow_mutations=False,
    )

    preview = await service.create(
        group="dcim", resource="devices", payload={"name": "d1"}, dry_run=True
    )

    assert preview["dry_run"] is True


async def test_explicit_pin_still_skips_detection_entirely() -> None:
    class _NoDetect(_Client):
        async def get_version(self) -> str:
            pytest.fail("an explicit pin must skip connected version detection")

    client = _NoDetect()
    service = _service(client, pinned_line="4.5")

    resolved = await service._dispatch_index(None)

    assert resolved is service.index
    assert resolved.schema is bundled_index("4.5").schema


async def test_injected_index_is_authoritative_and_skips_detection() -> None:
    class _NoDetect(_Client):
        async def get_version(self) -> str:
            pytest.fail("an injected index must skip connected version detection")

    injected = bundled_index("4.3")
    client = _NoDetect()
    service = _service(client, index=injected)

    resolved = await service._dispatch_index(None)

    assert resolved is injected
