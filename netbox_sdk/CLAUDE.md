# netbox_sdk — SDK Package

Standalone NetBox REST API client library.

## Invariants

- `netbox_sdk` must not import `netbox_cli` or `netbox_tui`.
- Public imports use `netbox_sdk.*`, never legacy `sdk.*`.
- Bundled schema lives at `netbox_sdk/reference/openapi/netbox-openapi.json`.

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
├── logging_runtime.py
├── output_safety.py
├── trace_ascii.py
├── formatting.py
├── demo_auth.py
├── django_models/
├── py.typed
└── reference/openapi/netbox-openapi.json
```

## Public Surface

- `netbox_sdk.config` — config model, profile persistence, auth headers
- `netbox_sdk.client` — async API client and connection probe
- `netbox_sdk.http_cache` — filesystem cache primitives
- `netbox_sdk.schema` — OpenAPI loading and indexing
- `netbox_sdk.services` — dynamic request resolution
- `netbox_sdk.plugin_discovery` — runtime plugin API discovery
- Shared cross-package helpers: `formatting`, `logging_runtime`, `output_safety`, `trace_ascii`, `demo_auth`, `django_models`

## Validation Expectations

- `python -c 'import netbox_sdk'` must work without CLI or TUI extras.
- SDK tests should import from `netbox_sdk`, not `sdk`.
- Consult [`reference/PYNETBOX.md`](../reference/PYNETBOX.md) when comparing SDK ergonomics to historical NetBox Python client behavior or prior-art feature patterns.
