# Command capture documentation

This folder contains tooling to produce **reference documentation** where each section shows:

1. The **command input** (what you would type).
2. The **command output** (stdout/stderr as captured at generation time).
3. **Exit code** and approximate **wall time**.

Live-API specs run against **demo.netbox.dev** by default using the `nbx demo` profile.
Pass `--live` to run them against your own NetBox instance instead.

## Files

| Path | Purpose |
|------|---------|
| [`generate_command_docs.py`](generate_command_docs.py) | Standalone shim that calls `netbox_cli.docgen_capture` directly (no Typer app startup). |
| **`nbx docs generate-capture`** | Preferred: built-in Typer command (same generator, accessible via the installed CLI). |
| [`run_capture_in_background.sh`](run_capture_in_background.sh) | Starts the generator under `nohup`, appends to `generated/capture-run.log`, writes PID to `generated/capture-run.pid`. |
| [`generated/nbx-command-capture.md`](generated/nbx-command-capture.md) | **Generated** long-form reference (input + output per command). |
| [`generated/raw/`](generated/raw/) | **Generated** per-command JSON files (`stdout_full`, exit code, timing). |
| [`../.github/workflows/docs-capture.yml`](../.github/workflows/docs-capture.yml) | CI workflow that runs on every push to `main`, authenticates with demo.netbox.dev, and commits the regenerated snapshot. |

---

## Quick start

From the `netbox-cli` repository root, with the package installed:

```bash
uv tool install --force .

# Default: live-API specs hit demo.netbox.dev (demo profile)
nbx docs generate-capture

# Optional: configure the demo profile first for real API output
nbx demo init   # prompts for demo.netbox.dev credentials

# Alternative: run against your own NetBox (default profile)
nbx docs generate-capture --live

# Equivalent standalone shim
python docs/generate_command_docs.py
python docs/generate_command_docs.py --live
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
| `--live` | off | Use the **default profile** (your real NetBox) instead of the demo profile |

---

## Environment variables

| Variable | Default | Effect |
|----------|---------|--------|
| `NETBOX_URL` | `https://netbox.example.com` | Base URL for `--live` mode (default profile) |
| `NETBOX_TOKEN_KEY` | `docgen-placeholder` | Token key injected as a stub when no real config exists on disk |
| `NETBOX_TOKEN_SECRET` | `placeholder` | Token secret injected as a stub when no real config exists on disk |
| `NBX_DOC_CAPTURE_TIMEOUT` | `30` | HTTP timeout in seconds for live API calls |
| `NBX_DOC_PYTHON` | auto-detected | Python interpreter for the background script |

---

## How it works

### Two modes: demo (default) vs. live (`--live`)

| | Demo mode (default) | Live mode (`--live`) |
|-|--------------------|--------------------|
| **Profile** | `demo` → `demo.netbox.dev` | `default` → your configured NetBox |
| **Live spec commands** | `nbx demo dcim devices list`, … | `nbx call GET /api/status/`, `nbx dcim devices list`, … |
| **Config source** | `nbx demo init` / disk | `nbx init` / disk |
| **CI workflow** | Uses Playwright to authenticate demo | Requires a real NetBox and credentials |

### Capture specs (`netbox_cli/docgen_capture.py`)

Each command to capture is declared as a `CaptureSpec`:

```python
@dataclass(frozen=True, slots=True)
class CaptureSpec:
    section: str      # Markdown section heading (e.g. "Top-level", "Live API — demo.netbox.dev")
    title: str        # Markdown sub-heading (e.g. "nbx demo dcim devices list")
    argv: list[str]   # Arguments passed to the Typer app (without "nbx")
    notes: str = ""   # Optional italic note below the input block
    safe: bool = True # True → catch_exceptions=False; False → catch_exceptions=True (network calls)
```

### Stub config injection

The generator may need to inject a temporary config so that CLI commands don't prompt
interactively when no real credentials are configured on disk.  The logic in `_inject_stub_config`:

```
load_profile_config(profile) → if complete on disk:
    cache it in _RUNTIME_CONFIGS[profile]  (real data, don't clear after invoke)
    return False
else:
    inject placeholder Config into _RUNTIME_CONFIGS[profile]
    return True  → caller clears the entry after invoke
```

When the demo profile is configured on disk (e.g. after `nbx demo init`), `_inject_stub_config`
loads the real token into the in-process cache.  The CliRunner invocation then calls
`_ensure_demo_runtime_config()` → `_load_cached_profile("demo")` and finds real credentials,
so live API calls succeed.

When no config exists (offline local run), a placeholder is injected and live calls return
401/403 — which is still useful documentation of real CLI behavior.

### Safe vs. unsafe specs

- **`safe=True`** (default) — `catch_exceptions=False`. Help banners, config display, and
  schema-discovery commands that read the local OpenAPI file. The generator aborts if these
  raise an unhandled exception (indicates a bug).
- **`safe=False`** — `catch_exceptions=True`. Live API specs (`nbx demo dcim devices list`,
  `nbx call GET /api/status/`, …). aiohttp connection errors are caught and surfaced in the
  output; the generator continues to the next spec.

### Schema-discovery commands

`groups`, `resources`, and `ops` read from `reference/openapi/netbox-openapi.json` via
`build_schema_index()`. This path is resolved relative to the repo root, so these specs only
produce output when the generator runs from a `netbox-cli` git checkout.

### Output format

For each spec the generator writes:

- **A Markdown section** in `docs/generated/nbx-command-capture.md` with the input, notes,
  exit code, wall time, and truncated output.
- **A raw JSON file** in `docs/generated/raw/NNN-<slug>.json` with the full untruncated output.
- **`docs/generated/raw/index.json`** — summary of all runs including generation metadata.

---

## GitHub Actions CI

The workflow at [`.github/workflows/docs-capture.yml`](../.github/workflows/docs-capture.yml)
runs automatically on every push to `main` (which includes merged pull requests).

### What it does

1. Checks out the repository.
2. Installs `netbox-cli` and its dependencies.
3. Installs Playwright and the Chromium browser (`uv tool run --from playwright playwright install chromium --with-deps`).
4. Runs `nbx demo init --username … --password … --headless` to authenticate with
   demo.netbox.dev and save the demo profile to disk.
5. Runs `nbx demo config` to verify the saved token.
6. Runs `nbx docs generate-capture` (demo mode, no `--live`).
7. Commits and pushes any changes to `docs/generated/` with the message
   `docs: regenerate command capture [skip ci]`.

### Required repository secrets

| Secret | Value |
|--------|-------|
| `DEMO_USERNAME` | `nbxuser` |
| `DEMO_PASSWORD` | `@nm12345678` |

Set these under **Settings → Secrets and variables → Actions** in the GitHub repository.

### `[skip ci]` tag

The commit message includes `[skip ci]` to prevent the docs-capture workflow from
re-triggering itself when it pushes the regenerated snapshot.

---

## Regenerating manually after CLI changes

Whenever subcommands, help text, or output formatting change, re-run the generator and commit:

```bash
nbx demo init          # if demo profile not yet configured
nbx docs generate-capture
git add docs/generated/
git commit -m "docs: regenerate command capture"
```
