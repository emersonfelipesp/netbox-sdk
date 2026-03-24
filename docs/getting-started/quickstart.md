# Quick Start

Get up and running in under a minute.

---

## 1. Install and configure

```bash
pip install netbox-cli
nbx init
# enter your NetBox URL and API token when prompted
```

---

## 1a. Contributor setup

If you are developing `netbox-cli` itself, use the repo-local environment and install the Git hooks:

```bash
cd /path/to/netbox-cli
uv sync --dev
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
uv run pre-commit run --all-files
```

---

## 2. Discover what's available

```bash
# list all OpenAPI app groups
nbx groups

# list resources in a group
nbx resources dcim

# list operations for a specific resource
nbx ops dcim devices
```

---

## 3. Query data

```bash
# list all devices
nbx dcim devices list

# get a specific device by ID
nbx dcim devices get --id 1

# filter results
nbx dcim devices list -q name=switch01
nbx dcim devices list -q site=nyc01 -q status=active

# output as JSON, YAML, or Markdown
nbx dcim devices list --json
nbx ipam prefixes list --yaml
nbx dcim devices list --markdown
```

---

## 4. Create, update, delete

```bash
# create a new IP address
nbx ipam ip-addresses create --body-json '{"address":"192.0.2.10/24","status":"active"}'

# create from a file
nbx dcim devices create --body-file ./new-device.json

# update a device
nbx dcim devices update --id 42 --body-json '{"status":"planned"}'

# patch a single field
nbx dcim devices patch --id 42 --body-json '{"comments":"rack shelf 3"}'

# delete
nbx dcim devices delete --id 42
```

---

## 5. Use the TUI

```bash
nbx tui
```

The TUI opens with a navigation tree on the left. Select a resource group to browse and filter objects interactively.

---

## 6. Try the demo profile (no config needed)

```bash
nbx demo init          # authenticates with demo.netbox.dev via Playwright
nbx demo dcim devices list
nbx demo tui
```

No NetBox instance required — `demo.netbox.dev` is a public playground.

---

## Next steps

- [CLI commands reference](../cli/commands.md) — all top-level commands
- [Dynamic commands](../cli/dynamic-commands.md) — how group/resource/action commands work
- [TUI guide](../tui/index.md) — navigation, themes, keyboard shortcuts
- [Command examples](../reference/command-examples.md) — live-captured output for every command
