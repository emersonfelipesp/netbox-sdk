# NetBox SDK Integration Certification Readiness

`netbox-sdk` is prepared for certification review as a NetBox ecosystem
integration package / SDK. It is not a NetBox plugin.

## Package Identity

| Field | Value |
| --- | --- |
| Repository | <https://github.com/emersonfelipesp/netbox-sdk> |
| PyPI package | `netbox-sdk` |
| Import packages | `netbox_sdk`, `netbox_cli`, `netbox_tui` |
| Console scripts | `nbx`, `nbx-mock` |
| Maintainer | Emerson Felipe (`emersonfelipesp`) |
| License | Apache-2.0 |
| License file | `LICENSE.txt` |
| Package metadata | `pyproject.toml` declares `license = "Apache-2.0"` and `license-files = ["LICENSE.txt"]` |

## Scope

This package runs outside NetBox and communicates with NetBox through public API
surfaces. It does not:

- install a Django app into NetBox;
- require `PLUGINS` or `PLUGINS_CONFIG`;
- create NetBox database models, views, templates, or navigation items;
- have a NetBox plugin config name;
- need plugin catalog screenshots or an icon for in-app plugin UI.

The package does provide a standalone SDK, an optional CLI, optional Textual
TUIs, a mock NetBox API, typed clients, schema discovery, and live API
compatibility tests.

## Compatibility Evidence

| Surface | Compatibility evidence |
| --- | --- |
| Python | `requires-python = ">=3.11,<3.14"`; CI runs Python 3.11, 3.12, and 3.13 |
| NetBox typed SDK | Versioned generated clients for NetBox `4.6`, `4.5`, `4.4`, and `4.3` |
| NetBox live API | CI live-tests the SDK against NetBox `v4.6.3`, `v4.6.2`, and `v4.5.10` |
| Pagination | Runtime pagination selection covers NetBox 4.6 cursor pagination and older offset pagination |
| Plugins/custom objects | Runtime discovery supports public plugin/custom-object REST resources exposed under NetBox APIs |
| Branching | Optional `branching` extra marks support for NetBox Branching workflows without adding runtime dependencies |

## Quality Gates

GitHub Actions cover the package as an SDK/integration artifact:

- `Lint and Format`: type checks plus pre-commit lint/format gates.
- `Tests`: mock SDK/CLI/TUI suites on Python 3.11, 3.12, and 3.13.
- `Tests` main-branch live suite: NetBox API integration against supported
  NetBox release tags.
- `Security Tests`: scoped SDK, CLI, and TUI security tests.
- `Certification Evidence`: repository evidence checks, package build,
  `twine check`, and wheel install/import smoke tests.
- `Build and deploy documentation`: PR strict MkDocs build and main-branch
  GitHub Pages deployment.
- `Release validation and publish`: tag validation, build artifacts, TestPyPI
  validation, and PyPI publish through GitHub Actions.

## Documentation Evidence

The README and MkDocs site document:

- package purpose and install modes;
- typed NetBox API support;
- runtime dependencies and optional extras;
- support channels;
- architecture and public SDK surface;
- authentication, request handling, error handling, schema indexing, branching,
  mock API, CLI, and TUI workflows.

## Application Notes

For a certification application, use this package type:

- **Integration package / SDK**

Do not present it as a NetBox plugin. If an application form requires
plugin-specific fields, use:

- **Plugin config name:** Not applicable; SDK/integration package.
- **NetBox `PLUGINS` install instructions:** Not applicable; install with
  `pip install netbox-sdk` or optional extras.
- **Plugin UI screenshots:** Not applicable for NetBox plugin UI; the project
  includes CLI/TUI screenshots in the documentation for terminal surfaces.
- **External dependencies:** None required beyond a reachable NetBox API for
  real usage. Optional local extras are documented in `pyproject.toml`.

## Release Readiness

Before applying with a release, confirm:

- the GitHub release tag matches `pyproject.toml` and `netbox_sdk.__version__`;
- `docs/snippets/package-version.txt`, pinned install snippets, and
  `mkdocs.yml` `extra.package_version` match the release;
- package build and `twine check` pass;
- strict docs build passes;
- all PR GitHub Actions checks are green;
- the PyPI project has the expected owner/maintainer configuration for any
  requested co-maintainer or break-glass publishing process.
