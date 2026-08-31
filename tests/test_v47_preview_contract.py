"""NetBox 4.7 preview-line contracts that must stay true after a pin bump."""

from __future__ import annotations

import json

import pytest

from netbox_sdk.client import ApiResponse
from netbox_sdk.custom_fields import custom_field_write_value, custom_fields_for_write
from netbox_sdk.exceptions import BulkOperationEntryError, RequestError
from netbox_sdk.schema import SchemaIndex, load_openapi_schema
from netbox_sdk.schema_resolution import resolve_index
from netbox_sdk.versioning import DEFAULT_NETBOX_VERSION

pytestmark = pytest.mark.suite_sdk


class _StatusClient:
    def __init__(self, version: str) -> None:
        self.version = version
        self.openapi_calls = 0

    async def status(self) -> dict[str, str]:
        return {"netbox-version": self.version}

    async def get_version(self) -> str:
        return self.version

    async def openapi(self) -> dict[str, object]:
        self.openapi_calls += 1
        raise AssertionError("a bundled 4.7 server must not fetch live OpenAPI")


def test_service_filters_drop_removed_protocol_lookups() -> None:
    schema = load_openapi_schema(version="4.7")
    parameters = schema["paths"]["/api/ipam/services/"]["get"]["parameters"]
    names = {item["name"] for item in parameters if isinstance(item, dict)}
    assert "port_mappings" in names
    assert "protocol" in names
    assert "port" in names
    assert "protocol__ic" not in names
    assert "protocol__isw" not in names
    assert "protocol__empty" not in names
    assert "port__empty" not in names


def test_cooling_and_module_bay_type_paths_are_indexed() -> None:
    index = SchemaIndex(load_openapi_schema(version="4.7"))
    assert index.resource_paths("dcim", "cooling-sources") is not None
    assert index.resource_paths("dcim", "cooling-feeds") is not None
    assert index.resource_paths("dcim", "cooling-intakes") is not None
    assert index.resource_paths("dcim", "cooling-outflows") is not None
    assert index.resource_paths("dcim", "module-bay-types") is not None
    default = SchemaIndex(load_openapi_schema(version="4.6"))
    assert default.resource_paths("dcim", "cooling-sources") is None


@pytest.mark.parametrize(
    ("incoming", "expected"),
    [
        ({"value": "datacenter", "label": "Data Center"}, "datacenter"),
        (
            [
                {"value": "east", "label": "East"},
                {"value": "west", "label": "West"},
            ],
            ["east", "west"],
        ),
        ("datacenter", "datacenter"),
        (["east", "west"], ["east", "west"]),
        ({"nested": True}, {"nested": True}),
        (
            {
                "value": {"rack": "R1"},
                "label": "primary",
                "metadata": {"preserve": True},
            },
            {
                "value": {"rack": "R1"},
                "label": "primary",
                "metadata": {"preserve": True},
            },
        ),
        (
            {"value": {"rack": "R1"}, "label": "primary"},
            {"value": {"rack": "R1"}, "label": "primary"},
        ),
        (None, None),
    ],
)
def test_custom_field_write_value_round_trips_selection_objects(
    incoming: object, expected: object
) -> None:
    assert custom_field_write_value(incoming) == expected


def test_custom_fields_for_write_prepares_a_device_payload() -> None:
    payload = {
        "site_role": {"value": "datacenter", "label": "Data Center"},
        "regions": [
            {"value": "east", "label": "East"},
            {"value": "west", "label": "West"},
        ],
        "asset_tag": "NB-1",
        "notes": {"value": "keep", "label": "JSON"},
        "history": [{"value": "keep", "label": "JSON"}],
    }
    prepared = custom_fields_for_write(payload, selection=("site_role", "regions"))
    assert prepared == {
        "site_role": "datacenter",
        "regions": ["east", "west"],
        "asset_tag": "NB-1",
        "notes": {"value": "keep", "label": "JSON"},
        "history": [{"value": "keep", "label": "JSON"}],
    }


def test_custom_fields_for_write_preserves_unnamed_exact_shaped_json() -> None:
    payload = {"notes": {"value": "keep", "label": "JSON"}}
    assert custom_fields_for_write(payload) == payload
    assert custom_fields_for_write(payload, selection=()) == payload


def test_bulk_request_error_exposes_per_object_failures() -> None:
    body = {
        "detail": "1 of 2 objects could not be created.",
        "errors": [
            {"index": 1, "errors": {"name": ["This field is required."], "__all__": ["denied"]}},
        ],
    }
    error = RequestError(ApiResponse(status=400, text=json.dumps(body), headers={}))
    assert error.detail == "1 of 2 objects could not be created."
    assert error.entry_errors == (
        BulkOperationEntryError(
            errors={"name": ["This field is required."], "__all__": ["denied"]},
            index=1,
            id=None,
        ),
    )
    assert "1 of 2 objects could not be created." in str(error)


def test_non_bulk_request_error_keeps_the_historical_message() -> None:
    error = RequestError(
        ApiResponse(status=404, text=json.dumps({"detail": "Not found."}), headers={})
    )
    assert error.detail == "Not found."
    assert error.entry_errors == ()
    assert str(error) == "Request failed with status 404"


@pytest.mark.parametrize(
    "entry",
    [
        {"index": 1, "id": 9, "errors": {"name": ["x"]}},
        {"errors": {"name": ["x"]}},
        {"index": True, "errors": {"name": ["x"]}},
        {"index": -1, "errors": {"name": ["x"]}},
        {"id": True, "errors": {"name": ["x"]}},
        {"id": -3, "errors": {"name": ["x"]}},
        {"index": "1", "errors": {"name": ["x"]}},
        {"id": "9", "errors": {"name": ["x"]}},
    ],
)
def test_malformed_bulk_error_entries_are_dropped(entry: dict[str, object]) -> None:
    body = {"detail": "partial failure", "errors": [entry]}
    error = RequestError(ApiResponse(status=400, text=json.dumps(body), headers={}))
    assert error.entry_errors == ()
    assert str(error) == "Request failed with status 400"


def test_bulk_update_error_exposes_object_id_without_index() -> None:
    body = {
        "detail": "1 of 2 objects could not be updated.",
        "errors": [{"id": 44, "errors": {"slug": ["taken"]}}],
    }
    error = RequestError(ApiResponse(status=400, text=json.dumps(body), headers={}))
    assert error.entry_errors == (
        BulkOperationEntryError(errors={"slug": ["taken"]}, index=None, id=44),
    )


async def test_detected_47_beta2_uses_the_47_bundle_not_the_46_default() -> None:
    """A 4.7.0-beta2 server must not be silently described by the 4.6 default.

    Silent fallback is the failure that makes a wrong answer look like a right
    one: cooling paths would be missing, service filters would include lookups
    4.7 removed, and selection custom fields would be typed as scalars.
    """
    assert DEFAULT_NETBOX_VERSION == "4.6"
    client = _StatusClient("4.7.0-beta2")
    index = await resolve_index(client)
    assert client.openapi_calls == 0
    assert index.schema["info"]["version"] == "4.7.0-beta2"
    assert "/api/dcim/cooling-sources/" in index.schema["paths"]
    default = load_openapi_schema(version=DEFAULT_NETBOX_VERSION)
    assert "/api/dcim/cooling-sources/" not in default["paths"]
    assert default["info"]["version"].startswith("4.6")
