# netbox-sdk — Project Guide — AGENTS.md Mirror

This file mirrors the sibling `CLAUDE.md` guidance for agents that read `AGENTS.md`. Treat `CLAUDE.md` as the source material; the content below preserves the current guide.

## Source

@CLAUDE.md

---

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
| `netbox_mcp/` | [→](netbox_mcp/CLAUDE.md) | Optional schema-driven MCP package: validated tools, stdio/HTTP transports, auth, mutation gate |
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
    ├── http_cache.py
    ├── http_ssl.py
    ├── telemetry.py
    ├── schema.py
    ├── services.py
    ├── plugin_discovery.py
    ├── proxbox.py
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
    ├── app.py / dev_app.py / cli_tui.py / logs_app.py / django_model_app.py / graphql_app.py / proxbox_app.py
    ├── branch_screen.py / filter_overlay.py / login_modal.py / ssl_verify_support.py
    ├── chrome.py / widgets.py / navigation.py / nav_blueprint.py / panels.py / state.py
    ├── theme_registry.py
    ├── *.tcss
    └── themes/*.json

netbox_cli/   optional Typer layer
    ├── __init__.py   root app + entrypoint
    ├── branching.py  NetBox Branching commands
    ├── decorators.py reusable Typer decorator factories
    ├── runtime.py    config/index/client factories
    ├── dynamic.py    OpenAPI command registration/execution
    ├── proxbox.py    netbox-proxbox catalog, CRUD, TUI, and sync commands
    ├── support.py    shared CLI rendering/error helpers
    ├── demo.py       demo profile command tree
    ├── dev.py        dev command tree
    ├── django_model.py
    ├── markdown_output.py
    └── docgen*/ docgen/

netbox_mcp/   optional Model Context Protocol layer
    ├── __init__.py   entrypoint + transport selection
    ├── app.py        explicit FastMCP tool registration
    ├── models.py     strict tool argument schemas
    └── service.py    SDK-backed dispatch + mutation gate
```

Data flow:
1. `netbox_sdk` owns API behavior and shared data transformation.
2. `netbox_cli` imports `netbox_sdk` and lazy-loads `netbox_tui` where needed.
3. `netbox_tui` imports `netbox_sdk` directly and only reaches into `netbox_cli` for CLI app/runtime callbacks where required.
4. `netbox_mcp` imports only `netbox_sdk`; it never imports CLI or TUI code.

## Contributor Workflow

Initial setup:

```bash
uv sync --dev --extra cli --extra tui --extra demo --extra mcp
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
```

Day-to-day:

```bash
uv run pre-commit run --all-files
uv run pytest
uv run pytest -m suite_sdk
uv run pytest -m suite_cli
uv run pytest -m suite_tui
uv run pytest -m suite_mcp
```

If you need a minimal install boundary check:

```bash
pip install -e .
pip install -e '.[cli]'
pip install -e '.[tui]'
pip install -e '.[mcp]'
pip install -e '.[all]'
```

## CLI Dynamic Command Surface

The CLI exposes NetBox API resources through `nbx <group> <resource> <action>`. Static command registration is network-free and defaults to the bundled NetBox 4.6 schema; command execution, discovery helpers, and TUI launch use `_get_runtime_index()` to honor `--netbox-version` / `NETBOX_SDK_NETBOX_VERSION` or detect the configured instance release line.

`list` supports `--all` / `--max-records`; write actions include `create`, `update`, `patch`, `delete`, plus `bulk-update`, `bulk-patch`, and `bulk-delete` on list paths; `filters` is a local schema action. `parse_key_value_pairs()` preserves repeated query keys as list values so filters like `tag=a&tag=b` survive through `aiohttp`. Dynamic commands, `nbx call`, and `nbx dev http` accept `-H` / `--header` in either `Header=Value` or `Header: Value` form for ETag/conditional request workflows.

## Core Rules

- SDK code in `netbox_sdk/` must not import `netbox_cli` or `netbox_tui`.
- CLI code in `netbox_cli/` must lazy-import TUI entrypoints so `import netbox_cli` works without `textual`.
- TUI code in `netbox_tui/` may depend on `netbox_sdk` and `textual`, not on old `netbox_cli/ui` paths.
- MCP code in `netbox_mcp/` may depend on `netbox_sdk` and `mcp`, never on `netbox_cli` or `netbox_tui`.
- Use absolute imports only: `netbox_sdk.*`, `netbox_tui.*`, `netbox_cli.*`, `netbox_mcp.*`.
- Never use pynetbox or direct NetBox model access. Use `aiohttp` via `netbox_sdk.client`.
- The SDK now exposes three public layers: raw `NetBoxApiClient`, async facade `api()`, and versioned typed client `typed_api()`.
- OpenTelemetry request tracing is opt-in and lives in `netbox_sdk.telemetry`; keep
  all `opentelemetry.*` imports lazy/guarded so base `import netbox_sdk` works
  without the `otel` extra.
- Bundled typed and OpenAPI support currently targets NetBox release lines `4.6`, `4.5`, `4.4`, and `4.3`; CLI defaults to 4.6 and can be pinned to 4.5/4.6 via `--netbox-version` or `NETBOX_SDK_NETBOX_VERSION`. The CI live-NetBox suite exercises `v4.6.6`, `v4.6.3`, `v4.6.2`, and `v4.5.10`.
- Never hardcode colors in TCSS. Use theme variables and JSON theme definitions.
- Consult [`reference/PYNETBOX.md`](reference/PYNETBOX.md) when evaluating prior-art NetBox client patterns or interoperability expectations.

## TUI Design Rules

- Consult `reference/design/NETBOX-DARK-PATTERNS.md` first, then `reference/design/TOAD-DESIGN-GUIDE.md`.
- Theme changes must propagate through nested Textual internals, not only parent widgets.
- Keep visual state in TCSS classes, not Python conditionals.

## Continuous Integration

`.gitea/workflows/ci.yml` is the secret-free Gitea-first review gate. It runs
the complete locked offline environment on the isolated
`ci-untrusted-python312` label: workflow policy, ty, Pyright, all-files
pre-commit, the full mocked suite, SDK/CLI/TUI/MCP security regressions, strict
documentation, lifecycle/package evidence, distribution metadata, and an
installed-wheel smoke check. Pull-request jobs have read-only repository
permissions and must never receive credentials, publish, deploy, push, or
contact a live NetBox service.

The Gitea workflow supplements rather than replaces GitHub's Python 3.11–3.13
and live-NetBox matrices. A workflow file alone is not a merge gate: require an
eligible runner, terminal successful contexts, protected-branch requirements,
and a PR branch current with its base. Gitea evaluates `refs/pull/<N>/head`, not
a synthetic merge commit; a queued job with `runner_id: 0` is missing evidence,
not a pass.

## Verification Before Done

- Run `uv run pre-commit run --all-files`.
- Run `uv run pyright netbox_sdk netbox_cli netbox_tui netbox_mcp` alongside
  `ty check`. Both gates must pass. All four packages ship `py.typed` PEP 561
  markers.
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
