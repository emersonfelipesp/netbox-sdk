# PyNetBox Reference

Internal reference for the `pynetbox` library as checked into `@pynetbox/` in this workspace. This is not a user guide; it is a maintainer-facing summary of how the library is structured, what features it exposes, and which design patterns matter when comparing it to `netbox-sdk`.

## What PyNetBox Is

- `pynetbox` is a synchronous Python client for the NetBox REST API.
- The local repo exports `pynetbox.api` as a lowercase alias of `pynetbox.core.api.Api`.
- The checked-in version is `7.6.1`.
- The checked-in docs say `pynetbox` 6.7+ supports NetBox 3.3 and above.

Its design is object-centric and `requests`-based: you navigate from an API object to apps, then endpoints, then records.

## Top-Level Architecture

PyNetBox is built around a small set of core abstractions:

- `Api`
  - entry point returned by `pynetbox.api(...)`
  - owns the base URL, token, `requests.Session`, threading flag, and strict-filter flag
  - pre-creates app objects like `dcim`, `ipam`, `extras`, `users`, `wireless`, `virtualization`, and `plugins`
- `App`
  - represents one NetBox app namespace such as `dcim` or `ipam`
  - turns attribute access into `Endpoint` objects
- `PluginsApp`
  - special app wrapper for plugin routes under `/api/plugins/...`
  - `nb.plugins.<plugin_name>` becomes an `App` with a `plugins/<plugin>` prefix
- `Endpoint`
  - represents one REST collection endpoint
  - implements CRUD and query helpers such as `.all()`, `.filter()`, `.get()`, `.create()`, `.update()`, `.delete()`, `.count()`, and `.choices()`
- `DetailEndpoint`
  - handles nested detail routes like `available-ips`, `available-prefixes`, `render-config`, or `units`
- `Request`
  - low-level HTTP transport wrapper around `requests.Session`
  - builds URLs, headers, query params, JSON vs multipart bodies, pagination, threading, and error translation
- `Record`
  - Python object built from one API response item
  - supports lazy detail hydration, diffing, save/update/delete, and nested object handling
- `RecordSet`
  - iterator wrapper returned by `.all()` and `.filter()`
  - streams paginated results and adds bulk update/delete helpers

The normal call path is:

`Api -> App -> Endpoint -> Request -> Record / RecordSet`

Example:

```python
import pynetbox

nb = pynetbox.api("https://netbox.example.com", token="...")
devices = nb.dcim.devices.all()
device = nb.dcim.devices.get(1)
```

## How the Main Components Work

### `Api`

`Api` normalizes the base URL to `<url>/api`, stores auth/session state, and exposes top-level NetBox apps as attributes.

Important methods and properties:

- `version`
  - issues a GET to the API root and reads the `API-Version` response header
- `status()`
  - fetches `/api/status/`
- `openapi()`
  - fetches and caches the OpenAPI schema in memory
  - for NetBox 3.5+ it uses `/api/schema/`
  - for older versions it uses `/api/docs/?format=openapi`
- `create_token(username, password)`
  - provisions a token via `/api/users/tokens/provision/`
  - stores the returned token on the `Api` instance
- `activate_branch(branch)`
  - context manager for the NetBox branching plugin
  - sets `X-NetBox-Branch` on the shared session using `branch.schema_id`

The transport is synchronous and built on a mutable shared `requests.Session`, exposed as `nb.http_session`. The docs explicitly position this as the extension point for custom headers, SSL settings, timeouts, retries, and other session-level behavior.

### `App` and `PluginsApp`

`App` is a thin namespace object. Accessing an attribute on an `App` creates an `Endpoint`.

```python
nb.dcim.devices
nb.ipam.prefixes
```

`PluginsApp` does the same thing but prefixes the path with `plugins/<plugin>`. This is how code reaches plugin endpoints:

```python
nb.plugins.branching.branches
```

`PluginsApp` also exposes `installed_plugins()` to query `/api/plugins/installed-plugins`.

### `Endpoint`

`Endpoint` is the main REST wrapper.

Key behavior:

- endpoint names convert underscores to dashes
  - `ip_addresses` maps to `ip-addresses`
- the return type is selected from app-specific model modules when possible
  - otherwise it falls back to generic `Record`
- all collection methods delegate to `Request`

Main methods:

- `.all(limit=0, offset=None)`
  - returns a `RecordSet`
  - iterates through paginated list responses
- `.filter(*args, **kwargs)`
  - converts positional arg to `q=<value>`
  - supports pagination kwargs like `limit` and `offset`
  - can validate GET parameters against the OpenAPI schema when strict filters are enabled
- `.get(...)`
  - fetches by ID or by filters
  - if filter-based lookup returns more than one object, it raises `ValueError`
  - returns `None` on 404 for ID lookups
- `.create(...)`
  - POSTs one object or a list of objects
  - returns `Record` or a list of `Record`s
- `.update(objects)`
  - bulk PATCH for a list of dicts or `Record`s
- `.delete(objects)`
  - bulk DELETE for a list of IDs, numeric strings, `Record`s, or `RecordSet`
- `.choices()`
  - issues `OPTIONS` and extracts choice metadata from `actions.POST` or `actions.PUT`
- `.count()`
  - requests only enough data to get the count

### `DetailEndpoint` Variants

PyNetBox treats nested detail routes as a separate abstraction instead of forcing everything through collection endpoints.

- `DetailEndpoint`
  - supports `.list()` and `.create()`
- `RODetailEndpoint`
  - read-only version
- `ROMultiFormatDetailEndpoint`
  - read-only endpoint that can return either structured JSON or raw non-JSON text
  - used for rack elevation, where `render="svg"` returns raw SVG

This is how PyNetBox models routes like:

- `available-ips`
- `available-prefixes`
- `available-vlans`
- `render-config`
- `napalm`
- `units`
- `elevation`

### `Request`

`Request` is the transport layer and owns most HTTP behavior.

Key responsibilities:

- normalize trailing slashes
- build object URLs from base path plus key
- merge filters and extra query params
- set auth headers
- choose JSON vs multipart encoding
- recurse through paginated responses
- optionally parallelize paginated GETs using a thread pool
- translate HTTP and content failures into library-specific exceptions

Auth behavior:

- v1 tokens use `Token <token>`
- v2 tokens are detected by the `nbt_...` format and use `Bearer <token>`

Pagination behavior:

- `.get()` detects list responses with `count`, `next`, and `results`
- if threading is enabled, it fetches later pages concurrently
- otherwise it follows `next` sequentially

File upload behavior:

- for POST/PUT/PATCH requests, file-like values are detected automatically
- when files are present, PyNetBox sends multipart form data instead of JSON
- supported inputs include:
  - real file objects
  - in-memory file-like objects with `.read()`
  - tuples such as `(filename, file_obj)` or `(filename, file_obj, content_type)`

### `Record` and `RecordSet`

`Record` is PyNetBox’s main data object. It is not just a DTO; it also owns mutation and lazy-loading behavior.

Important `Record` behavior:

- nested dicts are converted into nested `Record` instances unless explicitly treated as JSON fields
- generic object references can be mapped through content-type-aware model classes
- `__str__()` usually prefers `name`, `label`, or `display`
- missing attributes can trigger lazy hydration via `full_details()`
- `serialize()` converts the current object state back into API-ready data
- `updates()` computes a diff against the initial state
- `save()` PATCHes only changed fields
- `update({...})` is a convenience wrapper over assignment plus `save()`
- `delete()` deletes the single object

Lazy detail hydration matters: objects created from nested or brief responses may not contain every field. When code asks for a missing attribute, `Record.__getattr__` can issue another request to the object’s own URL and populate the full response.

`RecordSet` is an iterator around a streaming GET response:

- it is one-shot by default
- `len(recordset)` uses the cached count if available
- it supports bulk `.update(**kwargs)` and `.delete()`

This generator-oriented design is a recurring PyNetBox behavior. The docs repeatedly warn that `.all()` and `.filter()` results should be wrapped in `list(...)` if the caller needs to iterate more than once.

## Model Layer and App-Specific Features

PyNetBox adds endpoint-specific record classes under `pynetbox/models/*`. These classes mostly customize:

- string representations
- nested field typing
- detail endpoints exposed as properties
- trace/path helpers for cable-aware objects

Examples from the checked-in repo:

- `dcim.Devices`
  - typed nested fields like `device_type`, `primary_ip`, `primary_ip4`, `primary_ip6`
  - `.napalm`
  - `.render_config`
- `dcim.Interfaces`, `PowerPorts`, `PowerOutlets`, `ConsolePorts`, `ConsoleServerPorts`, `PowerFeeds`
  - inherit trace behavior via `TraceableRecord.trace()`
- `dcim.FrontPorts`, `RearPorts`
  - inherit path behavior via `PathableRecord.paths()`
- `dcim.Racks`
  - `.units`
  - `.elevation`
- `ipam.Prefixes`
  - `.available_ips`
  - `.available_prefixes`
- `ipam.IpRanges`
  - `.available_ips`
- `ipam.VlanGroups`
  - `.available_vlans`
- `circuits.CircuitTerminations` and `VirtualCircuitTerminations`
  - path-aware records

There is also a content-type mapper in `pynetbox.models.mapper` that maps generic object references like `dcim.device` or `ipam.prefix` back to specific `Record` subclasses where PyNetBox knows them.

## Main Features

Based on the local source, docs, and tests, the major features are:

- sync NetBox REST client with object-oriented traversal
- CRUD operations on standard endpoints
- bulk update and bulk delete helpers
- list query pagination with optional threaded page fetching
- OpenAPI retrieval and in-memory caching
- optional strict filter validation against OpenAPI
- pluggable `requests.Session`
- token provisioning
- branching plugin context support
- plugin endpoint support
- detail-endpoint helpers for allocation and generated resources
- file upload support for endpoints such as image attachments
- typed nested records and app-specific conveniences
- cable tracing and path traversal helpers
- multi-format detail endpoints such as rack elevation SVG rendering

## Exceptions and Failure Modes

PyNetBox defines a small set of transport and validation exceptions:

- `RequestError`
  - general HTTP failure wrapper
  - keeps the original request/response object and request body
- `ContentError`
  - response was successful enough to receive but not valid JSON when JSON was expected
- `AllocationError`
  - special case for 409 conflicts on allocation-style POSTs like `available-ips` or `available-prefixes`
- `ParameterValidationError`
  - strict filter validation failed against the OpenAPI spec

Important behavioral caveats:

- `.all()` and `.filter()` return one-shot iterators, not materialized lists
- `.get()` with filters can raise if more than one object matches
- lazy `full_details()` means attribute access can trigger extra network calls
- strict filter validation only applies to GET-style filtering, not every HTTP method
- threading improves large paginated reads but depends on sane NetBox pagination configuration
- the whole client is synchronous and session-shared, so transport behavior is process/thread sensitive in ways an async client is not

## Request and Data Semantics

PyNetBox is closer to a lightweight ORM-style client than to a schema-driven API wrapper.

Design characteristics:

- endpoint shape is inferred from attribute names instead of generated code or explicit operation tables
- response objects are long-lived and mutable
- object mutation is diff-based and patch-oriented
- nested objects are recursively wrapped instead of left as plain dicts
- the library leans on NetBox response conventions like `url`, `id`, `display`, `results`, and detail subroutes

This makes normal interactive use concise, but it also means behavior is tightly coupled to NetBox’s response structure and URL conventions.

## What Matters Relative to `netbox-sdk`

For `netbox-sdk` maintainers, the key comparisons are:

- `pynetbox` is synchronous and `requests`-based; `netbox-sdk` is async and `aiohttp`-based
- `pynetbox` is object/record oriented; `netbox-sdk` is schema-index and request-resolution oriented
- `pynetbox` discovers surface area mostly through attribute access and model classes; `netbox-sdk` leans on bundled OpenAPI and explicit runtime indexing
- `pynetbox` mutates hydrated record objects and diffs them on save; `netbox-sdk` does not use an ORM-like mutable record model
- `pynetbox` has transport/session mutability on a shared `requests.Session`; `netbox-sdk` keeps a clearer separation between config, client, schema, and service helpers

Useful prior-art ideas from `pynetbox`:

- strict filter validation to prevent accidental full-table scans
- detail-endpoint convenience wrappers for allocation and generated resources
- specialized helpers for domain-specific responses like cable tracing
- file upload auto-detection when an endpoint supports multipart

Patterns to understand but not copy blindly:

- implicit lazy network fetches on attribute access
- object mutation plus hidden diffing as the primary write path
- endpoint discovery primarily through dynamic attribute access
- tight coupling between response URL structure and runtime type reconstruction

For `netbox-sdk`, `pynetbox` is best treated as prior art on NetBox client ergonomics, not as a target architecture.
