# netbox-sdk

**SDK-first NetBox integration package for Python automation, terminal workflows, and Textual UIs.**

`netbox-sdk` is an SDK-first NetBox toolkit with terminal interfaces built on
one shared runtime:

- `netbox_cli` — Typer command-line interface
- `netbox_tui` — Textual terminal applications
- `netbox_sdk` — standalone REST API SDK shared by both

Published package names remain:

- `netbox-sdk`
- `netbox-console`

## Integration Package Details

`netbox-sdk` is an integration package, not a NetBox plugin. It is not installed
into NetBox with `PLUGINS`, does not add Django models or views, and does not
need a plugin config name. Its certification evidence therefore focuses on the
same quality criteria that apply to ecosystem packages: open-source licensing,
package metadata, API compatibility, tests, documentation, support channels, and
release maintainability.

| Area | Evidence |
| --- | --- |
| License | Apache-2.0 in `LICENSE.txt` and `pyproject.toml` package metadata |
| Package | `netbox-sdk` on PyPI, with `netbox_sdk`, `netbox_cli`, and `netbox_tui` import packages |
| Python | Python `3.11`, `3.12`, and `3.13` |
| NetBox API compatibility | Typed clients for NetBox `4.6`, `4.5`, `4.4`, and `4.3`; live CI against `v4.6.1`, `v4.5.10`, and `v4.5.8` |
| Tests | Mock API suite, live NetBox suite, security tests, type checks, package metadata checks, and strict docs builds in GitHub Actions |
| Support | GitHub issues for bugs/features/docs requests; docs at <https://emersonfelipesp.github.io/netbox-sdk/> |

## Quick Start with the Demo Instance

Install:

```bash
pip install 'netbox-sdk[all]'
```

Authenticate against the public demo instance:

```bash
nbx demo init
```

Try a few commands:

```bash
nbx demo dcim devices list
nbx demo ipam prefixes list
nbx demo tui
nbx demo dev tui
```

## Install

Current release documented on the docs site matches **`docs/snippets/package-version.txt`** (aligned with `pyproject.toml`). For the latest PyPI build you can omit the pin; add `==<version>` to match that documentation snapshot.

Minimal SDK only:

```bash
pip install netbox-sdk
```

CLI:

```bash
pip install 'netbox-sdk[cli]'
```

TUI:

```bash
pip install 'netbox-sdk[tui]'
```

Everything:

```bash
pip install 'netbox-sdk[all]'
```

Pinned (same version as the docs site / `package-version.txt`):

```bash
pip install 'netbox-sdk[all]==0.0.7.post1'
```

With `uv` as a user tool:

```bash
uv tool install --force 'netbox-sdk[cli]'
```

Developer checkout:

```bash
git clone https://github.com/emersonfelipesp/netbox-sdk.git
cd netbox-sdk
uv sync --dev --extra cli --extra tui --extra demo
uv run nbx --help
```

## Common Commands

```bash
nbx init
nbx dcim devices list
nbx dcim devices get --id 1
nbx tui
nbx dev tui
nbx cli tui
nbx logs
```

## Architecture

- `netbox_sdk` owns config, auth, caching, schema parsing, request resolution, shared formatting, and demo helpers.
- `netbox_cli` owns the `nbx` command tree and lazy-loads `netbox_tui` where needed.
- `netbox_tui` owns all Textual apps, themes, widgets, and TCSS.

## Runtime Dependencies

Base SDK installs depend on `aiohttp`, `pydantic`, `email-validator`, `rich`, and
`pyyaml`. Optional extras add the terminal surfaces and local test tools:

- `cli`: Typer-powered `nbx` command tree
- `tui`: Textual terminal applications
- `mock`: FastAPI/uvicorn mock NetBox API for integration tests
- `demo`: Playwright-powered demo setup automation
- `branching`: semantic marker for NetBox Branching workflows; no extra runtime
  dependency is required today

External services are optional at runtime. The Python SDK can target any NetBox
instance reachable over HTTPS/HTTP, and the local mock API can be used for
offline tests.

## Contributor Workflow

```bash
uv sync --dev --extra cli --extra tui --extra demo
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
uv run pre-commit run --all-files
uv run ty check netbox_sdk netbox_cli netbox_tui tests
uv run pytest
```

## IDE Support

Open the repository in VS Code. When prompted, install the recommended
extensions (`ms-python.vscode-pylance`, `ms-python.python`,
`charliermarsh.ruff`). Pylance picks up types from all three packages
automatically — each ships a `py.typed` PEP 561 marker.

Type checking uses two gates: `ty` (Astral, fast, pre-commit + CI) and
`pyright` (Pylance-compatible, pre-commit). Both run at `typeCheckingMode =
"basic"`. To run them manually:

```bash
uv run ty check netbox_sdk netbox_cli netbox_tui tests
uv run pyright netbox_sdk netbox_cli netbox_tui
```

## Release Process

Use a single GitHub release title pattern for every release:

- `netbox-sdk vX.Y.Z`

Example:

```bash
gh release create v0.0.7.post1 \
  --title "netbox-sdk v0.0.7.post1"
```

When cutting a release, bump **`pyproject.toml`** and **`netbox_sdk.__version__`**, then keep docs in sync: **`docs/snippets/package-version.txt`**, **`mkdocs.yml`** → **`extra.package_version`**, and the version strings in **`docs/snippets/documented-release-*.md`** and **`docs/snippets/pip-pinned-*.txt`** / **`uv-pinned-cli.txt`**. **`uv lock`** must reflect the new version. **`tests/test_docs_alignment.py`** asserts snippet and MkDocs metadata match **`pyproject.toml`**.
