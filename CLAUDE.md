# netbox-cli aims to be a TUI mirror of NetBox UI.
- You must "mirror" UI, such as navigation, cards, etc.
- For it, you must understand NetBox code and Django (mainly focusing on template understanding)
- All actions a user can do on NetBox UI or API, must also be able to do on TUI.

## NetBox Conneciton
- The NetBox connection must be only API-based, without ever touching NetBox Models directly or other any other way to get info from it.
- You must not implement pynetbox lib on this project or any other NetBox lib/SDK, use `aiohttp` instead with full async supports.
- For API construction, you can always check NetBox OpenAPI schema at `./reference/openapi/netbox-openapi.json` or `./reference/openapi/netbox-openapi.yaml`

## How create the TUI:
- Use `Textual` project. Reference for it can be found at `./reference/textual`
- Although I want to focus on TUI, the `netbox-cli` project must also support bash/terminal direct commands, using normal arguments such as `nbx dcim devices get --id 1`
- Both TUI and CLI must be interchangeable, everything must work on both scenarios, let to user choice its preference.

## TUI Visual Design:
- **Always** consult both design references before making any visual or styling changes:
  - `./reference/design/NETBOX-DARK-PATTERNS.md` — **Higher priority.** NetBox dark mode color palette, layer hierarchy, component styles, and status colors to mirror in the TUI. When this conflicts with TOAD-DESIGN-GUIDE.md on the same visual aspect, NetBox wins.
  - `./reference/design/TOAD-DESIGN-GUIDE.md` — Toad is the most advanced idiomatic Textual app and defines the Textual visual language (TCSS patterns, spacing, borders, states, animations). Use where NETBOX-DARK-PATTERNS.md has no opinion.
- Key rules:
  - Use only semantic CSS variables (`$primary`, `$secondary`, `$error`, etc.) — never hardcode hex colors in TCSS.
  - Use opacity-based tinting for hierarchy: `$primary 10%` (chip bg), `$primary 50%` (border), `$primary 100%` (full).
  - Use `border-left: blank $color` to visually categorize content blocks (e.g. by NetBox app section).
  - Express widget state via CSS modifier classes (`.-active`, `.-error`, `.-loading`, `.-expanded`) — keep visual logic in TCSS.
  - Use `border: tall transparent` at rest so focus-ring borders don't cause layout shift.
  - Use `layout: stream` + `align: left bottom` for any feed, log, or event list view.
  - Spacing rhythm: block content margins follow `1 1 1 0` (top right bottom left).

## Theme System
- TUI themes are JSON files loaded dynamically from `./netbox_cli/themes/`.
- Built-in themes live as:
  - `./netbox_cli/themes/default.json`
  - `./netbox_cli/themes/dracula.json`
- Any additional `<theme>.json` placed in this folder must be auto-discovered and available without code changes.
- Theme files must be strictly validated on load:
  - Required top-level keys: `name`, `label`, `dark`, `colors`
  - Optional top-level keys: `variables`, `aliases`
  - `colors` must include all semantic keys used by Textual theme registration (`primary`, `secondary`, `warning`, `error`, `success`, `accent`, `background`, `surface`, `panel`, `boost`)
  - Color values must use `#RRGGBB`
  - Unknown keys and alias/name collisions must raise clear errors
- Theme switching must be live in TUI and persisted in TUI state.
