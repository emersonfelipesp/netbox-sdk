# Installation

`netbox-sdk` requires Python 3.11 or newer.

--8<-- "snippets/documented-release-en.md"

## From PyPI

SDK only:

```bash
pip install netbox-sdk
```

The base package already includes the dependencies required by the async SDK and
the versioned typed SDK, including `pydantic` and `email-validator`.

CLI:

```bash
pip install 'netbox-sdk[cli]'
```

TUI:

```bash
pip install 'netbox-sdk[tui]'
```

MCP server:

```bash
pip install 'netbox-sdk[mcp]'
```

Everything:

```bash
pip install 'netbox-sdk[all]'
```

Pinned installs for the documented release (same extras, exact version):

```bash
--8<-- "snippets/pip-pinned-sdk.txt"
--8<-- "snippets/pip-pinned-cli.txt"
--8<-- "snippets/pip-pinned-tui.txt"
--8<-- "snippets/pip-pinned-all.txt"
```

## With uv tool

```bash
uv tool install --force 'netbox-sdk[cli]'
nbx --help
```

Pinned to the documented release:

```bash
--8<-- "snippets/uv-pinned-cli.txt"
nbx --help
```

## From source

```bash
git clone https://github.com/emersonfelipesp/netbox-sdk.git
cd netbox-sdk
uv sync --dev --extra cli --extra tui --extra demo --extra mcp
uv run nbx --help
```

## Typed SDK support

The repository ships committed OpenAPI bundles and generated Pydantic models for
NetBox `4.7`, `4.6`, `4.5`, `4.4`, and `4.3`. The default 4.7 line is generated from the official `v4.7.0` GA schema. Users do not need to run code generation
locally. CI live-tests the SDK against `v4.7.0`, `v4.6.6`, `v4.6.3`, `v4.6.2`, and `v4.5.10`.

## IDE type hints

All four installed packages (`netbox_sdk`, `netbox_cli`, `netbox_tui`,
`netbox_mcp`) ship
PEP 561 `py.typed` markers. Pylance, Pyright, and other PEP 561-aware editors
resolve types automatically from the installed wheel — no extra setup. See the
[IDE Support](../developer/ide-support.md) developer guide for the contributor
workspace and dual-checker pre-commit gates.

## Which install should I pick?

- `pip install netbox-sdk` if you only need the Python SDK
- `pip install 'netbox-sdk[cli]'` if you want the `nbx` command
- `pip install 'netbox-sdk[tui]'` if you want to launch Textual TUIs from the
  package in an existing Python environment
- `pip install 'netbox-sdk[mcp]'` if you want the `nbx-mcp` stdio or Streamable
  HTTP server
- `pip install 'netbox-sdk[all]'` if you want every interface available locally

## Contributor workflow

```bash
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
uv run pre-commit run --all-files
uv run pytest
```

## Optional demo automation

`nbx demo init` uses Playwright. The browser runtime must be installed separately:

```bash
uv tool run --from playwright playwright install chromium --with-deps
```
