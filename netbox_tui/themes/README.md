# Theme JSON Schema

`netbox-cli` discovers theme files from this directory at runtime.

Required keys:

- `name` (string, lowercase slug)
- `label` (string, user-facing)
- `dark` (boolean)
- `colors` (object)

Optional keys:

- `variables` (object)
- `aliases` (list of strings)

`colors` must include:

- `primary`
- `secondary`
- `warning`
- `error`
- `success`
- `accent`
- `background`
- `surface`
- `panel`
- `boost`

All color values in `colors` and `variables` must be `#RRGGBB`.

## Reference Themes

For inspiration and color palette ideas, see:

- [Dracula Theme](https://draculatheme.com/) - Official Dracula color scheme documentation
- [Tokyo Night](https://github.com/tokyo-night/tokyo-night-vscode-theme) - Official Tokyo Night theme for VS Code
- [OneDark Pro](https://github.com/Binaryify/OneDark-Pro) - Official OneDark Pro theme for VS Code

`variables` must include:

- `nb-success-text`
- `nb-info-text`
- `nb-warning-text`
- `nb-danger-text`
- `nb-secondary-text`
- `nb-success-bg`
- `nb-info-bg`
- `nb-warning-bg`
- `nb-danger-bg`
- `nb-secondary-bg`
- `nb-border`
- `nb-border-subtle`
- `nb-muted-text`
- `nb-link-text`
- `nb-id-text`
- `nb-key-text`

Unknown keys, invalid values, duplicate names, and alias conflicts are rejected.

## Palette Review Guidance

Passing schema validation is necessary but not sufficient for a good runtime theme.

When reviewing a dark theme, also verify the structural surface stack:

- `background` should be the darkest foundation
- `surface` should be slightly lifted from `background`
- `panel` should sit above `surface` for nested containers and modal bodies
- `boost` should be the strongest structural emphasis layer
- `nb-border` and `nb-border-subtle` should separate regions without looking like bright feature colors

If a theme renders large panes, endpoint lists, or modal bodies as obvious blue or purple slabs, the problem may be in the palette itself rather than the widget selectors.

Compare the candidate theme against a known-good built-in theme and check:

- progressive lightness: `background < surface < panel < boost`
- restrained saturation in structural tokens
- border colors that support hierarchy without dominating it

This was the key lesson from the Dracula fix: some remaining “blue background” bugs were ultimately caused by overly saturated surface tokens, not only missing Textual selectors.
