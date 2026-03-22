# netbox_cli/themes — JSON Theme Files

Each `.json` file here is auto-discovered by `theme_registry.load_theme_catalog()`. No code changes are needed to add a new theme — just drop a valid JSON file into this directory.

## Bundled Themes

| File | Name | Dark? | Default? | Description |
|---|---|---|---|---|
| `netbox-dark.json` | netbox-dark | yes | **yes** | NetBox UI dark mode palette — official project default. Aliases: `netbox`, `default` |
| `netbox-light.json` | netbox-light | no | no | NetBox UI light mode palette |
| `dracula.json` | dracula | yes | no | Dracula color scheme (`primary: #BD93F9`, `background: #282A36`) |

---

## Theme File Format

All themes must be valid JSON with this structure:

```json
{
  "name": "my-theme",
  "label": "My Theme",
  "dark": true,
  "colors": {
    "primary":    "#RRGGBB",
    "secondary":  "#RRGGBB",
    "warning":    "#RRGGBB",
    "error":      "#RRGGBB",
    "success":    "#RRGGBB",
    "accent":     "#RRGGBB",
    "background": "#RRGGBB",
    "surface":    "#RRGGBB",
    "panel":      "#RRGGBB",
    "boost":      "#RRGGBB"
  },
  "variables": {
    "nb-success-text":  "#RRGGBB",
    "nb-info-text":     "#RRGGBB",
    "nb-warning-text":  "#RRGGBB",
    "nb-danger-text":   "#RRGGBB",
    "nb-secondary-text":"#RRGGBB",
    "nb-success-bg":    "#RRGGBB",
    "nb-info-bg":       "#RRGGBB",
    "nb-warning-bg":    "#RRGGBB",
    "nb-danger-bg":     "#RRGGBB",
    "nb-secondary-bg":  "#RRGGBB",
    "nb-border":        "#RRGGBB",
    "nb-border-subtle": "#RRGGBB",
    "nb-muted-text":    "#RRGGBB",
    "nb-link-text":     "#RRGGBB",
    "nb-id-text":       "#RRGGBB",
    "nb-key-text":      "#RRGGBB"
  },
  "aliases": ["my-theme-alias"]
}
```

**Rules enforced by `theme_registry.py`:**
- All 10 `colors` keys are required
- All 16 `variables` keys are required
- Every color value must match `#[0-9A-Fa-f]{6}` exactly (no shorthand, no alpha)
- `aliases` is optional; alias names must not collide with any other theme's `name`
- Unknown top-level keys are rejected with a clear error

## Semantic Variable Reference

These 16 `variables` map directly to TCSS custom variables used throughout `tui.tcss` and `ui/formatting.py`.

| Variable | Usage |
|---|---|
| `nb-success-text` | Active/operational status text |
| `nb-info-text` | Info badge / notice text |
| `nb-warning-text` | Warning status text |
| `nb-danger-text` | Failed / error status text |
| `nb-secondary-text` | Secondary/planned status text |
| `nb-success-bg` | Success status badge background |
| `nb-info-bg` | Info badge background |
| `nb-warning-bg` | Warning badge background |
| `nb-danger-bg` | Danger badge background |
| `nb-secondary-bg` | Secondary badge background |
| `nb-border` | Primary borders |
| `nb-border-subtle` | Subtle / secondary borders |
| `nb-muted-text` | Null values, placeholders, de-emphasized text |
| `nb-link-text` | URL values, clickable links |
| `nb-id-text` | Numeric ID values |
| `nb-key-text` | Slug/key values |
