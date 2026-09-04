# netbox_sdk — SDK Package — AGENTS.md Mirror

This file mirrors the sibling `CLAUDE.md` guidance for agents that read `AGENTS.md`. Treat `CLAUDE.md` as the source material; the content below preserves the current guide.

## Source

@CLAUDE.md

---

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
├── schema_resolution.py
├── services.py
├── plugin_discovery.py
├── plugin_bridge.py
├── proxbox.py
├── proxbox_jobs.py
├── proxbox_sync.py
├── exceptions.py
├── custom_fields.py
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
- `netbox_sdk.client` — async API client and connection probe; `normalize_request_path()` is the shared client-free path validation/canonicalization authority used by previews and dispatch
- `netbox_sdk.decorators` — reusable decorator factories for SDK command/resource wrapper metadata
- `netbox_sdk.exceptions` — shared error types (`RequestError`, `BulkOperationEntryError`, facade errors, `JsonPayloadError`). `RequestError` parses NetBox 4.7 bulk-failure bodies onto `.detail` and `.entry_errors`; malformed locators (both, neither, bools, negatives) are dropped
- `netbox_sdk.custom_fields` — `custom_fields_for_write(..., selection=...)` unwraps only named 4.7 selection fields; unnamed JSON values, including exact `{value, label}` objects, are copied unchanged. `custom_field_write_value()` is the per-value converter for a value already known to be a selection
- `netbox_sdk.facade` — async convenience facade exposed via synchronous `api()`
  construction and asynchronous `async_api()` construction. `api()` performs no
  network access during construction; without `schema=`, it detects and installs
  the connected release before the first schema-dependent request. Detection
  failures propagate. Use `async_api()` for eager detection and runtime-resource
  discovery, or pass a matching `SchemaIndex` to pin the contract
- `netbox_sdk.typed_api` — versioned typed client factory exposed via `typed_api()`
- `netbox_sdk.typed_runtime` — shared request/response plumbing behind every generated typed binding. `response_model_for_payload()` selects the response model from the **shape of the request payload**, because NetBox's bulk endpoints reuse the collection path: a list body commits a batch and returns a list, while the upstream OpenAPI document declares only the singular response. Validating a committed batch against the singular model would raise `TypedResponseValidationError` *after the server had already applied it*, and a retry would duplicate the rows. Applies to `POST`/`PUT`/`PATCH` through the one shared request path; bulk `DELETE` returns a bodyless `204`, so the call returns `None` with nothing to validate
- `netbox_sdk.models` / `netbox_sdk.typed_versions` — committed generated models and typed bindings
- `netbox_sdk.http_cache` — filesystem cache primitives
- `netbox_sdk.http_ssl` — TLS verification configuration and connector construction
- `netbox_sdk.telemetry` — optional OpenTelemetry request tracing with lazy guarded imports
- `netbox_sdk.schema` — OpenAPI loading and indexing; `load_openapi_schema()` / `build_schema_index()` default to the bundled NetBox 4.7 GA schema and accept supported release lines such as `version="4.5"`; `SchemaIndex.filter_params(group, resource)` excludes pagination params including `limit`, `offset`, `start`, `format`
- `netbox_sdk.versioning` — frozen release-line registry records owning bundled OpenAPI, generated-model, and typed-module artifacts; compatibility constants and helpers are views over this registry
- `netbox_sdk.schema_resolution` — shared CLI/environment pin parsing, clone-isolated bundled-index cache, connected release detection, and bundled/live/default precedence used by every surface. **Clone isolation covers the derived maps only**: `SchemaIndex.clone()` copies `operations` and the resource-path map, but every clone shares the one parsed document for that release line, because copying a 7.7-9.6 MB document per clone would cost more than the parse it avoids. `bundled_index()` therefore `freeze_document()`s the document before caching it, so mutating any nested part of `index.schema` raises `SchemaDocumentFrozenError` at the offending line instead of silently corrupting every later SDK, CLI, TUI and MCP consumer in the process. `FrozenDict`/`FrozenList` subclass the real builtins rather than wrapping in `MappingProxyType`, because the parser guards with `isinstance(value, dict)` and a mapping proxy would fail that check and silently disable parsing. `fetch_schema_for_client()` likewise returns a shared, frozen document on the bundled path — treat every schema document as read-only
- `netbox_sdk.services` — dynamic request resolution; `parse_key_value_pairs()` preserves repeated query keys as list values; `parse_header_pairs()` accepts `Header=Value` and `Header: Value`; `list_all_pages` preserves repeated `next` query params
- `netbox_sdk.typed_runtime` — `response_model_for_request()` selects a write's response model from the **request**: an affirmative `background` query flag (NetBox 4.7 `?background=true`) yields `BackgroundJobReference` for the `202` job body, taking precedence over body shape, since a queued batch returns a job for either a single object or a list; otherwise a list body validates as `list[Model]`. The 4.7 `background` parameter is declared by the operation-level generator overlay `apply_background_bulk_overlay` because the official `v4.7.0` GA artifact does not describe it and the overlay is limited to JSON-array bulk writes; the committed bundle stays byte-faithful and a guard test fails once upstream does describe it
- `netbox_sdk.metrics` — opt-in OTLP **metrics** (request counter + duration histogram). Unlike `telemetry` tracing, which needs an explicit `otel_enabled` opt-in, metrics activate on the presence of `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT` **or** `OTEL_EXPORTER_OTLP_ENDPOINT` alone, so a deployment already exporting telemetry needs no per-service wiring; `OTEL_SDK_DISABLED` and `OTEL_METRICS_EXPORTER=none` still win. **Cardinality is bounded by `operation_template()`**, which rewrites numeric and UUID path segments to `{id}` — a metric attribute must never carry a raw object id or one time series is created per object. Attributes: method, `url.template`, status, server address. Recorded in a `finally` so a failed request is still counted (status `None`), and `record_client_request()` never raises — a telemetry failure must not break the call it observes. Provider setup is lazy and idempotent and **reuses an already-configured host `MeterProvider`** rather than replacing it. No OpenTelemetry import happens at module import time, so the base SDK stays usable without the `otel` extra
- `netbox_sdk.plugin_discovery` — runtime plugin API discovery. **Capability probing uses a concrete record, never the `{id}` template**: DRF routers 404 the literal placeholder, so `OPTIONS` there silently hid every supported PATCH/PUT/DELETE and discovery fell back to GET-only. `_concrete_detail_probe()` derives a real URL from the sampled record's `url` — accepted only when it normalizes to a path **directly under** the collection (exactly one extra segment), which rejects external hosts and collection-escaping values — else it percent-encodes an `id`/`pk` so a hostile identifier cannot inject path segments. Methods are recorded against the published template. **Conservative by construction**: no safe sample, or a denied/unanswered `OPTIONS`, yields `GET` only; write methods are never inferred without an affirmative answer, and `OPTIONS` is the only verb discovery ever sends. ObjectType pagination preserves repeated query keys (`?tag=a&tag=b` used to collapse to `tag=b`, so page two was fetched with a different filter than the server asked for), keeps `next` under the API root, and terminates on a repeated page or `MAX_DISCOVERY_PAGES`
- `netbox_sdk.django_models.catalog` — **the one** Django model-build catalog service, used by both the SDK fetcher and the TUI. Two stores: a read-only **bundled** set shipped as package data under `netbox_sdk/django_models/model_builds/` and read via `importlib.resources` (so it works from a wheel, a zipimport, or a checkout alike), and a **user-writable** store at `$XDG_DATA_HOME/netbox-sdk/django-model-builds` (override with `NETBOX_SDK_MODEL_BUILDS_DIR`) that downloads and generated builds go to — never `site-packages`, which is often read-only. A downloaded build shadows a bundled one of the same tag. `available_tags()` merges both, deterministically newest-first by **numeric** version (`v4.5.10` above `v4.5.9`), so the SDK and TUI can never disagree. The bundled set is the deliberate supported subset — newest non-prerelease build per supported release line, published in `model_builds/manifest.json` — which is what keeps ~9.5 MB of `django_models_builds/` history out of the wheel; regenerate it with `scripts/build_model_catalog.py`, which also strips transient `/tmp/netbox-<tag>/` build paths from provenance. `django_models_builds/` at the repository root remains the full archive and generator input; it is **not** shipped
- `netbox_sdk.plugin_bridge` — versioned semantic plugin-manifest discovery and strict contract/input/output validation; discovery uses fresh bounded non-redirecting responses, accepts configured NetBox URL prefixes, enforces aggregate root/request/body/tool/time budgets, keeps advertised links and fixed tool targets same-origin/plugin-local, requires strict finite JSON, applies lossless integer semantics (large floats never round into another identity), accepts leap seconds only at normalized UTC month boundaries, rejects date-time normalization overflow, restricts reads to query-encodable schemas, and rejects unbounded schema features. Descriptor version 1 is generic; plugin repositories own their operation payload snapshots.
- `netbox_sdk.proxbox` — stable netbox-proxbox resource catalog plus catalog-backed request helper used by the dedicated CLI and TUI surfaces
- `netbox_sdk.proxbox_sync` — Proxbox scheduling/SSE/job-fetch helpers and `ProxboxSyncError`, which carries an optional structured `job_id` once scheduling has succeeded
- `netbox_sdk.proxbox_jobs` — read-only Proxbox **sync job** retrieval: parses core `core.Job` rows carrying a `proxbox_sync` block into `ProxboxSyncJobRecord`, mirrors the plugin's `is_proxbox_sync_job` predicate (data key / legacy queue / default name on an accepted queue / targeted-VM name, with the `queue_name or ""` normalisation), and runs a **bounded** scan of `/api/core/jobs/` because NetBox cannot filter on `data`. Two invariants are load-bearing: `ProxboxJobFilters.server_query()` may emit only names in `SERVER_PARAM_WHITELIST` — NetBox *silently ignores* unknown query parameters, so a typo would widen the query to every job in the instance rather than fail — and every listing returns `scanned` / `matched` / `truncated` / `window` so a truncated scan can never be mistaken for an exhaustive one. Parameter parsing is total: hostile or malformed `data` degrades to empty params and never raises, an empty `proxmox_endpoint_ids` means "all endpoints", and `sync_types: ["all"]` (or absent) covers every requested type. A scope that cannot be parsed is recorded as `INVALID` and matches **no** scoped query rather than every one (an unreadable endpoint list is not "all endpoints"); a legacy `Proxbox Sync: Virtual machine <id>` row has its scope reconstructed from its name, mirroring the plugin's own `_infer_targeted_vm_job_params`; `--errored` and `--user` are evaluated client-side on purpose — pushing the failure statuses down would discard completed-with-error rows, and the core `user` filter is an integer on NetBox 4.5 but a username on 4.6+, so only a local comparison is correct on every supported line
- `netbox_sdk.mock` — FastAPI-backed mock NetBox API used by tests and local development
- Shared cross-package helpers: `formatting`, `logging_runtime`, `output_safety`, `trace_ascii`, `demo_auth`, `django_models`

## Validation Expectations

- `python -c 'import netbox_sdk'` must work without CLI or TUI extras.
- `typed_api()` and bundled OpenAPI helpers support the stable NetBox release lines `4.7`, `4.6`, `4.5`, `4.4`, and `4.3`; the registry-derived default is 4.7. CLI, TUI, and MCP consume the same `schema_resolution` policy and honor the same version pin.
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
