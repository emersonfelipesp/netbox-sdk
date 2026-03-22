# docs — MkDocs Documentation Site

Built with MkDocs Material theme. Source lives here; deployed to GitHub Pages by `.github/workflows/docs.yml`.

**Local preview:**
```bash
uv sync --group docs
uv run mkdocs serve
```

**Contributor hooks:**
```bash
uv sync --dev --group docs
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
uv run pre-commit run --all-files
```

**Deploy (CI only):**
```bash
mkdocs gh-deploy --force --clean --verbose
```

---

## Directory Structure

```
docs/
├── index.md                        # Home page
├── hooks.py                        # MkDocs hook (build-time docgen integration)
├── assets/
│   ├── logo.svg                    # Site logo + favicon
│   └── extra.css                   # Custom CSS overrides
├── getting-started/
│   ├── index.md
│   ├── installation.md
│   ├── configuration.md
│   └── quickstart.md
├── cli/
│   ├── index.md
│   ├── commands.md                 # Static command reference
│   ├── dynamic-commands.md         # How dynamic commands work
│   └── demo-profile.md             # Demo profile setup
├── tui/
│   ├── index.md
│   ├── themes.md                   # Theme system documentation
│   └── keybindings.md              # Keyboard shortcut reference
├── developer/
│   ├── index.md
│   ├── architecture.md             # System architecture overview
│   └── docgen.md                   # Documentation generation process
├── reference/
│   └── command-examples.md         # (may be generated or hand-written)
└── generated/                      # ← AUTO-GENERATED, do not edit by hand
    ├── nbx-command-capture.md      # CLI output captured by docgen_capture.py
    └── raw/                        # JSON output from each captured command
        └── *.json
```

---

## hooks.py

MkDocs build hook loaded via `mkdocs.yml`:
```yaml
hooks:
  - docs/hooks.py
```

Called during the MkDocs build phase. Responsible for any pre-build transformations (e.g., injecting generated content into the nav, post-processing Markdown). See the file directly for current behavior — it evolves alongside the docgen pipeline.

---

## generated/

**Never edit files in `docs/generated/` by hand.** They are overwritten by:

```bash
nbx docs generate-capture
```

This command runs `netbox_cli/docgen_capture.py`, which:
1. Stubs the in-memory config so `nbx` commands don't prompt for setup
2. Invokes each command via Typer's `CliRunner`
3. Writes captured output as `nbx-command-capture.md`
4. Writes raw JSON per-command to `raw/*.json`

In CI (`docs.yml`), docgen runs against `demo.netbox.dev` using `DEMO_USERNAME` / `DEMO_PASSWORD` secrets. If secrets are absent, the step is skipped and existing generated files are used.

---

## Navigation (from mkdocs.yml)

```
Home
Getting Started → Installation, Configuration, Quick Start
CLI Reference   → Commands, Dynamic Commands, Demo Profile
TUI             → Themes, Keyboard Shortcuts
Command Examples
Developer Guide → Architecture, Documentation Generation
```

To add a new page: create the `.md` file and add an entry to the `nav:` section in `mkdocs.yml`.
