"""Capture spec definitions for ``nbx`` documentation generation.

The capture pipeline documents two executable surfaces:

- ``cli``: command output for the ``netbox_cli`` package
- ``tui``: launch/help/theme entry points for the ``netbox_tui`` package

The Python SDK itself does not expose a direct command surface, so ``sdk``
documentation stays in handwritten API guides rather than captured CLI output.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CaptureSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    surface: str
    section: str
    title: str
    argv: list[str]
    notes: str = ""
    # safe=True → fail fast on bugs
    # safe=False → connection/auth failures are acceptable documentation output
    safe: bool = True


def _spec(
    surface: str,
    section: str,
    title: str,
    argv: list[str],
    *,
    notes: str = "",
    safe: bool = True,
) -> CaptureSpec:
    return CaptureSpec(
        surface=surface,
        section=section,
        title=title,
        argv=argv,
        notes=notes,
        safe=safe,
    )


def all_specs() -> list[CaptureSpec]:
    """Return the ordered list of capture specs.

    Docgen must only run against demo NetBox instances. Any capture that talks
    to a live API therefore uses the ``demo`` profile explicitly in the
    displayed command text.
    """
    return [
        # CLI: core
        _spec("cli", "Core Commands", "nbx --help", ["--help"]),
        _spec("cli", "Core Commands", "nbx init --help", ["init", "--help"]),
        _spec("cli", "Core Commands", "nbx config --help", ["config", "--help"]),
        _spec("cli", "Core Commands", "nbx logs --help", ["logs", "--help"]),
        _spec("cli", "Core Commands", "nbx docs --help", ["docs", "--help"]),
        _spec(
            "cli",
            "Core Commands",
            "nbx docs generate-capture --help",
            ["docs", "generate-capture", "--help"],
        ),
        # CLI: schema discovery
        _spec("cli", "Schema Discovery", "nbx groups --help", ["groups", "--help"]),
        _spec("cli", "Schema Discovery", "nbx resources --help", ["resources", "--help"]),
        _spec("cli", "Schema Discovery", "nbx ops --help", ["ops", "--help"]),
        _spec("cli", "Schema Discovery", "nbx groups", ["groups"]),
        _spec("cli", "Schema Discovery", "nbx resources dcim", ["resources", "dcim"]),
        _spec("cli", "Schema Discovery", "nbx ops dcim devices", ["ops", "dcim", "devices"]),
        # CLI: GraphQL and HTTP
        _spec("cli", "GraphQL and HTTP", "nbx graphql --help", ["graphql", "--help"]),
        _spec("cli", "GraphQL and HTTP", "nbx call --help", ["call", "--help"]),
        # CLI: dynamic commands
        _spec(
            "cli",
            "Dynamic Commands",
            "nbx dcim --help",
            ["dcim", "--help"],
            notes="Auto-generated Typer sub-app for the 'dcim' OpenAPI group.",
        ),
        _spec(
            "cli",
            "Dynamic Commands",
            "nbx dcim devices list --help",
            ["dcim", "devices", "list", "--help"],
        ),
        _spec(
            "cli",
            "Dynamic Commands",
            "nbx dcim interfaces get --help",
            ["dcim", "interfaces", "get", "--help"],
            notes="Shows ``--trace`` and ``--trace-only`` flags on ``get`` actions.",
        ),
        _spec(
            "cli",
            "Dynamic Commands",
            'nbx demo dcim devices create --dry-run --body-json {"name":"test"}',
            ["demo", "dcim", "devices", "create", "--dry-run", "--body-json", '{"name":"test"}'],
            notes="Preview a write operation without executing it.",
        ),
        # CLI: developer tools
        _spec("cli", "Developer Tools", "nbx dev --help", ["dev", "--help"]),
        _spec("cli", "Developer Tools", "nbx dev http --help", ["dev", "http", "--help"]),
        _spec(
            "cli",
            "Developer Tools",
            "nbx dev http paths --help",
            ["dev", "http", "paths", "--help"],
        ),
        _spec(
            "cli",
            "Developer Tools",
            "nbx dev http ops --help",
            ["dev", "http", "ops", "--help"],
        ),
        _spec(
            "cli",
            "Developer Tools",
            "nbx dev http paths",
            ["dev", "http", "paths"],
            notes="Lists all API paths from the bundled OpenAPI schema. No network call.",
        ),
        _spec(
            "cli",
            "Developer Tools",
            "nbx dev http ops --path /api/dcim/devices/",
            ["dev", "http", "ops", "--path", "/api/dcim/devices/"],
            notes="Lists HTTP operations available on the given path. No network call.",
        ),
        _spec(
            "cli",
            "Developer Tools",
            "nbx dev django-model --help",
            ["dev", "django-model", "--help"],
        ),
        _spec(
            "cli",
            "Developer Tools",
            "nbx dev django-model build --help",
            ["dev", "django-model", "build", "--help"],
        ),
        _spec(
            "cli",
            "Developer Tools",
            "nbx dev django-model fetch --help",
            ["dev", "django-model", "fetch", "--help"],
        ),
        # CLI: demo profile
        _spec("cli", "Demo Profile", "nbx demo --help", ["demo", "--help"]),
        _spec("cli", "Demo Profile", "nbx demo init --help", ["demo", "init", "--help"]),
        _spec("cli", "Demo Profile", "nbx demo config --help", ["demo", "config", "--help"]),
        _spec("cli", "Demo Profile", "nbx demo dev --help", ["demo", "dev", "--help"]),
        _spec(
            "cli",
            "Demo Profile",
            "nbx demo cli --help",
            ["demo", "cli", "--help"],
        ),
        _spec(
            "cli",
            "Demo Profile",
            "nbx demo dev django-model --help",
            ["demo", "dev", "django-model", "--help"],
        ),
        _spec(
            "cli",
            "Demo Profile",
            "nbx demo config",
            ["demo", "config"],
            notes="Shows the saved demo profile configuration.",
        ),
        # TUI: main browser and logs viewer
        _spec(
            "tui",
            "Main Browser",
            "nbx tui --help",
            ["tui", "--help"],
            notes="Launches the full Textual TUI when invoked without flags.",
        ),
        _spec(
            "tui",
            "Main Browser",
            "nbx tui --theme",
            ["tui", "--theme"],
            notes="Lists available themes without launching the TUI.",
        ),
        _spec(
            "tui",
            "Main Browser",
            "nbx demo tui --help",
            ["demo", "tui", "--help"],
            notes="Launches the main TUI against the demo profile.",
        ),
        _spec(
            "tui",
            "Logs Viewer",
            "nbx tui logs --theme",
            ["tui", "logs", "--theme"],
            notes="Lists available themes for the logs viewer TUI.",
        ),
        # TUI: developer workbench
        _spec(
            "tui",
            "Developer Workbench",
            "nbx dev tui --help",
            ["dev", "tui", "--help"],
            notes="Launches the developer request workbench TUI.",
        ),
        _spec(
            "tui",
            "Developer Workbench",
            "nbx dev tui --theme",
            ["dev", "tui", "--theme"],
            notes="Lists available themes without launching the developer TUI.",
        ),
        _spec(
            "tui",
            "Developer Workbench",
            "nbx demo dev tui --help",
            ["demo", "dev", "tui", "--help"],
            notes="Launches the developer request workbench against the demo profile.",
        ),
        _spec(
            "tui",
            "Developer Workbench",
            "nbx demo dev tui --theme",
            ["demo", "dev", "tui", "--theme"],
            notes="Lists available themes for the demo-backed developer TUI.",
        ),
        # TUI: GraphQL explorer
        _spec(
            "tui",
            "GraphQL TUI",
            "nbx graphql --help",
            ["graphql", "--help"],
            notes="Documents GraphQL query execution and the dedicated GraphQL TUI launch mode.",
        ),
        _spec(
            "tui",
            "GraphQL TUI",
            "nbx graphql tui --help",
            ["graphql", "tui", "--help"],
            notes="Shows GraphQL TUI launch flags without starting the interface.",
        ),
        _spec(
            "tui",
            "GraphQL TUI",
            "nbx graphql tui --theme",
            ["graphql", "tui", "--theme"],
            notes="Lists available themes without launching the GraphQL TUI.",
        ),
        _spec(
            "tui",
            "GraphQL TUI",
            "nbx demo graphql --help",
            ["demo", "graphql", "--help"],
            notes="Documents the demo-backed GraphQL query and TUI entry point.",
        ),
        _spec(
            "tui",
            "GraphQL TUI",
            "nbx demo graphql tui --help",
            ["demo", "graphql", "tui", "--help"],
            notes="Shows the demo-backed GraphQL TUI launch flags.",
        ),
        _spec(
            "tui",
            "GraphQL TUI",
            "nbx demo graphql tui --theme",
            ["demo", "graphql", "tui", "--theme"],
            notes="Lists available themes for the demo-backed GraphQL TUI.",
        ),
        # TUI: CLI builder
        _spec("tui", "CLI Builder", "nbx cli tui --help", ["cli", "tui", "--help"]),
        _spec(
            "tui",
            "CLI Builder",
            "nbx demo cli tui --help",
            ["demo", "cli", "tui", "--help"],
        ),
        _spec(
            "tui",
            "CLI Builder",
            "nbx demo cli tui --theme",
            ["demo", "cli", "tui", "--theme"],
            notes="Lists available themes for the demo-backed CLI builder.",
        ),
        # TUI: Django model browser
        _spec(
            "tui",
            "Django Models Browser",
            "nbx dev django-model tui --help",
            ["dev", "django-model", "tui", "--help"],
        ),
        _spec(
            "tui",
            "Django Models Browser",
            "nbx demo dev django-model tui --help",
            ["demo", "dev", "django-model", "tui", "--help"],
        ),
    ]
