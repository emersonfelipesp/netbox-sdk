---
hide:
  - navigation
  - toc
---

# NetBox SDK

**SDK-first NetBox toolkit for Python, the terminal, and Textual UIs.**

`netbox-sdk` is built as four sibling packages:

- `netbox_sdk` — standalone NetBox REST SDK
- `netbox_cli` — Typer-powered CLI
- `netbox_tui` — Textual-powered TUI
- `netbox_mcp` — schema-driven Model Context Protocol server

The repository ships four public surfaces:

- `netbox_sdk` for Python integrations
- `nbx` for CLI workflows
- multiple Textual TUIs for browsing, debugging, and guided command execution
- `nbx-mcp` for schema-driven agent access over stdio or authenticated Streamable HTTP

The SDK package itself exposes three layers:

- `NetBoxApiClient` for low-level async HTTP control
- `api()` / `Api` for the async facade layer
- `typed_api()` for the versioned typed client backed by committed Pydantic models

The current stable typed SDK release lines are NetBox `4.7`, `4.6`, `4.5`, `4.4`, and `4.3`; the default uses the official `v4.7.0` GA schema.
Continuous integration exercises the live-NetBox suite against
`v4.7.0`, `v4.6.6`, `v4.6.3`, `v4.6.2`, and `v4.5.10`.

--8<-- "snippets/documented-release-en.md"

<div class="grid cards" markdown>

-   :material-api:{ .lg .middle } **SDK**

    ```python
    from netbox_sdk import api, typed_api
    ```

    [:octicons-arrow-right-24: SDK Guide](sdk/index.md)

-   :material-console:{ .lg .middle } **CLI**

    ```bash
    nbx dcim devices list
    nbx dcim devices get --id 1
    ```

    [:octicons-arrow-right-24: CLI Guide](cli/index.md)

-   :material-monitor:{ .lg .middle } **TUI**

    ```bash
    nbx tui
    nbx demo tui --theme dracula
    ```

    [:octicons-arrow-right-24: TUI Guide](tui/index.md)

-   :material-robot:{ .lg .middle } **MCP**

    ```bash
    pip install 'netbox-sdk[mcp]'
    nbx-mcp
    ```

    [:octicons-arrow-right-24: MCP Guide](mcp/index.md)

-   :material-lightning-bolt:{ .lg .middle } **Quick Start**

    ```bash
    pip install 'netbox-sdk[all]'
    --8<-- "snippets/pip-pinned-all.txt"
    nbx init
    nbx dcim devices list
    ```

    [:octicons-arrow-right-24: Quick Start](getting-started/quickstart.md)

</div>

## Product split

- `SDK` docs focus on importable Python APIs, request layers, authentication,
  and versioned typed clients.
- `CLI` docs focus on the `nbx` command tree, dynamic commands, GraphQL, demo
  profile, and captured command examples.
- `TUI` docs focus on the main browser, developer workbench, CLI builder, logs
  viewer, and Django model browser.
- `MCP` docs focus on tools, transport authentication, mutation safety,
  release-line resolution, and semantic plugin bridge dispatch.

## Contributor standard

```bash
uv sync --dev --extra cli --extra tui --extra demo --extra mcp
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
uv run pre-commit run --all-files
uv run pytest
```
