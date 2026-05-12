# netbox_sdk/reference — Bundled SDK Reference Assets — AGENTS.md Mirror

This file mirrors the sibling `CLAUDE.md` guidance for agents that read `AGENTS.md`. Treat `CLAUDE.md` as the source material; the content below preserves the current guide.

## Source

@CLAUDE.md

---

# netbox_sdk/reference — Bundled SDK Reference Assets

## Workspace Context

This file lives at `/root/personal-context/nmulticloud-context/netbox-cli/netbox_sdk/reference/CLAUDE.md` inside the `personal-context` workspace.
Workspace guidance: `/root/personal-context/CLAUDE.md`.
Per-repo deep-dive: `/root/personal-context/claude-reference/netbox-cli.md`.
Submodule layout and cross-repo links: `/root/personal-context/claude-reference/dependency-map.md`.

---

This directory contains reference material packaged with or directly relevant to the SDK runtime.

## Contents

| Path | Purpose |
|---|---|
| `openapi/netbox-openapi.json` | Default bundled OpenAPI schema path used by compatibility helpers |
| `openapi/netbox-openapi-4.5.json` | Bundled NetBox 4.5 release-line schema |
| `openapi/netbox-openapi-4.4.json` | Bundled NetBox 4.4 release-line schema |
| `openapi/netbox-openapi-4.3.json` | Bundled NetBox 4.3 release-line schema |

## Notes

- Runtime code should prefer the versioned bundled schemas for typed and schema-loading workflows.
- `netbox_sdk.versioning` defines the supported release lines: `4.5`, `4.4`, and `4.3`.
- Broader design and prior-art references live in the repo-level [`reference/`](../../reference/) directory, including [`reference/PYNETBOX.md`](../../reference/PYNETBOX.md).
