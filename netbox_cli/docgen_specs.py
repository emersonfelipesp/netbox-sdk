"""Capture spec definitions for ``nbx`` CLI documentation generation.

``CaptureSpec`` is the data model for a single command capture entry.
``all_specs()`` returns the ordered list of specs used by ``docgen_capture``.

Keeping the spec list here (rather than inside ``docgen_capture.py``) lets the
file be browsed and edited without scrolling past the capture-runner
infrastructure.  To add a new command to the generated docs, add a
``CaptureSpec`` entry to ``all_specs()`` in the appropriate section.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CaptureSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    section: str
    title: str
    argv: list[str]
    notes: str = ""
    # safe=True → catch_exceptions=False (local/schema commands, fail fast on bugs)
    # safe=False → catch_exceptions=True (live API calls, connection errors are valid docs)
    safe: bool = True


def all_specs(*, use_demo: bool = True) -> list[CaptureSpec]:
    """Return the ordered list of capture specs.

    Args:
        use_demo: When True (default) live-API specs invoke commands through
            ``nbx demo …`` so they hit demo.netbox.dev with the configured demo
            profile.  When False they hit the default profile (real NetBox).
    """
    # ── Shared: help banners and schema-discovery (no network, no profile) ────
    specs: list[CaptureSpec] = [
        # Top-level help banners
        CaptureSpec(section="Top-level", title="nbx --help", argv=["--help"]),
        CaptureSpec(section="Top-level", title="nbx init --help", argv=["init", "--help"]),
        CaptureSpec(section="Top-level", title="nbx config --help", argv=["config", "--help"]),
        CaptureSpec(section="Top-level", title="nbx groups --help", argv=["groups", "--help"]),
        CaptureSpec(
            section="Top-level", title="nbx resources --help", argv=["resources", "--help"]
        ),
        CaptureSpec(section="Top-level", title="nbx ops --help", argv=["ops", "--help"]),
        CaptureSpec(section="Top-level", title="nbx graphql --help", argv=["graphql", "--help"]),
        CaptureSpec(section="Top-level", title="nbx call --help", argv=["call", "--help"]),
        CaptureSpec(
            section="Top-level",
            title="nbx tui --help",
            argv=["tui", "--help"],
            notes="Launches the full Textual TUI when invoked without flags. --help shown here only.",
        ),
        CaptureSpec(
            section="Top-level",
            title="nbx tui --theme",
            argv=["tui", "--theme"],
            notes="Lists available themes without launching the TUI.",
        ),
        CaptureSpec(section="Top-level", title="nbx docs --help", argv=["docs", "--help"]),
        CaptureSpec(
            section="Top-level",
            title="nbx docs generate-capture --help",
            argv=["docs", "generate-capture", "--help"],
        ),
        # Logs viewer
        CaptureSpec(
            section="Logs Viewer",
            title="nbx logs --help",
            argv=["logs", "--help"],
            notes="Launches a Textual log viewer TUI. --help shown here only.",
        ),
        # Developer tools help banners
        CaptureSpec(
            section="Developer Tools",
            title="nbx dev --help",
            argv=["dev", "--help"],
        ),
        CaptureSpec(
            section="Developer Tools",
            title="nbx dev tui --help",
            argv=["dev", "tui", "--help"],
            notes="Launches the developer request workbench TUI. --help shown here only.",
        ),
        CaptureSpec(
            section="Developer Tools",
            title="nbx dev tui --theme",
            argv=["dev", "tui", "--theme"],
            notes="Lists available themes without launching the TUI.",
        ),
        CaptureSpec(
            section="Developer Tools",
            title="nbx dev http --help",
            argv=["dev", "http", "--help"],
        ),
        CaptureSpec(
            section="Developer Tools",
            title="nbx dev http get --help",
            argv=["dev", "http", "get", "--help"],
        ),
        CaptureSpec(
            section="Developer Tools",
            title="nbx dev http post --help",
            argv=["dev", "http", "post", "--help"],
        ),
        CaptureSpec(
            section="Developer Tools",
            title="nbx dev http put --help",
            argv=["dev", "http", "put", "--help"],
        ),
        CaptureSpec(
            section="Developer Tools",
            title="nbx dev http patch --help",
            argv=["dev", "http", "patch", "--help"],
        ),
        CaptureSpec(
            section="Developer Tools",
            title="nbx dev http delete --help",
            argv=["dev", "http", "delete", "--help"],
        ),
        CaptureSpec(
            section="Developer Tools",
            title="nbx dev http paths --help",
            argv=["dev", "http", "paths", "--help"],
        ),
        CaptureSpec(
            section="Developer Tools",
            title="nbx dev http ops --help",
            argv=["dev", "http", "ops", "--help"],
        ),
        CaptureSpec(
            section="Developer Tools",
            title="nbx dev http paths",
            argv=["dev", "http", "paths"],
            notes="Lists all API paths from the bundled OpenAPI schema. No network call.",
        ),
        CaptureSpec(
            section="Developer Tools",
            title="nbx dev http ops --path /api/dcim/devices/",
            argv=["dev", "http", "ops", "--path", "/api/dcim/devices/"],
            notes="Lists all HTTP operations available on the given path. No network call.",
        ),
        # Demo sub-app help
        CaptureSpec(section="Demo profile", title="nbx demo --help", argv=["demo", "--help"]),
        CaptureSpec(
            section="Demo profile", title="nbx demo init --help", argv=["demo", "init", "--help"]
        ),
        CaptureSpec(
            section="Demo profile",
            title="nbx demo config --help",
            argv=["demo", "config", "--help"],
        ),
        CaptureSpec(
            section="Demo profile",
            title="nbx demo test --help",
            argv=["demo", "test", "--help"],
        ),
        CaptureSpec(
            section="Demo profile",
            title="nbx demo reset --help",
            argv=["demo", "reset", "--help"],
        ),
        CaptureSpec(
            section="Demo profile",
            title="nbx demo tui --help",
            argv=["demo", "tui", "--help"],
            notes="Launches the TUI against the demo profile. --help shown here only.",
        ),
        CaptureSpec(
            section="Demo profile",
            title="nbx demo tui --theme",
            argv=["demo", "tui", "--theme"],
            notes="Lists available themes without launching the TUI.",
        ),
        CaptureSpec(
            section="Demo profile",
            title="nbx demo dev --help",
            argv=["demo", "dev", "--help"],
        ),
        CaptureSpec(
            section="Demo profile",
            title="nbx demo dev tui --help",
            argv=["demo", "dev", "tui", "--help"],
            notes="Launches the developer request workbench TUI against the demo profile.",
        ),
        CaptureSpec(
            section="Demo profile",
            title="nbx demo dev tui --theme",
            argv=["demo", "dev", "tui", "--theme"],
            notes="Lists available themes without launching the TUI.",
        ),
        # Schema discovery (reads reference/openapi/netbox-openapi.json — no network)
        CaptureSpec(
            section="Schema Discovery",
            title="nbx groups",
            argv=["groups"],
            notes="Lists all OpenAPI app groups from the local schema file. No network call.",
        ),
        CaptureSpec(
            section="Schema Discovery",
            title="nbx resources dcim",
            argv=["resources", "dcim"],
            notes="Lists all resources under the 'dcim' app group.",
        ),
        CaptureSpec(
            section="Schema Discovery",
            title="nbx ops dcim devices",
            argv=["ops", "dcim", "devices"],
            notes="Lists HTTP operations (method, path, operationId) for dcim/devices.",
        ),
        CaptureSpec(
            section="Schema Discovery",
            title="nbx resources ipam",
            argv=["resources", "ipam"],
        ),
        # Dynamic sub-commands: --help is safe (no network)
        CaptureSpec(
            section="Dynamic Commands",
            title="nbx dcim --help",
            argv=["dcim", "--help"],
            notes="Auto-generated Typer sub-app for the 'dcim' OpenAPI group.",
        ),
        CaptureSpec(
            section="Dynamic Commands",
            title="nbx dcim devices --help",
            argv=["dcim", "devices", "--help"],
            notes="Auto-generated Typer sub-app for dcim/devices.",
        ),
        CaptureSpec(
            section="Dynamic Commands",
            title="nbx dcim devices list --help",
            argv=["dcim", "devices", "list", "--help"],
        ),
        CaptureSpec(
            section="Dynamic Commands",
            title="nbx ipam prefixes --help",
            argv=["ipam", "prefixes", "--help"],
        ),
        # Trace flag help (safe — schema/help, no network)
        CaptureSpec(
            section="Dynamic Commands",
            title="nbx dcim interfaces get --help",
            argv=["dcim", "interfaces", "get", "--help"],
            notes="Shows ``--trace`` and ``--trace-only`` flags available on ``get`` actions.",
        ),
        CaptureSpec(
            section="Dynamic Commands",
            title="nbx circuits circuit-terminations get --help",
            argv=["circuits", "circuit-terminations", "get", "--help"],
        ),
        # New option flags: --select, --columns, --max-columns, --dry-run
        CaptureSpec(
            section="Dynamic Commands",
            title="nbx dcim devices list --select results.0.name",
            argv=["dcim", "devices", "list", "--select", "results.0.name"],
            notes="Extract specific field from response using dot notation.",
        ),
        CaptureSpec(
            section="Dynamic Commands",
            title="nbx dcim devices list --columns id,name,status",
            argv=["dcim", "devices", "list", "--columns", "id,name,status"],
            notes="Display only specific columns in table output.",
        ),
        CaptureSpec(
            section="Dynamic Commands",
            title="nbx dcim devices list --max-columns 3",
            argv=["dcim", "devices", "list", "--max-columns", "3"],
            notes="Limit table to first 3 columns.",
        ),
        CaptureSpec(
            section="Dynamic Commands",
            title="nbx dcim devices create --dry-run",
            argv=["dcim", "devices", "create", "--dry-run", "--body-json", '{"name":"test"}'],
            notes="Preview write operation without executing.",
        ),
        # GraphQL API
        CaptureSpec(
            section="GraphQL API",
            title="nbx graphql --help",
            argv=["graphql", "--help"],
            notes="Execute GraphQL queries against NetBox API.",
        ),
    ]

    # ── Live API specs: differ between demo and default profile ───────────────
    if use_demo:
        specs += [
            CaptureSpec(
                section="Live API — demo.netbox.dev",
                title="nbx demo dcim devices list",
                argv=["demo", "dcim", "devices", "list"],
                notes=(
                    "Runs against demo.netbox.dev using the configured demo profile. "
                    "Returns real data when the demo token is valid; 401/403 otherwise."
                ),
                safe=False,
            ),
            CaptureSpec(
                section="Live API — demo.netbox.dev",
                title="nbx demo ipam prefixes list",
                argv=["demo", "ipam", "prefixes", "list"],
                notes="Requires a valid demo profile token.",
                safe=False,
            ),
            CaptureSpec(
                section="Live API — demo.netbox.dev",
                title="nbx demo dcim sites list",
                argv=["demo", "dcim", "sites", "list"],
                safe=False,
            ),
            # GraphQL live tests
            CaptureSpec(
                section="GraphQL API — demo.netbox.dev",
                title="nbx demo graphql query",
                argv=["demo", "graphql", "{ sites { name } }"],
                notes="Execute GraphQL query against demo.netbox.dev.",
                safe=False,
            ),
            # ── Cable trace: dcim/interfaces ──────────────────────────────────
            CaptureSpec(
                section="Cable Trace — demo.netbox.dev",
                title="nbx demo dcim interfaces get --id 1 --trace",
                argv=["demo", "dcim", "interfaces", "get", "--id", "1", "--trace"],
                notes=(
                    "Fetches the interface object and appends an ASCII cable trace diagram. "
                    "Requires the interface to have a connected cable in demo.netbox.dev."
                ),
                safe=False,
            ),
            CaptureSpec(
                section="Cable Trace — demo.netbox.dev",
                title="nbx demo dcim interfaces get --id 1 --trace-only",
                argv=["demo", "dcim", "interfaces", "get", "--id", "1", "--trace-only"],
                notes="Renders only the cable trace, omitting the object detail table.",
                safe=False,
            ),
            # ── Cable trace: circuits/circuit-terminations ────────────────────
            CaptureSpec(
                section="Cable Trace — demo.netbox.dev",
                title="nbx demo circuits circuit-terminations get --id 15 --trace",
                argv=["demo", "circuits", "circuit-terminations", "get", "--id", "15", "--trace"],
                notes=(
                    "Circuit terminations also expose a ``/trace/`` endpoint. "
                    "Renders the full path from the physical interface through the circuit."
                ),
                safe=False,
            ),
            CaptureSpec(
                section="Cable Trace — demo.netbox.dev",
                title="nbx demo circuits circuit-terminations get --id 15 --trace-only",
                argv=[
                    "demo",
                    "circuits",
                    "circuit-terminations",
                    "get",
                    "--id",
                    "15",
                    "--trace-only",
                ],
                notes="Trace-only view for a circuit termination — no object detail table.",
                safe=False,
            ),
        ]
    else:
        specs += [
            CaptureSpec(
                section="Live API — default profile",
                title="nbx call GET /api/status/",
                argv=["call", "GET", "/api/status/"],
                notes=(
                    "Requires a reachable NetBox at NETBOX_URL. "
                    "Connection errors are expected in offline runs and are still valid documentation."
                ),
                safe=False,
            ),
            CaptureSpec(
                section="Live API — default profile",
                title="nbx call GET /api/dcim/sites/ --json",
                argv=["call", "GET", "/api/dcim/sites/", "--json"],
                notes="Returns paginated list as raw JSON. Requires a configured default profile.",
                safe=False,
            ),
            CaptureSpec(
                section="Live API — default profile",
                title="nbx dcim devices list",
                argv=["dcim", "devices", "list"],
                notes="Dynamic sub-command against the default profile NetBox instance.",
                safe=False,
            ),
        ]

    return specs
