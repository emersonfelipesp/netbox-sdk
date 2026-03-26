# TUI Screenshots

The NetBox CLI ships with 5 different TUI applications, each designed for a specific use case. Below you'll find screenshots of each TUI across all available themes.

## Available TUI Applications

| TUI | Description | Launch Command |
|-----|-------------|-----------------|
| [Default TUI](screenshots-default.md) | Main browsing interface for NetBox resources | `nbx tui` / `nbx demo tui` |
| [Dev TUI](screenshots-dev.md) | Developer request workbench for API exploration | `nbx dev tui` / `nbx demo dev tui` |
| [Logs TUI](screenshots-logs.md) | Log viewer for debugging and diagnostics | `nbx logs tui` |
| [CLI TUI](screenshots-cli.md) | Interactive CLI with command palette | `nbx cli tui` |
| [Django Models TUI](screenshots-django.md) | Browser for NetBox's internal Django models | `nbx django tui` |

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

This script uses the demo profile (`demo.netbox.dev`) to capture the screenshots automatically. Ensure you have the demo profile configured first:

```bash
nbx demo init
```

Screenshots are saved to `docs/assets/screenshots/`. Each screenshot follows the naming pattern `tui-{app}-{theme}.svg`.