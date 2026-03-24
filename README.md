# NetBox CLI and TUI

`netbox-cli` is a terminal client for NetBox with two ways to work:

- fast command-line operations such as `nbx dcim devices get --id 1`
- interactive terminal apps such as `nbx tui` and `nbx dev tui`

## Quick Start with the Demo Instance

Install (official PyPI):

```bash
sudo apt-get update && sudo apt-get install -y curl
curl -fsSL https://raw.githubusercontent.com/emersonfelipesp/netbox-cli/main/install.sh | bash
```

Reload your shell:

```bash
source ~/.bashrc   # bash
source ~/.zshrc    # zsh
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

Install from official PyPI:

```bash
pip install netbox-cli
```

or with `uv`:

```bash
uv tool install --force netbox-cli
```

Install from a local checkout (developer workflow):

```bash
cd <path-to-netbox-cli>
uv tool install --force .
```

If `nbx` is not available after install, make sure `~/.local/bin` is in your `PATH`.

## Configure

Set up your normal profile:

```bash
nbx init
```

Set up the demo profile:

```bash
nbx demo init
```

You can also pass credentials directly when needed:

```bash
nbx demo init --username <your-demo-user> --password <your-demo-password>
```

## Common Commands

List and inspect resources:

```bash
nbx dcim devices list
nbx dcim devices get --id 1
nbx ipam prefixes list
```

Create or update objects:

```bash
nbx ipam ip-addresses create --body-json '{"address":"192.0.2.10/24","status":"active"}'
nbx dcim devices patch --id 1 --body-json '{"name":"edge-sw01"}'
```

Send direct HTTP requests:

```bash
nbx call GET /api/status/
nbx call POST /api/ipam/ip-addresses/ --body-file ./payload.json
```

Explore available groups, resources, and operations:

```bash
nbx groups
nbx resources dcim
nbx ops dcim devices
```

## TUI Modes

Main TUI:

```bash
nbx tui
nbx demo tui
```

Developer workbench:

```bash
nbx dev tui
nbx demo dev tui
```

Log viewer:

```bash
nbx logs
```

## Themes

List available themes:

```bash
nbx tui --theme
```

Start with a specific theme:

```bash
nbx tui --theme dracula
nbx tui --theme netbox-light
nbx dev tui --theme netbox-dark
```

You can also change themes live from the top-left theme selector in the TUI.

## Useful TUI Keys

- `/` focus search
- `g` focus navigation
- `s` focus results
- `r` refresh current resource
- `f` open filters
- `d` switch to details
- `q` quit

## Custom Themes

Built-in themes include:

- `netbox-dark`
- `dracula`
- `netbox-light`

You can add your own theme by placing a JSON theme file in `netbox_cli/themes/`.

## Tips

- `nbx demo ...` uses a separate demo profile from your normal `nbx ...` profile.
- If a command works in the CLI, there is usually a matching flow in the TUI.
- The Dev TUI is useful for exploring endpoints, request timing, and raw JSON responses.
