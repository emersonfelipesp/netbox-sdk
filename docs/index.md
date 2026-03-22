---
hide:
  - navigation
  - toc
---

# NetBox CLI

**API-first NetBox client for your terminal — CLI commands and interactive TUI in one tool.**

`netbox-cli` connects to any NetBox instance through its REST API and lets you list, inspect, create, update, and delete objects without ever opening a browser. Every resource available in the NetBox API is reachable from the command line, and the same backend powers a full interactive TUI.

If your NetBox instance exposes plugin endpoints under `/api/plugins/` with a full REST implementation, `netbox-cli` can discover those plugin resources automatically and surface them in both the CLI/TUI navigation and data views.

---

<div class="grid cards" markdown>

-   :material-console:{ .lg .middle } **CLI — OpenAPI-driven commands**

    ---

    Every NetBox resource is a first-class Typer subcommand, auto-generated from the OpenAPI schema. Full `--help` at every level.

    ```bash
    nbx dcim devices list
    nbx dcim devices get --id 1
    nbx ipam prefixes list -q status=active
    ```

    [:octicons-arrow-right-24: CLI Reference](cli/index.md)

-   :material-monitor:{ .lg .middle } **TUI — interactive Textual interface**

    ---

    A shell-style terminal UI that mirrors the NetBox web interface — navigation tree, tabbed workspace, filters, and live data.

    ```bash
    nbx tui
    nbx demo tui --theme dracula
    ```

    [:octicons-arrow-right-24: TUI Guide](tui/index.md)

-   :material-web:{ .lg .middle } **Demo profile — zero config**

    ---

    Try everything against the public `demo.netbox.dev` instance. Playwright authenticates automatically.

    ```bash
    nbx demo init
    nbx demo dcim devices list
    ```

    [:octicons-arrow-right-24: Demo Profile](cli/demo-profile.md)

-   :material-lightning-bolt:{ .lg .middle } **Quick start**

    ---

    Install, configure, and run your first command in under a minute.

    ```bash
    uv tool install --force .
    nbx init
    nbx dcim devices list
    ```

    [:octicons-arrow-right-24: Quick Start](getting-started/quickstart.md)

</div>

---

## Features at a glance

| Feature | Details |
|---------|---------|
| **OpenAPI-driven** | Every resource auto-discovered from the NetBox OpenAPI schema — no hard-coded endpoints |
| **CLI + TUI parity** | Same API client and schema index power both modes |
| **Profiles** | Separate `default` and `demo` profiles; environment variable overrides |
| **Token formats** | v2 (`nbt_key.secret`) and v1 (raw token) with automatic retry fallback |
| **Themes** | JSON-defined themes, auto-discovered, hot-switchable in TUI |
| **Cable trace** | ASCII cable trace diagram for interfaces with `--trace` |
| **Pure async** | `aiohttp` with `asyncio` throughout — no blocking I/O in TUI workers |
| **Output formats** | Rich tables (default), `--json`, `--yaml` |

---

## Contributor standard

Development uses `uv`, `ruff`, and `pre-commit` as the default workflow:

```bash
uv sync --dev
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
uv run pre-commit run --all-files
uv run pytest
```

The same pre-commit hooks are enforced in GitHub Actions, so local checks and CI stay aligned.

---

## Supported NetBox app groups

`circuits` · `core` · `dcim` · `extras` · `ipam` · `plugins` · `tenancy` · `users` · `virtualization` · `vpn` · `wireless`

All groups, resources, and operations are discovered at runtime from `reference/openapi/netbox-openapi.json`.
