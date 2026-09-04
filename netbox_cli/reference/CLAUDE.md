# netbox_cli/reference — Bundled Reference Data

## Workspace Context

This file lives at `/root/personal-context/nmulticloud-context/netbox-sdk/netbox_cli/reference/CLAUDE.md` inside the `personal-context` workspace.
Workspace guidance: `/root/personal-context/CLAUDE.md`.
Per-repo deep-dive: `/root/personal-context/claude-reference/netbox-sdk.md`.
Submodule layout and cross-repo links: `/root/personal-context/claude-reference/dependency-map.md`.

---

Static data files bundled with the package at install time (declared in `pyproject.toml` under `[tool.setuptools.package-data]`).

## Contents

| Path | Description |
|---|---|
| `openapi/netbox-openapi.json` | Legacy CLI-local OpenAPI schema copy |

## How It's Used

This package-local JSON file is a compatibility/reference copy only. Active
schema/index logic lives in `netbox_sdk.schema`, and dynamic CLI command
registration/execution uses committed versioned schemas from
`netbox_sdk/reference/openapi/`.

Current CLI schema behavior:
- `_get_registration_index()` builds the network-free command tree from the selected SDK bundled schema (default NetBox 4.7).
- `_get_runtime_index()` honors `--netbox-version` / `NETBOX_SDK_NETBOX_VERSION` or detects the configured instance release line for execution.
- Dynamic command routing and filter discovery should not be wired back to this directory.

## Updating the Schema

When the CLI reference copy needs to be refreshed, replace the JSON file with an
updated schema from a target NetBox instance:

```bash
curl https://<your-netbox>/api/schema/?format=json -o netbox_cli/reference/openapi/netbox-openapi.json
```

Do not treat this directory as the source of truth for typed version support.
That contract is owned by `netbox_sdk/reference/openapi/`, `netbox_sdk.models`,
and `netbox_sdk.typed_versions`.
