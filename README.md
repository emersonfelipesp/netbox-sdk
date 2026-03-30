# netbox-sdk

`netbox-sdk` is an SDK-first NetBox toolkit with terminal interfaces built on
one shared runtime:

- `netbox_cli` — Typer command-line interface
- `netbox_tui` — Textual terminal applications
- `netbox_sdk` — standalone REST API SDK shared by both

Published package names remain:

- `netbox-sdk`
- `netbox-console`

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

## Contributor Workflow

```bash
uv sync --dev --extra cli --extra tui --extra demo
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
uv run pre-commit run --all-files
uv run pytest
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
