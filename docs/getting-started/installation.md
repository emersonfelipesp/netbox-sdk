# Installation

`netbox-cli` requires **Python 3.11 or newer**.

---

## From source (development)

The recommended approach while the project is in active development:

```bash
git clone https://github.com/emersonfelipesp/netbox-cli.git
cd netbox-cli
pip install -e .
nbx --help
```

The `-e` flag installs in editable mode so code changes take effect immediately without reinstalling.

---

## Global install with pipx

[pipx](https://pipx.pypa.io) installs Python tools in isolated environments and puts them on your PATH automatically.

```bash
pipx install -e /path/to/netbox-cli
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

## Project virtual environment

```bash
cd netbox-cli
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
nbx --help
```

To use `nbx` without activating the venv each time, add the venv's `bin` to your PATH:

=== "bash"

    ```bash
    echo 'export PATH="/path/to/netbox-cli/.venv/bin:$PATH"' >> ~/.bashrc
    source ~/.bashrc
    ```

=== "zsh"

    ```bash
    echo 'export PATH="/path/to/netbox-cli/.venv/bin:$PATH"' >> ~/.zshrc
    source ~/.zshrc
    ```

---

## Playwright (optional — demo profile only)

The `nbx demo init` command uses [Playwright](https://playwright.dev/python/) to log in to `demo.netbox.dev` and retrieve a fresh API token. Playwright is already declared as a dependency, but the browser must be installed separately:

```bash
playwright install chromium
# or, to install system dependencies as well:
playwright install chromium --with-deps
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
