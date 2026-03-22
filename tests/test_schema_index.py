"""Tests for schema parsing and indexed NetBox resource lookup behavior."""

from netbox_cli.schema import build_schema_index, parse_group_resource
from tests.conftest import OPENAPI_PATH


def test_parse_group_resource():
    group, resource = parse_group_resource("/api/dcim/devices/")
    assert group == "dcim"
    assert resource == "devices"


def test_parse_group_resource_for_plugin_endpoint():
    group, resource = parse_group_resource("/api/plugins/gpon/olts/")
    assert group == "plugins"
    assert resource == "gpon/olts"


def test_schema_index_has_core_groups():
    index = build_schema_index(OPENAPI_PATH)
    groups = index.groups()
    assert "dcim" in groups
    assert "ipam" in groups


def test_schema_index_resource_paths_for_devices():
    index = build_schema_index(OPENAPI_PATH)
    paths = index.resource_paths("dcim", "devices")
    assert paths is not None
    assert paths.list_path == "/api/dcim/devices/"
    assert paths.detail_path == "/api/dcim/devices/{id}/"


def test_schema_index_resource_paths_for_plugin_resource():
    index = build_schema_index(OPENAPI_PATH)
    paths = index.resource_paths("plugins", "gpon/olts")
    assert paths is not None
    assert paths.list_path == "/api/plugins/gpon/olts/"
    assert paths.detail_path == "/api/plugins/gpon/olts/{id}/"


def test_schema_index_trace_path_for_interfaces():
    index = build_schema_index(OPENAPI_PATH)
    assert index.trace_path("dcim", "interfaces") == "/api/dcim/interfaces/{id}/trace/"
    assert index.trace_path("dcim", "cables") == "/api/dcim/cables/{id}/trace/"
    assert index.trace_path("dcim", "devices") is None
    assert (
        index.paths_path("circuits", "circuit-terminations")
        == "/api/circuits/circuit-terminations/{id}/paths/"
    )
