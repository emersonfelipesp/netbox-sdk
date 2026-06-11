"""Tests for schema parsing and indexed NetBox resource lookup behavior."""

import pytest

from netbox_sdk.schema import build_schema_index, parse_group_resource
from tests.conftest import OPENAPI_PATH

pytestmark = pytest.mark.suite_sdk


def test_parse_group_resource():
    group, resource = parse_group_resource("/api/dcim/devices/")
    assert group == "dcim"
    assert resource == "devices"


def test_parse_group_resource_for_plugin_endpoint():
    group, resource = parse_group_resource("/api/plugins/gpon/olts/")
    assert group == "plugins"
    assert resource == "gpon/olts"


def test_parse_group_resource_for_nested_plugin_endpoint():
    group, resource = parse_group_resource("/api/plugins/proxbox/resources/clusters/")
    assert group == "plugins"
    assert resource == "proxbox/resources/clusters"


def test_parse_group_resource_for_nested_plugin_detail_endpoint():
    group, resource = parse_group_resource("/api/plugins/proxbox/resources/clusters/{id}/")
    assert group == "plugins"
    assert resource == "proxbox/resources/clusters"


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


# ---------------------------------------------------------------------------
# filter_params
# ---------------------------------------------------------------------------


def test_filter_params_returns_nonempty_list_for_devices():
    from netbox_sdk.schema import FilterParam

    index = build_schema_index(OPENAPI_PATH)
    params = index.filter_params("dcim", "devices")
    assert len(params) > 0
    assert all(isinstance(p, FilterParam) for p in params)


def test_filter_params_have_required_attributes():
    index = build_schema_index(OPENAPI_PATH)
    params = index.filter_params("dcim", "devices")
    for p in params:
        assert isinstance(p.name, str) and p.name
        assert isinstance(p.label, str)
        assert p.type in {"string", "integer", "boolean", "enum", "array"}


def test_filter_params_q_sorted_first_when_present():
    index = build_schema_index(OPENAPI_PATH)
    params = index.filter_params("extras", "tags")
    names = [p.name for p in params]
    if "q" in names:
        assert names[0] == "q"


def test_filter_params_excludes_pagination_params():
    index = build_schema_index(OPENAPI_PATH)
    params = index.filter_params("dcim", "devices")
    names = {p.name for p in params}
    assert "limit" not in names
    assert "offset" not in names
    assert "start" not in names
    assert "format" not in names


def test_filter_params_excludes_netbox_46_cursor_start_param():
    index = build_schema_index(version="4.6")
    params = index.filter_params("dcim", "devices")
    names = {p.name for p in params}
    assert "start" not in names


def test_filter_params_excludes_lookup_suffixes():
    index = build_schema_index(OPENAPI_PATH)
    params = index.filter_params("dcim", "devices")
    for p in params:
        assert not any(
            p.name.endswith(s)
            for s in ("__ic", "__ie", "__iew", "__isw", "__n", "__nic", "__nie", "__niew", "__nisw")
        ), f"lookup suffix found in param name: {p.name!r}"


def test_filter_params_returns_empty_for_unknown_resource():
    index = build_schema_index(OPENAPI_PATH)
    assert index.filter_params("dcim", "no-such-resource") == []
    assert index.filter_params("no-such-group", "devices") == []


def test_filter_params_enum_type_has_choices():
    index = build_schema_index(OPENAPI_PATH)
    params = index.filter_params("dcim", "devices")
    enum_params = [p for p in params if p.type == "enum"]
    for p in enum_params:
        assert len(p.choices) > 0, f"enum param {p.name!r} has no choices"
