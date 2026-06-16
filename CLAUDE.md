# netbox-sdk — Project Guide

## Workspace Context

This file lives at `/root/personal-context/nmulticloud-context/netbox-sdk/CLAUDE.md` inside the `personal-context` workspace.
Workspace guidance: `/root/personal-context/CLAUDE.md`.
Per-repo deep-dive: `/root/personal-context/claude-reference/netbox-sdk.md`.
Submodule layout and cross-repo links: `/root/personal-context/claude-reference/dependency-map.md`.

---

## Codebase Index

| Path | CLAUDE.md | What's there |
|---|---|---|
| `netbox_sdk/` | [→](netbox_sdk/CLAUDE.md) | Standalone SDK package: client, config, schema, services, cache, shared formatting/logging/output helpers |
| `netbox_tui/` | [→](netbox_tui/CLAUDE.md) | Textual TUI package: apps, chrome, widgets, navigation, state, TCSS, theme registry |
| `netbox_tui/themes/` | [→](netbox_tui/themes/CLAUDE.md) | JSON theme files auto-discovered by the TUI |
| `netbox_cli/` | [→](netbox_cli/CLAUDE.md) | Typer CLI package: root app, runtime, dynamic commands, demo/dev/docgen wiring |
| `netbox_cli/reference/` | [→](netbox_cli/reference/CLAUDE.md) | Bundled CLI-local OpenAPI reference copy (schema driving dynamic commands) |
| `netbox_sdk/reference/` | [→](netbox_sdk/reference/CLAUDE.md) | Bundled SDK OpenAPI assets for supported NetBox release lines |
| `tests/` | [→](tests/CLAUDE.md) | pytest suite |
| `docs/` | [→](docs/CLAUDE.md) | MkDocs sources |
| `.github/` | [→](.github/CLAUDE.md) | GitHub Actions workflows |
| `reference/` | [→](reference/CLAUDE.md) | Design, Textual, and prior-art client references |
| `reference/PYNETBOX.md` | n/a | Maintainer reference for `pynetbox` architecture and prior-art client behavior |

## Architecture In One Page

```
netbox_sdk/   standalone runtime-independent API layer
    ├── branching.py
    ├── config.py
    ├── client.py
    ├── decorators.py
    ├── exceptions.py
    ├── http_cache.py
    ├── http_ssl.py
    ├── mock_main.py
    ├── schema.py
    ├── services.py
    ├── plugin_discovery.py
    ├── formatting.py
    ├── logging_runtime.py
    ├── output_safety.py
    ├── trace_ascii.py
    ├── demo_auth.py
    ├── facade.py
    ├── typed_api.py
    ├── typed_runtime.py
    ├── versioning.py
    ├── mock/
    ├── models/
    ├── typed_versions/
    ├── django_models/
    └── reference/openapi/

netbox_tui/   optional Textual layer
    ├── app.py / dev_app.py / cli_tui.py / logs_app.py / django_model_app.py / graphql_app.py
    ├── branch_screen.py / filter_overlay.py / login_modal.py / ssl_verify_support.py
    ├── chrome.py / widgets.py / navigation.py / nav_blueprint.py / panels.py / state.py
    ├── cli_completions.py / dev_rendering.py / lifecycle.py / logo_render.py
    ├── theme_registry.py
    ├── *.tcss
    └── themes/*.json

netbox_cli/   optional Typer layer
    ├── __init__.py   root app + entrypoint
    ├── branching.py  NetBox Branching commands
    ├── decorators.py reusable Typer decorator factories
    ├── runtime.py    config/index/client factories
    ├── dynamic.py    OpenAPI command registration/execution
    ├── support.py    shared CLI rendering/error helpers
    ├── demo.py       demo profile command tree
    ├── dev.py        dev command tree
    ├── django_model.py
    ├── markdown_output.py
    └── docgen*/ docgen/
```

Data flow:
1. `netbox_sdk` owns API behavior and shared data transformation.
2. `netbox_cli` imports `netbox_sdk` and lazy-loads `netbox_tui` where needed.
3. `netbox_tui` imports `netbox_sdk` directly and only reaches into `netbox_cli` for CLI app/runtime callbacks where required.

## Contributor Workflow

Initial setup:

```bash
uv sync --dev --extra cli --extra tui --extra demo
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
```

Day-to-day:

```bash
uv run pre-commit run --all-files
uv run pytest
uv run pytest -m suite_sdk
uv run pytest -m suite_cli
uv run pytest -m suite_tui
```

If you need a minimal install boundary check:

```bash
pip install -e .
pip install -e '.[cli]'
pip install -e '.[tui]'
pip install -e '.[all]'
```

## CLI Dynamic Command Surface

The CLI exposes NetBox API resources through `nbx <group> <resource> <action>`. Static command registration is network-free and defaults to the bundled NetBox 4.6 schema; command execution, discovery helpers, and TUI launch use `_get_runtime_index()` to honor `--netbox-version` / `NETBOX_SDK_NETBOX_VERSION` or detect the configured instance release line.

| Action | HTTP | Path | Notes |
|---|---|---|---|
| `list` | GET | list path | Supports `--all` for auto-pagination |
| `get` | GET | detail path | Requires `--id` |
| `create` | POST | list path | |
| `update` | PUT | detail path | Requires `--id` |
| `patch` | PATCH | detail path | Requires `--id` |
| `delete` | DELETE | detail path | Requires `--id` |
| `bulk-update` | PUT | list path | Array body; no `--id` |
| `bulk-patch` | PATCH | list path | Array body; no `--id` |
| `bulk-delete` | DELETE | list path | Array body; no `--id` |
| `filters` | — | local only | Prints available filter parameters from schema |

**Auto-pagination** (`--all` / `--max-records`): When `--all` is passed for a `list` action, `list_all_pages` in `netbox_sdk/services.py` follows the `next` URL chain and returns a single synthesised response. `--max-records N` (default 10 000) is the hard ceiling on accumulated records.

**Query/header forwarding**: `parse_key_value_pairs()` preserves repeated query keys as list values so filters like `tag=a&tag=b` survive through `aiohttp`. Dynamic commands, `nbx call`, and `nbx dev http` accept `-H` / `--header` in either `Header=Value` or `Header: Value` form for ETag/conditional request workflows.

**Bulk routing**: `bulk-update`, `bulk-patch`, and `bulk-delete` always target the list path, never the detail path. The `--id` option is silently ignored for bulk actions.

**Filter discovery**: `filters` is a synthetic local action that calls `SchemaIndex.filter_params()` and prints the available query parameters without making an HTTP request.

**Plugin auto-discovery** (`netbox_sdk/plugin_discovery.py`): when `dynamic.py` is asked to act on a `group/resource` pair that is absent from the bundled schema (`index.resource_paths(group, resource) is None`), it lazily calls `enrich_schema_index_with_runtime_resources(index, client)`. That function does a BFS walk starting at `GET /api/plugins/` and follows every URL found in API root responses, collecting collection and detail path pairs into the live `SchemaIndex`. Any installed NetBox plugin that exposes a `NetBoxRouter` root is therefore automatically reachable via `nbx plugins <plugin> <resource> <action>` — no CLI rebuild or SDK configuration required.

Plugin auto-discovery also runs unconditionally in `runtime.py::_get_enriched_index()`, which is used when the CLI needs a fully populated index without a prior resource-miss trigger.

**What a plugin needs to be auto-discovered:**
1. Register a `NetBoxRouter` with `APIRootView` in its `api/urls.py`.
2. Return a JSON dict of collection URLs from `GET /api/plugins/<plugin>/`.
3. Each collection URL must serve a paginated `{"count": …, "results": […]}` response.

Sub-namespaced endpoints (e.g. `endpoints/proxmox/`, `endpoints/pbs/`) are discovered through the same BFS as long as the plugin root links to the sub-namespace root, which `NetBoxRouter` includes automatically. `netbox-proxbox` satisfies all three requirements across all 29 of its ViewSets.

## Core Rules

- SDK code in `netbox_sdk/` must not import `netbox_cli` or `netbox_tui`.
- CLI code in `netbox_cli/` must lazy-import TUI entrypoints so `import netbox_cli` works without `textual`.
- TUI code in `netbox_tui/` may depend on `netbox_sdk` and `textual`, not on old `netbox_cli/ui` paths.
- Use absolute imports only: `netbox_sdk.*`, `netbox_tui.*`, `netbox_cli.*`.
- Never use pynetbox or direct NetBox model access. Use `aiohttp` via `netbox_sdk.client`.
- The SDK now exposes three public layers: raw `NetBoxApiClient`, async facade `api()`, and versioned typed client `typed_api()`.
- Bundled typed and OpenAPI support currently targets NetBox release lines `4.6`, `4.5`, `4.4`, and `4.3`; CLI defaults to 4.6 and can be pinned to 4.5/4.6 via `--netbox-version` or `NETBOX_SDK_NETBOX_VERSION`. The CI live-NetBox suite exercises `v4.6.3`, `v4.6.2`, and `v4.5.10`.
- Never hardcode colors in TCSS. Use theme variables and JSON theme definitions.
- Consult [`reference/PYNETBOX.md`](reference/PYNETBOX.md) when evaluating prior-art NetBox client patterns or interoperability expectations.

## TUI Design Rules

- Consult `reference/design/NETBOX-DARK-PATTERNS.md` first, then `reference/design/TOAD-DESIGN-GUIDE.md`.
- Theme changes must propagate through nested Textual internals, not only parent widgets.
- Keep visual state in TCSS classes, not Python conditionals.

## Verification Before Done

- Run `uv run pre-commit run --all-files`.
- Run `uv run pyright netbox_sdk netbox_cli netbox_tui` alongside `ty check`.
  Both gates must pass. All three packages ship `py.typed` PEP 561 markers.
- Run the package-specific marker suite for the package(s) you changed.
- Run `uv run pytest` when shared files or release/main validation paths are involved.
- For packaging changes, verify extras and import boundaries.

## Release Process

### Merging `main` into version branches (e.g. `v0.0.7.post1`)

When updating a release or topic branch from `main`, **`main` has priority on merge conflicts**: resolve by keeping the `main` side. With `git merge origin/main` checked out on the release branch, that is **`git checkout --theirs -- <path>`** (then review and `git add`). Re-port any branch-only work onto the post-merge tree if still needed.

- Use the Git tag as `vX.Y.Z` (including post-releases such as `v0.0.7.post1` when applicable).
- Use the GitHub release title as `netbox-sdk vX.Y.Z`.
- Do not mix bare tags and package-prefixed titles across releases.
- Example: tag `v0.0.7.post1`, title `netbox-sdk v0.0.7.post1`.
- When bumping the package version, also update **`docs/snippets/package-version.txt`**, **`mkdocs.yml`** → **`extra.package_version`**, and the pinned-command snippets under **`docs/snippets/`** (`documented-release-*.md`, `pip-pinned-*.txt`, `uv-pinned-cli.txt`), then run **`uv lock`**. **`tests/test_docs_alignment.py`** guards drift vs **`pyproject.toml`**.
