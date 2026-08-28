# netbox_cli — CLI Package

## Workspace Context

This file lives at `/root/personal-context/nmulticloud-context/netbox-sdk/netbox_cli/CLAUDE.md` inside the `personal-context` workspace.
Workspace guidance: `/root/personal-context/CLAUDE.md`.
Per-repo deep-dive: `/root/personal-context/claude-reference/netbox-sdk.md`.
Submodule layout and cross-repo links: `/root/personal-context/claude-reference/dependency-map.md`.

---

`netbox_cli` is the Typer-based command layer. It depends on `netbox_sdk` and optionally on `netbox_tui` for commands that launch Textual applications.

## Package Contract

- `import netbox_cli` must work with only the `cli` extra installed.
- Any command path that launches a TUI must lazy-import `netbox_tui` and raise a clear install hint if `textual` is unavailable.
- No old `netbox_cli/cli/` or `netbox_cli/ui/` paths remain in active code.

## Module Map

| File | Purpose |
|---|---|
| `__init__.py` | Root Typer app, `main()`, top-level command registration, script entrypoint target, and guarded raw-call execution/client-free dry-run preview |
| `branching.py` | `nbx branching ...`, `nbx branch ...`, and branch-aware command helpers; every mutating create/update/delete/sync/merge/revert/archive verb requires the shared process-local `--confirm` / `NETBOX_SDK_CONFIRM_WRITE=1` gate before client construction |
| `decorators.py` | Reusable Typer decorator factories for repeated option/argument metadata |
| `runtime.py` | Thin CLI adapter over `netbox_sdk.schema_resolution` (`_get_registration_index()` for network-free command registration, `_get_runtime_index()` for execution with `--netbox-version` override or connected-instance detection), plus runtime config cache, client factories, spinner integration, and demo refresh wiring. `_get_enriched_index()` resolves its base through `_get_runtime_index()` — so an explicit `--netbox-version` pin survives `--live` enrichment instead of being replaced by the connected instance's line — then calls `enrich_schema_index_with_runtime_resources` unconditionally so all plugin routes are pre-populated. |
| `dynamic.py` | OpenAPI-driven dynamic command registration and execution. Supports all CRUD actions plus: **shared process-local write confirmation** (`--confirm` or `NETBOX_SDK_CONFIRM_WRITE=1` before every dynamic action resolving to POST/PUT/PATCH/DELETE, including raw method spellings; the same helper also gates `dev.py` and `branching.py`; dry runs remain local); **NetBox 4.5/4.6 parallel command surfaces** (default registration 4.6, explicit `--netbox-version`/`NETBOX_SDK_NETBOX_VERSION` override); **headers** (`-H` / `--header` forwarded to SDK requests); **repeated filters** (duplicate `-q` keys preserved); **bulk ops** (`bulk-update` PUT, `bulk-patch` PATCH, `bulk-delete` DELETE — all to the list path with an array body, no `--id`); **auto-pagination** (`--all` flag on `list` calls `list_all_pages()`, `--max-records` caps accumulation, default 10 000); **filter discovery** (`filters` action — local-only, calls `SchemaIndex.filter_params()`, no HTTP); **lazy plugin auto-discovery** — when a requested `group/resource` is absent from the bundled schema, calls `enrich_schema_index_with_runtime_resources(index, client)` from `netbox_sdk.plugin_discovery` to walk `GET /api/plugins/` and add live plugin routes before failing |
| `support.py` | Shared CLI rendering, output selection, redacted request dry-run previews, and TUI lazy-import helpers |
| `demo.py` | `nbx demo ...` command tree |
| `dev.py` | `nbx dev ...` command tree; `dev http` POST/PUT/PATCH/DELETE share the process-local write-confirmation gate while GET remains confirmation-free |
| `django_model.py` | Django model CLI commands |
| `proxbox.py` | `nbx proxbox ...` catalog, generated Proxbox CRUD commands, confirmation-gated TUI launcher, and streaming sync commands; stream failures recover the authoritative job, poll within the remaining timeout, and report transport loss as a warning when the job succeeds; post-schedule authoritative-fetch failures preserve the structured `job_id` and warn automation to inspect that existing job before retrying |
| `proxbox_jobs.py` | `nbx proxbox jobs list|get|statuses` — read-only retrieval of Proxbox sync jobs from the core job list. Owns option parsing, the default 30-day scan window (`--since`/`--until`/`--date-field`/`--all-time`, suppressed by `--id`), `--endpoint`/`--cluster`/`--node` resolution as a union, column selection (`--fields`/`--wide`), and the scan footer that states window/scanned/matched/truncation on every result. Refuses `--since`/`--until` that collide with an explicit same-field bound rather than silently overwriting it, reports every bound in effect, and sanitizes every server-derived string before it becomes a Rich renderable (Rich `Text` preserves CSI/OSC verbatim, so a job field is an injection point). Read-only: no `--confirm` gate |
| `markdown_output.py` | Markdown rendering helpers |
| `docgen_capture.py` / `docgen_specs.py` / `docgen/` | Documentation capture pipeline |
| `tui_simulation.py` | TUI launch simulation helpers used by docs/tests |

## Import Rules

- Import SDK types/functions from `netbox_sdk.*`.
- Import TUI entrypoints only inside function bodies unless the module is explicitly TUI-only.
- Use `netbox_sdk.schema` as the source of truth for schema/index behavior; do not reintroduce separate CLI-local schema loaders.
- Keep repeated Typer option metadata in `netbox_cli.decorators` when a decorator factory improves readability without hiding command-specific behavior.
- Treat `typed_api()` as an SDK-facing surface, not a CLI dependency unless a command explicitly needs versioned typed validation.
- Keep root app references on `netbox_cli`, for example:
  - `from netbox_cli import app, main`
  - `from netbox_cli.runtime import _get_client, _get_registration_index, _get_runtime_index`
  - `from netbox_cli.dynamic import _register_openapi_subcommands`

## Packaging

- Console entrypoint: `nbx = netbox_cli:main`
- Extra required for this package: `.[cli]`
- TUI-launching commands additionally require `.[tui]`
