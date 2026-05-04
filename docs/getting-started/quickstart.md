# Quick Start

Get up and running with the interface you actually plan to use.

--8<-- "snippets/documented-release-en.md"

---

## 1. Install and configure the shared runtime

```bash
pip install 'netbox-sdk[all]'
nbx init
# enter your NetBox URL and API token when prompted
```

Pinned to the documented release:

```bash
--8<-- "snippets/pip-pinned-all.txt"
nbx init
# enter your NetBox URL and API token when prompted
```

---

## 1a. Contributor setup

If you are developing `netbox-sdk` itself, use the repo-local environment and install the Git hooks:

```bash
cd /path/to/netbox-sdk
uv sync --dev --extra cli --extra tui --extra demo
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
uv run pre-commit run --all-files
```

---

## 2. Use the CLI

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

## 4. Launch the main TUI

```bash
nbx tui
nbx dev tui
nbx cli tui
nbx logs
```

Use the main browser for day-to-day navigation, the dev workbench for request
inspection, the CLI builder to assemble commands interactively, and `nbx logs`
to inspect the shared application log.

---

## 5. Create, update, delete

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

## 6. Try the demo profile

```bash
nbx demo init          # authenticates with demo.netbox.dev via Playwright
nbx demo dcim devices list
nbx demo tui
```

No personal NetBox instance is required. `demo.netbox.dev` is a public
playground and exposes the same CLI and TUI surfaces under `nbx demo ...`.

---

## 7. Use the SDK directly

```python
import asyncio

from netbox_sdk import api


async def main() -> None:
    nb = api("https://netbox.example.com", token="your-token")
    device = await nb.dcim.devices.get(42)
    if device is not None:
        print(device.name)


asyncio.run(main())
```

---

## 8. Use the typed SDK

```python
import asyncio

from netbox_sdk import typed_api


async def main() -> None:
    nb = typed_api(
        "https://netbox.example.com",
        token="your-token",
        netbox_version="4.5",
    )
    device = await nb.dcim.devices.get(42)
    if device is not None:
        print(device.name)


asyncio.run(main())
```

The typed client validates request and response payloads with committed Pydantic
models for NetBox `4.6`, `4.5`, `4.4`, and `4.3`.

---

## Next steps

- [SDK guide](../sdk/index.md) for Python entrypoints and transport behavior
- [CLI guide](../cli/index.md) for `nbx`, GraphQL, and command captures
- [TUI guide](../tui/index.md) for the main browser and the specialized TUIs
