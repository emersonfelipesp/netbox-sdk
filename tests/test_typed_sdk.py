from __future__ import annotations

import io

import pytest
from pydantic import BaseModel

from netbox_sdk import (
    TypedRequestValidationError,
    TypedResponseValidationError,
    UnsupportedNetBoxVersionError,
    load_openapi_schema,
    typed_api,
)
from netbox_sdk.client import ApiResponse, RequestError
from netbox_sdk.typed_runtime import (
    TypedOperationMixin,
    validate_multipart_payload,
    validate_query,
)

pytestmark = pytest.mark.suite_sdk


def _require_email_validator() -> None:
    pytest.importorskip(
        "email_validator",
        reason="typed generated models require email-validator in the active environment",
    )


def test_versioned_openapi_bundles_are_available() -> None:
    schema_46 = load_openapi_schema(version="4.6")
    schema_45 = load_openapi_schema(version="4.5")
    schema_44 = load_openapi_schema(version="4.4")
    schema_43 = load_openapi_schema(version="4.3")

    assert str(schema_46["info"]["version"]).startswith("4.6")
    assert str(schema_45["info"]["version"]).startswith("4.5")
    assert str(schema_44["info"]["version"]).startswith("4.4")
    assert "(4.3)" in str(schema_43["info"]["version"])


def test_typed_api_rejects_unsupported_versions() -> None:
    with pytest.raises(UnsupportedNetBoxVersionError):
        typed_api("https://netbox.example.com", token="tok", netbox_version="4.2")


def test_typed_api_selects_versioned_client() -> None:
    _require_email_validator()
    api_46 = typed_api("https://netbox.example.com", token="tok", netbox_version="4.6.0")
    api_45 = typed_api("https://netbox.example.com", token="tok", netbox_version="4.5.5")
    api_44 = typed_api("https://netbox.example.com", token="tok", netbox_version="4.4.10")
    api_43 = typed_api("https://netbox.example.com", token="tok", netbox_version="4.3.7")

    assert api_46.netbox_version == "4.6"
    assert api_45.netbox_version == "4.5"
    assert api_44.netbox_version == "4.4"
    assert api_43.netbox_version == "4.3"
    assert hasattr(api_46.dcim.devices, "create")
    assert hasattr(api_45.dcim.devices, "create")
    assert hasattr(api_45.ipam.prefixes.available_ips, "create")


@pytest.mark.asyncio
async def test_typed_endpoint_validates_request_before_http_call(monkeypatch) -> None:
    _require_email_validator()
    api = typed_api("https://netbox.example.com", token="tok", netbox_version="4.5")

    async def unexpected_request(*args, **kwargs):
        raise AssertionError("request() should not be called when request validation fails")

    monkeypatch.setattr(api.client, "request", unexpected_request)

    with pytest.raises(TypedRequestValidationError):
        await api.ipam.prefixes.available_ips.create(7, body=[{"prefix_length": "invalid"}])


@pytest.mark.asyncio
async def test_typed_endpoint_validates_response_payload(monkeypatch) -> None:
    _require_email_validator()
    api = typed_api("https://netbox.example.com", token="tok", netbox_version="4.5")

    async def fake_request(method, path, **kwargs):
        assert method == "GET"
        assert path == "/api/dcim/devices/123/"
        return ApiResponse(status=200, text='{"id": "bad"}')

    monkeypatch.setattr(api.client, "request", fake_request)

    with pytest.raises(TypedResponseValidationError):
        await api.dcim.devices.get(123)


@pytest.mark.asyncio
async def test_typed_get_returns_none_on_404(monkeypatch) -> None:
    _require_email_validator()
    api = typed_api("https://netbox.example.com", token="tok", netbox_version="4.4")

    async def fake_request(method, path, **kwargs):
        return ApiResponse(status=404, text='{"detail":"Not found."}')

    monkeypatch.setattr(api.client, "request", fake_request)

    assert await api.dcim.devices.get(404) is None


@pytest.mark.asyncio
async def test_typed_non_get_endpoint_raises_on_404(monkeypatch) -> None:
    _require_email_validator()
    api = typed_api("https://netbox.example.com", token="tok", netbox_version="4.4")

    async def fake_request(method, path, **kwargs):
        assert method == "GET"
        assert path == "/api/ipam/prefixes/404/available-ips/"
        return ApiResponse(status=404, text='{"detail":"Not found."}')

    monkeypatch.setattr(api.client, "request", fake_request)

    with pytest.raises(RequestError):
        await api.ipam.prefixes.available_ips.list(404)


def test_validate_query_preserves_array_parameters() -> None:
    _require_email_validator()
    query = validate_query(
        None,
        {
            "tag": ["core", "edge"],
            "limit": 50,
            "brief": True,
        },
        method="GET",
        path="/api/dcim/devices/",
        version="4.5",
    )

    assert query == {
        "tag": ["core", "edge"],
        "limit": "50",
        "brief": "True",
    }


class _BinaryUploadRequest(BaseModel):
    file: bytes


def test_validate_multipart_payload_preserves_non_utf8_binary() -> None:
    payload = validate_multipart_payload(
        _BinaryUploadRequest,
        {"file": b"\xff\x00\x80"},
        binary_field_names=("file",),
        method="POST",
        path="/api/extras/scripts/upload/",
        version="4.6",
    )

    assert isinstance(payload["file"], io.BytesIO)
    assert payload["file"].read() == b"\xff\x00\x80"


def test_validate_multipart_payload_preserves_named_file_tuple() -> None:
    source = io.BytesIO(b"print('ok')")
    value = ("health.py", source, "text/x-python")

    payload = validate_multipart_payload(
        _BinaryUploadRequest,
        {"file": value},
        binary_field_names=("file",),
        method="POST",
        path="/api/extras/scripts/upload/",
        version="4.6",
    )

    assert payload["file"] is value


def test_v46_generated_device_query_models_keep_list_filters() -> None:
    _require_email_validator()
    from netbox_sdk.typed_versions.v4_6 import (
        DcimDevicesDetailGetQuery,
        DcimDevicesRootGetQuery,
    )

    root_aliases = {field.alias for field in DcimDevicesRootGetQuery.model_fields.values()}
    detail_aliases = {field.alias for field in DcimDevicesDetailGetQuery.model_fields.values()}

    assert {"tag__any", "tag_id__any"} <= root_aliases
    assert "tag__any" not in detail_aliases
    assert "tag_id__any" not in detail_aliases


@pytest.mark.asyncio
async def test_v46_typed_script_uploads_reach_client_as_multipart(monkeypatch) -> None:
    _require_email_validator()
    api = typed_api("https://netbox.example.com", token="tok", netbox_version="4.6.6")
    captured: list[tuple[str, str, dict[str, object]]] = []

    async def fake_response(
        self,
        method: str,
        path: str,
        *,
        query,
        payload,
        return_none_on_404: bool,
    ) -> None:
        assert query is None
        assert return_none_on_404 is False
        captured.append((method, path, payload))
        return None

    monkeypatch.setattr(TypedOperationMixin, "_typed_json_response", fake_response)

    await api.extras.scripts.upload.create(body={"file": b"\xff\x00"})
    source = io.BytesIO(b"print('patched')")
    await api.extras.scripts.upload_id.partial_update(
        "health.py",
        body={"file": ("health.py", source, "text/x-python")},
    )

    assert [(method, path) for method, path, _ in captured] == [
        ("POST", "/api/extras/scripts/upload/"),
        ("PATCH", "/api/extras/scripts/upload/health.py/"),
    ]
    for _, _, payload in captured:
        clean_payload, form = api.client._extract_files(payload)
        assert clean_payload == {}
        assert form is not None


@pytest.mark.asyncio
async def test_typed_action_endpoint_supports_other_versions(monkeypatch) -> None:
    _require_email_validator()
    api = typed_api("https://netbox.example.com", token="tok", netbox_version="4.3")

    async def fake_request(method, path, **kwargs):
        assert method == "GET"
        assert path == "/api/ipam/prefixes/5/available-ips/"
        return ApiResponse(status=200, text='[{"address":"10.0.0.1/24","family":4}]')

    monkeypatch.setattr(api.client, "request", fake_request)

    result = await api.ipam.prefixes.available_ips.list(5)
    assert result[0].address == "10.0.0.1/24"


def test_v47_service_write_contract_matches_upstream_and_v46_migration_is_pinned() -> None:
    """Pin NetBox 4.7's service write contract and the 4.6 -> 4.7 migration hazard.

    NetBox 4.7 replaces the single ``protocol``/``ports`` pair with
    ``port_mappings``. Upstream's *writable* service models deliberately drop
    ``protocol`` (the bundled schema documents it as "Deprecated; use
    port_mappings. Reported only for single-protocol services", and
    ``POST /api/ipam/services/`` references ``WritableServiceRequest``), while the
    read models keep it. The generated bindings mirror that faithfully.

    Do NOT "fix" this by overlaying ``protocol`` back onto the writable models:
    that would make the SDK send a field 4.7's write contract does not accept and
    would break provenance fidelity to the pinned upstream artifact.

    The real migration hazard is that 4.6's writable model *did* accept
    ``protocol``, and Pydantic's default ``extra='ignore'`` silently discards it
    on 4.7. This test pins that behaviour so a future regeneration cannot change
    it unnoticed, and so the documented migration note stays true.
    """
    from netbox_sdk.models.v4_6 import WritableServiceRequest as WritableV46
    from netbox_sdk.models.v4_7 import Service as ServiceV47
    from netbox_sdk.models.v4_7 import ServiceRequest as ServiceRequestV47
    from netbox_sdk.models.v4_7 import WritableServiceRequest as WritableV47

    # 4.6 accepted the legacy pair on write.
    assert "protocol" in WritableV46.model_fields
    assert "ports" in WritableV46.model_fields

    # 4.7 writable: protocol gone, ports retained, port_mappings added.
    assert "protocol" not in WritableV47.model_fields
    assert "ports" in WritableV47.model_fields
    assert "port_mappings" in WritableV47.model_fields

    # 4.7 read side still reports the deprecated fields.
    assert "protocol" in ServiceV47.model_fields
    assert "protocol" in ServiceRequestV47.model_fields

    # The migration hazard, pinned: a 4.6-shaped payload loses `protocol`.
    migrated = WritableV47(
        name="ssh",
        parent_object_id=1,
        parent_object_type="dcim.device",
        protocol="tcp",
        ports=[22],
    )
    dumped = migrated.model_dump(exclude_unset=True)
    assert "protocol" not in dumped
    assert dumped["ports"] == [22]

    # The 4.7-native spelling round-trips intact.
    native = WritableV47(
        name="dns",
        parent_object_id=1,
        parent_object_type="dcim.device",
        port_mappings=["tcp/53", "udp/53"],
    )
    assert native.model_dump(exclude_unset=True)["port_mappings"] == ["tcp/53", "udp/53"]
