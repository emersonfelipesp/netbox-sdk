# Installation

`netbox-cli` requires **Python 3.11 or newer**.

---

## From source (development)

The recommended approach while the project is in active development:

```bash
git clone https://github.com/emersonfelipesp/netbox-cli.git
cd netbox-cli
uv tool install --force .
nbx --help
```

For contributor workflows where you want repo-local commands without reinstalling the tool on each change:

```bash
uv sync --dev
uv run nbx --help
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
```

---

## From official PyPI (recommended)

```bash
pip install netbox-cli
nbx --help
```

If you want isolated CLI installation with `uv`:

```bash
uv tool install --force netbox-cli
nbx --help
```

---

## Global install with uv tool

[`uv tool`](https://docs.astral.sh/uv/concepts/tools/) installs Python CLIs in isolated environments and puts the executable on your PATH.

```bash
uv tool install --force /path/to/netbox-cli
nbx --help
```

If `nbx` is not found after install, add `~/.local/bin` to your PATH:

=== "bash"

    ```bash
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    source ~/.bashrc
    ```

=== "zsh"

    ```bash
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
    source ~/.zshrc
    ```

---

## Repo-local development environment

```bash
cd netbox-cli
uv sync --dev
uv run nbx --help
```

Use this for tests, docs, and local iteration. Use `uv tool install --force ...` when you want the `nbx` executable installed as a user tool.

Recommended contributor setup:

```bash
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
uv run pre-commit run --all-files
uv run pytest
```

The project standard is Ruff for linting/formatting and `pre-commit` for enforcing those checks before commits and pushes.

---

## Playwright (optional — demo profile only)

The `nbx demo init` command uses [Playwright](https://playwright.dev/python/) to log in to `demo.netbox.dev` and retrieve a fresh API token. Playwright is already declared as a dependency, but the browser must be installed separately:

```bash
uv tool run --from playwright playwright install chromium --with-deps
```

If you already have a demo API token, you can skip Playwright entirely — see [Demo Profile](../cli/demo-profile.md#direct-token-setup).

---

## Verifying the install

```bash
nbx --help
```

You should see the top-level help banner listing all available commands and OpenAPI app groups.

---

## Dependencies

| Package | Role |
|---------|------|
| `typer >= 0.12` | CLI framework |
| `textual >= 0.62` | TUI framework |
| `aiohttp >= 3.9` | Async HTTP client |
| `rich >= 13.7` | Terminal output formatting |
| `pyyaml >= 6.0` | YAML output support |
| `playwright >= 1.52` | Browser automation for `nbx demo init` |
