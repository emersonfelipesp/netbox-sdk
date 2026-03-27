"""Runtime support for versioned typed NetBox clients."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, TypeAdapter, ValidationError

from netbox_sdk.client import NetBoxApiClient, RequestError
from netbox_sdk.config import Config
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
        response = await self._api.client.request(
            method,
            path,
            query=request_query,
            payload=request_payload,
        )
        if response.status == 404 and return_none_on_404:
            return None
        if response.status >= 400:
            raise RequestError(response)
        if response.status == 204 or not response.text.strip():
            return None
        return validate_response(
            response_model,
            response.json(),
            method=method,
            path=path,
            version=self._api.netbox_version,
        )

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
        response = await self._api.client.request(
            method, path, query=request_query, expect_json=False
        )
        if response.status >= 400:
            raise RequestError(response)
        return response.text


class TypedAppBase(TypedOperationMixin):
    pass
