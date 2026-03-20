from pathlib import Path

from netbox_cli.schema import build_schema_index, parse_group_resource


def test_parse_group_resource():
    group, resource = parse_group_resource("/api/dcim/devices/")
    assert group == "dcim"
    assert resource == "devices"


def test_schema_index_has_core_groups():
    index = build_schema_index(
        Path("/root/nms/netbox-cli/reference/openapi/netbox-openapi.json")
    )
    groups = index.groups()
    assert "dcim" in groups
    assert "ipam" in groups


def test_schema_index_resource_paths_for_devices():
    index = build_schema_index(
        Path("/root/nms/netbox-cli/reference/openapi/netbox-openapi.json")
    )
    paths = index.resource_paths("dcim", "devices")
    assert paths is not None
    assert paths.list_path == "/api/dcim/devices/"
    assert paths.detail_path == "/api/dcim/devices/{id}/"


def test_schema_index_trace_path_for_interfaces():
    index = build_schema_index(
        Path("/root/nms/netbox-cli/reference/openapi/netbox-openapi.json")
    )
    assert index.trace_path("dcim", "interfaces") == "/api/dcim/interfaces/{id}/trace/"
    assert index.trace_path("dcim", "cables") == "/api/dcim/cables/{id}/trace/"
    assert index.trace_path("dcim", "devices") is None
