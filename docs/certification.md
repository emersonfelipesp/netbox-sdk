# Certification Readiness

`netbox-sdk` is prepared for review as a NetBox ecosystem integration package
or SDK. It is not a NetBox plugin.

## Why this is not a plugin application

`netbox-sdk` runs outside NetBox and connects to NetBox through public API
surfaces. It does not install a Django app into NetBox, does not use
`PLUGINS`, and does not provide NetBox-side models, templates, views, or
navigation. Plugin-specific fields such as plugin config name, plugin icon, and
NetBox plugin UI screenshots are therefore not applicable.

The certification evidence focuses on package quality, API compatibility,
tests, documentation, supportability, and maintainability.

## Evidence checklist

| Area | Evidence |
| --- | --- |
| License | Apache-2.0 in `LICENSE.txt` and package metadata |
| Package metadata | `pyproject.toml` declares project URLs, Python range, SPDX license, license files, entry points, optional extras, and package data |
| Python support | Python 3.11, 3.12, and 3.13 |
| NetBox compatibility | Stable typed SDK release lines for NetBox `4.7`, `4.6`, `4.5`, `4.4`, and `4.3`; the default 4.7 line uses the official `v4.7.0` GA schema |
| Live NetBox validation | CI runs live SDK tests against NetBox `v4.7.0`, `v4.6.6`, `v4.6.3`, `v4.6.2`, and `v4.5.10`; every bundled line including `4.7` also runs a schema-pinned bundled release-line job |
| Offline validation | Mock NetBox API, typed-client tests, schema tests, SDK/CLI/TUI suites, and security tests |
| Package validation | Build, `twine check`, and wheel install/import smoke tests in CI |
| Documentation | README plus MkDocs site covering install, auth, requests, typed SDK, schema, errors, branching, mock API, CLI, and TUI |
| Support | GitHub issues for bugs, feature requests, and documentation requests |

## Compatibility matrix

| `netbox-sdk` release | Python | Typed NetBox API lines | Live CI NetBox targets |
| --- | --- | --- | --- |
| `0.0.13` source candidate | `>=3.11,<3.14` | `4.7`, `4.6`, `4.5`, `4.4`, `4.3` | `v4.7.0`, `v4.6.6`, `v4.6.3`, `v4.6.2`, `v4.5.10`; one bundled-schema job per release line |

Patch releases normalize to their release line for the typed SDK. For example,
`4.6.2` uses the committed `4.6` typed client.

## Dependencies

Base SDK dependencies are declared in `pyproject.toml`:

- `aiohttp`
- `pydantic`
- `email-validator`
- `rich`
- `pyyaml`

Optional extras:

- `cli`: Typer command-line interface
- `tui`: Textual terminal applications
- `mock`: FastAPI/uvicorn mock NetBox API
- `demo`: Playwright demo setup automation
- `branching`: marker extra for NetBox Branching workflows
- `all`: all optional user-facing surfaces

## Certification application packet

Use the following application framing:

- **Package type:** Integration package / SDK
- **Repository:** <https://github.com/emersonfelipesp/netbox-sdk>
- **PyPI package:** `netbox-sdk`
- **Documentation:** <https://emersonfelipesp.github.io/netbox-sdk/>
- **Primary support channel:** GitHub issues
- **Plugin config name:** Not applicable
- **NetBox `PLUGINS` configuration:** Not applicable
- **NetBox plugin UI screenshots:** Not applicable; terminal screenshots are
  available in the TUI documentation

The top-level `CERTIFICATION.md` file contains the repository-level packet and
release checklist.
