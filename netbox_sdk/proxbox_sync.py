"""SDK helpers for netbox-proxbox synchronization jobs."""

import json
from collections.abc import AsyncIterator
from enum import StrEnum
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from pydantic import BaseModel, Field

from netbox_sdk.client import ApiResponse, NetBoxApiClient
from netbox_sdk.exceptions import ContentError


class SseFrame(BaseModel):
    event: str = "message"
    data: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def parse_block(cls, block: str) -> "SseFrame":
        event = "message"
        data_lines: list[str] = []
        for raw_line in block.splitlines():
            line = raw_line.rstrip("\r")
            if not line or line.startswith(":"):
                continue
            field, separator, value = line.partition(":")
            if separator and value.startswith(" "):
                value = value[1:]
            if field == "event":
                event = value or "message"
            elif field == "data":
                data_lines.append(value)

        data_text = "\n".join(data_lines)
        if not data_text:
            return cls(event=event, data={})
        try:
            decoded = json.loads(data_text)
        except json.JSONDecodeError:
            return cls(event=event, data={"raw": data_text})
        if isinstance(decoded, dict):
            return cls(event=event, data=decoded)
        return cls(event=event, data={"raw": data_text})


class SyncType(StrEnum):
    VIRTUAL_MACHINES = "virtual-machines"
    STORAGE = "storage"
    VM_DISKS = "vm-disks"
    VM_BACKUPS = "vm-backups"
    VM_SNAPSHOTS = "vm-snapshots"
    DEVICES = "devices"
    NETWORK_INTERFACES = "network-interfaces"
    VM_INTERFACES = "vm-interfaces"
    IP_ADDRESSES = "ip-addresses"
    SDN = "sdn"
    BACKUP_ROUTINES = "backup-routines"
    REPLICATIONS = "replications"
    TASK_HISTORY = "task-history"
    ALL = "all"


SYNC_TYPE_VALUES: tuple[str, ...] = tuple(item.value for item in SyncType)
ALL_VALUES = SYNC_TYPE_VALUES


class ScheduleResult(BaseModel):
    ok: bool
    job_id: int | None = None
    message: str


class ProxboxSyncError(RuntimeError):
    """Raised for Proxbox sync failures, preserving a known scheduled job ID."""

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        payload: Any = None,
        response: ApiResponse | None = None,
        job_id: int | str | None = None,
    ) -> None:
        self.status = status
        self.payload = payload
        self.response = response
        self.job_id = job_id
        super().__init__(message)

    @classmethod
    def from_response(cls, response: ApiResponse, *, action: str) -> "ProxboxSyncError":
        payload = _decode_response_payload(response)
        detail = _format_error_payload(payload)
        if response.status == 403:
            message = f"Permission denied for Proxbox {action}: {detail}"
        elif response.status == 400:
            message = f"Invalid Proxbox {action} request: {detail}"
        else:
            message = f"Proxbox {action} failed with HTTP {response.status}: {detail}"
        return cls(message, status=response.status, payload=payload, response=response)


class ProxboxSyncClient:
    """Ergonomic client for netbox-proxbox sync scheduling and job streaming."""

    BASE = "/api/plugins/proxbox"

    def __init__(self, client: NetBoxApiClient) -> None:
        self._client = client

    @classmethod
    def from_client(cls, client: NetBoxApiClient) -> "ProxboxSyncClient":
        return cls(client)

    async def schedule(
        self,
        sync_types: list[str],
        *,
        proxmox_endpoint_ids: list[int] | None = None,
        job_name: str | None = None,
    ) -> ScheduleResult:
        body: dict[str, Any] = {"sync_types": validate_sync_types(sync_types)}
        if proxmox_endpoint_ids is not None:
            body["proxmox_endpoint_ids"] = proxmox_endpoint_ids
        if job_name is not None:
            body["job_name"] = job_name

        response = await self._client.request(
            "POST",
            f"{self.BASE}/sync/schedule/",
            payload=body,
        )
        if response.status >= 400:
            raise ProxboxSyncError.from_response(response, action="schedule")
        payload = _decode_success_payload(response)
        return ScheduleResult.model_validate(payload)

    async def stream_job(
        self,
        job_id: int,
        *,
        timeout: float | None = None,
    ) -> AsyncIterator[SseFrame]:
        async for block in self._client.stream_sse(
            "GET",
            f"/plugins/proxbox/jobs/{job_id}/stream/",
            timeout=timeout,
        ):
            yield SseFrame.parse_block(block)

    async def resolve_endpoint(self, name_or_id: str | int) -> int:
        if isinstance(name_or_id, int) and not isinstance(name_or_id, bool):
            return name_or_id
        text = str(name_or_id).strip()
        if text.isdigit():
            return int(text)
        if not text:
            raise ValueError("Endpoint name cannot be empty")

        exact_payload = await self._request_object(
            "GET",
            f"{self.BASE}/endpoints/proxmox/",
            query={"name": text},
            action="endpoint lookup",
        )
        exact_results = _paginated_results(exact_payload)
        if exact_results:
            return _pick_endpoint_id(exact_results, text, exact=True)

        all_results = await self._list_endpoint_pages()
        return _pick_endpoint_id(all_results, text, exact=False)

    async def fetch_job(self, job_id: int) -> dict[str, Any]:
        return await self._request_object("GET", f"/api/core/jobs/{job_id}/", action="job fetch")

    async def _list_endpoint_pages(self) -> list[dict[str, Any]]:
        path = f"{self.BASE}/endpoints/proxmox/"
        query: dict[str, Any] | None = None
        rows: list[dict[str, Any]] = []
        for _ in range(1000):
            payload = await self._request_object("GET", path, query=query, action="endpoint lookup")
            rows.extend(_paginated_results(payload))
            next_url = payload.get("next")
            if not isinstance(next_url, str) or not next_url:
                return rows
            parsed = urlsplit(next_url)
            path = parsed.path
            query = dict(parse_qsl(parsed.query, keep_blank_values=True)) or None
        raise ProxboxSyncError("Endpoint pagination did not terminate during Proxbox lookup")

    async def _request_object(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        action: str,
    ) -> dict[str, Any]:
        response = await self._client.request(method, path, query=query)
        if response.status >= 400:
            raise ProxboxSyncError.from_response(response, action=action)
        return _decode_success_payload(response)


def validate_sync_types(sync_types: list[str]) -> list[str]:
    values = [str(item).strip() for item in sync_types if str(item).strip()]
    if not values:
        raise ValueError("At least one Proxbox sync type is required")
    unknown = [item for item in values if item not in SYNC_TYPE_VALUES]
    if unknown:
        available = ", ".join(SYNC_TYPE_VALUES)
        raise ValueError(
            f"Unknown Proxbox sync type(s): {', '.join(unknown)}. Available: {available}"
        )
    if SyncType.ALL.value in values and len(values) > 1:
        raise ValueError("'all' cannot be combined with any other Proxbox sync type")
    deduped: list[str] = []
    for value in values:
        if value not in deduped:
            deduped.append(value)
    return deduped


def _decode_response_payload(response: ApiResponse) -> Any:
    try:
        return response.json()
    except json.JSONDecodeError:
        return response.text.strip()


def _decode_success_payload(response: ApiResponse) -> dict[str, Any]:
    payload = _decode_response_payload(response)
    if not isinstance(payload, dict):
        raise ContentError(response)
    return payload


def _format_error_payload(payload: Any) -> str:
    if isinstance(payload, dict):
        detail = payload.get("detail")
        if isinstance(detail, str) and detail.strip():
            return detail.strip()
        errors = payload.get("errors")
        if errors is not None:
            return json.dumps(errors, sort_keys=True, default=str)
        return json.dumps(payload, sort_keys=True, default=str)
    text = str(payload).strip()
    return text or "empty response body"


def _paginated_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = payload.get("results")
    if not isinstance(results, list):
        raise ContentError(ApiResponse(status=200, text=json.dumps(payload), headers={}))
    return [item for item in results if isinstance(item, dict)]


def _pick_endpoint_id(rows: list[dict[str, Any]], name: str, *, exact: bool) -> int:
    if exact:
        matches = [row for row in rows if row.get("name") == name]
        if not matches:
            matches = rows
    else:
        lowered = name.casefold()
        matches = [
            row
            for row in rows
            if isinstance(row.get("name"), str) and str(row["name"]).casefold() == lowered
        ]
    if not matches:
        raise ValueError(f"No Proxmox endpoint found with name {name!r}")
    if len(matches) > 1:
        names = ", ".join(str(row.get("name") or row.get("id")) for row in matches)
        raise ValueError(f"Multiple Proxmox endpoints matched {name!r}: {names}")
    value = matches[0].get("id")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    raise ValueError(f"Proxmox endpoint {name!r} did not include a numeric id")


__all__ = [
    "ALL_VALUES",
    "ProxboxSyncClient",
    "ProxboxSyncError",
    "SYNC_TYPE_VALUES",
    "ScheduleResult",
    "SseFrame",
    "SyncType",
    "validate_sync_types",
]
