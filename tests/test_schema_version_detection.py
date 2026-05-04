"""Tests for version-aware OpenAPI schema selection (issue #14)."""

from __future__ import annotations

import pytest

from netbox_sdk.schema import fetch_schema_for_client

pytestmark = pytest.mark.suite_cli


# ---------------------------------------------------------------------------
# fetch_schema_for_client
# ---------------------------------------------------------------------------


@pytest.fixture()
def minimal_schema() -> dict:
    return {
        "paths": {
            "/api/dcim/devices/": {
                "get": {"operationId": "dcim_devices_list", "summary": "List devices"}
            }
        }
    }


class _FakeClient:
    def __init__(
        self, version: str, openapi_schema: dict | None = None, raise_on_version: bool = False
    ) -> None:
        self._version = version
        self._openapi_schema = openapi_schema or {}
        self._raise_on_version = raise_on_version
        self.openapi_called = False

    async def get_version(self) -> str:
        if self._raise_on_version:
            raise RuntimeError("connection refused")
        return self._version

    async def openapi(self) -> dict:
        self.openapi_called = True
        return self._openapi_schema


@pytest.mark.asyncio
async def test_bundled_version_uses_bundled_schema(monkeypatch) -> None:
    import netbox_sdk.schema as schema_mod

    loaded: list[dict] = []

    def _mock_load(openapi_path=None, *, version=None):
        doc = {"paths": {}, "_loaded_version": version}
        loaded.append(doc)
        return doc

    monkeypatch.setattr(schema_mod, "load_openapi_schema", _mock_load)
    client = _FakeClient(version="4.5.3")

    result = await fetch_schema_for_client(client)

    assert not client.openapi_called
    assert len(loaded) == 1
    assert loaded[0]["_loaded_version"] == "4.5"
    assert result["_loaded_version"] == "4.5"


@pytest.mark.asyncio
async def test_unsupported_version_fetches_dynamically(minimal_schema) -> None:
    client = _FakeClient(version="5.0.0", openapi_schema=minimal_schema)

    result = await fetch_schema_for_client(client)

    assert client.openapi_called
    assert result == minimal_schema


@pytest.mark.asyncio
async def test_unsupported_version_with_minor_variant_fetches_dynamically(minimal_schema) -> None:
    client = _FakeClient(version="4.9.1", openapi_schema=minimal_schema)

    result = await fetch_schema_for_client(client)

    assert client.openapi_called
    assert result == minimal_schema


# ---------------------------------------------------------------------------
# _load_schema_for_connected_instance (CLI runtime helper)
# ---------------------------------------------------------------------------


def test_load_schema_falls_back_when_no_base_url(monkeypatch) -> None:
    from netbox_cli import runtime

    fallback_doc = {"paths": {}, "_source": "fallback"}

    monkeypatch.setattr(runtime, "load_openapi_schema", lambda **kw: fallback_doc)
    monkeypatch.setattr(
        runtime,
        "load_profile_config",
        lambda profile: type("cfg", (), {"base_url": None})(),
    )

    result = runtime._load_schema_for_connected_instance()
    assert result["_source"] == "fallback"


def test_load_schema_falls_back_on_connection_error(monkeypatch) -> None:
    from netbox_cli import runtime

    fallback_doc = {"paths": {}, "_source": "fallback"}

    monkeypatch.setattr(runtime, "load_openapi_schema", lambda **kw: fallback_doc)
    monkeypatch.setattr(
        runtime,
        "load_profile_config",
        lambda profile: type("cfg", (), {"base_url": "https://netbox.example.com"})(),
    )

    def _raise(coro):
        coro.close()
        raise RuntimeError("unreachable")

    monkeypatch.setattr(runtime, "run_with_spinner", _raise)

    result = runtime._load_schema_for_connected_instance()
    assert result["_source"] == "fallback"


def test_get_index_uses_bundled_schema_without_connected_probe(monkeypatch) -> None:
    from netbox_cli import runtime

    bundled_doc = {"paths": {}, "_source": "bundled"}

    monkeypatch.setattr(runtime, "_SCHEMA_DOCUMENT", None)
    monkeypatch.setattr(runtime, "load_openapi_schema", lambda **kw: bundled_doc)
    monkeypatch.setattr(
        runtime,
        "_load_schema_for_connected_instance",
        lambda *args, **kwargs: pytest.fail("_get_index must not probe the live instance"),
    )

    result = runtime._get_index()

    assert result.schema["_source"] == "bundled"
