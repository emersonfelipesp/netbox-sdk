"""Tests for service-layer request resolution and dynamic CLI argument parsing."""

import pytest

from netbox_cli.schema import build_schema_index
from netbox_cli.services import parse_key_value_pairs, resolve_dynamic_request
from tests.conftest import OPENAPI_PATH


def _index():
    return build_schema_index(OPENAPI_PATH)


def test_parse_key_value_pairs_ok():
    assert parse_key_value_pairs(["name=switch01", "role=leaf"]) == {
        "name": "switch01",
        "role": "leaf",
    }


def test_parse_key_value_pairs_invalid():
    with pytest.raises(ValueError):
        parse_key_value_pairs(["invalid"])


def test_resolve_list_path():
    resolved = resolve_dynamic_request(
        _index(),
        "dcim",
        "devices",
        "list",
        object_id=None,
        query={},
        payload=None,
    )
    assert resolved.method == "GET"
    assert resolved.path == "/api/dcim/devices/"


def test_resolve_get_requires_id():
    with pytest.raises(ValueError):
        resolve_dynamic_request(
            _index(),
            "dcim",
            "devices",
            "get",
            object_id=None,
            query={},
            payload=None,
        )


def test_resolve_get_detail_path():
    resolved = resolve_dynamic_request(
        _index(),
        "dcim",
        "devices",
        "get",
        object_id=12,
        query={},
        payload=None,
    )
    assert resolved.method == "GET"
    assert resolved.path == "/api/dcim/devices/12/"
