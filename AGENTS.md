# AGENTS.md — netbox-sdk Agent Index

## Quick Start

| What you need | Go here |
|---|---|
| Architecture overview | [CLAUDE.md](CLAUDE.md) |
| SDK package details | [netbox_sdk/CLAUDE.md](netbox_sdk/CLAUDE.md) |
| CLI package details | [netbox_cli/CLAUDE.md](netbox_cli/CLAUDE.md) |
| TUI package details | [netbox_tui/CLAUDE.md](netbox_tui/CLAUDE.md) |
| Docs build details | [docs/CLAUDE.md](docs/CLAUDE.md) |
| CI workflow details | [.github/CLAUDE.md](.github/CLAUDE.md) |

## CLAUDE.md Index

| File | Covers |
|---|---|
| [CLAUDE.md](CLAUDE.md) | Project-wide architecture, workflow, package boundaries |
| [netbox_sdk/CLAUDE.md](netbox_sdk/CLAUDE.md) | Standalone SDK package |
| [netbox_cli/CLAUDE.md](netbox_cli/CLAUDE.md) | Typer CLI package |
| [netbox_tui/CLAUDE.md](netbox_tui/CLAUDE.md) | Textual TUI package |
| [netbox_tui/themes/CLAUDE.md](netbox_tui/themes/CLAUDE.md) | Theme catalog and JSON schema |
| [netbox_sdk/reference/CLAUDE.md](netbox_sdk/reference/CLAUDE.md) | Bundled OpenAPI schema notes |
| [tests/CLAUDE.md](tests/CLAUDE.md) | Test suite structure and conventions |
| [docs/CLAUDE.md](docs/CLAUDE.md) | Docs structure and generation |
| [.github/CLAUDE.md](.github/CLAUDE.md) | CI workflows |
| [reference/CLAUDE.md](reference/CLAUDE.md) | Design/Textual references |

## Package Snapshot

```
netbox_sdk/   core install
netbox_cli/   optional cli extra
netbox_tui/   optional tui extra
```

Rules:
1. Read the local `CLAUDE.md` before editing in that area.
2. Preserve package boundaries: SDK independent, CLI lazy-loads TUI, TUI depends on SDK.
3. Use absolute imports only.
4. Run the owning package suite (`uv run pytest -m suite_sdk|suite_cli|suite_tui`) for package-local changes, and `uv run pytest` for shared/main/release validation paths.
