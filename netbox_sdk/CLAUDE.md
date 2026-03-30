# netbox_sdk — SDK Package

Standalone NetBox REST API client library.

## Invariants

- `netbox_sdk` must not import `netbox_cli` or `netbox_tui`.
- Public imports use `netbox_sdk.*`, never legacy `sdk.*`.
- Bundled OpenAPI release-line schemas live under `netbox_sdk/reference/openapi/`.

## Package Structure

```
netbox_sdk/
├── __init__.py
├── client.py
├── config.py
├── http_cache.py
├── schema.py
├── services.py
├── plugin_discovery.py
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
├── models/
├── typed_versions/
├── django_models/
├── py.typed
└── reference/openapi/netbox-openapi-*.json
```

## Public Surface

- `netbox_sdk.config` — config model, profile persistence, auth headers
- `netbox_sdk.client` — async API client and connection probe
- `netbox_sdk.exceptions` — shared error types (`RequestError`, facade errors, `JsonPayloadError`)
- `netbox_sdk.facade` — async convenience facade exposed via `api()`
- `netbox_sdk.typed_api` — versioned typed client factory exposed via `typed_api()`
- `netbox_sdk.models` / `netbox_sdk.typed_versions` — committed generated models and typed bindings
- `netbox_sdk.http_cache` — filesystem cache primitives
- `netbox_sdk.schema` — OpenAPI loading and indexing
- `netbox_sdk.services` — dynamic request resolution
- `netbox_sdk.plugin_discovery` — runtime plugin API discovery
- Shared cross-package helpers: `formatting`, `logging_runtime`, `output_safety`, `trace_ascii`, `demo_auth`, `django_models`

## Validation Expectations

- `python -c 'import netbox_sdk'` must work without CLI or TUI extras.
- `typed_api()` currently supports NetBox release lines `4.5`, `4.4`, and `4.3`.
- SDK tests should import from `netbox_sdk`, not `sdk`.
- Consult [`reference/PYNETBOX.md`](../reference/PYNETBOX.md) when comparing SDK ergonomics to historical NetBox Python client behavior or prior-art feature patterns.

## Logging policy

- Use `logging.getLogger(__name__)` per module. Do not log secrets (tokens, passwords, full `Authorization` headers, or response bodies that may contain credentials).
- Prefer structured `extra` keys for machine-readable logs: `nbx_event` (short stable name), `request_path`, `http_method`, `http_status`, `profile`, `path` (filesystem), etc.
- **INFO**: one-line lifecycle (config save, request completed, logging init). **DEBUG**: cache/schema/plugin discovery detail, parse failures that are handled. **WARNING**: unreadable config, TLS verification disabled. **ERROR/exception**: unexpected failures with traceback when appropriate.
