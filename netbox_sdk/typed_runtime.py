"""Runtime support for versioned typed NetBox clients."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, TypeAdapter, ValidationError

from netbox_sdk.client import ApiResponse, NetBoxApiClient
from netbox_sdk.config import Config
from netbox_sdk.decorators import api_json_response, api_raw_response
from netbox_sdk.facade import _is_v2_token
from netbox_sdk.versioning import SupportedNetBoxVersion

QueryParamValue = str | list[str]
QueryParams = dict[str, QueryParamValue]


class TypedRequestValidationError(ValueError):
    """Raised when a typed request payload fails validation."""

    def __init__(
        self, method: str, path: str, version: SupportedNetBoxVersion, error: ValidationError
    ) -> None:
        self.method = method
        self.path = path
        self.version = version
        self.error = error
        super().__init__(f"{method} {path} request validation failed for NetBox {version}: {error}")


class TypedResponseValidationError(ValueError):
    """Raised when a typed response payload fails validation."""

    def __init__(
        self, method: str, path: str, version: SupportedNetBoxVersion, error: ValidationError
    ) -> None:
        self.method = method
        self.path = path
        self.version = version
        self.error = error
        super().__init__(
            f"{method} {path} response validation failed for NetBox {version}: {error}"
        )


def build_typed_client(url: str, token: str | None) -> NetBoxApiClient:
    """Construct a :class:`~netbox_sdk.client.NetBoxApiClient` with token layout inferred from ``token``."""
    token_version = "v2" if _is_v2_token(token) else "v1"
    token_key = None
    token_secret = token
    if token_version == "v2" and token:
        token_key, token_secret = token.split(".", 1)
    return NetBoxApiClient(
        Config(
            base_url=url,
            token_version=token_version,
            token_key=token_key,
            token_secret=token_secret,
        )
    )


def _dump_validated(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", by_alias=True, exclude_none=True)
    if isinstance(value, list):
        return [_dump_validated(item) for item in value]
    if isinstance(value, dict):
        return {key: _dump_validated(item) for key, item in value.items()}
    return value


def validate_query(
    model_type: type[Any] | None,
    query: BaseModel | dict[str, Any] | None,
    *,
    method: str,
    path: str,
    version: SupportedNetBoxVersion,
) -> QueryParams | None:
    if query is None:
        return None
    if model_type is None:
        if isinstance(query, BaseModel):
            raw = query.model_dump(mode="json", by_alias=True, exclude_none=True)
        else:
            raw = query
    else:
        try:
            raw = TypeAdapter(model_type).validate_python(query)
        except ValidationError as exc:
            raise TypedRequestValidationError(method, path, version, exc) from exc
        raw = _dump_validated(raw)
    normalized: QueryParams = {}
    for key, value in raw.items():
        if value is None:
            continue
        if isinstance(value, list):
            normalized[str(key)] = [str(item) for item in value if item is not None]
            continue
        normalized[str(key)] = str(value)
    return normalized


def validate_payload(
    model_type: type[Any] | None,
    payload: Any,
    *,
    method: str,
    path: str,
    version: SupportedNetBoxVersion,
) -> Any:
    if payload is None or model_type is None:
        return payload
    try:
        validated = TypeAdapter(model_type).validate_python(payload)
    except ValidationError as exc:
        raise TypedRequestValidationError(method, path, version, exc) from exc
    return _dump_validated(validated)


def validate_response(
    model_type: type[Any] | None,
    data: Any,
    *,
    method: str,
    path: str,
    version: SupportedNetBoxVersion,
) -> Any:
    if model_type is None:
        return data
    try:
        return TypeAdapter(model_type).validate_python(data)
    except ValidationError as exc:
        raise TypedResponseValidationError(method, path, version, exc) from exc


@dataclass(slots=True)
class TypedApiBase:
    client: NetBoxApiClient
    netbox_version: SupportedNetBoxVersion


class TypedOperationMixin:
    def __init__(self, api: TypedApiBase) -> None:
        self._api = api

    @api_json_response(none_on_404_kwarg="return_none_on_404")
    async def _typed_json_response(
        self,
        method: str,
        path: str,
        *,
        query: QueryParams | None,
        payload: Any,
        return_none_on_404: bool,
    ) -> ApiResponse:
        return await self._api.client.request(
            method,
            path,
            query=query,
            payload=payload,
        )

    async def _typed_json_request(
        self,
        method: str,
        path: str,
        *,
        query_model: type[Any] | None = None,
        query: BaseModel | dict[str, Any] | None = None,
        body_model: type[Any] | None = None,
        body: Any = None,
        response_model: type[Any] | None = None,
        return_none_on_404: bool = False,
    ) -> Any:
        request_query = validate_query(
            query_model,
            query,
            method=method,
            path=path,
            version=self._api.netbox_version,
        )
        request_payload = validate_payload(
            body_model,
            body,
            method=method,
            path=path,
            version=self._api.netbox_version,
        )
        payload = await self._typed_json_response(
            method,
            path,
            query=request_query,
            payload=request_payload,
            return_none_on_404=return_none_on_404,
        )
        if payload is None:
            return None
        return validate_response(
            response_model,
            payload,
            method=method,
            path=path,
            version=self._api.netbox_version,
        )

    @api_raw_response()
    async def _typed_raw_response(
        self,
        method: str,
        path: str,
        *,
        query: QueryParams | None,
    ) -> ApiResponse:
        return await self._api.client.request(method, path, query=query, expect_json=False)

    async def _typed_raw_request(
        self,
        method: str,
        path: str,
        *,
        query_model: type[Any] | None = None,
        query: BaseModel | dict[str, Any] | None = None,
    ) -> str:
        request_query = validate_query(
            query_model,
            query,
            method=method,
            path=path,
            version=self._api.netbox_version,
        )
        return await self._typed_raw_response(method, path, query=request_query)


class TypedAppBase(TypedOperationMixin):
    pass


class RawBranchingApp(TypedAppBase):
    """Dict-based accessor for the ``netbox-branching`` plugin on typed clients.

    The plugin owns its URL space, so it stays stable across NetBox 4.3–4.6.
    Versions that do not bundle generated Pydantic models for the plugin use
    this helper to expose branching as raw dictionaries while still routing
    through the typed runtime client.
    """

    BASE = "/api/plugins/branching"

    @api_json_response()
    async def _json_response(
        self,
        method: str,
        path: str,
        *,
        query: QueryParams | None = None,
        payload: dict[str, Any] | None = None,
    ) -> ApiResponse:
        return await self._api.client.request(method, path, query=query, payload=payload)

    @api_json_response(none_on_statuses={404})
    async def _delete_response(self, path: str) -> ApiResponse:
        return await self._api.client.request("DELETE", path)

    async def _get(self, path: str, **params: Any) -> Any:
        query = {k: v for k, v in params.items() if v is not None} or None
        return await self._json_response("GET", path, query=query)

    async def _post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        return await self._json_response("POST", path, payload=payload or {})

    async def _patch(self, path: str, payload: dict[str, Any]) -> Any:
        return await self._json_response("PATCH", path, payload=payload)

    async def _delete(self, path: str) -> None:
        await self._delete_response(path)

    async def list_branches(self, **filters: Any) -> Any:
        return await self._get(f"{self.BASE}/branches/", **filters)

    async def get_branch(self, id: int) -> Any:
        return await self._get(f"{self.BASE}/branches/{id}/")

    async def create_branch(self, **fields: Any) -> Any:
        return await self._post(f"{self.BASE}/branches/", payload=fields)

    async def update_branch(self, id: int, **fields: Any) -> Any:
        return await self._patch(f"{self.BASE}/branches/{id}/", payload=fields)

    async def delete_branch(self, id: int) -> None:
        await self._delete(f"{self.BASE}/branches/{id}/")

    async def sync(
        self, id: int, *, commit: bool = True, acknowledge_conflicts: bool = False
    ) -> Any:
        return await self._post(
            f"{self.BASE}/branches/{id}/sync/",
            payload={"commit": commit, "acknowledge_conflicts": acknowledge_conflicts},
        )

    async def merge(
        self, id: int, *, commit: bool = True, acknowledge_conflicts: bool = False
    ) -> Any:
        return await self._post(
            f"{self.BASE}/branches/{id}/merge/",
            payload={"commit": commit, "acknowledge_conflicts": acknowledge_conflicts},
        )

    async def revert(self, id: int) -> Any:
        return await self._post(f"{self.BASE}/branches/{id}/revert/")

    async def archive(self, id: int) -> Any:
        return await self._post(f"{self.BASE}/branches/{id}/archive/")

    async def branch_events(self, **filters: Any) -> Any:
        return await self._get(f"{self.BASE}/branch-events/", **filters)

    async def changes(self, **filters: Any) -> Any:
        return await self._get(f"{self.BASE}/changes/", **filters)

    async def branchable_models(self) -> Any:
        return await self._get(f"{self.BASE}/branchable-models/")
