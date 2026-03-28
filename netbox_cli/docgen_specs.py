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
        _spec("cli", "Schema Discovery", "nbx resources ipam", ["resources", "ipam"]),
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
            "nbx dcim devices --help",
            ["dcim", "devices", "--help"],
            notes="Auto-generated Typer sub-app for dcim/devices.",
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
            "nbx ipam prefixes --help",
            ["ipam", "prefixes", "--help"],
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
            "nbx circuits circuit-terminations get --help",
            ["circuits", "circuit-terminations", "get", "--help"],
        ),
        _spec(
            "cli",
            "Dynamic Commands",
            "nbx demo dcim devices list --select results.0.name",
            ["demo", "dcim", "devices", "list", "--select", "results.0.name"],
            notes="Extract a specific field from the demo response using dot notation.",
            safe=False,
        ),
        _spec(
            "cli",
            "Dynamic Commands",
            "nbx demo dcim devices list --columns id,name,status",
            ["demo", "dcim", "devices", "list", "--columns", "id,name,status"],
            notes="Display only selected columns in table output.",
            safe=False,
        ),
        _spec(
            "cli",
            "Dynamic Commands",
            "nbx demo dcim devices list --max-columns 3",
            ["demo", "dcim", "devices", "list", "--max-columns", "3"],
            notes="Limit visible table columns for a demo-backed response.",
            safe=False,
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
            "nbx dev http get --help",
            ["dev", "http", "get", "--help"],
        ),
        _spec(
            "cli",
            "Developer Tools",
            "nbx dev http post --help",
            ["dev", "http", "post", "--help"],
        ),
        _spec(
            "cli",
            "Developer Tools",
            "nbx dev http put --help",
            ["dev", "http", "put", "--help"],
        ),
        _spec(
            "cli",
            "Developer Tools",
            "nbx dev http patch --help",
            ["dev", "http", "patch", "--help"],
        ),
        _spec(
            "cli",
            "Developer Tools",
            "nbx dev http delete --help",
            ["dev", "http", "delete", "--help"],
        ),
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
            "nbx demo dev http get --path /api/status/",
            ["demo", "dev", "http", "get", "--path", "/api/status/"],
            notes="Explicit demo-backed HTTP request via the developer tooling surface.",
            safe=False,
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
        _spec("cli", "Demo Profile", "nbx demo test --help", ["demo", "test", "--help"]),
        _spec("cli", "Demo Profile", "nbx demo reset --help", ["demo", "reset", "--help"]),
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
        # CLI: live demo-backed output
        _spec(
            "cli",
            "Live API",
            "nbx demo dcim devices list",
            ["demo", "dcim", "devices", "list"],
            notes="Runs against demo.netbox.dev using the configured demo profile.",
            safe=False,
        ),
        _spec(
            "cli",
            "Live API",
            "nbx demo ipam prefixes list",
            ["demo", "ipam", "prefixes", "list"],
            notes="Requires a valid demo profile token.",
            safe=False,
        ),
        _spec(
            "cli",
            "Live API",
            "nbx demo dcim sites list",
            ["demo", "dcim", "sites", "list"],
            safe=False,
        ),
        # CLI: cable trace
        _spec(
            "cli",
            "Cable Trace",
            "nbx demo dcim interfaces get --id 1 --trace",
            ["demo", "dcim", "interfaces", "get", "--id", "1", "--trace"],
            notes="Fetches the object and appends an ASCII cable trace diagram.",
            safe=False,
        ),
        _spec(
            "cli",
            "Cable Trace",
            "nbx demo dcim interfaces get --id 1 --trace-only",
            ["demo", "dcim", "interfaces", "get", "--id", "1", "--trace-only"],
            notes="Renders only the cable trace, omitting the object detail table.",
            safe=False,
        ),
        _spec(
            "cli",
            "Cable Trace",
            "nbx demo circuits circuit-terminations get --id 15 --trace",
            ["demo", "circuits", "circuit-terminations", "get", "--id", "15", "--trace"],
            notes="Circuit terminations also expose a ``/trace/`` endpoint.",
            safe=False,
        ),
        _spec(
            "cli",
            "Cable Trace",
            "nbx demo circuits circuit-terminations get --id 15 --trace-only",
            ["demo", "circuits", "circuit-terminations", "get", "--id", "15", "--trace-only"],
            notes="Trace-only view for a circuit termination.",
            safe=False,
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
            "Main Browser",
            "nbx demo tui --theme",
            ["demo", "tui", "--theme"],
            notes="Lists available themes for the demo-backed main TUI.",
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
        # TUI: CLI builder
        _spec("tui", "CLI Builder", "nbx cli --help", ["cli", "--help"]),
        _spec("tui", "CLI Builder", "nbx cli tui --help", ["cli", "tui", "--help"]),
        _spec(
            "tui",
            "CLI Builder",
            "nbx demo cli --help",
            ["demo", "cli", "--help"],
        ),
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
