"""Internal decorators for shared SDK response handling."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from functools import wraps
from typing import Any, ParamSpec

from netbox_sdk.client import ApiResponse
from netbox_sdk.exceptions import (
    BranchConflictError,
    BranchingPluginUnavailableError,
    ContentError,
    RequestError,
)

P = ParamSpec("P")

ResponseErrorMapper = Callable[[ApiResponse, tuple[Any, ...], dict[str, Any]], Exception | None]


@dataclass(frozen=True, slots=True)
class JsonResponse:
    response: ApiResponse
    payload: Any


def decode_json_response(response: ApiResponse) -> Any:
    try:
        return response.json()
    except json.JSONDecodeError as exc:
        raise ContentError(response) from exc


def ensure_response_type(
    response: ApiResponse,
    payload: Any,
    expected_type: type[Any] | tuple[type[Any], ...] | None,
) -> Any:
    if expected_type is not None and not isinstance(payload, expected_type):
        raise ContentError(response)
    return payload


def branching_response_error(
    response: ApiResponse,
    _args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Exception | None:
    if 200 <= response.status < 300:
        return None
    if response.status == 404:
        if kwargs.get("resource_op"):
            return RequestError(response)
        return BranchingPluginUnavailableError()
    if response.status == 409:
        try:
            payload = response.json()
        except json.JSONDecodeError:
            payload = response.text
        if isinstance(payload, dict):
            raw_conflicts = payload.get("conflicts")
            conflicts: Any = (
                raw_conflicts if raw_conflicts is not None else (payload.get("detail") or payload)
            )
        else:
            conflicts = payload
        return BranchConflictError(conflicts, response=response)
    return RequestError(response)


def api_json_response(
    *,
    expected_type: type[Any] | tuple[type[Any], ...] | None = None,
    none_on_empty: bool = True,
    none_on_statuses: Iterable[int] = (),
    none_on_404_kwarg: str | None = None,
    include_response: bool = False,
    error_mapper: ResponseErrorMapper | None = None,
) -> Callable[[Callable[P, Awaitable[ApiResponse]]], Callable[P, Awaitable[Any]]]:
    none_statuses = frozenset(none_on_statuses)

    def _decorator(func: Callable[P, Awaitable[ApiResponse]]) -> Callable[P, Awaitable[Any]]:
        @wraps(func)
        async def _wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            response = await func(*args, **kwargs)
            if response.status in none_statuses:
                return None
            if (
                response.status == 404
                and none_on_404_kwarg is not None
                and bool(kwargs.get(none_on_404_kwarg))
            ):
                return None
            if error_mapper is not None:
                mapped = error_mapper(response, args, kwargs)
                if mapped is not None:
                    raise mapped
            elif response.status >= 400:
                raise RequestError(response)
            if none_on_empty and (response.status == 204 or not response.text.strip()):
                if include_response:
                    return JsonResponse(response=response, payload=None)
                return None
            payload = decode_json_response(response)
            payload = ensure_response_type(response, payload, expected_type)
            if include_response:
                return JsonResponse(response=response, payload=payload)
            return payload

        return _wrapper

    return _decorator


def api_raw_response(
    *,
    error_mapper: ResponseErrorMapper | None = None,
) -> Callable[[Callable[P, Awaitable[ApiResponse]]], Callable[P, Awaitable[str]]]:
    def _decorator(func: Callable[P, Awaitable[ApiResponse]]) -> Callable[P, Awaitable[str]]:
        @wraps(func)
        async def _wrapper(*args: P.args, **kwargs: P.kwargs) -> str:
            response = await func(*args, **kwargs)
            if error_mapper is not None:
                mapped = error_mapper(response, args, kwargs)
                if mapped is not None:
                    raise mapped
            elif response.status >= 400:
                raise RequestError(response)
            return response.text

        return _wrapper

    return _decorator
