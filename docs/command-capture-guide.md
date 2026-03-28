# Command Capture Guide

This repository ships a docs-safe capture pipeline for `nbx`. It records the
exact command input and output used to build the generated reference pages.

## Rule of operation

Docgen must only talk to demo NetBox instances.

- allowed: `demo.netbox.dev` or another dedicated non-production demo instance
- not allowed: a real production NetBox
- generated API examples should appear as `nbx demo ...` in the docs

## Main entry points

| Path | Purpose |
|------|---------|
| [`generate_command_docs.py`](generate_command_docs.py) | Standalone shim for local regeneration |
| `nbx docs generate-capture` | Preferred CLI entry point |
| [`run_capture_in_background.sh`](run_capture_in_background.sh) | Starts docgen under `nohup` |
| [`generated/nbx-command-capture.md`](generated/nbx-command-capture.md) | Combined Markdown snapshot |
| `generated/raw/` | Full JSON artifacts consumed by the MkDocs hook |

## Generated site output

The public docs separate generated artifacts by package surface:

- [CLI Command Output](reference/cli/command-examples/index.md)
- [TUI Launch Output](reference/tui/launch-examples/index.md)
- TUI screenshots remain under the [TUI screenshot gallery](tui/screenshots.md)

`netbox_sdk` does not get a generated command-output section because it is a
Python API package rather than an executable command surface.

## Usage

```bash
uv run nbx demo init
uv run nbx docs generate-capture
uv run mkdocs build --strict
```

## Output model

Each capture spec carries:

- `surface`: `cli` or `tui`
- `section`: generated page bucket
- `title`: page heading
- `argv`: command arguments
- `notes`: extra explanation shown in docs
- `safe`: whether failures are treated as valid captured output

The engine writes raw JSON first, then `docs/hooks.py` converts those artifacts
into surface-specific MkDocs pages.
