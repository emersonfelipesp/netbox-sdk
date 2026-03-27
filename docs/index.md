---
hide:
  - navigation
  - toc
---

# netbox-sdk

**API-first NetBox client for your terminal: CLI, TUI, and reusable SDK.**

`netbox-sdk` is built as three sibling packages:

- `netbox_sdk` — standalone NetBox REST SDK
- `netbox_cli` — Typer-powered CLI
- `netbox_tui` — Textual-powered TUI

The SDK itself exposes three layers:

- `NetBoxApiClient` for low-level async HTTP control
- `api()` / `Api` for the async facade layer
- `typed_api()` for the versioned typed client backed by committed Pydantic models

The current typed SDK release lines are NetBox `4.5`, `4.4`, and `4.3`.

<div class="grid cards" markdown>

-   :material-console:{ .lg .middle } **CLI**

    ```bash
    nbx dcim devices list
    nbx dcim devices get --id 1
    ```

    [:octicons-arrow-right-24: CLI Reference](cli/index.md)

-   :material-monitor:{ .lg .middle } **TUI**

    ```bash
    nbx tui
    nbx demo tui --theme dracula
    ```

    [:octicons-arrow-right-24: TUI Guide](tui/index.md)

-   :material-api:{ .lg .middle } **SDK**

    ```bash
    pip install netbox-sdk
    python -c "import netbox_sdk"
    ```

    [:octicons-arrow-right-24: SDK Guide](sdk/index.md)

-   :material-lightning-bolt:{ .lg .middle } **Quick Start**

    ```bash
    pip install 'netbox-sdk[all]'
    nbx init
    nbx dcim devices list
    ```

    [:octicons-arrow-right-24: Quick Start](getting-started/quickstart.md)

</div>

## Contributor standard

```bash
uv sync --dev --extra cli --extra tui --extra demo
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
uv run pre-commit run --all-files
uv run pytest
```
