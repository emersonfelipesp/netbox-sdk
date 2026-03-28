# Documentation Generation

`netbox-sdk` includes a built-in capture system that runs selected `nbx`
commands, records their output, and generates package-oriented reference pages
for the CLI and TUI surfaces.

The output is split deliberately:

- [CLI Command Output](../reference/cli/command-examples/index.md) covers `netbox_cli`
- [TUI Launch Output](../reference/tui/launch-examples/index.md) covers `netbox_tui`
- `netbox_sdk` stays documented through handwritten SDK guides, because it does
  not expose a direct command surface

## Safety rule

Docgen is restricted to the demo profile only. It must never run against a
production NetBox instance.

- live API captures use `nbx demo ...`
- help and local schema-discovery captures may use root commands like `nbx groups`
- no `--live` mode is supported

## Quick start

```bash
cd /path/to/netbox-sdk
uv sync --group docs --group dev --extra cli --extra tui --extra demo
uv run nbx demo init
uv run nbx docs generate-capture
```

## CLI options

| Flag | Default | Description |
|------|---------|-------------|
| `-o` / `--output` | `docs/generated/nbx-command-capture.md` | Markdown snapshot path |
| `--raw-dir` | `docs/generated/raw/` | Per-command JSON artifact directory |
| `--markdown` | on | Append `--markdown` to compatible captures |
| `-j` / `--concurrency` | `4` | Parallel capture worker count |

## Output files

| File | Description |
|------|-------------|
| `docs/generated/raw/NNN-<slug>.json` | Full per-command capture artifact |
| `docs/generated/raw/index.json` | Summary metadata consumed by MkDocs |
| `docs/reference/cli/command-examples/index.md` | Generated CLI output landing page |
| `docs/reference/tui/launch-examples/index.md` | Generated TUI launch-output landing page |
| `docs/generated/nbx-command-capture.md` | Combined raw Markdown snapshot |

## Capture model

Each captured command is declared in `netbox_cli/docgen_specs.py` as a
`CaptureSpec` with:

- `surface`: `cli` or `tui`
- `section`: the generated page bucket inside that surface
- `title`: the heading shown in the generated docs
- `argv`: the command arguments passed after `nbx`
- `notes`: optional context shown above the output
- `safe`: whether command failures should abort the run or be captured as output

The capture engine writes raw JSON artifacts first. The MkDocs hook at
`docs/hooks.py` then rebuilds two separate generated trees before every docs
build:

- `docs/reference/cli/command-examples/`
- `docs/reference/tui/launch-examples/`

## Regeneration

```bash
uv run nbx demo init
uv run nbx docs generate-capture
uv run mkdocs build --strict
```
