# AGENTS.md — netbox-cli Agent Index

> **Purpose:** Single entry point for AI coding agents. All project context lives in `CLAUDE.md` files and documentation across the repo. This file indexes them — it does not duplicate their content.

---

## Quick Start

| What you need | Go here |
|---|---|
| Architecture overview + data flow | [CLAUDE.md](CLAUDE.md) |
| How to set up the dev environment | [CLAUDE.md § Contributor Workflow](CLAUDE.md) |
| Prompting rules (mandatory) | [PROMPTING-GUIDE.md](PROMPTING-GUIDE.md) |
| Security hardening controls | [SECURITY-GUIDE.md](SECURITY-GUIDE.md) |
| Full CLI/TUI command reference | [docs/getting-started/quickstart.md](docs/getting-started/quickstart.md) |
| MkDocs site (local preview) | `uv run mkdocs serve` |

---

## CLAUDE.md Index

Every subdirectory with non-trivial logic has its own `CLAUDE.md`. **Read the relevant one before editing any file in that directory.**

### Root

| File | Covers |
|---|---|
| [CLAUDE.md](CLAUDE.md) | Project-wide guide: architecture diagram, data flow, contributor workflow, prompting contract, TUI design rules, theme system, NetBox connection policy |

### `netbox_cli/` — Core Package

| File | Covers |
|---|---|
| [netbox_cli/CLAUDE.md](netbox_cli/CLAUDE.md) | Module map for every file in the package: `api.py`, `config.py`, `schema.py`, `services.py`, `http_cache.py`, `theme_registry.py`, `output_safety.py`, `trace_ascii.py`, `docgen_capture.py`, `logging_runtime.py`, TCSS files |
| [netbox_cli/cli/CLAUDE.md](netbox_cli/cli/CLAUDE.md) | CLI subpackage: module map, dependency direction, import rules, command groups, dynamic command resolution |
| [netbox_cli/ui/CLAUDE.md](netbox_cli/ui/CLAUDE.md) | TUI subpackage: `app.py` layout/keybindings/async patterns, `formatting.py`, `navigation.py`, `panels.py`, `state.py`, `chrome.py`, `widgets.py`, `plugin_discovery.py`, `logs_app.py` |
| [netbox_cli/themes/CLAUDE.md](netbox_cli/themes/CLAUDE.md) | Theme JSON format spec, bundled themes table, validation rules, semantic variable reference (16 custom CSS variables) |
| [netbox_cli/reference/CLAUDE.md](netbox_cli/reference/CLAUDE.md) | Bundled NetBox OpenAPI schema files, update procedure, offline guarantee |

### Tests, Docs, CI

| File | Covers |
|---|---|
| [tests/CLAUDE.md](tests/CLAUDE.md) | Test file map, mocking patterns, live-test skip behavior, filesystem isolation, TCSS color enforcement |
| [docs/CLAUDE.md](docs/CLAUDE.md) | MkDocs site structure, `hooks.py` build hook, `generated/` pipeline, navigation tree, local preview commands |
| [.github/CLAUDE.md](.github/CLAUDE.md) | CI workflows: `lint.yml`, `test.yml` (matrix 3.11–3.13), `docs.yml` (docgen + gh-deploy), required secrets |

### `reference/` — Design & Framework Guides

| File | Covers |
|---|---|
| [reference/CLAUDE.md](reference/CLAUDE.md) | Index of design guides and Textual app references; priority rules for visual conflicts |
| [reference/textual/CLAUDE.md](reference/textual/CLAUDE.md) | Cross-project Textual pattern index (Dolphie, Memray, Posting, Toad, Toolong) with per-project pattern lookup tables |

---

## Documentation Files

### Getting Started

- [docs/getting-started/installation.md](docs/getting-started/installation.md) — Install methods (pip, uv, brew, etc.)
- [docs/getting-started/configuration.md](docs/getting-started/configuration.md) — Profile config, env vars, token versions
- [docs/getting-started/quickstart.md](docs/getting-started/quickstart.md) — First-run walkthrough

### CLI Reference

- [docs/cli/commands.md](docs/cli/commands.md) — Static command reference
- [docs/cli/dynamic-commands.md](docs/cli/dynamic-commands.md) — OpenAPI-driven dynamic command system
- [docs/cli/demo-profile.md](docs/cli/demo-profile.md) — Demo profile setup with demo.netbox.dev

### TUI Reference

- [docs/tui/themes.md](docs/tui/themes.md) — Theme system user docs
- [docs/tui/keybindings.md](docs/tui/keybindings.md) — Keyboard shortcut reference

### Developer Guide

- [docs/developer/architecture.md](docs/developer/architecture.md) — System architecture deep dive
- [docs/developer/textual-composition.md](docs/developer/textual-composition.md) — React-style Textual composition pattern
- [docs/developer/docgen.md](docs/developer/docgen.md) — Documentation generation pipeline

### Design References (read before UI changes)

- [reference/design/NETBOX-DARK-PATTERNS.md](reference/design/NETBOX-DARK-PATTERNS.md) — **Priority 1.** NetBox dark mode palette, layer hierarchy, component styles, status colors
- [reference/design/TOAD-DESIGN-GUIDE.md](reference/design/TOAD-DESIGN-GUIDE.md) — **Priority 2.** Textual idiomatic visual language (TCSS, spacing, borders, animations)

### Textual Framework References

- [reference/textual/TEXTUAL.md](reference/textual/TEXTUAL.md) — Official Textual docs extract
- [reference/textual/TOAD.md](reference/textual/TOAD.md) — Toad: AI agent TUI (PTY, streaming, command palette)
- [reference/textual/DOLPHIE.md](reference/textual/DOLPHIE.md) — Dolphie: MySQL monitoring TUI (workers, tabs, live DataTable)
- [reference/textual/MEMRAY.md](reference/textual/MEMRAY.md) — Memray: memory profiler TUI (custom widgets, reactive DataTable)
- [reference/textual/POSTING.md](reference/textual/POSTING.md) — Posting: HTTP client TUI (jump mode, file watcher, YAML config)
- [reference/textual/TOOLONG.md](reference/textual/TOOLONG.md) — Toolong: log viewer TUI (deferred tabs, file tail, multi-file merge)
- [reference/textual/NMS-CLI.md](reference/textual/NMS-CLI.md) — nms-cli: prior art for this project

### Project Meta

- [README.md](README.md) — Public-facing project overview
- [PROMPTING-GUIDE.md](PROMPTING-GUIDE.md) — Metaprompting workflow (mandatory for all tasks)
- [SECURITY-GUIDE.md](SECURITY-GUIDE.md) — URL validation, secret storage, cache privacy, terminal output sanitization
- [netbox_cli/docgen_guidelines.md](netbox_cli/docgen_guidelines.md) — Docgen output conventions
- [netbox_cli/themes/README.md](netbox_cli/themes/README.md) — Theme contributor guide

### Auto-Generated (do not edit)

- [docs/generated/nbx-command-capture.md](docs/generated/nbx-command-capture.md) — Captured CLI output
- [docs/reference/command-examples/](docs/reference/command-examples/) — Build-time generated command example pages

---

## Architecture Snapshot

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
```

---

## Rules for Agents

1. **Read the CLAUDE.md** in the directory you are editing before making changes.
2. **Read both design references** before any UI/styling change: `NETBOX-DARK-PATTERNS.md` (wins on conflict) then `TOAD-DESIGN-GUIDE.md`.
3. **Follow the prompting workflow** from `PROMPTING-GUIDE.md` for every non-trivial task.
4. **Never hardcode colors** in TCSS — use semantic theme variables only.
5. **Never use pynetbox** or any NetBox SDK — use `aiohttp` directly against the API.
6. **Run `uv run pre-commit run --all-files`** and `uv run pytest` before considering any change complete.
7. **Keep CLI and TUI interchangeable** — every feature must work in both modes.
