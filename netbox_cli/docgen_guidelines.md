# Documentation Generation Guidelines

These rules govern how `nbx` CLI reference documentation is captured and published.

## Golden Rule: Demo Instance Only

- **All captured output MUST come from `demo.netbox.dev`** (demo profile).
- **Never** use a production NetBox instance to generate docs — it will leak customer data.
- There is no production-targeting capture mode.

## Command Display Convention

- Commands that talk to the API should be documented in their demo-safe form:
  - Document as `nbx demo dcim devices list`
  - Do not present production-profile command output as captured documentation
- Help banners (`--help`) and schema discovery commands are profile-agnostic and shown as-is.

## Output Format Tabs

Each command entry gets up to five tabs in the generated MkDocs pages:

| Tab | Content | When available |
|-----|---------|----------------|
| **Command** | The CLI invocation string | Always |
| **Output** | Human-readable Rich/text terminal output | Always |
| **JSON Output** | `--json` format variant | Live API calls and dynamic commands only |
| **YAML Output** | YAML derived from JSON response | Same as JSON |
| **Markdown Output** | `--markdown` format variant (plain Markdown tables) | Same as JSON |

Format variants are captured by re-running the command with `--json` and deriving YAML and Markdown from the parsed JSON. Help-only and schema-discovery commands do not get format tabs.

## Error Handling

- Commands that fail with configuration errors are **skipped** entirely:
  - `"NetBox endpoint configuration is required"` — interactive prompt triggered
  - `"NetBox host (example:"` — interactive prompt triggered
  - `"Aborted."` — CliRunner abort
- Connection errors (401, 403, timeout) from valid stub configs **are** included — they document real CLI behavior.

## Stub Configuration

When no real config exists on disk, `docgen_capture.py` injects a placeholder stub into `_RUNTIME_CONFIGS`:

- **Demo profile**: `https://demo.netbox.dev` with placeholder tokens
This ensures commands return HTTP errors instead of hanging at interactive prompts. The stub is cleared after each command invocation.

## Capturing New Commands

To add a command to the generated docs, add a `CaptureSpec` to `all_specs()` in `docgen_specs.py`:

```python
CaptureSpec(
    surface="cli",
    section="My Section",
    title="nbx my-command --help",
    argv=["my-command", "--help"],
    notes="Optional note shown in the docs.",
    safe=True,  # True for local/help, False for live API calls
)
```

Then regenerate:

```bash
nbx demo init
nbx docs generate-capture
```

## CI/CD

The `.github/workflows/docs.yml` workflow:

1. Initializes the demo profile via `nbx demo init` (requires `DEMO_USERNAME` / `DEMO_PASSWORD` secrets)
2. Runs `nbx docs generate-capture` (demo profile only)
3. Builds and deploys MkDocs to GitHub Pages

If demo secrets are absent, the capture step is skipped and existing generated files are used.
