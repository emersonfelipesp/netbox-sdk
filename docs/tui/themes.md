# Themes

The TUI ships with four built-in themes and supports unlimited custom themes defined as JSON files.

---

## Built-in themes

| Theme name | Label | Aliases |
|-----------|-------|---------|
| `default` | Default | - |
| `dracula` | Dracula | `dracula-dark` |
| `netbox-dark` | NetBox Dark | `netbox` |
| `netbox-light` | NetBox Light | `light` |

---

## Selecting a theme

=== "At launch"

    ```bash
    nbx tui --theme dracula
    nbx demo tui --theme netbox
    nbx tui --theme netbox-light
    ```

=== "At runtime"

    Use the **Theme** dropdown in the top-left corner of the TUI to switch themes live.

=== "List available themes"

    ```bash
    nbx tui --theme
    ```

---

## Theme compliance

Theme switching is not limited to top-level containers. Every Textual widget and widget subcomponent must follow the selected theme, including:

- overlays and dropdowns
- tab bars and active indicators
- tree cursor and highlight states
- option list hover and selected rows
- `TextArea` gutter, cursor line, selection, cursor, and placeholder styling

Theme audits must be recursive. For every themed widget, check the framework-owned internals that Textual mounts inside it, not just the parent selector. This includes:

- tab internals like `ContentTab` and `Underline`
- select internals like `SelectCurrent Static#label`, arrow glyphs, and `SelectOverlay`
- input internals like `.input--cursor`, `.input--selection`, `.input--placeholder`, and `.input--suggestion`
- list-style internals like `.option-list--option-*` and `ListItem` state classes
- tree internals like `.tree--label`, `.tree--guides*`, `.tree--cursor`, and hover/highlight states
- table internals like `.datatable--header`, `.datatable--cursor`, and hover states
- editor internals like `.text-area--gutter`, `.text-area--cursor-line`, `.text-area--selection`, and `.text-area--placeholder`
- footer internals like `.footer-key--key` and `.footer-key--description`
- notification internals like `ToastRack`, `ToastHolder`, `Toast`, and `.toast--title`

When a custom widget composes nested Textual widgets internally, propagate semantic theme intent down to those children and verify the final rendered child states after a runtime theme switch, including focus, hover, active, overlay, and ANSI paths.

Project rules:

- Never hardcode runtime colors in Python or TCSS outside `netbox_tui/themes/*.json`
- Never leave Textual default colors visible after a theme switch
- Avoid built-in widget palettes when they bypass the repo theme tokens; style component classes with semantic variables instead

### Debugging theme-specific mismatches

If one built-in theme renders correctly and another still shows stray color blocks, do not assume the remaining issue is always a widget selector bug. Compare the theme JSON palette itself against a known-good built-in theme before adding more TCSS overrides.

Use this workflow:

- compare `background`, `surface`, `panel`, `boost`, `nb-border`, and `nb-border-subtle` between the broken theme and a known-good theme
- verify the dark-surface hierarchy is progressive: `background < surface < panel < boost` in perceived lightness
- for dark themes, keep the surface stack low-saturation enough that panel layers read as neutral structure, not bright blue-violet blocks
- check Textual ANSI paths separately, because `Screen` / `ModalScreen` and nested framework widgets may still apply ANSI-mode defaults in a real terminal even when headless tests look fine

Practical lesson from the Dracula fix:

- the remaining blue support-modal and Dev-TUI pane backgrounds were not only widget-style leaks
- Dracula's own `surface` / `panel` / `boost` / border tokens were too blue compared with the calmer NetBox Dark surface stack
- the durable fix was two-part:
  - rebalance the Dracula surface hierarchy in `netbox_tui/themes/dracula.json`
  - explicitly account for Textual ANSI-mode screen / modal behavior and runtime-mounted inner widgets

When reviewing or creating a dark theme, treat the following as a built-in sanity check:

- surfaces should get progressively lighter from app background to nested panel emphasis
- adjacent surface tokens should not jump too far in saturation
- border tokens should separate regions without reading as neon outlines
- modal bodies and large content panes should look like neutral structure, not colored feature blocks

---

## Creating a custom theme

Place a JSON file in `netbox_tui/themes/`. It will be discovered automatically — no code changes required.

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

Additional surface guidance for dark themes:

- `background` should be the darkest neutral foundation
- `surface` should lift slightly from `background` without becoming obviously colored
- `panel` should sit above `surface` for nested containers and modal bodies
- `boost` should be the strongest neutral emphasis layer, not a substitute for accent color
- if a theme's surface stack reads as blue or purple slabs in large panes, reduce saturation in those structural tokens before patching widgets

See `reference/design/NETBOX-DARK-PATTERNS.md` in the repository for the full design reference.
