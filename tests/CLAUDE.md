# tests — Test Suite

## Workspace Context

This file lives at `/root/personal-context/nmulticloud-context/netbox-sdk/tests/CLAUDE.md` inside the `personal-context` workspace.
Workspace guidance: `/root/personal-context/CLAUDE.md`.
Per-repo deep-dive: `/root/personal-context/claude-reference/netbox-sdk.md`.
Submodule layout and cross-repo links: `/root/personal-context/claude-reference/dependency-map.md`.

---

pytest + pytest-asyncio. All tests live here; there are no inline tests in the source packages.

**Canonical commands:**
```bash
uv run pytest                 # full suite
uv run pytest -m suite_sdk    # netbox_sdk-owned tests
uv run pytest -m suite_cli    # netbox_cli-owned tests
uv run pytest -m suite_tui    # netbox_tui-owned tests
```

**Async mode:** `asyncio_mode = "auto"` (set in `pyproject.toml`) — every `async def test_*` runs automatically under an event loop without needing `@pytest.mark.asyncio`.

## Suite Ownership

Each test module is marked with exactly one package ownership marker:

- `suite_sdk` — tests whose primary contract is the standalone `netbox_sdk` package
- `suite_cli` — tests whose primary contract is the optional `netbox_cli` package
- `suite_tui` — tests whose primary contract is the optional `netbox_tui` package

The default `pytest` invocation still means “test everything”. Marker runs are for package-scoped validation and CI routing.

---

## Test Files

| File | What it covers |
|---|---|
| `test_api_auth.py` | Authorization header generation, config completeness, URL validation, v2→v1 token fallback |
| `test_api_cache.py` | Cache TTL policies, stale-if-error, ETag/Last-Modified conditional requests |
| `test_branching_cli.py` | Branching CLI commands, aliases, scoped headers, and help output |
| `test_branching_client.py` | Branching API client, job polling, and scoped header helpers |
| `test_branching_live.py` | Live NetBox Branching smoke paths; skips when a live Branching plugin is unavailable |
| `test_branching_tui.py` | Branch switcher overlay and TUI branch-state behavior |
| `test_branching_typed.py` | Branch-aware typed SDK request behavior |
| `test_certification_readiness.py` | Integration package certification evidence, metadata, and documentation checks |
| `test_cli_decorators.py` | Reusable CLI decorator factories and Typer metadata behavior |
| `test_cli_error_handling.py` | CLI error output formatting and exit code behavior |
| `test_cli_new_options.py` | New CLI option wiring and command defaults |
| `test_cli_trace.py` | Cable trace ASCII rendering (Unicode boxes, endpoint labels, status, cable segments) |
| `test_cli_tui.py` | `NbxCliTuiApp` Pilot tests: command tree navigation, leaf action resolution, command construction |
| `test_cli_tui_theme.py` | TUI theme selection, live switching, persistence via `tui_state.json` |
| `test_client_header_scope.py` | Client-level scoped header isolation and cleanup |
| `test_client_session_pooling.py` | API client session reuse and lifecycle behavior |
| `test_config_profiles.py` | Profile save/load, legacy flat-config migration, file permissions (0o700/0o600) |
| `test_demo_auth.py` | Playwright demo.netbox.dev automation validation and token provisioning |
| `test_demo_cli.py` | Demo profile CLI commands; live API calls when `DEMO_USERNAME`/`DEMO_PASSWORD` are set |
| `test_http_ssl.py` | TLS failure detection, `connector_for_config`, `NETBOX_SSL_VERIFY`, `ssl_verify` save/load |
| `test_demo_runtime_refresh.py` | Demo profile config cache invalidation and runtime refresh behavior |
| `test_dev_tui.py` | `NetBoxDevTuiApp` Pilot tests: request workbench layout, textarea/input theme tokens, support modal, theme switching |
| `test_graphql_tui.py` | `NetBoxGraphqlTuiApp` Pilot tests: schema introspection fallback, guided query builders, execution, history restore, clipboard, theme switching |
| `test_django_model_tui.py` | `DjangoModelTuiApp` instantiation and basic layout verification |
| `test_docgen_paths.py` | `docgen_capture.py` output path resolution and stub config injection |
| `test_docgen_specs.py` | Documentation capture spec inventory and rendering contracts |
| `test_docs_alignment.py` | Package/docs version alignment and localized docs completeness |
| `test_graphql.py` | CLI GraphQL and raw HTTP command behavior |
| `test_instance_isolation.py` | Per-process config and schema index isolation (no cross-test state leakage) |
| `test_logging_runtime.py` | Structured JSON log writing, file rotation, log entry format |
| `test_login_modal.py` | Login modal state and theme behavior |
| `test_logo_render.py` | NetBox logo wordmark rendering against each built-in theme |
| `test_logs_tui.py` | `NetBoxLogsTuiApp` Pilot tests: log entry display, surface theming across all built-in themes |
| `test_markdown_output.py` | Markdown rendering helpers and `--output markdown` flag handling |
| `test_mock_api.py` | FastAPI mock NetBox API CRUD, pagination, filtering, and Branching routes |
| `test_no_hardcoded_colors.py` | Two checks: (1) zero hex literals in any runtime TCSS file; (2) all `$token` references in TCSS are in the explicit `_ALLOWED_THEME_TOKENS` allowlist |
| `test_output_safety.py` | ANSI stripping, control character replacement, safe Rich Text rendering |
| `test_pagination_cursor.py` | Cursor and paginated response handling |
| `test_plugin_discovery.py` | `discover_plugin_resource_paths()` — mock API walk, collection detection, deduplication |
| `test_proxbox_cli.py` | `nbx proxbox` catalog, CRUD dry-run, read-only command protection, and sync stream rendering |
| `test_proxbox_resources.py` | Dedicated netbox-proxbox SDK catalog, schema registration, and catalog-backed request helper |
| `test_proxbox_sync.py` | Proxbox sync scheduling, endpoint resolution, SSE parsing, and stream transport |
| `test_proxbox_tui.py` | Proxbox-only request workbench catalog and resource activation behavior |
| `test_return_annotations.py` | Repo-wide non-test return annotation regression guard |
| `test_schema_index.py` | Group/resource extraction, list/detail path identification, trace path support |
| `test_schema_version_detection.py` | Schema version detection and release-line selection |
| `test_sdk_completeness.py` | Generated SDK/model completeness against bundled schemas |
| `test_sdk_decorators.py` | SDK decorator factories and reusable metadata behavior |
| `test_sdk_imports.py` | Top-level SDK exports and standalone import/constructor behavior |
| `test_sdk_pynetbox_parity.py` | Async facade parity behaviors such as detail endpoints, branch scoping, and record helpers |
| `test_security_cli.py` | CLI security behavior and secret-safe output |
| `test_security_sdk.py` | SDK security behavior, token handling, and unsafe input guards |
| `test_security_tui.py` | TUI security behavior and secret-safe rendering |
| `test_demo_live.py` | **Live** integration tests against demo.netbox.dev — connection, list, filter discovery, single-object CRUD, bulk operations, auto-pagination, and CLI-level commands. Guarded by `pytest.mark.demo_live`; requires `NETBOX_DEMO_LIVE=1`, `DEMO_USERNAME`, and `DEMO_PASSWORD`. Token provisioned via `POST /api/users/tokens/provision/` (REST) with Playwright fallback for first-time account registration. |
| `test_dynamic_bulk.py` | CLI bulk operations (`bulk-update`, `bulk-patch`, `bulk-delete`), `--all` auto-pagination, `--max-records`, and `filters` action — covers `_supported_actions`, `_parse_dynamic_options`, and `_handle_dynamic_invocation` |
| `test_services.py` | Request resolution from (group, resource, action, id) tuples, key-value arg parsing, bulk op routing to list path, and `list_all_pages` multi-page aggregation |
| `test_ssl_verify_cli.py` | TLS verification prompts and `nbx test` probe retry (`_prompt_ssl_verify_if_unset`, `_retry_probe_after_ssl_prompt`) |
| `test_theme_registry.py` | Theme JSON loading, `#RRGGBB` format enforcement, required variable keys, alias conflicts |
| `test_typed_sdk.py` | Versioned typed SDK bundles, request/response validation, and version selection |
| `test_typed_generation.py` | OpenAPI typed-binding generation, query-model identity, and multipart selection |
| `test_live_netbox.py` | Read-only core API/runtime OpenAPI checks plus a `NETBOX_LIVE_TEST=1`-gated disposable NetBox 4.6.6 any-tag fixture roundtrip against ephemeral CI instances |
| `test_tui_interaction.py` | Main TUI Pilot integration tests: navigation, `ContextBreadcrumb`, filtering, detail panel, cable trace, `SupportModal`, theme tokens for `Input`/`OptionList`/`DataTable`/`Footer`/toast internals |
| `test_tui_screenshots.py` | Screenshot harness registration and deterministic GraphQL screenshot setup for docs generation |
| `test_tui_simulation.py` | TUI launch simulation helpers used by docs/tests |

---

## CI Behavior

- Branch and pull request CI routes to the affected package suites based on changed files.
- Shared files such as `pyproject.toml`, `uv.lock`, `tests/conftest.py`, and test workflow definitions trigger the full suite instead of package-selective runs.
- Direct pushes to `main` always run the full `uv run pytest` matrix.
- SDK-affecting branch/PR changes and every direct push to `main` run live NetBox SDK integration tests against `v4.6.6`, `v4.6.3`, `v4.6.2`, and `v4.5.10`.
- Security CI path-routes `test_security_sdk.py`, `test_security_cli.py`, and `test_security_tui.py`.
- Release validation always runs the full `uv run pytest` matrix before publish.

When you add a new test module, assign it to one owning package and add the matching `pytestmark = pytest.mark.suite_*` at module scope.

---

## Patterns

### Mocking the API client
Most tests that touch `NetBoxApiClient` inject a mock via `monkeypatch` or a fixture that replaces `aiohttp.ClientSession`. Never mock at the HTTP level inside `test_tui_interaction.py` — use the `NetBoxApiClient` mock boundary instead.

### Live tests (skip if secrets absent)
`test_demo_cli.py` and `test_demo_auth.py` check for `DEMO_USERNAME` / `DEMO_PASSWORD` environment variables and skip gracefully when absent. CI sets these from repository secrets.

`test_demo_live.py` uses `pytest.mark.demo_live` and requires **both** `NETBOX_DEMO_LIVE=1` **and** `DEMO_USERNAME` / `DEMO_PASSWORD`. To run:

```bash
NETBOX_DEMO_LIVE=1 DEMO_USERNAME=myuser DEMO_PASSWORD=mypass \
  uv run pytest tests/test_demo_live.py -v --override-ini="addopts="
```

Token provisioning uses `POST /api/users/tokens/provision/` (returns a v2 Bearer token) with a Playwright fallback for first-time account registration. The live tests exercise: connection probe, paginated list, filter discovery, single-object CRUD, bulk-patch/update/delete, auto-pagination, and CLI list/filter commands.

### Typed SDK dependency expectation
The committed generated typed models use Pydantic network/email field types. If
`email-validator` is unavailable in the active environment, typed SDK tests
should skip only the affected import/execution paths with a clear reason rather
than failing unrelated suites.

### Filesystem isolation
Tests that write to `~/.config/netbox-sdk/` or read the legacy `~/.config/netbox-cli/` migration path use `tmp_path` (pytest fixture) and patch the config directory to a temporary location so they never pollute the developer's real config.

### TCSS color and token tests
`test_no_hardcoded_colors.py` enforces two rules across all six runtime TCSS files (`tui.tcss`, `ui_common.tcss`, `dev_tui.tcss`, `graphql_tui.tcss`, `logs_tui.tcss`, `django_model_tui.tcss`):

1. **No hex literals** — asserts zero `#RRGGBB` occurrences in any runtime TCSS file
2. **No unknown tokens** — scans every `$token` reference and asserts it appears in `_ALLOWED_THEME_TOKENS`; this prevents stray variable names like the old `$text-muted` from slipping back in
