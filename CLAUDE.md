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

## Core Rules

The canonical collaboration rules (including **No Co-Author** and **No Self-Promotion**) are defined once in the [Core Principles](#core-principles) section; refer there for the full policy text.

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

## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for any non-trivial task (3+ steps, architectural decisions, or cross-cutting changes)
- If something goes sideways mid-task, STOP and re-plan before continuing
- Write specs upfront for UI changes — describe the target state before touching TCSS or widget code

### 2. Subagent Strategy
- Offload codebase exploration, Textual internals research, and parallel analysis to subagents
- Keep the main context clean: one subagent per investigation thread
- For complex TUI layout or theme problems, throw more compute at it rather than guessing

### 3. Self-Improvement Loop
- After any correction: record the pattern in `tasks/lessons.md`
- Write a rule that prevents the same mistake, not just a note about what went wrong
- Review lessons at the start of each session before touching TUI or theme code

### 4. Verification Before Done
- Never mark a task complete without visually or programmatically confirming the output
- For TUI changes: confirm all theme switch paths, focus states, and nested widget internals
- For CLI changes: run the command and confirm output matches expected behavior
- Run `uv run pre-commit run --all-files` and `uv run pytest` before calling anything done

### 5. Demand Elegance (Balanced)
- For non-trivial changes: ask "is there a more elegant way?" before committing to an approach
- If a fix feels hacky, step back: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes — don't over-engineer one-liners
- Prefer small composable Textual widgets over large monolithic ones

### 6. Autonomous Bug Fixing
- When given a bug report: diagnose and fix it — don't ask for hand-holding
- Use logs at `~/.config/netbox-cli/logs/netbox-cli.log` as first-line evidence
- Fix failing CI tests without being told how; check `.github/` workflows for context

---

## Task Management

1. **Plan First:** Write a plan to `tasks/todo.md` with checkable items before starting
2. **Verify Plan:** Align with the user before beginning implementation on non-trivial tasks
3. **Track Progress:** Mark items complete as you go — never batch completions at the end
4. **Explain Changes:** Give a high-level summary at each step, not a line-by-line recap
5. **Document Results:** Add a review section to `tasks/todo.md` when done
6. **Capture Lessons:** Update `tasks/lessons.md` after any user correction

---

## Core Principles

- **Simplicity First:** Make every change as simple as possible. Impact minimal code.
- **No Laziness:** Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact:** Only touch what's necessary. No side effects, no incidental refactors.
- **API-Only NetBox:** Never bypass the REST API. No pynetbox, no direct model access — `aiohttp` only.
- **No Co-Author:** Never add `Co-Authored-By: Claude` or any Claude/Anthropic co-authorship trailer to git commits.
- **No Self-Promotion:** Never add "Generated with Claude Code" or any Claude/Anthropic attribution to PR descriptions, commit messages, or any user-facing content.

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

## Release Process

Follow these steps whenever a new release (e.g. `vX.Y.Z`) is needed:

### Pre-flight checks
1. Confirm all CI workflows are green on `main` before tagging:
   ```bash
   gh run list --branch main --limit 5
   ```
2. Ensure you are on the latest `main`:
   ```bash
   git checkout main && git pull origin main
   ```

### Version bump
3. Update `version = "X.Y.Z"` in `pyproject.toml`.
4. Commit the bump:
   ```bash
   git add pyproject.toml
   git commit -m "release: bump version to vX.Y.Z"
   ```

### Tag and push
5. Create an annotated tag:
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   ```
6. Push commit and tag together:
   ```bash
   git push origin main --tags
   ```

### GitHub Release
7. Generate a changelog since the previous tag:
   ```bash
   git log vPREV..vX.Y.Z --oneline --no-merges
   ```
8. Create the GitHub release with a detailed description:
   ```bash
   gh release create vX.Y.Z \
     --title "vX.Y.Z" \
     --notes "$(cat <<'EOF'
   ## What's New in vX.Y.Z

   ### <Category>
   - <change>

   EOF
   )"
   ```

### Release notes guidelines
- Group commits into categories: **Features**, **Bug Fixes**, **Documentation**, **CI/Build**.
- For each feature, write one sentence describing user-visible impact, not the internal implementation.
- Reference any new CLI flags, commands, or packages introduced.
- Check CI is green on the release tag after pushing (GitHub Actions re-runs on tag push).

---

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
