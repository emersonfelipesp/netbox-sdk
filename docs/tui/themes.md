# Themes

The TUI ships with two built-in themes and supports unlimited custom themes defined as JSON files.

---

## Built-in themes

| Theme name | Label | Aliases |
|-----------|-------|---------|
| `default` | NetBox Dark | `netbox`, `netbox-dark` |
| `dracula` | Dracula | `dracula-dark` |

---

## Selecting a theme

=== "At launch"

    ```bash
    nbx tui --theme dracula
    nbx demo tui --theme netbox
    ```

=== "At runtime"

    Use the **Theme** dropdown in the top-left corner of the TUI to switch themes live.

=== "List available themes"

    ```bash
    nbx tui --theme
    ```

---

## Creating a custom theme

Place a JSON file in `netbox_cli/themes/`. It will be discovered automatically — no code changes required.

### Required structure

```json
{
  "name": "my-theme",
  "label": "My Theme",
  "dark": true,
  "aliases": ["my", "mytheme"],
  "colors": {
    "primary":    "#BD93F9",
    "secondary":  "#6272A4",
    "warning":    "#FFB86C",
    "error":      "#FF5555",
    "success":    "#50FA7B",
    "accent":     "#FF79C6",
    "background": "#282A36",
    "surface":    "#343746",
    "panel":      "#21222C",
    "boost":      "#414558"
  },
  "variables": {
    "nb-success-text":    "#82D18E",
    "nb-success-bg":      "#1C3326",
    "nb-info-text":       "#79C0FF",
    "nb-info-bg":         "#172131",
    "nb-warning-text":    "#F2CC60",
    "nb-warning-bg":      "#332B00",
    "nb-danger-text":     "#FF7B7B",
    "nb-danger-bg":       "#3B1111",
    "nb-border":          "#414558",
    "nb-border-subtle":   "#343746",
    "nb-muted-text":      "#6272A4",
    "nb-link-text":       "#8BE9FD",
    "nb-id-text":         "#FFB86C",
    "nb-key-text":        "#F1FA8C",
    "nb-tag-text":        "#FF79C6",
    "nb-tag-bg":          "#3A1F3A"
  }
}
```

### Required fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique identifier used in CLI flags |
| `label` | string | Human-readable display name |
| `dark` | boolean | Whether this is a dark theme |
| `colors` | object | 10 Textual semantic color keys (all required) |

### Optional fields

| Field | Type | Description |
|-------|------|-------------|
| `aliases` | array of strings | Alternative names for this theme |
| `variables` | object | 16 NetBox-specific CSS variable overrides |

### Validation rules

Themes are strictly validated at load time:

- All 10 `colors` keys are required
- All 16 `variables` keys are required when the `variables` object is present
- All color values must be `#RRGGBB` hex strings
- No duplicate theme names or alias conflicts allowed
- Unknown top-level keys cause an error

A malformed theme raises `ThemeCatalogError` with a clear message indicating which key or value failed.

---

## Design guidelines

Themes should follow the NetBox dark mode visual hierarchy:

- Use `primary` for interactive elements and focus rings
- Use `surface` for card/panel backgrounds
- Use `panel` for nested containers
- Use `boost` for highlighted backgrounds
- Use `nb-border` for standard borders, `nb-border-subtle` for inner/secondary borders
- Status colors: `nb-success-*`, `nb-info-*`, `nb-warning-*`, `nb-danger-*`

See `reference/design/NETBOX-DARK-PATTERNS.md` in the repository for the full design reference.
