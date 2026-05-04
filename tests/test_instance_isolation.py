from __future__ import annotations

import pytest

from netbox_cli import runtime
from netbox_tui.dev_state import (
    DevTuiState,
    DevViewState,
    dev_tui_state_path,
    load_dev_tui_state,
    save_dev_tui_state,
)
from netbox_tui.state import TuiState, ViewState, load_tui_state, save_tui_state, tui_state_path

pytestmark = pytest.mark.suite_cli


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
    monkeypatch.setattr(runtime, "_SCHEMA_DOCUMENT", None)
    monkeypatch.setattr(runtime, "load_openapi_schema", lambda **kwargs: schema)

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
