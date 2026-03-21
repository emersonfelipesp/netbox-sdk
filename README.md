# NetBox CLI and TUI

## Contents

- [Quick Test with NetBox Demo Instance](#quick-test-with-netbox-demo-instance)
- [Install](#install)
  - [Install `nbx` Globally (bash + zsh)](#install-nbx-globally-bash--zsh)
- [Configure](#configure)
- [Command Modes](#command-modes)
  - [1) Dynamic mode (OpenAPI app/resource/action)](#1-dynamic-mode-openapi-appresourceaction)
  - [2) Explicit HTTP mode](#2-explicit-http-mode)
  - [3) Discovery helpers](#3-discovery-helpers)
  - [4) TUI mode](#4-tui-mode)
  - [Custom Themes (JSON)](#custom-themes-json)
- [Project Layout](#project-layout)
- [Notes](#notes)

---

`netbox-cli` is an API-first NetBox client that supports both:

- direct command execution (`nbx dcim devices get --id 1`)
- interactive Textual TUI (`nbx tui`)

The project is bootstrapped from `CLAUDE.md` requirements:

- API-only integration with NetBox (no model access)
- async HTTP via `aiohttp`
- shared backend logic for CLI and TUI
- OpenAPI-driven command/resource discovery

## Quick Test with NetBox Demo Instance

The fastest way to try `netbox-cli` — one command installs everything and connects to the public [demo.netbox.dev](https://demo.netbox.dev) instance.

**Install:**

```bash
# Debian/Ubuntu — install curl if not present
sudo apt-get update && sudo apt-get install -y curl

curl -fsSL https://raw.githubusercontent.com/emersonfelipesp/netbox-cli/main/install.sh | bash
```

The script installs [`uv`](https://github.com/astral-sh/uv) if not present, fetches `netbox-cli` directly from this GitHub repository, and sets up Playwright Chromium for the demo login flow.

**Authenticate with the demo instance:**

```bash
nbx demo init
# enter your demo.netbox.dev username and password when prompted
```

Or non-interactively (CI / scripted):

```bash
nbx demo init --username <your-demo-user> --password <your-demo-password>
```

**Run CLI commands against demo.netbox.dev:**

```bash
nbx demo dcim devices list
nbx demo dcim sites list
nbx demo ipam prefixes list
nbx demo circuits circuit-terminations get --id 15 --trace-only
```

**Launch the interactive TUI:**

```bash
nbx demo tui
```

Use `/` to search, `g` to focus the nav tree, `q` to quit. All commands that work under `nbx demo …` are available inside the TUI with the same demo profile.

---

## Install

```bash
cd <path-to-netbox-cli>
pip install -e .
```

## Install `nbx` Globally (bash + zsh)

Preferred (`pipx`):

```bash
pipx install -e <path-to-netbox-cli>
nbx --help
```

If `nbx` is not found, ensure your shell PATH includes `~/.local/bin`.

For **bash**:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
nbx --help
```

For **zsh**:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
nbx --help
```

Alternative (project venv, no activation needed):

```bash
cd <path-to-netbox-cli>
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

Then add the venv `bin` to your shell PATH:

For **bash**:

```bash
echo 'export PATH="<path-to-netbox-cli>/.venv/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
nbx --help
```

For **zsh**:

```bash
echo 'export PATH="<path-to-netbox-cli>/.venv/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
nbx --help
```

## Configure

```bash
nbx init
# prompts for base URL, token key, token secret, timeout
```

If configuration is missing, `nbx` will prompt for host/token credentials automatically before executing commands (including `nbx tui`).

Demo profile bootstrap:

```bash
nbx demo init
```

This always targets `https://demo.netbox.dev/`, opens the NetBox login flow in Playwright, prompts for demo username/password in the terminal, creates a fresh API token, and stores that token in the separate `demo` profile.

Install Playwright first if you want browser-based demo bootstrap:

```bash
pip install playwright
playwright install chromium
```

If you already have a demo API token, you can skip Playwright entirely:

```bash
nbx demo --token-key <key> --token-secret <secret>
```

The normal `nbx` profile and the `nbx demo` profile are stored separately in the same config file.

Stored config path:

- `$XDG_CONFIG_HOME/netbox-cli/config.json`
- or `~/.config/netbox-cli/config.json`

Environment overrides:

- `NETBOX_URL`
- `NETBOX_TOKEN_KEY`
- `NETBOX_TOKEN_SECRET`

Authentication is v2-token only and sent as:

- `Authorization: Bearer nbt_<KEY>.<TOKEN>`

## Command Modes

### 1) Dynamic mode (OpenAPI app/resource/action)

```bash
nbx dcim devices list
nbx dcim devices get --id 1
nbx ipam ip-addresses create --body-json '{"address":"192.0.2.10/24","status":"active"}'
nbx dcim devices list -q name=switch01
```

This path is now fully registered as real Typer subcommands generated from OpenAPI, so `--help` works at each level:

```bash
nbx dcim --help
nbx dcim devices --help
nbx dcim devices get --help
```

Demo mode uses the same command tree against `https://demo.netbox.dev/`:

```bash
nbx demo dcim devices list
nbx demo ipam prefixes list
nbx demo tui
```

Supported action aliases:

- `list -> GET`
- `get -> GET` (requires `--id`)
- `create -> POST`
- `update -> PUT` (requires `--id`)
- `patch -> PATCH` (requires `--id`)
- `delete -> DELETE` (requires `--id`)

### 2) Explicit HTTP mode

```bash
nbx call GET /api/status/
nbx call POST /api/ipam/ip-addresses/ --body-file ./payload.json
```

### 3) Discovery helpers

```bash
nbx groups
nbx resources dcim
nbx ops dcim devices
```

### 4) TUI mode

```bash
nbx tui
```

Theme options:

```bash
nbx tui --theme          # list available themes
nbx tui --theme dracula  # start with Dracula
```

You can also switch theme live from the top-left `Theme` dropdown in the TUI.

### Custom Themes (JSON)

Themes are loaded dynamically from:

- `netbox_cli/themes/`

Built-ins:

- `netbox_cli/themes/default.json`
- `netbox_cli/themes/dracula.json`

To add a custom theme, place `<theme>.json` in that folder. It will be auto-discovered.

Strict validation rules:

- required top-level keys: `name`, `label`, `dark`, `colors`
- optional keys: `variables`, `aliases`
- `colors` must define: `primary`, `secondary`, `warning`, `error`, `success`, `accent`, `background`, `surface`, `panel`, `boost`
- all color values must be `#RRGGBB`
- unknown keys, malformed colors, duplicate names, and alias conflicts fail fast with clear errors

TUI behavior (initial bootstrap):

- shell layout inspired by NetBox web UI:
  - top quick-search bar
  - left navigation tree (group -> resource)
  - main tabbed workspace (`Results`, `Details`, `Filters`)
  - footer status/help
- results view with incremental async refresh and row selection tracking
- details view rendered as panelized object attributes
- filters view with field picker + filter modal
- persisted last context/filter in local TUI state

Useful TUI keys:

- `/`: focus search
- `g`: focus navigation
- `s`: focus results table
- `r`: refresh current resource
- `f`: open filter modal
- `space`: toggle row selection
- `a`: toggle select all visible rows
- `d`: jump to details tab
- `q`: quit

## Project Layout

- `netbox_cli/config.py`: config storage + env overrides
- `netbox_cli/schema.py`: OpenAPI loading and indexing
- `netbox_cli/api.py`: async `aiohttp` client
- `netbox_cli/services.py`: shared request resolution and action mapping
- `netbox_cli/cli.py`: Typer entrypoint (CLI + dynamic parser)
- `netbox_cli/ui/app.py`: shell-style Textual app
- `netbox_cli/ui/panels.py`: panel widgets for detail rendering
- `netbox_cli/ui/state.py`: persisted TUI view state
- `netbox_cli/tui.py`: compatibility wrapper

## Notes

This is the initial bootstrap version. It establishes the architecture needed to mirror NetBox UI workflows over time while keeping CLI and TUI parity on top of the same API execution layer.
