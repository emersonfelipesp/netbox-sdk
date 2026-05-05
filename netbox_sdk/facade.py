"""Async convenience layer that exposes PyNetBox-like NetBox SDK features."""

from __future__ import annotations

import json
import logging
import os
from collections import deque
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, ClassVar, Literal, Self, cast
from urllib.parse import parse_qsl, urlsplit

from netbox_sdk.client import ApiResponse, NetBoxApiClient
from netbox_sdk.config import Config
from netbox_sdk.exceptions import (
    AllocationError,
    ContentError,
    ParameterValidationError,
    RequestError,
)
from netbox_sdk.schema import ResourcePaths, SchemaIndex, build_schema_index, parse_group_resource

logger = logging.getLogger(__name__)

PaginationMode = Literal["cursor", "offset", "auto"]
ResolvedPaginationMode = Literal["cursor", "offset"]
DEFAULT_CURSOR_PAGE_SIZE = 50
_PAGINATION_MODE_ENV_VAR = "NETBOX_SDK_PAGINATION_MODE"
_VALID_PAGINATION_MODES = ("cursor", "offset", "auto")


def _normalize_pagination_mode(value: str | None) -> PaginationMode | None:
    """Normalize a user-supplied pagination mode string.

    Args:
        value: Free-form string such as ``"Cursor"``, ``" offset "``, or ``None``.

    Returns:
        One of ``"cursor"``, ``"offset"``, ``"auto"`` when the input is recognised,
        otherwise ``None`` (caller decides whether the absence is fatal).
    """
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in _VALID_PAGINATION_MODES:
        return cast(PaginationMode, normalized)
    return None


APP_NAMES = (
    "circuits",
    "core",
    "dcim",
    "extras",
    "ipam",
    "tenancy",
    "users",
    "virtualization",
    "vpn",
    "wireless",
)


def _is_v2_token(token: str | None) -> bool:
    return bool(token and token.startswith("nbt_") and "." in token)


def api(
    url: str,
    token: str | None = None,
    *,
    strict_filters: bool = False,
    client: NetBoxApiClient | None = None,
    schema: SchemaIndex | None = None,
    pagination_mode: PaginationMode = "auto",
) -> Api:
    """Build a high-level async NetBox API wrapper (PyNetBox-style).

    Args:
        url: NetBox base URL (with or without trailing slash).
        token: API token (v1 ``Token`` or v2 ``nbt_`` form). Ignored if ``client`` is passed.
        strict_filters: When True, unknown filter keys raise instead of being dropped.
        client: Optional pre-built :class:`~netbox_sdk.client.NetBoxApiClient`.
        schema: Optional pre-built OpenAPI index (defaults to bundled schema).

    Returns:
        Root :class:`Api` instance with app attributes (``dcim``, ``ipam``, etc.).
    """
    if client is None:
        token_version = "v2" if _is_v2_token(token) else "v1"
        token_key = None
        token_secret = token
        if token_version == "v2" and token:
            key, secret = token.split(".", 1)
            token_key = key
            token_secret = secret
        client = NetBoxApiClient(
            Config(
                base_url=url,
                token_version=token_version,
                token_key=token_key,
                token_secret=token_secret,
            )
        )
        logger.debug(
            "api() built default client",
            extra={
                "nbx_event": "facade_api_init",
                "token_version": token_version,
                "strict_filters": strict_filters,
            },
        )
    return Api(
        client=client,
        schema=schema,
        strict_filters=strict_filters,
        pagination_mode=pagination_mode,
    )


async def async_api(
    url: str,
    token: str | None = None,
    *,
    strict_filters: bool = False,
    client: NetBoxApiClient | None = None,
    discover_resources: bool = True,
    pagination_mode: PaginationMode = "auto",
) -> Api:
    """Like :func:`api` but auto-detects the NetBox version and selects the right schema.

    Fetches the schema from the connected instance when the version is not a bundled
    release line; otherwise uses the matching bundled schema.
    """
    from netbox_sdk.schema import fetch_schema_for_client  # noqa: PLC0415

    if client is None:
        token_version = "v2" if _is_v2_token(token) else "v1"
        token_key = None
        token_secret = token
        if token_version == "v2" and token:
            key, secret = token.split(".", 1)
            token_key = key
            token_secret = secret
        client = NetBoxApiClient(
            Config(
                base_url=url,
                token_version=token_version,
                token_key=token_key,
                token_secret=token_secret,
            )
        )
    schema_dict = await fetch_schema_for_client(client)
    schema = SchemaIndex(schema_dict)
    if discover_resources:
        from netbox_sdk.plugin_discovery import (  # noqa: PLC0415
            enrich_schema_index_with_runtime_resources,
        )

        await enrich_schema_index_with_runtime_resources(schema, client)
    return Api(
        client=client,
        schema=schema,
        strict_filters=strict_filters,
        pagination_mode=pagination_mode,
    )


class Api:
    def __init__(
        self,
        *,
        client: NetBoxApiClient,
        schema: SchemaIndex | None = None,
        strict_filters: bool = False,
        pagination_mode: PaginationMode = "auto",
    ) -> None:
        self.client = client
        self.schema = schema or build_schema_index()
        self.strict_filters = strict_filters
        env_override = _normalize_pagination_mode(os.environ.get(_PAGINATION_MODE_ENV_VAR))
        self.pagination_mode: PaginationMode = env_override or pagination_mode
        self._resolved_pagination_mode: ResolvedPaginationMode | None = (
            self.pagination_mode if self.pagination_mode in ("cursor", "offset") else None  # type: ignore[assignment]
        )
        for name in APP_NAMES:
            setattr(self, name, App(self, name))
        self.plugins = PluginsApp(self)

    async def _resolve_pagination_mode(self) -> ResolvedPaginationMode:
        """Resolve ``"auto"`` to a concrete pagination mode for the running server.

        The result is cached on the :class:`Api` instance so the version probe
        runs at most once. NetBox ``>= 4.6`` uses cursor pagination (``start=``);
        older releases fall back to offset. Any error during the probe is logged
        at debug level and the engine falls back to offset, since offset is
        supported by every NetBox release the SDK targets.
        """
        if self._resolved_pagination_mode is not None:
            return self._resolved_pagination_mode
        try:
            version = await self.client.get_version()
            parts = version.split(".") if version else []
            major = int(parts[0]) if len(parts) >= 1 else 0
            minor = int(parts[1]) if len(parts) >= 2 else 0
            self._resolved_pagination_mode = "cursor" if (major, minor) >= (4, 6) else "offset"
        except Exception as exc:
            logger.debug(
                "pagination mode auto-detect failed; falling back to offset: %s",
                exc,
                extra={"nbx_event": "facade_pagination_mode_fallback"},
            )
            self._resolved_pagination_mode = "offset"
        return self._resolved_pagination_mode

    async def status(self) -> dict[str, Any]:
        return await self.client.status()

    async def openapi(self) -> dict[str, Any]:
        return await self.client.openapi()

    async def get_version(self) -> str:
        return await self.client.get_version()

    async def version(self) -> str:
        return await self.get_version()

    async def create_token(self, username: str, password: str) -> Record:
        response = await self.client.create_token(username, password)
        _raise_for_status(response)
        payload = _decode_json(response)
        return Record(self, None, payload, has_details=True)

    @contextmanager
    def activate_branch(self, branch: Any) -> Iterator[Api]:
        schema_id = getattr(branch, "schema_id", None) or getattr(branch, "id", None) or str(branch)
        with self.client.header_scope(**{"X-NetBox-Branch": str(schema_id)}):
            yield self

    def endpoint_for(self, group: str, resource: str) -> Endpoint:
        if group == "plugins":
            plugin_name, _, plugin_resource = resource.partition("/")
            if not plugin_name or not plugin_resource:
                raise ValueError(f"Invalid plugin resource: {resource}")
            app = App(self, f"plugins/{plugin_name}")
            return Endpoint(self, app, plugin_resource)
        return Endpoint(self, getattr(self, group), resource)

    def endpoint_for_path(self, path: str) -> Endpoint | None:
        group, resource = parse_group_resource(path)
        if group is None or resource is None:
            return None
        return self.endpoint_for(group, resource)


class App:
    def __init__(self, api: Api, name: str) -> None:
        self.api = api
        self.name = name

    def __getattr__(self, name: str) -> Endpoint:
        return Endpoint(self.api, self, name)

    async def config(self) -> dict[str, Any]:
        response = await self.api.client.request("GET", f"/api/{self.name}/config/")
        _raise_for_status(response)
        return _decode_json(response)


class PluginsApp:
    def __init__(self, api: Api) -> None:
        self.api = api
        self.name = "plugins"

    def __getattr__(self, name: str) -> App:
        return App(self.api, f"plugins/{name.replace('_', '-')}")

    async def installed_plugins(self) -> list[dict[str, Any]]:
        response = await self.api.client.request("GET", "/api/plugins/installed-plugins")
        _raise_for_status(response)
        payload = _decode_json(response)
        if not isinstance(payload, list):
            raise ContentError(response)
        return payload


@dataclass(frozen=True)
class DetailEndpointSpec:
    name: str
    read_only: bool = False
    multi_format: bool = False


DETAIL_ENDPOINT_SPECS: dict[tuple[str, str], dict[str, DetailEndpointSpec]] = {
    ("dcim", "devices"): {
        "napalm": DetailEndpointSpec("napalm", read_only=True),
        "render_config": DetailEndpointSpec("render-config"),
    },
    ("dcim", "interfaces"): {"trace": DetailEndpointSpec("trace", read_only=True)},
    ("dcim", "power-ports"): {"trace": DetailEndpointSpec("trace", read_only=True)},
    ("dcim", "power-outlets"): {"trace": DetailEndpointSpec("trace", read_only=True)},
    ("dcim", "console-ports"): {"trace": DetailEndpointSpec("trace", read_only=True)},
    ("dcim", "console-server-ports"): {"trace": DetailEndpointSpec("trace", read_only=True)},
    ("dcim", "power-feeds"): {"trace": DetailEndpointSpec("trace", read_only=True)},
    ("dcim", "racks"): {
        "units": DetailEndpointSpec("units", read_only=True),
        "elevation": DetailEndpointSpec("elevation", read_only=True, multi_format=True),
    },
    ("ipam", "ip-ranges"): {"available_ips": DetailEndpointSpec("available-ips")},
    ("ipam", "prefixes"): {
        "available_ips": DetailEndpointSpec("available-ips"),
        "available_prefixes": DetailEndpointSpec("available-prefixes"),
    },
    ("ipam", "vlan-groups"): {"available_vlans": DetailEndpointSpec("available-vlans")},
    ("virtualization", "virtual-machines"): {
        "render_config": DetailEndpointSpec("render-config"),
    },
    ("circuits", "circuit-terminations"): {"paths": DetailEndpointSpec("paths", read_only=True)},
    ("circuits", "virtual-circuit-terminations"): {
        "paths": DetailEndpointSpec("paths", read_only=True)
    },
}


class Endpoint:
    def __init__(self, api: Api, app: App | PluginsApp, name: str) -> None:
        self.api = api
        self.app = app
        self.name = name.replace("_", "-")
        self.group = "plugins" if str(app.name).startswith("plugins/") else str(app.name)
        self.resource = (
            f"{str(app.name).split('/', 1)[1]}/{self.name}"
            if self.group == "plugins"
            else self.name
        )

    @property
    def _paths(self) -> ResourcePaths | None:
        return self.api.schema.resource_paths(self.group, self.resource)

    @property
    def _list_path(self) -> str:
        paths = self._paths
        if paths is None or not paths.list_path:
            raise ValueError(f"Resource does not expose list path: {self.group}/{self.resource}")
        return paths.list_path

    @property
    def _detail_path_template(self) -> str:
        paths = self._paths
        if paths is None or not paths.detail_path:
            raise ValueError(f"Resource does not expose detail path: {self.group}/{self.resource}")
        return paths.detail_path

    def all(
        self,
        limit: int = 0,
        offset: int | None = None,
        *,
        start: int | None = None,
        mode: PaginationMode | None = None,
        **filters: Any,
    ) -> RecordSet:
        """Return a :class:`RecordSet` over every record in the resource.

        Accepts the same filter keywords as :meth:`filter`, so callers can mix
        pagination arguments with filter terms freely
        (for example ``all(role="leaf-switch", limit=100)``).

        Args:
            limit: Page size. ``0`` (default) lets the SDK pick: the cursor
                engine uses :data:`DEFAULT_CURSOR_PAGE_SIZE`; the offset engine
                lets the server choose.
            offset: Legacy offset seed. Mutually exclusive with ``start``.
            start: Cursor seed (NetBox >= 4.6). Forces cursor mode when set.
            mode: ``"cursor"``, ``"offset"``, ``"auto"`` or ``None`` (use the
                client default). Mutually exclusive with the implicit forcing
                that ``start`` and ``offset`` perform.
            **filters: Arbitrary filter keywords forwarded to NetBox.

        Returns:
            A lazily-paginated :class:`RecordSet`.
        """
        return self.filter(
            limit=limit,
            offset=offset,
            start=start,
            mode=mode,
            **filters,
        )

    def filter(self, *args: str, **kwargs: Any) -> RecordSet:
        """Return a :class:`RecordSet` filtered by ``**kwargs``.

        Recognised pagination keywords (popped before building the query):
        ``limit``, ``offset``, ``start``, ``mode``, ``strict_filters``.
        Any positional argument is mapped to NetBox's free-text ``q=`` filter.
        Remaining keywords become filter parameters.

        Raises:
            ValueError: If ``offset`` is set without a positive ``limit``, or
                if ``start`` and ``offset`` are passed together.
            ParameterValidationError: When ``strict_filters`` is enabled and
                an unknown filter key is supplied.
        """
        raw_limit = kwargs.pop("limit", 0)
        limit = int(raw_limit) if raw_limit is not None else 0
        raw_offset = kwargs.pop("offset", None)
        offset = int(raw_offset) if raw_offset is not None else None
        raw_start = kwargs.pop("start", None)
        start = int(raw_start) if raw_start is not None else None
        mode_arg = kwargs.pop("mode", None)
        mode: PaginationMode | None = (
            _normalize_pagination_mode(mode_arg) if isinstance(mode_arg, str) else None
        )
        strict_filters = bool(kwargs.pop("strict_filters", self.api.strict_filters))
        if args:
            kwargs["q"] = args[0]
        if limit == 0 and offset is not None:
            raise ValueError("offset requires a positive limit value")
        if start is not None and offset is not None:
            raise ValueError("'start' and 'offset' are mutually exclusive")
        query: dict[str, str] = {
            key: "null" if value is None else str(value) for key, value in kwargs.items()
        }
        if strict_filters:
            _validate_filters(self.api.schema, self.group, self.resource, self._list_path, query)
        return RecordSet(self, query=query, limit=limit, offset=offset, start=start, mode=mode)

    async def get(self, *args: Any, **kwargs: Any) -> Record | None:
        """Return a single :class:`Record` by primary key or filter terms.

        ``get(42)`` issues a detail request. ``get(role="leaf-switch")`` runs
        a filtered list and asserts exactly one match.

        Returns:
            The matching :class:`Record`, or ``None`` when no record matches.

        Raises:
            ValueError: When the filter form returns more than one record.
        """
        key = args[0] if args else None
        if key is None:
            matches = await self.filter(**kwargs).to_list(limit_override=2)
            if not matches:
                return None
            if len(matches) > 1:
                raise ValueError(
                    "get() returned more than one result. Use filter() or all() instead."
                )
            return matches[0]

        response = await self.api.client.request(
            "GET", self._detail_path_template.replace("{id}", str(key))
        )
        if response.status == 404:
            return None
        _raise_for_status(response)
        payload = _decode_json(response)
        return self._make_record(payload, has_details=True)

    async def create(self, *args: Any, **kwargs: Any) -> Record | list[Record]:
        """Create one or many records via ``POST`` to the list endpoint.

        Calling ``create(name="sw-1", site={"id": 1})`` posts a single object;
        calling ``create([{...}, {...}])`` posts a bulk list.

        Returns:
            A :class:`Record` for single-object creates, or a ``list[Record]``
            for bulk creates.
        """
        payload = _payload_from_args(*args, **kwargs)
        response = await self.api.client.request("POST", self._list_path, payload=payload)
        _raise_for_status(response)
        decoded = _decode_json(response)
        return self._wrap_result(decoded, has_details=True)

    async def update(self, objects: list[Any]) -> list[Record]:
        """Bulk-update records via ``PATCH`` to the list endpoint.

        Args:
            objects: A list where each item is either a :class:`Record` or a
                ``dict`` carrying the fields to update (each must include
                ``id``).

        Returns:
            The list of updated records as returned by the server.
        """
        response = await self.api.client.request(
            "PATCH", self._list_path, payload=_normalize_bulk_objects(objects)
        )
        _raise_for_status(response)
        decoded = _decode_json(response)
        wrapped = self._wrap_result(decoded, has_details=True)
        return wrapped if isinstance(wrapped, list) else [wrapped]

    async def delete(self, objects: Any) -> bool:
        """Bulk-delete records by id(s) or Record instance(s) via ``DELETE``.

        ``objects`` may be a single id, a single ``Record``, or a list of
        either. :class:`RecordSet` instances are **not** accepted directly —
        call ``await recordset.delete()`` instead, which materialises the set
        first.

        Returns:
            ``True`` on success. The server returns ``204 No Content`` and the
            facade does not surface a body.
        """
        payload = _normalize_delete_objects(objects)
        response = await self.api.client.request("DELETE", self._list_path, payload=payload)
        _raise_for_status(response)
        return True

    async def choices(self) -> dict[str, Any]:
        """Return the ``OPTIONS`` action map for the list endpoint.

        Falls back from ``POST`` to ``PUT`` actions and to an empty mapping
        when neither is present. Useful for introspecting writable fields and
        their declared choices.
        """
        response = await self.api.client.request("OPTIONS", self._list_path)
        _raise_for_status(response)
        payload = _decode_json(response)
        if not isinstance(payload, dict):
            raise ContentError(response)
        actions = payload.get("actions", {})
        if not isinstance(actions, dict):
            return {}
        post_actions = actions.get("POST")
        if isinstance(post_actions, dict):
            return post_actions
        put_actions = actions.get("PUT")
        return put_actions if isinstance(put_actions, dict) else {}

    async def count(self, *args: str, **kwargs: Any) -> int:
        """Return the total number of records matching the given filters.

        Accepts the same arguments as :meth:`filter`. Works regardless of the
        active pagination mode: cursor responses set ``count: null``, so this
        method probes the offset representation under the hood when needed.
        """
        records = self.filter(*args, **kwargs)
        return await records.total()

    def detail_endpoint(self, spec: DetailEndpointSpec) -> DetailEndpoint:
        if spec.multi_format:
            return ROMultiFormatDetailEndpoint(self.api, self, spec.name)
        if spec.read_only:
            return RODetailEndpoint(self.api, self, spec.name)
        return DetailEndpoint(self.api, self, spec.name)

    def _make_record(self, payload: dict[str, Any], *, has_details: bool) -> Record:
        record_type = RECORD_TYPES.get((self.group, self.resource), Record)
        return record_type(self.api, self, payload, has_details=has_details)

    def _wrap_result(self, payload: Any, *, has_details: bool) -> Any:
        if isinstance(payload, list):
            return [
                self._make_record(item, has_details=has_details) if isinstance(item, dict) else item
                for item in payload
            ]
        if isinstance(payload, dict):
            return self._make_record(payload, has_details=has_details)
        return payload


class DetailEndpoint:
    def __init__(self, api: Api, endpoint: Endpoint, name: str) -> None:
        self.api = api
        self.endpoint = endpoint
        self.name = name

    def _path(self, record: Record) -> str:
        record_id = getattr(record, "id", None)
        if record_id is None:
            raise ValueError("Detail endpoints require a record with an id")
        return f"{self.endpoint._detail_path_template.replace('{id}', str(record_id)).rstrip('/')}/{self.name}/"

    async def list(self, record: Record, **query: Any) -> Any:
        response = await self.api.client.request(
            "GET",
            self._path(record),
            query={key: str(value) for key, value in query.items()},
            expect_json=not self._returns_raw(query),
        )
        _raise_for_status(response, detail_endpoint=True)
        if self._returns_raw(query):
            return response.text
        return _decode_json(response)

    async def create(self, record: Record, data: Any = None) -> Any:
        response = await self.api.client.request("POST", self._path(record), payload=data)
        _raise_for_status(response, detail_endpoint=True)
        return _decode_json(response)

    def _returns_raw(self, query: dict[str, Any]) -> bool:
        return False


class RODetailEndpoint(DetailEndpoint):
    async def create(self, record: Record, data: Any = None) -> Any:
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute 'create'")


class ROMultiFormatDetailEndpoint(RODetailEndpoint):
    def _returns_raw(self, query: dict[str, Any]) -> bool:
        render = query.get("render")
        return render is not None and str(render).lower() != "json"


class RecordSet:
    """Async-iterable, lazily-paginated view of a NetBox list endpoint.

    Selects between cursor and offset pagination based on the resolved mode:

    - ``"cursor"`` (NetBox >= 4.6) seeds ``start=`` / ``limit=`` and derives the
      next cursor from the last result's ``id``.
    - ``"offset"`` walks the server-provided ``next`` URL.
    - ``"auto"`` defers the decision until the first fetch and resolves via a
      cached ``Api.client.get_version()`` probe.

    Public attributes:
        endpoint: The :class:`Endpoint` that produced this record set.
        query: The original filter query (read-only copy).
        limit: Page size requested by the caller (``0`` means "let the SDK pick").
        offset: Offset seed (offset mode), if any.
        start: Cursor seed (cursor mode), if any.
        count: Total row count, populated from ``count`` in offset responses or
            via :meth:`total` in cursor mode.
    """

    def __init__(
        self,
        endpoint: Endpoint,
        *,
        query: dict[str, str],
        limit: int = 0,
        offset: int | None = None,
        start: int | None = None,
        mode: PaginationMode | None = None,
    ) -> None:
        if start is not None and offset is not None:
            raise ValueError("'start' and 'offset' are mutually exclusive")
        self.endpoint: Endpoint = endpoint
        self.query: dict[str, str] = dict(query)
        self.limit: int = limit
        self.offset: int | None = offset
        self.start: int | None = start
        self.count: int | None = None
        # Mode resolution: explicit kwarg > Api.pagination_mode > "auto".
        if mode is not None:
            self._requested_mode: PaginationMode = mode
        else:
            self._requested_mode = endpoint.api.pagination_mode
        # If the caller passed start=, force cursor mode.
        if start is not None:
            self._requested_mode = "cursor"
        # If the caller passed offset=, force offset mode (preserve legacy).
        elif offset is not None:
            self._requested_mode = "offset"
        self._mode: ResolvedPaginationMode | None = (
            cast(ResolvedPaginationMode, self._requested_mode)
            if self._requested_mode in ("cursor", "offset")
            else None
        )
        self._next_path: str | None = endpoint._list_path
        self._next_query: dict[str, str] = dict(query)
        self._buffer: deque[Record] = deque()
        self._started: bool = False
        self._last_pk: int | None = None

    def __aiter__(self) -> RecordSet:
        return self

    async def __anext__(self) -> Record:
        if self._buffer:
            return self._buffer.popleft()
        if self._started and self._next_path is None:
            raise StopAsyncIteration
        if not self._started:
            await self._initialize_first_page()
            self._started = True
        await self._fetch_next_page()
        if not self._buffer:
            raise StopAsyncIteration
        return self._buffer.popleft()

    async def _initialize_first_page(self) -> None:
        """Resolve auto mode and seed the first request's query parameters.

        In cursor mode this rejects an ``ordering`` filter (NetBox enforces
        this server-side) and seeds ``start`` and ``limit``. In offset mode
        this only adds ``limit`` / ``offset`` when the caller supplied them.
        """
        if self._mode is None:
            self._mode = await self.endpoint.api._resolve_pagination_mode()
        if self._mode == "cursor":
            if "ordering" in self._next_query:
                raise ValueError(
                    "Ordering cannot be specified in conjunction with cursor-based pagination"
                )
            self._next_query["start"] = str(self.start if self.start is not None else 0)
            self._next_query["limit"] = str(self.limit or DEFAULT_CURSOR_PAGE_SIZE)
        else:
            if self.limit:
                self._next_query["limit"] = str(self.limit)
            if self.offset is not None:
                self._next_query["offset"] = str(self.offset)

    async def _fetch_next_page(self) -> None:
        """Fetch the next page and populate the internal record buffer."""
        if self._next_path is None:
            return
        response = await self.endpoint.api.client.request(
            "GET", self._next_path, query=self._next_query or None
        )
        _raise_for_status(response)
        payload = _decode_json(response)
        if not isinstance(payload, dict):
            raise ContentError(response)
        results = payload.get("results", [])
        if not isinstance(results, list):
            raise ContentError(response)
        raw_count = payload.get("count")
        if isinstance(raw_count, int):
            self.count = raw_count
        self._buffer = deque(
            self.endpoint._make_record(item, has_details=False) if isinstance(item, dict) else item
            for item in results
        )
        if self._mode == "cursor":
            self._advance_cursor(results)
        else:
            self._advance_offset(payload)

    def _advance_cursor(self, results: list[Any]) -> None:
        """Derive the next cursor from the last item's ``id``.

        Pagination terminates when the page is empty, shorter than the
        requested limit, or when the last item is missing a usable ``id``.
        """
        page_limit = int(self._next_query.get("limit") or DEFAULT_CURSOR_PAGE_SIZE)
        last_pk: int | None = None
        if results:
            last = results[-1]
            if isinstance(last, dict):
                value = last.get("id")
                if isinstance(value, int):
                    last_pk = value
        # Stop when the page is short or we cannot derive a cursor.
        if not results or len(results) < page_limit or last_pk is None:
            self._next_path = None
            self._next_query = {}
            return
        self._last_pk = last_pk
        self._next_query = {**self._next_query, "start": str(last_pk + 1)}

    def _advance_offset(self, payload: dict[str, Any]) -> None:
        """Follow the server-provided ``next`` URL for offset pagination."""
        next_value = payload.get("next")
        if isinstance(next_value, str) and next_value:
            split = urlsplit(next_value)
            self._next_path = split.path
            self._next_query = dict(parse_qsl(split.query))
        else:
            self._next_path = None
            self._next_query = {}

    async def to_list(self, *, limit_override: int | None = None) -> list[Record]:
        """Materialise the record set into a list.

        Args:
            limit_override: Stop after this many records. ``None`` (default)
                drains the entire iterator.
        """
        items: list[Record] = []
        async for item in self:
            items.append(item)
            if limit_override is not None and len(items) >= limit_override:
                break
        return items

    async def total(self) -> int:
        """Return the total row count for this filter, regardless of mode.

        Cursor responses set ``count: null`` for performance, so this method
        probes the offset representation (``?limit=1&offset=0``) once and
        caches the result on :attr:`count`.

        Raises:
            ContentError: When the probe response is malformed.
        """
        if self.count is not None:
            return self.count
        # Always probe with offset=0 — cursor responses set count: null for performance,
        # so we explicitly use the offset-paginated representation here.
        probe_query: dict[str, str] = {
            key: value for key, value in self.query.items() if key not in ("start", "ordering")
        }
        probe_query["limit"] = "1"
        probe_query["offset"] = "0"
        response = await self.endpoint.api.client.request(
            "GET",
            self.endpoint._list_path,
            query=probe_query,
        )
        _raise_for_status(response)
        payload = _decode_json(response)
        if not isinstance(payload, dict):
            raise ContentError(response)
        count = payload.get("count")
        if not isinstance(count, int):
            raise ContentError(response)
        self.count = count
        return count

    async def update(self, **kwargs: Any) -> list[Record] | None:
        """Apply ``kwargs`` to every record in the set and bulk-update.

        Iterates the record set, assigns the supplied fields, then issues a
        single bulk PATCH for records whose state actually changed.

        Returns:
            The list of updated records, or ``None`` when no record changed.
        """
        updates: list[dict[str, Any]] = []
        async for record in self:
            record.assign(kwargs)
            changed = record.updates()
            if changed:
                changed["id"] = record.id
                updates.append(changed)
        if not updates:
            return None
        return await self.endpoint.update(updates)

    async def delete(self) -> bool:
        """Materialise this RecordSet and bulk-delete every record it yields.

        Iteration drains the paginator (one or more GETs) before the DELETE
        request is issued; an empty set is a no-op DELETE — no DELETE request
        is sent and ``True`` is returned.
        """
        records = await self.to_list()
        if not records:
            return True
        return await self.endpoint.delete(records)


class Record:
    # Attribute names that bypass __setattr__'s data-coercion path. Any other
    # name lands in self._data and will be sent to the server on save().
    # Keep this in sync with the attributes assigned in __init__ below.
    _RECORD_ATTRS: ClassVar[frozenset[str]] = frozenset(
        {"api", "endpoint", "_data", "_has_details", "_initial"}
    )

    def __init__(
        self, api: Api, endpoint: Endpoint | None, values: dict[str, Any], *, has_details: bool
    ) -> None:
        object.__setattr__(self, "api", api)
        object.__setattr__(
            self, "endpoint", endpoint or api.endpoint_for_path(values.get("url", ""))
        )
        object.__setattr__(self, "_data", {})
        object.__setattr__(self, "_has_details", has_details)
        object.__setattr__(self, "_initial", {})
        self._merge(values)
        object.__setattr__(self, "_initial", self.serialize())

    def __getattr__(self, name: str) -> Any:
        data = object.__getattribute__(self, "_data")
        if name in data:
            return data[name]
        endpoint = object.__getattribute__(self, "endpoint")
        if endpoint is not None:
            specs = DETAIL_ENDPOINT_SPECS.get((endpoint.group, endpoint.resource), {})
            if name in specs:
                return BoundDetailEndpoint(endpoint.detail_endpoint(specs[name]), self)
        raise AttributeError(f'object has no attribute "{name}"')

    def __setattr__(self, name: str, value: Any) -> None:
        if name in type(self)._RECORD_ATTRS:
            object.__setattr__(self, name, value)
        else:
            self._data[name] = _coerce_nested(self.api, self.endpoint, value)

    def __iter__(self) -> Iterator[tuple[str, Any]]:
        return iter(self._data.items())

    def __str__(self) -> str:
        for key in ("name", "label", "display", "display_name"):
            value = self._data.get(key)
            if value:
                return str(value)
        return repr(self._data.get("id", self._data))

    def assign(self, data: dict[str, Any]) -> None:
        for key, value in data.items():
            setattr(self, key, value)

    async def full_details(self) -> Self:
        if self._has_details:
            return self
        url = self._data.get("url")
        if not isinstance(url, str) or not url:
            return self
        split = urlsplit(url)
        response = await self.api.client.request(
            "GET", split.path, query=dict(parse_qsl(split.query)) or None
        )
        _raise_for_status(response)
        payload = _decode_json(response)
        if not isinstance(payload, dict):
            raise ContentError(response)
        self._merge(payload)
        object.__setattr__(self, "_has_details", True)
        object.__setattr__(self, "_initial", self.serialize())
        return self

    def serialize(self) -> dict[str, Any]:
        return {key: _serialize_value(value) for key, value in self._data.items() if key != "url"}

    def updates(self) -> dict[str, Any]:
        current = self.serialize()
        initial = object.__getattribute__(self, "_initial")
        return {key: value for key, value in current.items() if initial.get(key) != value}

    async def save(self) -> bool | None:
        endpoint = self.endpoint
        if endpoint is None:
            raise ValueError("Record is not attached to an endpoint")
        changes = self.updates()
        if not changes:
            return None
        record_id = self._data.get("id")
        if record_id is None:
            raise ValueError("Record is missing an id")
        response = await self.api.client.request(
            "PATCH",
            endpoint._detail_path_template.replace("{id}", str(record_id)),
            payload=changes,
        )
        _raise_for_status(response)
        payload = _decode_json(response)
        if isinstance(payload, dict):
            self._merge(payload)
            object.__setattr__(self, "_initial", self.serialize())
        return True

    async def update(self, data: dict[str, Any]) -> bool | None:
        self.assign(data)
        return await self.save()

    async def delete(self) -> bool:
        endpoint = self.endpoint
        if endpoint is None:
            raise ValueError("Record is not attached to an endpoint")
        record_id = self._data.get("id")
        if record_id is None:
            raise ValueError("Record is missing an id")
        response = await self.api.client.request(
            "DELETE", endpoint._detail_path_template.replace("{id}", str(record_id))
        )
        _raise_for_status(response)
        return True

    def _merge(self, values: dict[str, Any]) -> None:
        for key, value in values.items():
            self._data[key] = _coerce_nested(self.api, self.endpoint, value)


class TraceableRecord(Record):
    async def trace(self) -> Any:
        endpoint = self.endpoint
        if endpoint is None:
            raise ValueError("Record is not attached to an endpoint")
        path = endpoint.api.schema.trace_path(endpoint.group, endpoint.resource)
        if path is None:
            raise AttributeError("trace")
        record_id = self._data.get("id")
        if record_id is None:
            raise ValueError("Record is missing an id")
        response = await self.api.client.request("GET", path.replace("{id}", str(record_id)))
        _raise_for_status(response, detail_endpoint=True)
        return _decode_json(response)


class PathableRecord(Record):
    async def paths(self) -> Any:
        endpoint = self.endpoint
        if endpoint is None:
            raise ValueError("Record is not attached to an endpoint")
        path = endpoint.api.schema.paths_path(endpoint.group, endpoint.resource)
        if path is None:
            raise AttributeError("paths")
        record_id = self._data.get("id")
        if record_id is None:
            raise ValueError("Record is missing an id")
        response = await self.api.client.request("GET", path.replace("{id}", str(record_id)))
        _raise_for_status(response, detail_endpoint=True)
        return _decode_json(response)


class DeviceRecord(TraceableRecord):
    pass


class RackRecord(Record):
    pass


class PrefixRecord(Record):
    pass


class IpRangeRecord(Record):
    pass


class VlanGroupRecord(Record):
    pass


class VirtualMachineRecord(Record):
    pass


class CircuitTerminationRecord(PathableRecord):
    pass


RECORD_TYPES: dict[tuple[str, str], type[Record]] = {
    ("dcim", "devices"): DeviceRecord,
    ("dcim", "interfaces"): TraceableRecord,
    ("dcim", "power-ports"): TraceableRecord,
    ("dcim", "power-outlets"): TraceableRecord,
    ("dcim", "console-ports"): TraceableRecord,
    ("dcim", "console-server-ports"): TraceableRecord,
    ("dcim", "power-feeds"): TraceableRecord,
    ("dcim", "front-ports"): PathableRecord,
    ("dcim", "rear-ports"): PathableRecord,
    ("dcim", "racks"): RackRecord,
    ("ipam", "prefixes"): PrefixRecord,
    ("ipam", "ip-ranges"): IpRangeRecord,
    ("ipam", "vlan-groups"): VlanGroupRecord,
    ("virtualization", "virtual-machines"): VirtualMachineRecord,
    ("circuits", "circuit-terminations"): CircuitTerminationRecord,
    ("circuits", "virtual-circuit-terminations"): CircuitTerminationRecord,
}


class BoundDetailEndpoint:
    def __init__(self, endpoint: DetailEndpoint, record: Record) -> None:
        self._endpoint = endpoint
        self._record = record

    async def list(self, **query: Any) -> Any:
        return await self._endpoint.list(self._record, **query)

    async def create(self, data: Any = None) -> Any:
        return await self._endpoint.create(self._record, data=data)


def _payload_from_args(*args: Any, **kwargs: Any) -> Any:
    if args and kwargs:
        raise ValueError("Use either positional payload or keyword fields, not both")
    if args:
        return args[0]
    return kwargs


def _normalize_bulk_objects(objects: list[Any]) -> list[Any]:
    normalized: list[Any] = []
    for item in objects:
        if isinstance(item, Record):
            normalized.append(item.serialize() | {"id": getattr(item, "id", None)})
        else:
            normalized.append(item)
    return normalized


def _normalize_delete_objects(objects: Any) -> list[Any]:
    if isinstance(objects, RecordSet):
        raise ValueError("Use await recordset.delete() to delete a RecordSet")
    if not isinstance(objects, list):
        objects = [objects]
    normalized: list[Any] = []
    for item in objects:
        if isinstance(item, Record):
            normalized.append(getattr(item, "id"))
        else:
            normalized.append(item)
    return normalized


def _validate_filters(
    schema: SchemaIndex,
    group: str,
    resource: str,
    list_path: str,
    query: dict[str, str],
) -> None:
    """Reject query keys that are not declared as filter params on the OpenAPI list operation.

    Pure function: no side effects, no dependence on any Endpoint instance state.
    Raises ``ParameterValidationError`` with the offending parameter names.
    """
    allowed = {param.name for param in schema.filter_params(group, resource)}
    invalid = sorted(key for key in query if key not in allowed)
    if invalid:
        errors = [f"'{key}' is not allowed as parameter on path '{list_path}'." for key in invalid]
        raise ParameterValidationError(errors)


def _coerce_nested(api: Api, endpoint: Endpoint | None, value: Any) -> Any:
    if isinstance(value, dict) and _looks_like_record(value):
        nested_endpoint = api.endpoint_for_path(value.get("url", "")) or endpoint
        record_type = Record
        if nested_endpoint is not None:
            record_type = RECORD_TYPES.get(
                (nested_endpoint.group, nested_endpoint.resource), Record
            )
        return record_type(api, nested_endpoint, value, has_details=bool(value.get("url")))
    if isinstance(value, list):
        return [_coerce_nested(api, endpoint, item) for item in value]
    return value


def _looks_like_record(value: dict[str, Any]) -> bool:
    keys = set(value)
    if "url" in keys:
        return True
    if {"label", "value"} <= keys:
        return True
    if "id" in keys and keys & {"name", "display", "display_name", "label", "value"}:
        return True
    return False


def _serialize_value(value: Any) -> Any:
    if isinstance(value, Record):
        record_id = value._data.get("id")
        if record_id is not None:
            return record_id
        return value.serialize()
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize_value(item) for key, item in value.items()}
    return value


def _decode_json(response: ApiResponse) -> Any:
    try:
        return response.json()
    except json.JSONDecodeError as exc:
        raise ContentError(response) from exc


def _raise_for_status(response: ApiResponse, *, detail_endpoint: bool = False) -> None:
    if 200 <= response.status < 300:
        return
    if detail_endpoint and response.status == 409:
        raise AllocationError(response)
    raise RequestError(response)
