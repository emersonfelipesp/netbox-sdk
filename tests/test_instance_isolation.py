from __future__ import annotations

import pytest

from netbox_cli import runtime
from netbox_sdk import schema_resolution
from netbox_sdk.client import NetBoxApiClient
from netbox_sdk.config import Config
from netbox_tui.app import NetBoxTuiApp
from netbox_tui.dev_state import (
    DevTuiState,
    DevViewState,
    dev_tui_state_path,
    load_dev_tui_state,
    save_dev_tui_state,
)
from netbox_tui.state import TuiState, ViewState, load_tui_state, save_tui_state, tui_state_path

pytestmark = pytest.mark.suite_cli


def _reset_runtime_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    schema_resolution.clear_schema_caches()


def test_shared_cache_reset_reloads_after_cli_cache_was_populated(monkeypatch) -> None:
    first = runtime._get_index()
    assert "_replacement" not in first.schema

    replacement = {"paths": {}, "_replacement": True}
    monkeypatch.setattr(
        schema_resolution.schema_module,
        "load_openapi_schema",
        lambda **kwargs: replacement,
    )

    schema_resolution.clear_schema_caches()

    assert runtime._get_index().schema["_replacement"] is True


def test_runtime_schema_indexes_are_isolated_between_callers(monkeypatch) -> None:
    schema = {
        "paths": {
            "/api/dcim/devices/": {
                "get": {"operationId": "dcim_devices_list", "summary": "List devices"}
            },
            "/api/dcim/devices/{id}/": {
                "get": {"operationId": "dcim_devices_detail", "summary": "Get device"}
            },
        }
    }
    _reset_runtime_schema(monkeypatch)
    monkeypatch.setattr(
        schema_resolution.schema_module,
        "load_openapi_schema",
        lambda **kwargs: schema,
    )
    first = runtime._get_index()
    assert "plugins" not in first.groups()

    changed = first.add_discovered_resource(
        group="plugins",
        resource="gpon/boards",
        list_path="/api/plugins/gpon/boards/",
        detail_path="/api/plugins/gpon/boards/{id}/",
    )
    assert changed is True
    assert "gpon/boards" in first.resources("plugins")

    second = runtime._get_index()
    assert "plugins" not in second.groups()
    assert second.schema is first.schema


def test_tui_consumes_the_cli_resolved_pinned_index(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("NETBOX_SDK_NETBOX_VERSION", "4.5")
    monkeypatch.setattr(runtime.sys, "argv", ["nbx"])
    _reset_runtime_schema(monkeypatch)

    cli_index = runtime._get_registration_index()
    app = NetBoxTuiApp(
        client=NetBoxApiClient(Config(base_url="https://netbox.example.com")),
        index=cli_index,
    )

    assert app.index is cli_index
    assert app.index.schema["info"]["version"].startswith("4.5")
    assert set(app.index.schema["paths"]) == set(cli_index.schema["paths"])


def test_tui_state_is_scoped_per_instance(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    prod_url = "https://netbox.example.com"
    demo_url = "https://demo.netbox.dev"

    save_tui_state(
        TuiState(last_view=ViewState(group="dcim", resource="devices"), theme_name="dracula"),
        prod_url,
    )
    save_tui_state(
        TuiState(last_view=ViewState(group="ipam", resource="prefixes"), theme_name="netbox-dark"),
        demo_url,
    )

    assert tui_state_path(prod_url) != tui_state_path(demo_url)
    assert load_tui_state(prod_url).last_view.resource == "devices"
    assert load_tui_state(demo_url).last_view.resource == "prefixes"


def test_dev_tui_state_is_scoped_per_instance(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    prod_url = "https://netbox.example.com"
    demo_url = "https://demo.netbox.dev"

    save_dev_tui_state(
        DevTuiState(
            last_view=DevViewState(group="dcim", resource="devices", path="/api/dcim/devices/")
        ),
        prod_url,
    )
    save_dev_tui_state(
        DevTuiState(
            last_view=DevViewState(group="ipam", resource="prefixes", path="/api/ipam/prefixes/")
        ),
        demo_url,
    )

    assert dev_tui_state_path(prod_url) != dev_tui_state_path(demo_url)
    assert load_dev_tui_state(prod_url).last_view.path == "/api/dcim/devices/"
    assert load_dev_tui_state(demo_url).last_view.path == "/api/ipam/prefixes/"
