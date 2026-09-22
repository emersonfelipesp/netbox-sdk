"""Fixed, first-class transport contract for ``netbox-openbao``.

The inventory is intentionally maintained independently from runtime OpenAPI
discovery.  It is the review boundary for secret material and OpenBao
administration: callers never need to assemble a plugin URL themselves.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from netbox_sdk.client import ApiResponse, NetBoxApiClient
from netbox_sdk.http_cache import QueryParams
from netbox_sdk.schema import SchemaIndex, parse_group_resource
from netbox_sdk.services import resolve_dynamic_request

OPENBAO_BASE = "/api/plugins/openbao"
DEFAULT_SNAPSHOT_LIMIT = 512 * 1024 * 1024
_PARAMETER_RE = re.compile(r"\{([a-z][a-z0-9_]*)\}")
_SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@-]{0,199}$")


class OpenBaoResourceSpec(BaseModel):
    """One canonical plugin collection and its exact CRUD surface."""

    model_config = ConfigDict(frozen=True)
    key: str
    command: str
    list_methods: tuple[str, ...]
    detail_methods: tuple[str, ...]

    @property
    def list_path(self) -> str:
        return f"{OPENBAO_BASE}/{self.key}/"

    @property
    def detail_path(self) -> str:
        return f"{self.list_path}{{id}}/"

    @property
    def resource(self) -> str:
        group, resource = parse_group_resource(self.list_path)
        if group != "plugins" or resource is None:
            raise ValueError(f"Invalid OpenBao list path: {self.list_path}")
        return resource

    @property
    def supported_actions(self) -> tuple[str, ...]:
        actions: list[str] = []
        list_methods, detail_methods = set(self.list_methods), set(self.detail_methods)
        for method, action, methods in (
            ("GET", "list", list_methods),
            ("GET", "get", detail_methods),
            ("POST", "create", list_methods),
            ("PUT", "update", detail_methods),
            ("PATCH", "patch", detail_methods),
            ("DELETE", "delete", detail_methods),
            ("PUT", "bulk-update", list_methods),
            ("PATCH", "bulk-patch", list_methods),
            ("DELETE", "bulk-delete", list_methods),
        ):
            if method in methods:
                actions.append(action)
        return tuple(actions)


class OpenBaoActionSpec(BaseModel):
    """A named custom REST action with an exact path and wire shape."""

    model_config = ConfigDict(frozen=True)
    key: str
    command: str
    methods: tuple[str, ...]
    path_template: str
    material: bool = False
    binary: Literal["none", "download", "upload"] = "none"
    planned: bool = False

    @property
    def path_parameters(self) -> tuple[str, ...]:
        return tuple(_PARAMETER_RE.findall(self.path_template))


def _resource(
    key: str,
    *,
    command: str | None = None,
    read_only: bool = False,
) -> OpenBaoResourceSpec:
    if read_only:
        return OpenBaoResourceSpec(
            key=key, command=command or key, list_methods=("GET",), detail_methods=("GET",)
        )
    return OpenBaoResourceSpec(
        key=key,
        command=command or key,
        list_methods=("GET", "POST", "PUT", "PATCH", "DELETE"),
        detail_methods=("GET", "PUT", "PATCH", "DELETE"),
    )


OPENBAO_RESOURCES: tuple[OpenBaoResourceSpec, ...] = (
    _resource("clusters"),
    _resource("engines"),
    _resource("policies"),
    _resource("credentials"),
    _resource("assignments"),
    _resource("type-schemas"),
    _resource("access-logs", read_only=True),
    _resource("administration-logs", read_only=True),
    _resource("procedure-runs", read_only=True),
    _resource("settings"),
)


def _action(
    key: str,
    methods: str | tuple[str, ...],
    path: str,
    *,
    material: bool = False,
    binary: Literal["none", "download", "upload"] = "none",
    planned: bool = False,
) -> OpenBaoActionSpec:
    normalized_methods = (methods,) if isinstance(methods, str) else methods
    return OpenBaoActionSpec(
        key=key,
        command=key.replace(".", "-"),
        methods=tuple(method.upper() for method in normalized_methods),
        path_template=f"{OPENBAO_BASE}/{path.lstrip('/')}",
        material=material,
        binary=binary,
        planned=planned,
    )


# Fixed from netbox-openbao origin/main at 8a7f9a2 (2026-09-22), plus the
# atomic quick-add route implemented by the coordinated plugin change.
OPENBAO_ACTIONS: tuple[OpenBaoActionSpec, ...] = (
    _action("engine.health", "GET", "engines/{id}/health/"),
    _action("engine.run-procedure", "POST", "engines/{id}/run-procedure/"),
    _action(
        "credential.resolve-automation", "POST", "credentials/resolve-automation/", material=True
    ),
    _action("credential.reveal", ("GET", "POST"), "credentials/{id}/reveal/", material=True),
    _action("credential.rotate", "POST", "credentials/{id}/rotate/", material=True),
    _action("credential.stage", "POST", "credentials/{id}/stage/", material=True),
    _action("credential.promote", "POST", "credentials/{id}/promote/", material=True),
    _action("credential.discard", "POST", "credentials/{id}/discard/", material=True),
    _action("credential.versions", "GET", "credentials/{id}/versions/"),
    _action("credential.quick-add-ssh", "POST", "credentials/quick-add-ssh/", material=True),
    _action("cluster.health", "GET", "clusters/{id}/health/"),
    _action("cluster.capabilities", "GET", "clusters/{id}/capabilities/"),
    _action("cluster.state", "GET", "clusters/{id}/state/"),
    _action("cluster.initialize", "POST", "clusters/{id}/initialize/", material=True),
    _action("cluster.raft-join", "POST", "clusters/{id}/raft/join/", material=True),
    _action("cluster.unseal", "POST", "clusters/{id}/unseal/", material=True),
    _action("cluster.seal", "POST", "clusters/{id}/seal/"),
    _action("cluster.raft-remove-peer", "POST", "clusters/{id}/raft/remove-peer/"),
    _action(
        "cluster.raft-snapshot-download",
        ("GET", "POST"),
        "clusters/{id}/raft/snapshot/",
        binary="download",
    ),
    _action(
        "cluster.raft-snapshot-restore",
        "POST",
        "clusters/{id}/raft/snapshot/restore/",
        binary="upload",
    ),
    _action(
        "cluster.raft-snapshot-restore-force",
        "POST",
        "clusters/{id}/raft/snapshot/restore-force/",
        binary="upload",
    ),
    _action("cluster.access-resources", "GET", "clusters/{id}/access-resources/"),
    _action("cluster.access-preview", "POST", "clusters/{id}/access-resources/preview/"),
    _action(
        "cluster.access-execute", "POST", "clusters/{id}/access-resources/execute/", material=True
    ),
    _action("cluster.secret-engines", "GET", "clusters/{id}/secret-engines/"),
    _action(
        "cluster.secret-engine-configuration", "POST", "clusters/{id}/secret-engines/configuration/"
    ),
    _action("cluster.secret-engine-tuning", "POST", "clusters/{id}/secret-engines/tuning/"),
    _action("cluster.secret-engine-enable", "POST", "clusters/{id}/secret-engines/enable/"),
    _action("cluster.secret-engine-tune", "POST", "clusters/{id}/secret-engines/tune/"),
    _action("cluster.secret-engine-remount", "POST", "clusters/{id}/secret-engines/remount/"),
    _action(
        "cluster.secret-engine-remount-status",
        "POST",
        "clusters/{id}/secret-engines/remount-status/",
    ),
    _action("cluster.secret-engine-disable", "POST", "clusters/{id}/secret-engines/disable/"),
    _action("cluster.secret-operations", "GET", "clusters/{id}/secret-operations/"),
    _action(
        "cluster.secret-operation-execute",
        "POST",
        "clusters/{id}/secret-operations/execute/",
        material=True,
    ),
    _action("cluster.secret-engine-journeys", "GET", "clusters/{id}/secret-engine-journeys/"),
    _action(
        "cluster.secret-engine-journey-execute",
        "POST",
        "clusters/{id}/secret-engine-journeys/execute/",
        material=True,
    ),
    _action("cluster.final-resources", "GET", "clusters/{id}/final-resources/"),
    _action("cluster.final-conformance", "GET", "clusters/{id}/final-conformance/"),
    _action(
        "cluster.final-resource-operate",
        "POST",
        "clusters/{id}/final-resources/operate/",
        material=True,
    ),
    _action("cluster.auth-methods", ("GET", "POST"), "clusters/{id}/auth-methods/"),
    _action(
        "cluster.auth-method", ("GET", "POST", "DELETE"), "clusters/{id}/auth-methods/{mount_path}/"
    ),
    _action("cluster.auth-remount", "POST", "clusters/{id}/auth-remount/"),
    _action("cluster.auth-remount-status", "GET", "clusters/{id}/auth-remount/{migration_id}/"),
    _action("cluster.auth-config", ("GET", "POST"), "clusters/{id}/auth-config/{mount_path}/"),
    _action(
        "cluster.auth-resource-list",
        ("GET", "POST", "DELETE"),
        "clusters/{id}/auth-resources/{mount_path}/{resource_key}/",
    ),
    _action(
        "cluster.auth-resource",
        ("GET", "POST", "DELETE"),
        "clusters/{id}/auth-resources/{mount_path}/{resource_key}/{name}/",
    ),
    _action(
        "cluster.approle-secret-id",
        "POST",
        "clusters/{id}/auth-approle/{mount_path}/{role_name}/secret-id/",
        material=True,
    ),
    _action(
        "cluster.approle-role-id",
        ("GET", "POST"),
        "clusters/{id}/auth-approle/{mount_path}/{role_name}/role-id/",
        material=True,
    ),
    _action(
        "cluster.approle-secret-id-accessor",
        ("POST", "DELETE"),
        "clusters/{id}/auth-approle/{mount_path}/{role_name}/secret-id-accessor/",
        material=True,
    ),
    _action("cluster.auth-login", "POST", "clusters/{id}/auth-login/{mount_path}/", material=True),
    _action(
        "cluster.auth-oidc-start",
        "POST",
        "clusters/{id}/auth-oidc/{mount_path}/start/",
        material=True,
    ),
    _action(
        "cluster.auth-oidc-poll",
        "POST",
        "clusters/{id}/auth-oidc/{mount_path}/poll/",
        material=True,
    ),
    _action("cluster.auth-mfa-validate", "POST", "clusters/{id}/auth-mfa/validate/", material=True),
    _action("cluster.auth-mfa-methods", "GET", "clusters/{id}/auth-mfa/methods/"),
    _action(
        "cluster.auth-mfa-method",
        ("GET", "POST", "DELETE"),
        "clusters/{id}/auth-mfa/methods/{method_type}/{method_id}/",
    ),
    _action(
        "cluster.auth-mfa-method-create", "POST", "clusters/{id}/auth-mfa/methods/{method_type}/"
    ),
    _action(
        "cluster.auth-mfa-totp-self",
        "POST",
        "clusters/{id}/auth-mfa/totp/{method_id}/self/",
        material=True,
    ),
    _action(
        "cluster.auth-mfa-totp-self-reset",
        "POST",
        "clusters/{id}/auth-mfa/totp/{method_id}/self/reset/",
        material=True,
    ),
    _action(
        "cluster.auth-mfa-totp-entity",
        ("POST", "DELETE"),
        "clusters/{id}/auth-mfa/totp/{method_id}/entities/{entity_id}/",
    ),
    _action("cluster.auth-mfa-enforcements", "GET", "clusters/{id}/auth-mfa/enforcements/"),
    _action(
        "cluster.auth-mfa-enforcement",
        ("GET", "POST", "DELETE"),
        "clusters/{id}/auth-mfa/enforcements/{name}/",
    ),
    _action("cluster.auth-token", "POST", "clusters/{id}/auth-tokens/{operation}/", material=True),
)


def openbao_resources() -> tuple[OpenBaoResourceSpec, ...]:
    return OPENBAO_RESOURCES


def openbao_actions() -> tuple[OpenBaoActionSpec, ...]:
    return OPENBAO_ACTIONS


def find_openbao_resource(identifier: str) -> OpenBaoResourceSpec:
    normalized = identifier.strip().strip("/")
    for spec in OPENBAO_RESOURCES:
        if normalized in {spec.key, spec.command, spec.resource, spec.list_path.strip("/")}:
            return spec
    raise KeyError(f"Unknown OpenBao resource {identifier!r}")


def find_openbao_action(identifier: str) -> OpenBaoActionSpec:
    normalized = identifier.strip().casefold()
    for spec in OPENBAO_ACTIONS:
        if normalized in {spec.key.casefold(), spec.command.casefold()}:
            return spec
    raise KeyError(f"Unknown OpenBao action {identifier!r}")


def register_openbao_resources(index: SchemaIndex) -> SchemaIndex:
    for spec in OPENBAO_RESOURCES:
        index.add_discovered_resource(
            group="plugins",
            resource=spec.resource,
            list_path=spec.list_path,
            detail_path=spec.detail_path,
            list_methods=spec.list_methods,
            detail_methods=spec.detail_methods,
        )
    return index


def build_openbao_schema_index() -> SchemaIndex:
    return register_openbao_resources(SchemaIndex({"openapi": "3.0.0", "paths": {}}))


def _render_action_path(spec: OpenBaoActionSpec, parameters: dict[str, str | int]) -> str:
    required = set(spec.path_parameters)
    supplied = set(parameters)
    if supplied != required:
        missing = sorted(required - supplied)
        extra = sorted(supplied - required)
        raise ValueError(f"Invalid path parameters; missing={missing}, extra={extra}")
    values: dict[str, str] = {}
    for key, raw in parameters.items():
        value = str(raw)
        if not _SAFE_SEGMENT_RE.fullmatch(value):
            raise ValueError(f"Unsafe OpenBao path parameter: {key}")
        values[key] = value
    return spec.path_template.format_map(values)


def _snapshot_restore_headers(
    *,
    force: bool,
    reason: str,
    confirmation: str,
    openbao_cluster_id: str,
    configuration_index: int,
    headers: dict[str, str] | None,
) -> dict[str, str]:
    prefix = "FORCE RESTORE SNAPSHOT " if force else "RESTORE SNAPSHOT "
    if not reason.strip():
        raise ValueError("Snapshot restore reason is required")
    if not confirmation.startswith(prefix) or not confirmation.removeprefix(prefix).strip():
        raise ValueError(f"Snapshot confirmation must start with {prefix!r}")
    if not openbao_cluster_id.strip():
        raise ValueError("OpenBao cluster ID is required")
    if configuration_index < 0:
        raise ValueError("Raft configuration index cannot be negative")
    reserved = {
        "x-openbao-reason",
        "x-openbao-confirmation",
        "x-openbao-cluster-id",
        "x-openbao-raft-index",
    }
    result = {
        key: value for key, value in (headers or {}).items() if key.casefold() not in reserved
    }
    result.update(
        {
            "X-OpenBao-Reason": reason,
            "X-OpenBao-Confirmation": confirmation,
            "X-OpenBao-Cluster-ID": openbao_cluster_id,
            "X-OpenBao-Raft-Index": str(configuration_index),
        }
    )
    return result


class OpenBaoClient:
    """Workflow-aware client with uncached material and state operations."""

    def __init__(self, client: NetBoxApiClient, *, index: SchemaIndex | None = None) -> None:
        self.client = client
        self.index = index or build_openbao_schema_index()

    async def request_resource(
        self,
        resource: str,
        action: str,
        *,
        object_id: int | None = None,
        query: QueryParams | None = None,
        payload: dict[str, Any] | list[Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> ApiResponse:
        spec = find_openbao_resource(resource)
        if action not in spec.supported_actions:
            raise ValueError(f"Action {action!r} is not supported for {spec.command!r}")
        resolved = resolve_dynamic_request(
            self.index,
            "plugins",
            spec.resource,
            action,
            object_id=object_id,
            query=query or {},
            payload=payload,
        )
        return await self.client.request_one_shot(
            resolved.method,
            resolved.path,
            query=resolved.query,
            payload=resolved.payload,
            headers=headers,
        )

    async def request_action(
        self,
        action: str,
        *,
        method: str | None = None,
        path_parameters: dict[str, str | int] | None = None,
        query: QueryParams | None = None,
        payload: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> ApiResponse:
        spec = find_openbao_action(action)
        selected = (method or spec.methods[0]).upper()
        if selected not in spec.methods:
            raise ValueError(f"Method {selected!r} is not supported for {spec.key!r}")
        if spec.binary != "none":
            raise ValueError("Use download_snapshot() or upload_snapshot() for binary actions")
        path = _render_action_path(spec, path_parameters or {})
        return await self.client.request_one_shot(
            selected,
            path,
            query=query,
            payload=payload,
            headers=headers,
        )

    async def download_snapshot(
        self,
        cluster_id: int,
        *,
        method: str = "GET",
        payload: dict[str, Any] | None = None,
        max_bytes: int = DEFAULT_SNAPSHOT_LIMIT,
    ) -> bytes:
        spec = find_openbao_action("cluster.raft-snapshot-download")
        selected = method.upper()
        if selected not in spec.methods:
            raise ValueError(f"Method {selected!r} is not supported for {spec.key!r}")
        if selected == "GET" and payload is not None:
            raise ValueError("GET snapshot downloads do not accept a request body")
        path = _render_action_path(spec, {"id": cluster_id})
        return await self.client.request_binary(
            selected,
            path,
            payload=payload,
            max_response_bytes=max_bytes,
        )

    async def upload_snapshot(
        self,
        cluster_id: int,
        source: Path,
        *,
        force: bool = False,
        reason: str,
        confirmation: str,
        openbao_cluster_id: str,
        configuration_index: int,
        headers: dict[str, str] | None = None,
        max_bytes: int = DEFAULT_SNAPSHOT_LIMIT,
    ) -> ApiResponse:
        key = "cluster.raft-snapshot-restore-force" if force else "cluster.raft-snapshot-restore"
        path = _render_action_path(find_openbao_action(key), {"id": cluster_id})
        metadata_headers = _snapshot_restore_headers(
            force=force,
            reason=reason,
            confirmation=confirmation,
            openbao_cluster_id=openbao_cluster_id,
            configuration_index=configuration_index,
            headers=headers,
        )
        return await self.client.request_binary_upload(
            "POST",
            path,
            source=source,
            headers=metadata_headers,
            max_request_bytes=max_bytes,
        )


__all__ = [
    "DEFAULT_SNAPSHOT_LIMIT",
    "OPENBAO_ACTIONS",
    "OPENBAO_BASE",
    "OPENBAO_RESOURCES",
    "OpenBaoActionSpec",
    "OpenBaoClient",
    "OpenBaoResourceSpec",
    "build_openbao_schema_index",
    "find_openbao_action",
    "find_openbao_resource",
    "openbao_actions",
    "openbao_resources",
    "register_openbao_resources",
]
