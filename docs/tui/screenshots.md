# TUI Screenshots

`netbox-sdk` ships with six Textual applications, each aimed at a different
workflow. This gallery collects the themed screenshots for each one.

## Available TUI Applications

| TUI | Description | Launch Command |
|-----|-------------|-----------------|
| [Default TUI](screenshots-default.md) | Main browsing interface for NetBox resources | `nbx tui` / `nbx demo tui` |
| [Dev TUI](screenshots-dev.md) | Developer request workbench for API exploration | `nbx dev tui` / `nbx demo dev tui` |
| [GraphQL TUI](screenshots-graphql.md) | Interactive GraphQL explorer, query editor, and response viewer | `nbx graphql tui` / `nbx demo graphql tui` |
| [Logs Viewer](screenshots-logs.md) | Structured log viewer for debugging and diagnostics | `nbx tui logs` |
| [CLI Builder](screenshots-cli.md) | Guided command composition for `nbx` | `nbx cli tui` / `nbx demo cli tui` |
| [Django Models Browser](screenshots-django.md) | Browser for NetBox's internal Django models | `nbx dev django-model tui` |

## Available Themes

All TUI applications support 5 built-in themes:

- **NetBox Dark** — Dark theme matching NetBox's default appearance
- **NetBox Light** — Light theme for daytime use
- **Dracula** — Popular dark theme with purple accents
- **Tokyo Night** — Serene dark theme with blue undertones
- **One Dark Pro** — Atom's One Dark theme port

## Capturing New Screenshots

To capture fresh screenshots of all TUIs with all themes, run:

```bash
python scripts/tui_screenshots.py
```

This script uses the demo profile for the shared NetBox connection, while the
GraphQL TUI screenshots use deterministic mocked introspection and query
responses so the gallery stays stable across runs and themes. Ensure you have
the demo profile configured first:

```bash
nbx demo init
```

Screenshots are saved to `docs/assets/screenshots/`. Each screenshot follows the naming pattern `tui-{app}-{theme}.svg`.

For the non-visual launch/help output of these applications, see
[TUI Launch Output](../reference/tui/launch-examples/index.md).
