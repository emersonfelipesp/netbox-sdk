# netbox_sdk/reference — Bundled SDK Reference Assets

This directory contains reference material packaged with or directly relevant to the SDK runtime.

## Contents

| Path | Purpose |
|---|---|
| `openapi/netbox-openapi.json` | Bundled OpenAPI schema used by `netbox_sdk.schema` |

## Notes

- Runtime code should treat `netbox_sdk/reference/openapi/netbox-openapi.json` as the canonical bundled schema.
- Broader design and prior-art references live in the repo-level [`reference/`](../../reference/) directory, including [`reference/PYNETBOX.md`](../../reference/PYNETBOX.md).
