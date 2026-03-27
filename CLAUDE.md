# netbox-sdk — Project Guide

## Codebase Index

| Path | CLAUDE.md | What's there |
|---|---|---|
| `netbox_sdk/` | [→](netbox_sdk/CLAUDE.md) | Standalone SDK package: client, config, schema, services, cache, shared formatting/logging/output helpers |
| `netbox_tui/` | [→](netbox_tui/CLAUDE.md) | Textual TUI package: apps, chrome, widgets, navigation, state, TCSS, theme registry |
| `netbox_tui/themes/` | [→](netbox_tui/themes/CLAUDE.md) | JSON theme files auto-discovered by the TUI |
| `netbox_cli/` | [→](netbox_cli/CLAUDE.md) | Typer CLI package: root app, runtime, dynamic commands, demo/dev/docgen wiring |
| `netbox_sdk/reference/` | [→](netbox_sdk/reference/CLAUDE.md) | Bundled SDK OpenAPI assets for supported NetBox release lines |
| `tests/` | [→](tests/CLAUDE.md) | pytest suite |
| `docs/` | [→](docs/CLAUDE.md) | MkDocs sources |
| `.github/` | [→](.github/CLAUDE.md) | GitHub Actions workflows |
| `reference/` | [→](reference/CLAUDE.md) | Design, Textual, and prior-art client references |
| `reference/PYNETBOX.md` | n/a | Maintainer reference for `pynetbox` architecture and prior-art client behavior |

## Architecture In One Page

```
netbox_sdk/   standalone runtime-independent API layer
    ├── config.py
    ├── client.py
    ├── http_cache.py
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
    ├── models/
    ├── typed_versions/
    ├── django_models/
    └── reference/openapi/

netbox_tui/   optional Textual layer
    ├── app.py / dev_app.py / cli_tui.py / logs_app.py / django_model_app.py
    ├── chrome.py / widgets.py / navigation.py / panels.py / state.py
    ├── theme_registry.py
    ├── *.tcss
    └── themes/*.json

netbox_cli/   optional Typer layer
    ├── __init__.py   root app + entrypoint
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

## Core Rules

- SDK code in `netbox_sdk/` must not import `netbox_cli` or `netbox_tui`.
- CLI code in `netbox_cli/` must lazy-import TUI entrypoints so `import netbox_cli` works without `textual`.
- TUI code in `netbox_tui/` may depend on `netbox_sdk` and `textual`, not on old `netbox_cli/ui` paths.
- Use absolute imports only: `netbox_sdk.*`, `netbox_tui.*`, `netbox_cli.*`.
- Never use pynetbox or direct NetBox model access. Use `aiohttp` via `netbox_sdk.client`.
- The SDK now exposes three public layers: raw `NetBoxApiClient`, async facade `api()`, and versioned typed client `typed_api()`.
- Bundled typed support currently targets NetBox release lines `4.5`, `4.4`, and `4.3`.
- Never hardcode colors in TCSS. Use theme variables and JSON theme definitions.
- Consult [`reference/PYNETBOX.md`](reference/PYNETBOX.md) when evaluating prior-art NetBox client patterns or interoperability expectations.

## TUI Design Rules

- Consult `reference/design/NETBOX-DARK-PATTERNS.md` first, then `reference/design/TOAD-DESIGN-GUIDE.md`.
- Theme changes must propagate through nested Textual internals, not only parent widgets.
- Keep visual state in TCSS classes, not Python conditionals.

## Verification Before Done

- Run `uv run pre-commit run --all-files`.
- Run the package-specific marker suite for the package(s) you changed.
- Run `uv run pytest` when shared files or release/main validation paths are involved.
- For packaging changes, verify extras and import boundaries.
