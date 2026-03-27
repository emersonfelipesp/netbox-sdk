"""Async convenience layer that exposes PyNetBox-like NetBox SDK features."""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from netbox_sdk.client import ApiResponse, NetBoxApiClient, RequestError
from netbox_sdk.config import Config
from netbox_sdk.schema import ResourcePaths, SchemaIndex, build_schema_index, parse_group_resource

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


class ContentError(RuntimeError):
    def __init__(self, response: ApiResponse) -> None:
        self.response = response
        super().__init__("The server returned invalid (non-json) data.")


class AllocationError(RuntimeError):
    def __init__(self, response: ApiResponse) -> None:
        self.response = response
        super().__init__("The requested allocation could not be fulfilled.")


class ParameterValidationError(ValueError):
    def __init__(self, errors: list[str] | str) -> None:
        self.error = errors
        super().__init__(f"The request parameter validation returned an error: {errors}")


def _is_v2_token(token: str | None) -> bool:
    return bool(token and token.startswith("nbt_") and "." in token)


def api(
    url: str,
    token: str | None = None,
    *,
    strict_filters: bool = False,
    client: NetBoxApiClient | None = None,
    schema: SchemaIndex | None = None,
) -> Api:
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
    return Api(client=client, schema=schema, strict_filters=strict_filters)


class Api:
    def __init__(
        self,
        *,
        client: NetBoxApiClient,
        schema: SchemaIndex | None = None,
        strict_filters: bool = False,
    ) -> None:
        self.client = client
        self.schema = schema or build_schema_index()
        self.strict_filters = strict_filters
        for name in APP_NAMES:
            setattr(self, name, App(self, name))
        self.plugins = PluginsApp(self)

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

    def all(self, limit: int = 0, offset: int | None = None) -> RecordSet:
        if limit == 0 and offset is not None:
            raise ValueError("offset requires a positive limit value")
        return RecordSet(self, query={}, limit=limit, offset=offset)

    def filter(self, *args: str, **kwargs: Any) -> RecordSet:
        limit = int(kwargs.pop("limit")) if "limit" in kwargs else 0
        offset = int(kwargs.pop("offset")) if "offset" in kwargs else None
        strict_filters = kwargs.pop("strict_filters", self.api.strict_filters)
        if args:
            kwargs["q"] = args[0]
        if limit == 0 and offset is not None:
            raise ValueError("offset requires a positive limit value")
        query = {key: "null" if value is None else str(value) for key, value in kwargs.items()}
        if strict_filters:
            self._validate_filters(query)
        return RecordSet(self, query=query, limit=limit, offset=offset)

    async def get(self, *args: Any, **kwargs: Any) -> Record | None:
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

    async def create(self, *args: Any, **kwargs: Any) -> Any:
        payload = _payload_from_args(*args, **kwargs)
        response = await self.api.client.request("POST", self._list_path, payload=payload)
        _raise_for_status(response)
        decoded = _decode_json(response)
        return self._wrap_result(decoded, has_details=True)

    async def update(self, objects: list[Any]) -> Any:
        response = await self.api.client.request(
            "PATCH", self._list_path, payload=_normalize_bulk_objects(objects)
        )
        _raise_for_status(response)
        decoded = _decode_json(response)
        return self._wrap_result(decoded, has_details=True)

    async def delete(self, objects: Any) -> bool:
        payload = _normalize_delete_objects(objects)
        response = await self.api.client.request("DELETE", self._list_path, payload=payload)
        _raise_for_status(response)
        return True

    async def choices(self) -> dict[str, Any]:
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
        records = self.filter(*args, **kwargs)
        return await records.total()

    def _validate_filters(self, query: dict[str, str]) -> None:
        allowed = {param.name for param in self.api.schema.filter_params(self.group, self.resource)}
        invalid = sorted(key for key in query if key not in allowed)
        if invalid:
            errors = [
                f"'{key}' is not allowed as parameter on path '{self._list_path}'."
                for key in invalid
            ]
            raise ParameterValidationError(errors)

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
    def __init__(
        self,
        endpoint: Endpoint,
        *,
        query: dict[str, str],
        limit: int = 0,
        offset: int | None = None,
    ) -> None:
        self.endpoint = endpoint
        self.query = dict(query)
        self.limit = limit
        self.offset = offset
        self.count: int | None = None
        self._next_path: str | None = endpoint._list_path
        self._next_query: dict[str, str] = dict(query)
        if limit:
            self._next_query["limit"] = str(limit)
        if offset is not None:
            self._next_query["offset"] = str(offset)
        self._buffer: list[Record] = []
        self._started = False

    def __aiter__(self) -> RecordSet:
        return self

    async def __anext__(self) -> Record:
        if self._buffer:
            return self._buffer.pop(0)
        if self._started and self._next_path is None:
            raise StopAsyncIteration
        self._started = True
        await self._fetch_next_page()
        if not self._buffer:
            raise StopAsyncIteration
        return self._buffer.pop(0)

    async def _fetch_next_page(self) -> None:
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
        self.count = payload.get("count") if isinstance(payload.get("count"), int) else self.count
        if not isinstance(results, list):
            raise ContentError(response)
        self._buffer = [
            self.endpoint._make_record(item, has_details=False) if isinstance(item, dict) else item
            for item in results
        ]
        next_value = payload.get("next")
        if isinstance(next_value, str) and next_value:
            split = urlsplit(next_value)
            self._next_path = split.path
            self._next_query = {key: value for key, value in parse_qsl(split.query)}
        else:
            self._next_path = None
            self._next_query = {}

    async def to_list(self, *, limit_override: int | None = None) -> list[Record]:
        items: list[Record] = []
        async for item in self:
            items.append(item)
            if limit_override is not None and len(items) >= limit_override:
                break
        return items

    async def total(self) -> int:
        if self.count is not None:
            return self.count
        response = await self.endpoint.api.client.request(
            "GET",
            self.endpoint._list_path,
            query={**self.query, "limit": "1"},
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

    async def update(self, **kwargs: Any) -> Any:
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
        return await self.endpoint.delete(self)


class Record:
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
        if name in {"api", "endpoint", "_data", "_has_details", "_initial"}:
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

    async def full_details(self) -> Record:
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
        response = await self.api.client.request("GET", path.replace("{id}", str(self._data["id"])))
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
        response = await self.api.client.request("GET", path.replace("{id}", str(self._data["id"])))
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
