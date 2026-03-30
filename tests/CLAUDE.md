# tests — Test Suite

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
| `test_cli_error_handling.py` | CLI error output formatting and exit code behavior |
| `test_cli_trace.py` | Cable trace ASCII rendering (Unicode boxes, endpoint labels, status, cable segments) |
| `test_cli_tui.py` | `NbxCliTuiApp` Pilot tests: command tree navigation, leaf action resolution, command construction |
| `test_cli_tui_theme.py` | TUI theme selection, live switching, persistence via `tui_state.json` |
| `test_config_profiles.py` | Profile save/load, legacy flat-config migration, file permissions (0o700/0o600) |
| `test_demo_auth.py` | Playwright demo.netbox.dev automation validation and token provisioning |
| `test_demo_cli.py` | Demo profile CLI commands; live API calls when `DEMO_USERNAME`/`DEMO_PASSWORD` are set |
| `test_http_ssl.py` | TLS failure detection, `connector_for_config`, `NETBOX_SSL_VERIFY`, `ssl_verify` save/load |
| `test_demo_runtime_refresh.py` | Demo profile config cache invalidation and runtime refresh behavior |
| `test_dev_tui.py` | `NetBoxDevTuiApp` Pilot tests: request workbench layout, textarea/input theme tokens, support modal, theme switching |
| `test_graphql_tui.py` | `NetBoxGraphqlTuiApp` Pilot tests: schema introspection fallback, guided query builders, execution, history restore, clipboard, theme switching |
| `test_django_model_tui.py` | `DjangoModelTuiApp` instantiation and basic layout verification |
| `test_docgen_paths.py` | `docgen_capture.py` output path resolution and stub config injection |
| `test_instance_isolation.py` | Per-process config and schema index isolation (no cross-test state leakage) |
| `test_logging_runtime.py` | Structured JSON log writing, file rotation, log entry format |
| `test_logo_render.py` | NetBox logo wordmark rendering against each built-in theme |
| `test_logs_tui.py` | `NetBoxLogsTuiApp` Pilot tests: log entry display, surface theming across all built-in themes |
| `test_markdown_output.py` | Markdown rendering helpers and `--output markdown` flag handling |
| `test_no_hardcoded_colors.py` | Two checks: (1) zero hex literals in any runtime TCSS file; (2) all `$token` references in TCSS are in the explicit `_ALLOWED_THEME_TOKENS` allowlist |
| `test_output_safety.py` | ANSI stripping, control character replacement, safe Rich Text rendering |
| `test_plugin_discovery.py` | `discover_plugin_resource_paths()` — mock API walk, collection detection, deduplication |
| `test_return_annotations.py` | Repo-wide non-test return annotation regression guard |
| `test_schema_index.py` | Group/resource extraction, list/detail path identification, trace path support |
| `test_sdk_imports.py` | Top-level SDK exports and standalone import/constructor behavior |
| `test_sdk_pynetbox_parity.py` | Async facade parity behaviors such as detail endpoints, branch scoping, and record helpers |
| `test_services.py` | Request resolution from (group, resource, action, id) tuples, key-value arg parsing |
| `test_ssl_verify_cli.py` | TLS verification prompts and `nbx test` probe retry (`_prompt_ssl_verify_if_unset`, `_retry_probe_after_ssl_prompt`) |
| `test_theme_registry.py` | Theme JSON loading, `#RRGGBB` format enforcement, required variable keys, alias conflicts |
| `test_typed_sdk.py` | Versioned typed SDK bundles, request/response validation, and version selection |
| `test_tui_interaction.py` | Main TUI Pilot integration tests: navigation, `ContextBreadcrumb`, filtering, detail panel, cable trace, `SupportModal`, theme tokens for `Input`/`OptionList`/`DataTable`/`Footer`/toast internals |
| `test_tui_screenshots.py` | Screenshot harness registration and deterministic GraphQL screenshot setup for docs generation |

---

## CI Behavior

- Branch and pull request CI routes to the affected package suites based on changed files.
- Shared files such as `pyproject.toml`, `uv.lock`, `tests/conftest.py`, and test workflow definitions trigger the full suite instead of package-selective runs.
- Direct pushes to `main` always run the full `uv run pytest` matrix.
- Release validation always runs the full `uv run pytest` matrix before publish.

When you add a new test module, assign it to one owning package and add the matching `pytestmark = pytest.mark.suite_*` at module scope.

---

## Patterns

### Mocking the API client
Most tests that touch `NetBoxApiClient` inject a mock via `monkeypatch` or a fixture that replaces `aiohttp.ClientSession`. Never mock at the HTTP level inside `test_tui_interaction.py` — use the `NetBoxApiClient` mock boundary instead.

### Live tests (skip if secrets absent)
`test_demo_cli.py` and `test_demo_auth.py` check for `DEMO_USERNAME` / `DEMO_PASSWORD` environment variables and skip gracefully when absent. CI sets these from repository secrets.

### Typed SDK dependency expectation
The committed generated typed models use Pydantic network/email field types. If
`email-validator` is unavailable in the active environment, typed SDK tests
should skip only the affected import/execution paths with a clear reason rather
than failing unrelated suites.

### Filesystem isolation
Tests that write to `~/.config/netbox-cli/` use `tmp_path` (pytest fixture) and patch the config directory to a temporary location so they never pollute the developer's real config.

### TCSS color and token tests
`test_no_hardcoded_colors.py` enforces two rules across all six runtime TCSS files (`tui.tcss`, `ui_common.tcss`, `dev_tui.tcss`, `graphql_tui.tcss`, `logs_tui.tcss`, `django_model_tui.tcss`):

1. **No hex literals** — asserts zero `#RRGGBB` occurrences in any runtime TCSS file
2. **No unknown tokens** — scans every `$token` reference and asserts it appears in `_ALLOWED_THEME_TOKENS`; this prevents stray variable names like the old `$text-muted` from slipping back in
