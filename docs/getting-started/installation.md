# Installation

`netbox-sdk` requires Python 3.11 or newer.

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

Everything:

```bash
pip install 'netbox-sdk[all]'
```

## With uv tool

```bash
uv tool install --force 'netbox-sdk[cli]'
nbx --help
```

## From source

```bash
git clone https://github.com/emersonfelipesp/netbox-sdk.git
cd netbox-sdk
uv sync --dev --extra cli --extra tui --extra demo
uv run nbx --help
```

## Typed SDK support

The repository ships committed OpenAPI bundles and generated Pydantic models for
NetBox `4.5`, `4.4`, and `4.3`. Users do not need to run code generation locally.

## Which install should I pick?

- `pip install netbox-sdk` if you only need the Python SDK
- `pip install 'netbox-sdk[cli]'` if you want the `nbx` command
- `pip install 'netbox-sdk[tui]'` if you want to launch Textual TUIs from the
  package in an existing Python environment
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
