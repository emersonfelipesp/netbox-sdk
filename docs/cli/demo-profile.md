# Demo Profile

The `demo` profile lets you run every `nbx` command against the public [demo.netbox.dev](https://demo.netbox.dev) instance — no personal NetBox server required.

---

## Setup with Playwright

`nbx demo init` uses Playwright to open a headless Chromium browser, log in to `demo.netbox.dev`, create a fresh API token, and store it automatically:

```bash
nbx demo init
# prompts for demo.netbox.dev username and password
```

For CI or scripted use, pass credentials as flags:

```bash
nbx demo init --username nbxuser --password mypassword --headless
```

**Options for `nbx demo init`**

| Flag | Description |
|------|-------------|
| `--username` / `-u` | demo.netbox.dev username (prompted if omitted) |
| `--password` / `-p` | demo.netbox.dev password (prompted if omitted) |
| `--headless` / `--headed` | Run Playwright headless (default) or with a visible browser window |
| `--token-key` | Skip Playwright — set token directly |
| `--token-secret` | Skip Playwright — set token directly |

!!! tip "Playwright installation"
    Install Playwright and the Chromium browser before running `nbx demo init`:

    ```bash
    pip install playwright
    playwright install chromium --with-deps
    ```

---

## Direct token setup

If you already have a demo API token, skip Playwright entirely:

```bash
# v2 token (key + secret)
nbx demo init --token-key <key> --token-secret <secret>

# v1 token (single string) — set token_version manually in config.json
nbx demo --token-key "" --token-secret <40-char-token>
```

---

## Verify the demo config

```bash
nbx demo config
nbx demo config --show-token   # reveal token values
```

---

## Running commands against demo

The `nbx demo` subcommand tree mirrors the full `nbx` tree, using the demo profile's token and `https://demo.netbox.dev` as the base URL:

```bash
nbx demo dcim devices list
nbx demo ipam prefixes list -q status=active
nbx demo dcim sites list --json
nbx demo dcim interfaces get --id 4 --trace
nbx demo call GET /api/status/
```

---

## Demo TUI

```bash
nbx demo tui
nbx demo tui --theme dracula
```

Launches the Textual TUI pre-connected to the demo instance.

---

## Reset

Remove saved demo credentials:

```bash
nbx demo reset
```

---

## How the demo profile is stored

The demo profile is stored alongside the default profile in `~/.config/netbox-cli/config.json`:

```json
{
  "profiles": {
    "default": { "...": "..." },
    "demo": {
      "base_url": "https://demo.netbox.dev",
      "token_version": "v1",
      "token_key": null,
      "token_secret": "40-character-token-here",
      "timeout": 30.0
    }
  }
}
```

The `base_url` for the demo profile is always hardcoded to `https://demo.netbox.dev` regardless of what is stored in the config file.
