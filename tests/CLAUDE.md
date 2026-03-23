# tests — Test Suite

pytest + pytest-asyncio. All tests live here; there are no inline tests in the source package.

**Run all tests:**
```bash
pytest
```

**Async mode:** `asyncio_mode = "auto"` (set in `pyproject.toml`) — every `async def test_*` runs automatically under an event loop without needing `@pytest.mark.asyncio`.

---

## Test Files

| File | What it covers |
|---|---|
| `test_api_auth.py` | Authorization header generation, config completeness, URL validation, v2→v1 token fallback |
| `test_api_cache.py` | Cache TTL policies, stale-if-error, ETag/Last-Modified conditional requests |
| `test_cli_error_handling.py` | CLI error output formatting and exit code behavior |
| `test_cli_trace.py` | Cable trace ASCII rendering (Unicode boxes, endpoint labels, status, cable segments) |
| `test_cli_tui_theme.py` | TUI theme selection, live switching, persistence via `tui_state.json` |
| `test_config_profiles.py` | Profile save/load, legacy flat-config migration, file permissions (0o700/0o600) |
| `test_demo_auth.py` | Playwright demo.netbox.dev automation validation and token provisioning |
| `test_demo_cli.py` | Demo profile CLI commands; live API calls when `DEMO_USERNAME`/`DEMO_PASSWORD` are set |
| `test_demo_runtime_refresh.py` | Demo profile config cache invalidation and runtime refresh behavior |
| `test_dev_tui.py` | `NetBoxDevTuiApp` Pilot tests: request workbench layout, textarea/input theme tokens, support modal, theme switching |
| `test_docgen_paths.py` | `docgen_capture.py` output path resolution and stub config injection |
| `test_instance_isolation.py` | Per-process config and schema index isolation (no cross-test state leakage) |
| `test_logging_runtime.py` | Structured JSON log writing, file rotation, log entry format |
| `test_logo_render.py` | NetBox logo wordmark rendering against each built-in theme |
| `test_logs_tui.py` | `NetBoxLogsTuiApp` Pilot tests: log entry display, surface theming across all built-in themes |
| `test_no_hardcoded_colors.py` | Two checks: (1) zero hex literals in any runtime TCSS file; (2) all `$token` references in TCSS are in the explicit `_ALLOWED_THEME_TOKENS` allowlist |
| `test_output_safety.py` | ANSI stripping, control character replacement, safe Rich Text rendering |
| `test_plugin_discovery.py` | `discover_plugin_resource_paths()` — mock API walk, collection detection, deduplication |
| `test_schema_index.py` | Group/resource extraction, list/detail path identification, trace path support |
| `test_services.py` | Request resolution from (group, resource, action, id) tuples, key-value arg parsing |
| `test_theme_registry.py` | Theme JSON loading, `#RRGGBB` format enforcement, required variable keys, alias conflicts |
| `test_tui_interaction.py` | Main TUI Pilot integration tests: navigation, `ContextBreadcrumb`, filtering, detail panel, cable trace, `SupportModal`, theme tokens for `Input`/`OptionList`/`DataTable`/`Footer`/toast internals |

---

## Patterns

### Mocking the API client
Most tests that touch `NetBoxApiClient` inject a mock via `monkeypatch` or a fixture that replaces `aiohttp.ClientSession`. Never mock at the HTTP level inside `test_tui_interaction.py` — use the `NetBoxApiClient` mock boundary instead.

### Live tests (skip if secrets absent)
`test_demo_cli.py` and `test_demo_auth.py` check for `DEMO_USERNAME` / `DEMO_PASSWORD` environment variables and skip gracefully when absent. CI sets these from repository secrets.

### Filesystem isolation
Tests that write to `~/.config/netbox-cli/` use `tmp_path` (pytest fixture) and patch the config directory to a temporary location so they never pollute the developer's real config.

### TCSS color and token tests
`test_no_hardcoded_colors.py` enforces two rules across all four runtime TCSS files (`tui.tcss`, `ui_common.tcss`, `dev_tui.tcss`, `logs_tui.tcss`):

1. **No hex literals** — asserts zero `#RRGGBB` occurrences in any runtime TCSS file
2. **No unknown tokens** — scans every `$token` reference and asserts it appears in `_ALLOWED_THEME_TOKENS`; this prevents stray variable names like the old `$text-muted` from slipping back in
