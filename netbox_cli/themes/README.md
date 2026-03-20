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

Unknown keys, invalid values, duplicate names, and alias conflicts are rejected.
