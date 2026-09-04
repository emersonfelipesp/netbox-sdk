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
| NetBox typed SDK | Stable versioned generated clients for NetBox `4.7`, `4.6`, `4.5`, `4.4`, and `4.3`; NetBox 4.7 is generated from the official `v4.7.0` GA schema |
| NetBox live API | CI live-tests the SDK against NetBox `v4.7.0`, `v4.6.6`, `v4.6.3`, `v4.6.2`, and `v4.5.10` |
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
- `docs/snippets/package-version.txt`, `mkdocs.yml` `extra.package_version`,
  package metadata, and source/TestPyPI release examples match the candidate;
- default-index pins match `docs/snippets/published-package-version.txt`, which
  advances only after that PEP 440 final or post-release package is verified on
  PyPI; prerelease, development, and local versions remain TestPyPI-only;
- the exact release commit is already present on canonical Gitea `main`, Gitea
  retains the immutable annotated release tag object, and any divergent
  published lineage entered through the required two-parent merge;
- every action in credentialed publishing workflows uses a full commit SHA and
  the build/publisher toolchain is locked in `uv.lock`;
- an RC is triggered only by an exact direct `v*rc*` tag push, while final and
  post-release PyPI publication requires a published GitHub Release;
- exactly one correctly identified wheel plus one sdist is captured before any
  network-installed smoke dependency runs, and smoke testing uses a downstream
  artifact copy;
- TestPyPI wheel smoke installation is bound to the locally verified SHA-256,
  canonical authorization plus the exact TestPyPI artifact set are rechecked,
  and only verified-missing PyPI files enter a fresh approved-only directory
  whose manifest is revalidated in the Twine step, allowing safe partial-upload
  retries without `--skip-existing`; a bounded final check requires PyPI to
  expose exactly the expected filenames and hashes;
- metadata generation runs without credentials on every canonical `main` push;
  the serialized mirror confirms the latest canonical tip, creates the
  GitHub-side metadata follow-up, retries a changed push lease at most three
  times, and exposes its canonical-fetch and GitHub-push credentials only to
  separate steps; the dedicated read-only provenance workflow validates the
  result;
- registry jobs install only the audited, locked `publish` dependency group;
- package build and `twine check` pass;
- strict docs build passes;
- all PR GitHub Actions checks are green;
- the PyPI project has the expected owner/maintainer configuration for any
  requested co-maintainer or break-glass publishing process.
