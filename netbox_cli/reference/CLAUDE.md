# netbox_cli/reference — Bundled Reference Data

Static data files bundled with the package at install time (declared in `pyproject.toml` under `[tool.setuptools.package-data]`).

## Contents

| Path | Description |
|---|---|
| `openapi/netbox-openapi.json` | NetBox OpenAPI 3.0 schema (JSON) |

## How It's Used

This package-local JSON file is a compatibility/reference copy used by CLI-facing
workflows. The active schema/index logic lives in `netbox_sdk.schema`, and the
typed SDK uses committed versioned schemas from `netbox_sdk/reference/openapi/`.

This schema drives:
- `nbx groups` — lists all API groups
- `nbx resources <group>` — lists resources per group
- `nbx ops <group> <resource>` — shows available HTTP operations
- Dynamic command routing — maps action names to correct HTTP methods and paths
- Filter parameter discovery — populates `--filter` options in the TUI

## Updating the Schema

When the CLI reference copy needs to be refreshed, replace the JSON file with an
updated schema from a target NetBox instance:

```bash
curl https://<your-netbox>/api/schema/?format=json -o netbox_cli/reference/openapi/netbox-openapi.json
```

Do not treat this directory as the source of truth for typed version support.
That contract is owned by `netbox_sdk/reference/openapi/`, `netbox_sdk.models`,
and `netbox_sdk.typed_versions`.
