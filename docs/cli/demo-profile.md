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

When you initialize the demo profile this way, `nbx` also stores the demo username and password in the same private config file so it can automatically refresh the demo token later if `demo.netbox.dev` resets and starts returning `Invalid v1 token`.

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
    uv tool run --from playwright playwright install chromium --with-deps
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

The config output also shows whether demo login credentials are available for automatic token refresh.

---

## Running commands against demo

The `nbx demo` subcommand tree mirrors the full `nbx` tree, using the demo profile's token and `https://demo.netbox.dev` as the base URL:

```bash
nbx demo dcim devices list
nbx demo ipam prefixes list -q status=active
nbx demo dcim sites list --json
nbx demo dcim interfaces get --id 4 --trace
nbx demo call GET /api/status/
nbx demo dev tui
```

If the saved demo token has expired because the public demo instance reset overnight, `nbx` will automatically try to provision a fresh demo token using the saved demo username and password before surfacing the auth failure to you.

---

## Demo TUI

```bash
nbx demo tui
nbx demo tui --theme dracula
```

Launches the Textual TUI pre-connected to the demo instance.

---

## Demo Dev TUI

```bash
nbx demo dev tui
nbx demo dev tui --theme dracula
```

Launches the developer request workbench pre-connected to the demo instance, so you can inspect paths and execute requests against `demo.netbox.dev` without switching profiles.

---

## Demo Dev HTTP

`nbx demo dev http` mirrors `nbx dev http`: the same verbs (`get`, `post`, `put`, `patch`, `delete`, `paths`, `ops`) and output flags (`--json`, `--yaml`, `--markdown`) apply, and every HTTP call uses the demo profile.

```bash
nbx demo dev http get --path /api/status/
nbx demo dev http get --path /dcim/devices/ -q limit=3 --markdown
```

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
      "demo_username": "nbxuser",
      "demo_password": "mypassword",
      "timeout": 30.0
    }
  }
}
```

The `base_url` for the demo profile is always hardcoded to `https://demo.netbox.dev` regardless of what is stored in the config file.
The config file is written with private user-only permissions so the stored demo credentials stay local to your machine.
