# netbox_sdk — SDK Package

## Workspace Context

This file lives at `/root/personal-context/nmulticloud-context/netbox-sdk/netbox_sdk/CLAUDE.md` inside the `personal-context` workspace.
Workspace guidance: `/root/personal-context/CLAUDE.md`.
Per-repo deep-dive: `/root/personal-context/claude-reference/netbox-sdk.md`.
Submodule layout and cross-repo links: `/root/personal-context/claude-reference/dependency-map.md`.

---

Standalone NetBox REST API client library.

## Invariants

- `netbox_sdk` must not import `netbox_cli` or `netbox_tui`.
- Public imports use `netbox_sdk.*`, never legacy `sdk.*`.
- Bundled OpenAPI release-line schemas live under `netbox_sdk/reference/openapi/`.

## Package Structure

```
netbox_sdk/
├── __init__.py
├── branching.py
├── client.py
├── config.py
├── decorators.py
├── http_cache.py
├── http_ssl.py
├── telemetry.py
├── schema.py
├── services.py
├── plugin_discovery.py
├── proxbox.py
├── exceptions.py
├── logging_runtime.py
├── output_safety.py
├── trace_ascii.py
├── formatting.py
├── demo_auth.py
├── facade.py
├── typed_api.py
├── typed_runtime.py
├── versioning.py
├── mock/
├── models/
├── typed_versions/
├── django_models/
├── py.typed
└── reference/openapi/netbox-openapi-*.json
```

## Public Surface

- `netbox_sdk.config` — config model, profile persistence, auth headers
- `netbox_sdk.branching` — NetBox Branching API client, branch-scoped header helpers, job polling helpers
- `netbox_sdk.client` — async API client and connection probe; caller-supplied paths reject percent-encoded `/` and `\` separators before cache or network dispatch; normal and SSE request Authorization precedence is presence-based, so an explicitly empty per-call/scoped/persistent override remains anonymous and never falls through to the configured client credential; cache-generation lock outages explicitly bypass existing entries and persistence, synchronous filesystem-cache operations run through worker threads so lock contention cannot stall the asyncio event loop, and detail-action invalidation supports namespaced plugin routes ending in `resource/id/action`
- `netbox_sdk.decorators` — reusable decorator factories for SDK command/resource wrapper metadata
- `netbox_sdk.exceptions` — shared error types (`RequestError`, facade errors, `JsonPayloadError`, `PaginationError`)
- `netbox_sdk.facade` — async convenience facade exposed via `api()`
- `netbox_sdk.typed_api` — versioned typed client factory exposed via `typed_api()`
- `netbox_sdk.models` / `netbox_sdk.typed_versions` — committed generated models and typed bindings
- `netbox_sdk.http_cache` — filesystem cache primitives, including per-path and digest-keyed unavailable markers for failed invalidations/corrupted indexes, bounded contention-only `flock` retries, and ownership-safe portable stale-lock reclamation
- `netbox_sdk.http_ssl` — TLS verification configuration and connector construction
- `netbox_sdk.telemetry` — optional OpenTelemetry request tracing with lazy guarded imports
- `netbox_sdk.schema` — OpenAPI loading and indexing; `load_openapi_schema()` / `build_schema_index()` default to the bundled NetBox 4.6 schema and accept supported release lines such as `version="4.5"`; `SchemaIndex.filter_params(group, resource)` returns a sorted `list[FilterParam]` of filterable query parameters for the list endpoint (excludes pagination params including `limit`, `offset`, `start`, `format`, plus lookup-suffix variants such as `__ic`, `__n`; puts `q` first); `FilterParam` is a frozen Pydantic model with `.name`, `.label`, `.type` (`string|integer|boolean|enum|array`), `.choices` (non-empty only for enum), and `.description`
- `netbox_sdk.services` — dynamic request resolution; `parse_key_value_pairs()` preserves repeated query keys as list values; `parse_header_pairs()` accepts `Header=Value` and `Header: Value` forms; `ACTION_METHOD_MAP` includes bulk ops (`bulk-update`, `bulk-patch`, `bulk-delete`); `list_all_pages` follows NetBox pagination `next` links and returns a synthesised single-page response while preserving repeated `next` query params; a non-2xx status or unparseable body on any page (including a later page after earlier ones succeeded) returns that raw failing response instead of folding partial results into a synthesised `status=200` envelope, while malformed result arrays, repeated page targets, and non-progressing pages raise `PaginationError`
- `netbox_sdk.plugin_discovery` — runtime plugin API discovery
- `netbox_sdk.proxbox` — stable netbox-proxbox resource catalog plus catalog-backed request helper used by the dedicated CLI and TUI surfaces
- `netbox_sdk.proxbox_sync` — Proxbox scheduling/SSE/job-fetch helpers and `ProxboxSyncError`, which carries an optional structured `job_id` once scheduling has succeeded
- `netbox_sdk.mock` — FastAPI-backed mock NetBox API used by tests and local development
- Shared cross-package helpers: `formatting`, `logging_runtime`, `output_safety`, `trace_ascii`, `demo_auth`, `django_models`

## Validation Expectations

- `python -c 'import netbox_sdk'` must work without CLI or TUI extras.
- `typed_api()` and bundled OpenAPI helpers currently support NetBox release lines `4.6`, `4.5`, `4.4`, and `4.3`; the CLI defaults to 4.6 and can be pinned to 4.5/4.6 via `--netbox-version` or `NETBOX_SDK_NETBOX_VERSION`.
- SDK tests should import from `netbox_sdk`, not `sdk`.
- Consult [`reference/PYNETBOX.md`](../reference/PYNETBOX.md) when comparing SDK ergonomics to historical NetBox Python client behavior or prior-art feature patterns.

## Logging policy

- Use `logging.getLogger(__name__)` per module. Do not log secrets (tokens, passwords, full `Authorization` headers, or response bodies that may contain credentials).
- Prefer structured `extra` keys for machine-readable logs: `nbx_event` (short stable name), `request_path`, `http_method`, `http_status`, `profile`, `path` (filesystem), etc.
- **INFO**: one-line lifecycle (config save, request completed, logging init). **DEBUG**: cache/schema/plugin discovery detail, parse failures that are handled. **WARNING**: unreadable config, TLS verification disabled. **ERROR/exception**: unexpected failures with traceback when appropriate.

## Telemetry policy

- OpenTelemetry request tracing must stay disabled by default and must not import
  `opentelemetry.*` unless tracing is enabled.
- Spans may include HTTP method, host, path, response status, and SDK cache
  status. Never add tokens, `Authorization` headers, credentials, full URLs with
  query strings, or request/response bodies to spans or logs.
- Use a host application's global tracer provider when one exists; only
  `netbox_sdk.telemetry` may install the SDK fallback provider.
