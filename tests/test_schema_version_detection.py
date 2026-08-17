"""Tests for version-aware OpenAPI schema selection (issue #14)."""

from __future__ import annotations

import inspect
import re

import pytest
import typer
from typer.testing import CliRunner

import netbox_cli as cli
from netbox_cli import runtime
from netbox_cli.dynamic import _register_openapi_subcommands
from netbox_sdk import schema_resolution
from netbox_sdk.config import Config
from netbox_sdk.schema import fetch_schema_for_client

pytestmark = pytest.mark.suite_cli
runner = CliRunner()


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


def _reset_runtime_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    schema_resolution._clear_bundled_index_cache()
    monkeypatch.setattr(runtime, "_SCHEMA_DOCUMENT", None)
    monkeypatch.setattr(runtime, "_SCHEMA_INDEX", None)
    monkeypatch.setattr(runtime, "_SCHEMA_VERSION", None)
    for name in runtime._NETBOX_VERSION_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(runtime.sys, "argv", ["nbx"])


def test_netbox_version_help_uses_the_shared_registry_description() -> None:
    callback_source = inspect.getsource(cli.root_callback)

    assert "describe_supported_versions()" in callback_source
    assert "4.3 through 4.6" not in callback_source

    result = runner.invoke(cli.app, ["--help"])
    plain_output = re.sub(r"\x1b\[[0-9;]*m", "", result.output).replace("│", " ")
    normalized_output = " ".join(plain_output.replace("│", " ").split())

    assert result.exit_code == 0
    assert "4.3, 4.4, 4.5, 4.6, 4.7 (preview)" in normalized_output


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

    schema_resolution._clear_bundled_index_cache()
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

    schema_resolution._clear_bundled_index_cache()
    monkeypatch.setattr(
        schema_resolution.schema_module,
        "load_openapi_schema",
        lambda **kw: fallback_doc,
    )
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

    schema_resolution._clear_bundled_index_cache()
    monkeypatch.setattr(
        schema_resolution.schema_module,
        "load_openapi_schema",
        lambda **kw: fallback_doc,
    )
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


def test_load_schema_falls_back_on_non_openapi_response(monkeypatch) -> None:
    from netbox_cli import runtime

    fallback_doc = {"paths": {}, "_source": "fallback"}

    schema_resolution._clear_bundled_index_cache()
    monkeypatch.setattr(
        schema_resolution.schema_module,
        "load_openapi_schema",
        lambda **kw: fallback_doc,
    )
    monkeypatch.setattr(
        runtime,
        "load_profile_config",
        lambda profile: type("cfg", (), {"base_url": "https://netbox.example.com"})(),
    )

    def _return_error(coro):
        coro.close()
        return {"error": "authentication required"}

    monkeypatch.setattr(runtime, "run_with_spinner", _return_error)

    result = runtime._load_schema_for_connected_instance()
    assert result["_source"] == "fallback"


def test_get_index_uses_bundled_schema_without_connected_probe(monkeypatch) -> None:
    bundled_doc = {"paths": {}, "_source": "bundled"}

    monkeypatch.setattr(runtime, "_SCHEMA_DOCUMENT", None)
    monkeypatch.setattr(runtime, "_SCHEMA_INDEX", None)
    monkeypatch.setattr(runtime, "_SCHEMA_VERSION", None)
    schema_resolution._clear_bundled_index_cache()
    monkeypatch.setattr(
        schema_resolution.schema_module,
        "load_openapi_schema",
        lambda **kw: bundled_doc,
    )
    monkeypatch.setattr(
        runtime,
        "_load_schema_for_connected_instance",
        lambda *args, **kwargs: pytest.fail("_get_index must not probe the live instance"),
    )

    result = runtime._get_index()

    assert result.schema["_source"] == "bundled"


def test_registration_index_defaults_to_netbox_46(monkeypatch, minimal_schema) -> None:
    _reset_runtime_schema(monkeypatch)
    versions: list[str | None] = []

    def _mock_load(openapi_path=None, *, version=None):
        versions.append(version)
        return minimal_schema

    monkeypatch.setattr(schema_resolution.schema_module, "load_openapi_schema", _mock_load)

    result = runtime._get_registration_index()

    assert result.resources("dcim") == ["devices"]
    assert versions == ["4.6"]


def test_registration_index_honors_cli_netbox_version_override(monkeypatch, minimal_schema) -> None:
    _reset_runtime_schema(monkeypatch)
    versions: list[str | None] = []

    def _mock_load(openapi_path=None, *, version=None):
        versions.append(version)
        return minimal_schema

    monkeypatch.setattr(schema_resolution.schema_module, "load_openapi_schema", _mock_load)
    monkeypatch.setattr(runtime.sys, "argv", ["nbx", "--netbox-version", "4.5"])

    runtime._get_registration_index()

    assert versions == ["4.5"]


def test_runtime_index_detects_configured_instance(monkeypatch) -> None:
    _reset_runtime_schema(monkeypatch)
    cfg = Config(base_url="https://netbox.example.com")
    calls: list[tuple[str, Config]] = []
    connected = runtime.SchemaIndex(
        {
            "paths": {
                "/api/ipam/prefixes/": {
                    "get": {"operationId": "ipam_prefixes_list", "summary": "List prefixes"}
                }
            }
        }
    )

    def _connected(profile: str, cfg_arg: Config):
        calls.append((profile, cfg_arg))
        return connected

    monkeypatch.setattr(runtime, "load_profile_config", lambda profile: cfg)
    monkeypatch.setattr(runtime, "_get_connected_index", _connected)
    monkeypatch.setattr(
        schema_resolution.schema_module,
        "load_openapi_schema",
        lambda **kw: pytest.fail("configured instances should use connected schema detection"),
    )

    result = runtime._get_runtime_index()

    assert result.resources("ipam") == ["prefixes"]
    assert calls == [(runtime.DEFAULT_PROFILE, cfg)]


def test_runtime_index_override_skips_connected_detection(monkeypatch, minimal_schema) -> None:
    _reset_runtime_schema(monkeypatch)
    versions: list[str | None] = []

    def _mock_load(openapi_path=None, *, version=None):
        versions.append(version)
        return minimal_schema

    monkeypatch.setattr(runtime.sys, "argv", ["nbx", "--api-version=4.5"])
    monkeypatch.setattr(schema_resolution.schema_module, "load_openapi_schema", _mock_load)
    monkeypatch.setattr(
        runtime,
        "_get_connected_index",
        lambda *a, **kw: pytest.fail("explicit version must skip live detection"),
    )

    runtime._get_runtime_index(profile=runtime.DEFAULT_PROFILE, cfg=Config(base_url="https://n"))

    assert versions == ["4.5"]


def test_registered_command_tree_defaults_to_netbox_46(monkeypatch) -> None:
    _reset_runtime_schema(monkeypatch)
    target = typer.Typer(no_args_is_help=True)

    _register_openapi_subcommands(target)

    result = runner.invoke(target, ["dcim", "cable-bundles", "list", "--help"])

    assert result.exit_code == 0
    assert "list dcim/cable-bundles" in result.output


def test_registered_command_tree_can_be_pinned_to_netbox_45(monkeypatch) -> None:
    _reset_runtime_schema(monkeypatch)
    monkeypatch.setattr(runtime.sys, "argv", ["nbx", "--netbox-version", "4.5"])
    target = typer.Typer(no_args_is_help=True)

    _register_openapi_subcommands(target)

    result = runner.invoke(target, ["dcim", "cable-bundles", "list", "--help"])

    assert result.exit_code != 0
    assert "No such command" in result.output


def test_enriched_index_honors_the_explicit_pin(monkeypatch, minimal_schema) -> None:
    """`--live` enrichment must not discard an explicit --netbox-version pin.

    `_get_enriched_index()` previously always started from the *connected*
    instance's line, so `nbx --netbox-version 4.5 ... --live` could describe a 4.6
    server while every non-live path stayed on 4.5.
    """
    from netbox_sdk.config import Config as _Config

    _reset_runtime_schema(monkeypatch)
    monkeypatch.setattr(runtime.sys, "argv", ["nbx", "--netbox-version", "4.5"])

    requested: list[str | None] = []

    def _mock_load(openapi_path=None, *, version=None):
        requested.append(version)
        return minimal_schema

    monkeypatch.setattr(schema_resolution.schema_module, "load_openapi_schema", _mock_load)
    monkeypatch.setattr(
        runtime,
        "_get_connected_index",
        lambda *a, **k: pytest.fail("an explicit pin must skip connected detection"),
    )

    async def _no_discovery(_index, _client):
        return False

    import netbox_sdk.plugin_discovery as discovery_mod

    monkeypatch.setattr(discovery_mod, "enrich_schema_index_with_runtime_resources", _no_discovery)

    class _Client:
        config = _Config(base_url="https://netbox.example.com")

        async def close(self) -> None:
            return None

    runtime._get_enriched_index(_Client())  # type: ignore[arg-type]

    assert requested == ["4.5"]


def test_tui_launch_passes_the_pin_and_reload_keeps_it(monkeypatch) -> None:
    """The TUI must rebuild against its launch line after an interactive login.

    Without the pin, logging in swaps contracts: a 4.5-pinned TUI connected to a
    4.6 instance came back describing 4.6 while CLI and MCP stayed on 4.5.
    """
    import inspect

    from netbox_tui.app import NetBoxTuiApp, run_tui

    assert "pinned_line" in inspect.signature(run_tui).parameters
    assert "pinned_line" in inspect.signature(NetBoxTuiApp.__init__).parameters

    reload_src = inspect.getsource(NetBoxTuiApp._reload_schema_for_authenticated_client)
    assert "self._pinned_line" in reload_src, (
        "the post-login reload must resolve against the launch pin"
    )
    assert "fetch_schema_for_client" not in reload_src
