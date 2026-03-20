# Command capture documentation

This folder contains tooling to produce **reference documentation** where each section shows:

1. The **command input** (what you would type).
2. The **command output** (stdout/stderr as captured at generation time).
3. **Exit code** and approximate **wall time**.

## Files

| Path | Purpose |
|------|---------|
| [`generate_command_docs.py`](generate_command_docs.py) | Standalone shim that calls `netbox_cli.docgen_capture` directly (no Typer app startup). |
| **`nbx docs generate-capture`** | Preferred: built-in Typer command (same generator, accessible via the installed CLI). |
| [`run_capture_in_background.sh`](run_capture_in_background.sh) | Starts the generator under `nohup`, appends to `generated/capture-run.log`, writes PID to `generated/capture-run.pid`. |
| [`generated/nbx-command-capture.md`](generated/nbx-command-capture.md) | **Generated** long-form reference (input + output per command). |
| [`generated/raw/`](generated/raw/) | **Generated** per-command JSON files (`stdout_full`, exit code, timing). |

---

## Quick start

From the `netbox-cli` repository root, with the package installed:

```bash
pip install -e .
nbx docs generate-capture
# equivalent: python docs/generate_command_docs.py
```

### Background run

```bash
chmod +x docs/run_capture_in_background.sh
./docs/run_capture_in_background.sh
tail -f docs/generated/capture-run.log
```

Stop with `kill "$(cat docs/generated/capture-run.pid)"` if still running.

---

## CLI options

```text
nbx docs generate-capture --help
python docs/generate_command_docs.py --help
```

| Flag | Default | Effect |
|------|---------|--------|
| `--output` / `-o` | `docs/generated/nbx-command-capture.md` | Markdown destination |
| `--raw-dir` | `docs/generated/raw/` next to the Markdown file | Raw JSON artifact directory |
| `--max-lines` | `200` | Lines of output embedded per command in Markdown (full text stays in `raw/*.json`) |
| `--max-chars` | `120000` | Characters of output embedded per command in Markdown |

---

## Environment variables

| Variable | Default | Effect |
|----------|---------|--------|
| `NETBOX_URL` | `https://demo.netbox.dev` | NetBox base URL used for live API specs |
| `NETBOX_TOKEN_KEY` | `docgen-placeholder` | Token key for live API specs (use a real key for authenticated output) |
| `NETBOX_TOKEN_SECRET` | `placeholder` | Token secret for live API specs |
| `NBX_DOC_CAPTURE_TIMEOUT` | `30` | HTTP timeout in seconds for live API calls |
| `NBX_DOC_PYTHON` | auto-detected | Python interpreter for the background script |

With real credentials pointing at a live NetBox instance, the live API specs will produce real response output. Without credentials, help banners and schema-discovery commands still work correctly.

---

## How it works

### Capture specs (`netbox_cli/docgen_capture.py`)

Each command to capture is declared as a `CaptureSpec`:

```python
@dataclass(frozen=True, slots=True)
class CaptureSpec:
    section: str      # Markdown section heading (e.g. "Top-level", "Live API")
    title: str        # Markdown sub-heading (e.g. "nbx groups")
    argv: list[str]   # Arguments passed to the Typer app (without "nbx")
    notes: str = ""   # Optional italic note printed below the input block
    safe: bool = True # True → catch_exceptions=False (fast fail); False → catch_exceptions=True (network calls)
```

### Stub config injection

Most `nbx` commands call `_ensure_runtime_config()` in `root_callback`, which would prompt for NetBox credentials if none are configured. The generator bypasses this by injecting a stub `Config` object directly into `cli._RUNTIME_CONFIG` before each CliRunner invocation:

```
_inject_stub_config()  → sets cli._RUNTIME_CONFIG = Config(base_url=..., token_key=..., ...)
CliRunner.invoke(app, spec.argv)
    └─ root_callback → _ensure_runtime_config() sees _RUNTIME_CONFIG is complete → returns early
_clear_stub_config()   → resets cli._RUNTIME_CONFIG = None
```

The `"docs"` subcommand is also excluded from the `root_callback` config check so that `nbx docs generate-capture` itself never prompts:

```python
if ctx.invoked_subcommand not in {"init", "tui", "docs"}:
    _ensure_runtime_config()
```

### Safe vs. unsafe specs

- **`safe=True`** (default) — `catch_exceptions=False` in CliRunner. The generator aborts if the command raises an unhandled exception. Used for help banners, config display, and schema-discovery commands that read the local OpenAPI file.
- **`safe=False`** — `catch_exceptions=True` in CliRunner. Unhandled exceptions (e.g. `aiohttp.ClientConnectionError` on live API calls) are captured and included in the output. The generator continues to the next spec. Used for `call` and dynamic-form specs.

### Schema-discovery commands

`groups`, `resources`, and `ops` commands read from `reference/openapi/netbox-openapi.json` via `build_schema_index()`. This file is resolved relative to the repo root, so these specs only produce output when the generator is run from a `netbox-cli` git checkout (same constraint as the `docs/` directory requirement).

### Dynamic sub-commands

`_register_openapi_subcommands()` in `cli.py` runs at import time and registers a full Typer sub-app tree from the OpenAPI schema (e.g. `nbx dcim devices list`). The generator captures `--help` for these commands (safe, no network) and live invocations (unsafe, require NetBox).

### Output format

For each spec the generator writes:

- **A Markdown section** in `docs/generated/nbx-command-capture.md` with the input, notes, exit code, wall time, and truncated output.
- **A raw JSON file** in `docs/generated/raw/NNN-<slug>.json` with the full untruncated output plus metadata.
- **`docs/generated/raw/index.json`** — a summary of all runs including generation metadata.

---

## Regenerating after CLI changes

Whenever subcommands, help text, or output formatting change, re-run the generator and commit the updated `docs/generated/` snapshot:

```bash
nbx docs generate-capture
git add docs/generated/
git commit -m "docs: regenerate command capture"
```
