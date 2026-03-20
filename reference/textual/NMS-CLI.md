# NMS-CLI — Standalone NMS Backend CLI

**Repository:** Local project (`/root/nms/nms-cli`)
**Language:** Python
**Frameworks:** Typer + Rich + Textual + prompt_toolkit
**Package:** `nms-cli` (`nms` entrypoint)
**Runtime target:** `nms-backend` FastAPI service over HTTP

---

## What It Does

`nms-cli` is a standalone operational CLI for network-management workflows. It exposes:

- A broad Typer command tree for NMS backend APIs (`snmp`, `netconf`, `gnmi`, `devices`, `auth`, `netbox`, etc.)
- A generic OpenAPI-aware HTTP invoker (`nms call`, `nms endpoints`, `nms endpoint`)
- A Textual interactive console (`nms console`) with command execution, completions, and health gating
- Captured examples/docs generation (`nms docs generate-capture`) used by `--example`/`-E`

It is CLI-first, with Textual used where interactive UX has clear operational value.

---

## Top-Level Command Index

From `nms --help`, major command groups are:

- Session/config: `init`, `whoami`, `token-set`, `token-clear`, `login`, `ping`
- Generic API: `call`, `endpoints`, `endpoint`
- Interactive UI: `console`
- Protocol domains: `snmp`, `netconf`, `gnmi`, `connection`
- Inventory/admin: `devices`, `credentials`, `auth`, `settings`, `nmt`, `capabilities`, `interfaces`, `ports`
- NetBox integration: `netbox` (including GPON sync flows)
- Docs/capture: `docs`

Global options include `--base-url`, `--token`, `--timeout`, `--json`, and `--example/-E`.

---

## Architecture Index

### CLI composition

- `nms_cli/cli.py`
  - Declares Typer app tree and all command handlers
  - Mounts nested sub-apps via `add_typer(...)` (e.g., `gnmi openconfig interfaces ...`)
  - Implements startup stderr feedback ("submitted"/"still running")
  - Integrates `--example` capture lookup via `example_help.py`

### HTTP/runtime layer

- `nms_cli/http.py`
  - `RuntimeContext` (base URL, token, timeout, output mode)
  - Blocking urllib request primitive + async wrapper (`request_async`)
  - Response rendering in human tables or raw JSON
  - Query/header/body parsing helpers and validation

### Config/cache

- `nms_cli/config.py`
  - XDG-aware config path resolution
  - Persistent `config.json` with `base_url`, `token`, `timeout`
  - Device cache file for picker/autocomplete workflows

### Textual interfaces

- `nms_cli/console_ui.py`
  - Fixed-layout Textual console (`NmsConsole`)
  - Worker-group based async execution and health checks
  - OpenAPI-assisted endpoint picker flows
- `nms_cli/device_picker.py`
  - Minimal Textual selector for `--device` omission flows
- `nms_cli/gpon_sync_stream.py`
  - SSE streaming presentation for NetBox GPON full sync
  - Textual live log outside console mode, Rich stdout in console mode

### Docs/capture pipeline

- `nms_cli/docgen_capture.py`
  - Defines capture specs and emits:
    - `docs/generated/nms-command-capture.md`
    - `docs/generated/raw/*.json`
  - Refreshes packaged examples used by `nms ... --example`

### Command UX support

- `nms_cli/console_completions.py`
  - Structured completion tree for `nms console` input
- `nms_cli/example_help.py`
  - Shared wiring for `--example` exits and key mapping

---

## Key Design Patterns

### 1. CLI-first with optional TUI layer

Core operations are always available as plain commands; Textual is additive (`console`, device picker, GPON stream viewer).

### 2. Shared runtime context

Commands normalize config/env/flags into one `RuntimeContext`, keeping HTTP behavior consistent across the entire tree.

### 3. OpenAPI-driven operator workflows

`endpoints`/`endpoint` consume local or live schemas to expose discoverable API metadata, then feed directly into `call` UX patterns.

### 4. Explicit long-run feedback

Every top-level invocation emits immediate stderr status and delayed "still running" hints for slow backend jobs.

### 5. Reproducible command examples

`--example` outputs are package-shipped artifacts generated from executable capture specs, not hand-written snippets.

### 6. Console-safe execution boundary

`nms console` executes subcommands in controlled worker/thread flow and avoids nested Textual for GPON stream output.

---

## Useful File Index

- `README.md` — install paths, quick start, console behavior, command examples
- `pyproject.toml` — dependencies and `nms = nms_cli.cli:main` entrypoint
- `nms_cli/cli.py` — command tree and command handlers
- `nms_cli/http.py` — request/response primitives and renderers
- `nms_cli/config.py` — persisted config + device cache
- `nms_cli/console_ui.py` — interactive console app
- `nms_cli/device_picker.py` — Textual device selector
- `nms_cli/docgen_capture.py` — docs/capture generator
- `docs/README.md` — documentation index
- `docs/command-capture-guide.md` — capture workflow usage
- `docs/generated/nms-command-capture.md` — generated command I/O reference

---

## Relevance to NMS-CLI Textual Research

Compared with external reference projects in this folder, `nms-cli` is the in-repo implementation target that combines:

- Deep Typer command topology (production API surface)
- Practical Textual operator UX (`console`, pickers, stream viewers)
- OpenAPI-driven discoverability
- Operational documentation automation via captured executions

It serves as the canonical local baseline for architecture and UX decisions.
