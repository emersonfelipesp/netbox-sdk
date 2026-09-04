# netbox_sdk/reference — Bundled SDK Reference Assets

## Workspace Context

This file lives at `/root/personal-context/nmulticloud-context/netbox-sdk/netbox_sdk/reference/CLAUDE.md` inside the `personal-context` workspace.
Workspace guidance: `/root/personal-context/CLAUDE.md`.
Per-repo deep-dive: `/root/personal-context/claude-reference/netbox-sdk.md`.
Submodule layout and cross-repo links: `/root/personal-context/claude-reference/dependency-map.md`.

---

This directory contains reference material packaged with or directly relevant to the SDK runtime.

## Contents

| Path | Purpose |
|---|---|
| `openapi/netbox-openapi.json` | Legacy compatibility alias; do not treat as the active default |
| `openapi/netbox-openapi-4.7.json` | Bundled official NetBox v4.7.0 GA release-line schema and default for `load_openapi_schema()` |
| `openapi/netbox-openapi-4.6.json` | Bundled NetBox 4.6 release-line schema |
| `openapi/netbox-openapi-4.6.provenance.json` | Immutable source and generator provenance for the NetBox 4.6 artifacts |
| `openapi/netbox-openapi-4.5.json` | Bundled NetBox 4.5 release-line schema |
| `openapi/netbox-openapi-4.4.json` | Bundled NetBox 4.4 release-line schema |
| `openapi/netbox-openapi-4.3.json` | Bundled NetBox 4.3 release-line schema |

## Notes

- Runtime code should prefer the versioned bundled schemas for typed and schema-loading workflows; default CLI/static SDK schema selection is NetBox 4.7 unless overridden.
- The 4.7 schema is pinned to the official NetBox v4.7.0 GA release, and its provenance file records the upstream commit/blob plus artifact hashes.
- The 4.6 schema is pinned to the NetBox v4.6.6 release and its provenance file records the upstream commit/blob plus artifact hashes.
- Release generation requires an upstream Git checkout. The generator verifies
  that the release tag peels to the reviewed commit, the source path resolves to
  the reviewed blob, the blob bytes match the independently pinned SHA-256, and
  the NetBox 4.7 source bytes exactly equal the committed bundle. Verification also
  regenerates the model and typed modules into temporary outputs and byte-compares
  them with the committed artifacts, independently of the mutable provenance
  sidecar hashes. GitHub live CI repeats this in `--verify-only` mode for every
  provenance-managed live line.
- `netbox_sdk.versioning` owns the release-line registry and artifact mapping;
  `netbox_sdk.schema_resolution` owns bundled/live/default selection for every
  runtime surface.
- Broader design and prior-art references live in the repo-level [`reference/`](../../reference/) directory, including [`reference/PYNETBOX.md`](../../reference/PYNETBOX.md).
