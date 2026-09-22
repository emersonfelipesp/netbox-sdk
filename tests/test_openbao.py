"""Fixed transport oracles for the maintained netbox-openbao contract."""

from __future__ import annotations

import json
import stat
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from netbox_cli import openbao as openbao_cli
from netbox_sdk.client import ApiResponse, NetBoxApiClient
from netbox_sdk.config import Config
from netbox_sdk.exceptions import RequestError, ResponseSizeLimitError
from netbox_sdk.openbao import (
    OpenBaoClient,
    build_openbao_schema_index,
    find_openbao_action,
    find_openbao_resource,
    openbao_actions,
    openbao_resources,
)
from netbox_sdk.plugins import official_plugin

pytestmark = pytest.mark.suite_sdk

EXPECTED_COLLECTIONS = {
    "clusters",
    "engines",
    "policies",
    "credentials",
    "assignments",
    "type-schemas",
    "access-logs",
    "administration-logs",
    "procedure-runs",
    "settings",
}

# Independent route oracle transcribed from netbox-openbao origin/main 8a7f9a2.
EXPECTED_ACTION_PATHS = {
    "engine.health": "engines/{id}/health/",
    "engine.run-procedure": "engines/{id}/run-procedure/",
    "credential.resolve-automation": "credentials/resolve-automation/",
    "credential.reveal": "credentials/{id}/reveal/",
    "credential.rotate": "credentials/{id}/rotate/",
    "credential.stage": "credentials/{id}/stage/",
    "credential.promote": "credentials/{id}/promote/",
    "credential.discard": "credentials/{id}/discard/",
    "credential.versions": "credentials/{id}/versions/",
    "credential.quick-add-ssh": "credentials/quick-add-ssh/",
    "cluster.health": "clusters/{id}/health/",
    "cluster.capabilities": "clusters/{id}/capabilities/",
    "cluster.state": "clusters/{id}/state/",
    "cluster.initialize": "clusters/{id}/initialize/",
    "cluster.raft-join": "clusters/{id}/raft/join/",
    "cluster.unseal": "clusters/{id}/unseal/",
    "cluster.seal": "clusters/{id}/seal/",
    "cluster.raft-remove-peer": "clusters/{id}/raft/remove-peer/",
    "cluster.raft-snapshot-download": "clusters/{id}/raft/snapshot/",
    "cluster.raft-snapshot-restore": "clusters/{id}/raft/snapshot/restore/",
    "cluster.raft-snapshot-restore-force": "clusters/{id}/raft/snapshot/restore-force/",
    "cluster.access-resources": "clusters/{id}/access-resources/",
    "cluster.access-preview": "clusters/{id}/access-resources/preview/",
    "cluster.access-execute": "clusters/{id}/access-resources/execute/",
    "cluster.secret-engines": "clusters/{id}/secret-engines/",
    "cluster.secret-engine-configuration": "clusters/{id}/secret-engines/configuration/",
    "cluster.secret-engine-tuning": "clusters/{id}/secret-engines/tuning/",
    "cluster.secret-engine-enable": "clusters/{id}/secret-engines/enable/",
    "cluster.secret-engine-tune": "clusters/{id}/secret-engines/tune/",
    "cluster.secret-engine-remount": "clusters/{id}/secret-engines/remount/",
    "cluster.secret-engine-remount-status": "clusters/{id}/secret-engines/remount-status/",
    "cluster.secret-engine-disable": "clusters/{id}/secret-engines/disable/",
    "cluster.secret-operations": "clusters/{id}/secret-operations/",
    "cluster.secret-operation-execute": "clusters/{id}/secret-operations/execute/",
    "cluster.secret-engine-journeys": "clusters/{id}/secret-engine-journeys/",
    "cluster.secret-engine-journey-execute": "clusters/{id}/secret-engine-journeys/execute/",
    "cluster.final-resources": "clusters/{id}/final-resources/",
    "cluster.final-conformance": "clusters/{id}/final-conformance/",
    "cluster.final-resource-operate": "clusters/{id}/final-resources/operate/",
    "cluster.auth-methods": "clusters/{id}/auth-methods/",
    "cluster.auth-method": "clusters/{id}/auth-methods/{mount_path}/",
    "cluster.auth-remount": "clusters/{id}/auth-remount/",
    "cluster.auth-remount-status": "clusters/{id}/auth-remount/{migration_id}/",
    "cluster.auth-config": "clusters/{id}/auth-config/{mount_path}/",
    "cluster.auth-resource-list": "clusters/{id}/auth-resources/{mount_path}/{resource_key}/",
    "cluster.auth-resource": "clusters/{id}/auth-resources/{mount_path}/{resource_key}/{name}/",
    "cluster.approle-secret-id": "clusters/{id}/auth-approle/{mount_path}/{role_name}/secret-id/",
    "cluster.approle-role-id": "clusters/{id}/auth-approle/{mount_path}/{role_name}/role-id/",
    "cluster.approle-secret-id-accessor": "clusters/{id}/auth-approle/{mount_path}/{role_name}/secret-id-accessor/",
    "cluster.auth-login": "clusters/{id}/auth-login/{mount_path}/",
    "cluster.auth-oidc-start": "clusters/{id}/auth-oidc/{mount_path}/start/",
    "cluster.auth-oidc-poll": "clusters/{id}/auth-oidc/{mount_path}/poll/",
    "cluster.auth-mfa-validate": "clusters/{id}/auth-mfa/validate/",
    "cluster.auth-mfa-methods": "clusters/{id}/auth-mfa/methods/",
    "cluster.auth-mfa-method": "clusters/{id}/auth-mfa/methods/{method_type}/{method_id}/",
    "cluster.auth-mfa-method-create": "clusters/{id}/auth-mfa/methods/{method_type}/",
    "cluster.auth-mfa-totp-self": "clusters/{id}/auth-mfa/totp/{method_id}/self/",
    "cluster.auth-mfa-totp-self-reset": "clusters/{id}/auth-mfa/totp/{method_id}/self/reset/",
    "cluster.auth-mfa-totp-entity": "clusters/{id}/auth-mfa/totp/{method_id}/entities/{entity_id}/",
    "cluster.auth-mfa-enforcements": "clusters/{id}/auth-mfa/enforcements/",
    "cluster.auth-mfa-enforcement": "clusters/{id}/auth-mfa/enforcements/{name}/",
    "cluster.auth-token": "clusters/{id}/auth-tokens/{operation}/",
}

EXPECTED_GET_ONLY = {
    "engine.health",
    "credential.versions",
    "cluster.health",
    "cluster.capabilities",
    "cluster.state",
    "cluster.access-resources",
    "cluster.secret-engines",
    "cluster.secret-operations",
    "cluster.secret-engine-journeys",
    "cluster.final-resources",
    "cluster.final-conformance",
    "cluster.auth-remount-status",
    "cluster.auth-mfa-methods",
    "cluster.auth-mfa-enforcements",
}
EXPECTED_MULTI_METHODS = {
    "credential.reveal": ("GET", "POST"),
    "cluster.raft-snapshot-download": ("GET", "POST"),
    "cluster.auth-methods": ("GET", "POST"),
    "cluster.auth-method": ("GET", "POST", "DELETE"),
    "cluster.auth-config": ("GET", "POST"),
    "cluster.auth-resource-list": ("GET", "POST", "DELETE"),
    "cluster.auth-resource": ("GET", "POST", "DELETE"),
    "cluster.approle-role-id": ("GET", "POST"),
    "cluster.approle-secret-id-accessor": ("POST", "DELETE"),
    "cluster.auth-mfa-method": ("GET", "POST", "DELETE"),
    "cluster.auth-mfa-totp-entity": ("POST", "DELETE"),
    "cluster.auth-mfa-enforcement": ("GET", "POST", "DELETE"),
}
EXPECTED_MATERIAL = {
    "credential.resolve-automation",
    "credential.reveal",
    "credential.rotate",
    "credential.stage",
    "credential.promote",
    "credential.discard",
    "credential.quick-add-ssh",
    "cluster.initialize",
    "cluster.raft-join",
    "cluster.unseal",
    "cluster.access-execute",
    "cluster.secret-operation-execute",
    "cluster.secret-engine-journey-execute",
    "cluster.final-resource-operate",
    "cluster.approle-secret-id",
    "cluster.approle-role-id",
    "cluster.approle-secret-id-accessor",
    "cluster.auth-login",
    "cluster.auth-oidc-start",
    "cluster.auth-oidc-poll",
    "cluster.auth-mfa-validate",
    "cluster.auth-mfa-totp-self",
    "cluster.auth-mfa-totp-self-reset",
    "cluster.auth-token",
}
EXPECTED_BINARY = {
    "cluster.raft-snapshot-download": "download",
    "cluster.raft-snapshot-restore": "upload",
    "cluster.raft-snapshot-restore-force": "upload",
}


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def request(self, method: str, path: str, **kwargs: Any) -> ApiResponse:
        self.calls.append({"kind": "json", "method": method, "path": path, **kwargs})
        return ApiResponse(status=200, text=json.dumps({"ok": True}), headers={})

    async def request_one_shot(self, method: str, path: str, **kwargs: Any) -> ApiResponse:
        self.calls.append({"kind": "json", "method": method, "path": path, **kwargs})
        return ApiResponse(status=200, text=json.dumps({"ok": True}), headers={})

    async def request_binary(self, method: str, path: str, **kwargs: Any) -> bytes:
        self.calls.append({"kind": "download", "method": method, "path": path, **kwargs})
        return b"snapshot"

    async def request_binary_upload(self, method: str, path: str, **kwargs: Any) -> ApiResponse:
        self.calls.append({"kind": "upload", "method": method, "path": path, **kwargs})
        return ApiResponse(status=202, text="{}", headers={})


class _ChunkedContent:
    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = chunks

    async def iter_chunked(self, size: int):
        del size
        for chunk in self.chunks:
            yield chunk


class _TransportResponse:
    def __init__(self, *, status: int = 200, chunks: list[bytes] | None = None) -> None:
        self.status = status
        self.headers: dict[str, str] = {}
        self.charset = "utf-8"
        self.content = _ChunkedContent(chunks or [b"{}"])

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


class _TransportSession:
    def __init__(self, response: _TransportResponse) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def request(self, **kwargs: Any) -> _TransportResponse:
        self.calls.append(kwargs)
        return self.response


async def _async_value(value: object):
    return value


def test_openbao_is_an_official_plugin() -> None:
    plugin = official_plugin("netbox-openbao")
    assert plugin is not None
    assert plugin.sdk_module == "netbox_sdk.openbao"
    assert plugin.cli_command == "openbao"


def test_fixed_collection_inventory_and_restrictions() -> None:
    assert {spec.key for spec in openbao_resources()} == EXPECTED_COLLECTIONS
    assert find_openbao_resource("access-logs").supported_actions == ("list", "get")
    assert "create" in find_openbao_resource("credentials").supported_actions
    index = build_openbao_schema_index()
    assert index.resource_paths("plugins", "openbao/credentials") is not None


def test_fixed_action_inventory_matches_canonical_routes() -> None:
    actual = {
        spec.key: spec.path_template.removeprefix("/api/plugins/openbao/")
        for spec in openbao_actions()
    }
    assert actual == EXPECTED_ACTION_PATHS
    assert find_openbao_action("credential.quick-add-ssh").planned is False
    assert not any("generated-key" in key for key in actual)


def test_fixed_action_methods_material_and_binary_are_independent_oracles() -> None:
    actions = {spec.key: spec for spec in openbao_actions()}
    for key, spec in actions.items():
        expected_methods = EXPECTED_MULTI_METHODS.get(
            key, ("GET",) if key in EXPECTED_GET_ONLY else ("POST",)
        )
        assert spec.methods == expected_methods, key
        assert spec.material is (key in EXPECTED_MATERIAL), key
        assert spec.binary == EXPECTED_BINARY.get(key, "none"), key


def test_fixed_collection_crud_matrix_is_independent() -> None:
    actual = {spec.key: spec.supported_actions for spec in openbao_resources()}
    mutable = (
        "list",
        "get",
        "create",
        "update",
        "patch",
        "delete",
        "bulk-update",
        "bulk-patch",
        "bulk-delete",
    )
    assert actual == {
        "clusters": mutable,
        "engines": mutable,
        "policies": mutable,
        "credentials": mutable,
        "assignments": mutable,
        "type-schemas": mutable,
        "access-logs": ("list", "get"),
        "administration-logs": ("list", "get"),
        "procedure-runs": ("list", "get"),
        "settings": mutable,
    }


async def test_json_action_forwards_exact_transport_without_cache() -> None:
    transport = FakeClient()
    client = OpenBaoClient(transport)  # type: ignore[arg-type]
    await client.request_action(
        "cluster.auth-resource",
        method="POST",
        path_parameters={
            "id": 7,
            "mount_path": "userpass",
            "resource_key": "users",
            "name": "alice",
        },
        query={"list": "true"},
        payload={"policies": ["ops"]},
        headers={"If-Match": "etag"},
    )
    assert transport.calls == [
        {
            "kind": "json",
            "method": "POST",
            "path": "/api/plugins/openbao/clusters/7/auth-resources/userpass/users/alice/",
            "query": {"list": "true"},
            "payload": {"policies": ["ops"]},
            "headers": {"If-Match": "etag"},
        }
    ]


async def test_generated_key_uses_standard_credentials_create_payload() -> None:
    transport = FakeClient()
    client = OpenBaoClient(transport)  # type: ignore[arg-type]
    await client.request_resource(
        "credentials",
        "create",
        payload={"name": "router", "generate_ssh_key": True, "ssh_key_type": "ed25519"},
    )
    call = transport.calls[0]
    assert call["method"] == "POST"
    assert call["path"] == "/api/plugins/openbao/credentials/"
    assert call["payload"]["generate_ssh_key"] is True


async def test_binary_snapshot_helpers_are_bounded_and_exact(tmp_path: Path) -> None:
    transport = FakeClient()
    client = OpenBaoClient(transport)  # type: ignore[arg-type]
    source = tmp_path / "snapshot.snap"
    source.write_bytes(b"raft")
    assert await client.download_snapshot(3, max_bytes=99) == b"snapshot"
    await client.upload_snapshot(
        3,
        source,
        force=True,
        reason="recovery",
        confirmation="FORCE RESTORE SNAPSHOT primary",
        openbao_cluster_id="raft-cluster-a",
        configuration_index=17,
        max_bytes=99,
    )
    assert transport.calls[0]["path"] == "/api/plugins/openbao/clusters/3/raft/snapshot/"
    assert transport.calls[0]["max_response_bytes"] == 99
    assert transport.calls[1]["path"].endswith("/raft/snapshot/restore-force/")
    assert transport.calls[1]["max_request_bytes"] == 99
    assert transport.calls[1]["headers"]["X-OpenBao-Raft-Index"] == "17"


async def test_invalid_path_values_and_snapshot_metadata_fail_before_transport(
    tmp_path: Path,
) -> None:
    transport = FakeClient()
    client = OpenBaoClient(transport)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Unsafe"):
        await client.request_action(
            "cluster.auth-method", path_parameters={"id": 1, "mount_path": "../root"}
        )
    source = tmp_path / "snapshot.snap"
    source.write_bytes(b"12345")
    with pytest.raises(ValueError, match="must start"):
        await client.upload_snapshot(
            1,
            source,
            reason="recovery",
            confirmation="FORCE RESTORE SNAPSHOT primary",
            openbao_cluster_id="raft-cluster-a",
            configuration_index=17,
        )
    assert transport.calls == []


def test_cli_write_confirmation_precedes_client_creation(monkeypatch: pytest.MonkeyPatch) -> None:
    created = False

    def forbidden_client() -> None:
        nonlocal created
        created = True
        raise AssertionError("client was created before confirmation")

    monkeypatch.setattr(openbao_cli, "_get_client", forbidden_client)
    result = CliRunner().invoke(
        openbao_cli.openbao_app,
        [
            "actions",
            "credential-rotate",
            "--id",
            "12",
            "--body-json",
            '{"secret_data":{"password":"new"}}',
        ],
    )
    assert result.exit_code != 0
    assert created is False


def test_material_get_confirmation_precedes_client_creation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        openbao_cli, "_get_client", lambda: pytest.fail("material GET created a client")
    )
    result = CliRunner().invoke(
        openbao_cli.openbao_app,
        ["actions", "credential-reveal", "--id", "12"],
    )
    assert result.exit_code != 0


def test_private_snapshot_write_is_exclusive_and_mode_0600(tmp_path: Path) -> None:
    output = tmp_path / "cluster.snap"
    openbao_cli._write_private_exclusive(output, b"snapshot")
    assert output.read_bytes() == b"snapshot"
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
    with pytest.raises(Exception, match="already exists"):
        openbao_cli._write_private_exclusive(output, b"replacement")
    assert output.read_bytes() == b"snapshot"


def test_private_snapshot_write_removes_partial_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    output = tmp_path / "cluster.snap"

    def fail_sync(descriptor: int) -> None:
        raise RuntimeError(f"fsync failed for {descriptor}")

    monkeypatch.setattr(openbao_cli.os, "fsync", fail_sync)
    with pytest.raises(RuntimeError, match="fsync failed"):
        openbao_cli._write_private_exclusive(output, b"snapshot")
    assert not output.exists()


async def test_one_shot_transport_disables_redirects_preserves_auth_and_does_not_replay(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    session = _TransportSession(_TransportResponse(status=403, chunks=[b"invalid v2 token"]))
    client = NetBoxApiClient(
        Config(
            base_url="https://netbox.example.com",
            token_version="v2",
            token_key="key",
            token_secret="secret",
        )
    )
    client.persistent_headers = {"Authorization": "Bearer persistent"}
    monkeypatch.setattr(client, "_get_session", lambda: _async_value(session))
    response = await client.request_one_shot(
        "GET", "/api/plugins/openbao/credentials/", headers={"authorization": "Bearer call"}
    )
    assert response.status == 403
    assert len(session.calls) == 1
    assert session.calls[0]["allow_redirects"] is False
    assert session.calls[0]["headers"]["Authorization"] == "Bearer call"


async def test_one_shot_write_defensively_invalidates_after_transport_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    client = NetBoxApiClient(Config(base_url="https://netbox.example.com"))
    invalidated: list[tuple[str, object]] = []

    async def failed_request(*args: object, **kwargs: object) -> ApiResponse:
        del args, kwargs
        raise RuntimeError("connection lost")

    async def invalidate(path: str, payload: object) -> None:
        invalidated.append((path, payload))

    monkeypatch.setattr(client, "_request_once", failed_request)
    monkeypatch.setattr(client, "_get_session", lambda: _async_value(object()))
    monkeypatch.setattr(client, "_safe_invalidate_related_cache", invalidate)
    payload = {"name": "router"}
    with pytest.raises(RuntimeError, match="connection lost"):
        await client.request_one_shot("POST", "/api/plugins/openbao/credentials/", payload=payload)
    assert invalidated == [("/api/plugins/openbao/credentials/", payload)]


async def test_binary_upload_streams_bounded_error_and_invalidates(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    source = tmp_path / "snapshot.snap"
    source.write_bytes(b"raft")
    session = _TransportSession(_TransportResponse(status=500, chunks=[b'{"detail":"failed"}']))
    client = NetBoxApiClient(Config(base_url="https://netbox.example.com"))
    invalidated: list[str] = []

    async def invalidate(path: str, payload: object) -> None:
        del payload
        invalidated.append(path)

    monkeypatch.setattr(client, "_get_session", lambda: _async_value(session))
    monkeypatch.setattr(client, "_safe_invalidate_related_cache", invalidate)
    with pytest.raises(RequestError):
        await client.request_binary_upload(
            "POST",
            "/api/plugins/openbao/clusters/1/raft/snapshot/restore/",
            source=source,
            max_request_bytes=4,
        )
    assert session.calls[0]["allow_redirects"] is False
    assert invalidated == ["/api/plugins/openbao/clusters/1/raft/snapshot/restore/"]


async def test_binary_upload_rejects_streamed_oversized_response(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    source = tmp_path / "snapshot.snap"
    source.write_bytes(b"raft")
    session = _TransportSession(_TransportResponse(chunks=[b"123", b"456"]))
    client = NetBoxApiClient(Config(base_url="https://netbox.example.com", max_response_bytes=5))
    monkeypatch.setattr(client, "_get_session", lambda: _async_value(session))
    with pytest.raises(ResponseSizeLimitError):
        await client.request_binary_upload(
            "POST",
            "/api/plugins/openbao/clusters/1/raft/snapshot/restore/",
            source=source,
            max_request_bytes=4,
        )


async def test_binary_upload_rejects_symlink_and_oversized_descriptor(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    source = tmp_path / "snapshot.snap"
    source.write_bytes(b"12345")
    link = tmp_path / "linked.snap"
    link.symlink_to(source)
    client = NetBoxApiClient(Config(base_url="https://netbox.example.com"))
    monkeypatch.setattr(
        client, "_get_session", lambda: pytest.fail("invalid source created a session")
    )
    with pytest.raises(ValueError, match="between 1 and 4"):
        await client.request_binary_upload(
            "POST",
            "/api/plugins/openbao/clusters/1/raft/snapshot/restore/",
            source=source,
            max_request_bytes=4,
        )
    with pytest.raises(ValueError, match="regular, readable"):
        await client.request_binary_upload(
            "POST",
            "/api/plugins/openbao/clusters/1/raft/snapshot/restore/",
            source=link,
            max_request_bytes=10,
        )
