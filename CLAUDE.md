# netbox-cli — Project Guide

## Codebase Index

| Path | CLAUDE.md | What's there |
|---|---|---|
| `netbox_cli/` | [→](netbox_cli/CLAUDE.md) | Core package: API client, CLI, config, schema, services, docgen, utilities |
| `netbox_cli/ui/` | [→](netbox_cli/ui/CLAUDE.md) | Textual TUI app, panels, navigation, formatting, state persistence |
| `netbox_cli/themes/` | [→](netbox_cli/themes/CLAUDE.md) | JSON theme files (auto-discovered, strictly validated) |
| `netbox_cli/reference/` | [→](netbox_cli/reference/CLAUDE.md) | Bundled NetBox OpenAPI schema (runtime source of truth) |
| `tests/` | [→](tests/CLAUDE.md) | pytest + pytest-asyncio test suite |
| `docs/` | [→](docs/CLAUDE.md) | MkDocs documentation source + generated capture outputs |
| `.github/` | [→](.github/CLAUDE.md) | GitHub Actions workflows (CI tests, docs build + deploy) |
| `reference/` | [→](reference/CLAUDE.md) | Design guides (NETBOX-DARK-PATTERNS, TOAD), Textual app references |
| `PROMPTING-GUIDE.md` | n/a | Project metaprompting workflow: how prompts must be internally reframed before execution |
| `SECURITY-GUIDE.md` | n/a | Security hardening guide: URL validation, secret storage, cache privacy, terminal output sanitization, security tests |

---

## Architecture in One Page

```
CLI (cli/ / Typer)                    TUI (ui/app.py / Textual)
    │                                        │
    ├── SchemaIndex (schema.py)  ────────────┤
    ├── services.py                          ├── ui/navigation.py
    ├── NetBoxApiClient (api.py) ────────────┤
    │     └── HttpCacheStore (http_cache.py) ├── ui/formatting.py
    │                                        ├── ui/panels.py
    └── output_safety.py                     └── ui/state.py
                                                   (tui_state.json)
Shared:
  config.py          → ~/.config/netbox-cli/config.json
  theme_registry.py  → netbox_cli/themes/*.json
  logging_runtime.py → ~/.config/netbox-cli/logs/netbox-cli.log
  trace_ascii.py, demo_auth.py, docgen_capture.py

Security Reference:
  SECURITY-GUIDE.md → implemented hardening controls + verification commands
```

**Data flow:**
1. User runs `nbx <cmd>` or `nbx tui`
2. `config.py` loads profile (env vars → disk → interactive setup)
3. `schema.py` indexes bundled OpenAPI JSON once
4. `services.py` maps (group, resource, action) → (method, path)
5. `api.py` checks cache, makes `aiohttp` request, handles token fallback
6. Output: CLI prints via Rich; TUI renders in DataTable + ObjectAttributesPanel

---

## Contributor Workflow

Use `uv` as the default local environment manager and `pre-commit` as the default gate before commits and pushes.

Initial setup:

```bash
uv sync --dev
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
```

Day-to-day:

```bash
uv run pre-commit run --all-files
uv run pytest
```

Expect every commit and every push to pass the Ruff lint/format hooks. GitHub Actions enforces the same `.pre-commit-config.yaml` checks in CI.

---

## Prompting Workflow

`PROMPTING-GUIDE.md` is part of the project contract.

Every prompt in this project must be internally re-prompted using that guide before execution. This internal reframing does not need to be shown to the user unless it is useful, but it must shape the work.

Minimum internal prompting loop:

1. restate the real objective
2. list assumptions
3. define quality criteria
4. choose the response or implementation structure
5. execute
6. self-check against the criteria

Use the heavier metaprompting patterns from `./PROMPTING-GUIDE.md` for architecture, code generation, debugging, code review, design work, security-sensitive changes, and other high-impact tasks.

For trivial requests, use the compact version of the same workflow rather than skipping it entirely.

---

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
  - Every Textual widget and subcomponent must visually follow the active theme. This includes built-in parts such as `OptionList` rows, `Tree` cursor states, `TextArea` gutter/selection/cursor states, tabs, overlays, and notifications.
  - Always audit Textual internals recursively, not just the outer widget selector. When styling or reviewing any widget, also inspect and theme its framework-owned child parts, wrappers, component classes, and ANSI/focus variants.
  - Required examples of internal surfaces to check include: `ContentTab`, `Underline`, `SelectCurrent Static#label`, `SelectOverlay`, `.input--cursor`, `.input--selection`, `.input--placeholder`, `.option-list--option-*`, `.tree--*`, `.datatable--*`, `.text-area--*`, `.footer-key--*`, `ToastRack`, `ToastHolder`, `Toast`, and `.toast--title`.
  - If a widget mounts nested Textual primitives internally, pass semantic theme intent down to those inner widgets and verify the final rendered child states, not only the parent container.
  - Do not use built-in Textual widget palettes when they override repo theme tokens. If a widget offers a separate palette/theme API, only use it when its colors still resolve from the active app theme; otherwise style the component classes in TCSS.
  - Use a React-style composition pattern for Textual widgets. Prefer small reusable primitives and nested `compose()` trees over inheritance chains built only for layout reuse.
  - Use opacity-based tinting for hierarchy: `$primary 10%` (chip bg), `$primary 50%` (border), `$primary 100%` (full).
  - Use `border-left: blank $color` to visually categorize content blocks (e.g. by NetBox app section).
  - Express widget state via CSS modifier classes (`.-active`, `.-error`, `.-loading`, `.-expanded`) — keep visual logic in TCSS.
  - Use `border: tall transparent` at rest so focus-ring borders don't cause layout shift.
  - Use `layout: stream` + `align: left bottom` for any feed, log, or event list view.
  - Spacing rhythm: block content margins follow `1 1 1 0` (top right bottom left).

## Theme System
- TUI themes are JSON files loaded dynamically from `./netbox_cli/themes/`.
- Built-in themes live as:
  - `./netbox_cli/themes/netbox-dark.json`
  - `./netbox_cli/themes/dracula.json`
  - `./netbox_cli/themes/netbox-light.json`
- Any additional `<theme>.json` placed in this folder must be auto-discovered and available without code changes.
- Theme files must be strictly validated on load:
  - Required top-level keys: `name`, `label`, `dark`, `colors`
  - Optional top-level keys: `variables`, `aliases`
  - `colors` must include all semantic keys used by Textual theme registration (`primary`, `secondary`, `warning`, `error`, `success`, `accent`, `background`, `surface`, `panel`, `boost`)
  - Color values must use `#RRGGBB`
  - Unknown keys and alias/name collisions must raise clear errors
- Theme switching must be live in TUI and persisted in TUI state.
- Theme switching is a hard contract for every TUI surface: changing theme must update all Textual components, component classes, overlays, and editor chrome with no stray default or hardcoded colors left behind.
- Theme review is incomplete unless it checks nested Textual internals after runtime theme switch, including focus states, hover states, active selections, ANSI branches, overlays, and notifications.
