# Security Guide

This document describes the concrete security mechanisms implemented in `netbox-cli`, the attack classes they address, and the tests that enforce them.

## Scope

`netbox-cli` has four primary security-sensitive areas:

1. NetBox endpoint and request URL handling
2. On-disk storage of API credentials and HTTP cache data
3. Rendering untrusted API data into terminal output
4. Regression coverage for the above

This guide documents the current implementation state in the codebase as of commit `aceaf48`.

## Implemented Controls

### 1. Base URL validation

Implemented in [config.py](./netbox_cli/config.py).

`normalize_base_url()` now rejects:

- Empty values
- Non-HTTP schemes such as `ftp://`
- URLs without a host
- Embedded credentials such as `https://user:pass@host`
- Query strings or fragments on the configured base URL

Accepted URLs are normalized to a clean `http` or `https` base URL without trailing slash noise.

Security purpose:

- Prevent accidental credential leakage inside config values
- Reduce ambiguous or dangerous base URL forms
- Keep request construction deterministic

### 2. Relative-path enforcement for outbound requests

Implemented in [api.py](./netbox_cli/api.py).

`NetBoxApiClient.build_url()` now normalizes request paths through `_normalize_request_path()` and rejects:

- Absolute URLs such as `https://evil.example/api/status/`
- Network-path references
- Paths that include query strings
- Paths that include fragments
- Empty request paths

Security purpose:

- Prevent host escape / SSRF-style misuse through `urljoin()`
- Ensure every outbound request remains scoped to the configured NetBox base URL

### 3. Private filesystem permissions for secrets and cache

Implemented in:

- [config.py](./netbox_cli/config.py)
- [http_cache.py](./netbox_cli/http_cache.py)

Config protections:

- Config directory permissions are forced to `0700` on POSIX
- Config file writes use `0600` on POSIX
- Writes use an explicit private-mode open path instead of relying on ambient umask

HTTP cache protections:

- Cache directory permissions are forced to `0700` on POSIX
- Cache entry files are forced to `0600` on POSIX

Security purpose:

- Prevent other local users from reading API tokens
- Prevent cached authenticated API data from being left world-readable

### 4. Terminal output sanitization

Implemented in:

- [output_safety.py](./netbox_cli/output_safety.py)
- [ui/formatting.py](./netbox_cli/ui/formatting.py)
- [cli.py](./netbox_cli/cli.py)

The sanitizer strips:

- ANSI ESC-based sequences (CSI, OSC, two-character forms)
- C1 control characters (U+0080–U+009F), including U+009B (C1 CSI) and U+009D (C1 OSC) — these are escape-sequence initiators that some terminals accept without a leading ESC byte
- Raw C0 control characters other than newline, carriage return, and tab

The sanitizer is applied before rendering:

- Plain CLI output
- Rich table cells
- TUI semantic cells
- Trace output
- Link-like object labels rendered in detail views

Security purpose:

- Prevent terminal escape injection from untrusted API payloads
- Prevent clickable/hyperlink terminal payload injection
- Keep logs and screenshots trustworthy

### 5. TUI regression fixes related to current framework behavior

Implemented in [ui/app.py](./netbox_cli/ui/app.py).

The TUI theme-select label cleanup now uses `Static.content` instead of the removed `renderable` attribute. The structured filter dropdown also excludes the generic `q` search parameter and orders actual filter fields consistently.

Security purpose:

- Indirect: keeps the TUI test suite green so the security controls remain verifiable in CI
- Prevents framework drift from masking future security regressions

## Tests

Security-specific automated coverage exists in:

- [tests/test_config_profiles.py](./tests/test_config_profiles.py)
- [tests/test_api_auth.py](./tests/test_api_auth.py)
- [tests/test_api_cache.py](./tests/test_api_cache.py)
- [tests/test_output_safety.py](./tests/test_output_safety.py)

These tests validate:

- Unsafe base URLs are rejected
- Absolute request URLs are rejected
- Request paths with query/fragment components are rejected
- Config files/directories use private POSIX permissions
- Cache files/directories use private POSIX permissions
- ANSI / OSC / control-character payloads are stripped before rendering

Broader TUI regression coverage also lives in:

- [tests/test_tui_interaction.py](./tests/test_tui_interaction.py)

## Operational Notes

### `--show-token`

`nbx config --show-token` and `nbx demo config --show-token` intentionally reveal credentials because the user explicitly asked for secret output. This is operationally sensitive by design.

Guidance:

- Use only when necessary
- Avoid recording terminals or logs while using it
- Do not copy that output into docs, issues, or CI logs

### Cache contents

The HTTP cache may contain authenticated API responses. Permissions are hardened, but the cache is still sensitive local data.

Guidance:

- Treat `~/.config/netbox-cli/http-cache/` as sensitive
- Do not publish or archive cache contents

### Demo credentials

`demo_auth.py` automates browser-based login and token provisioning for `demo.netbox.dev`. Those credentials and tokens should be treated like any other authentication secret.

## Secure Development Rules

When changing security-sensitive code in this repository:

1. Keep outbound requests relative to the configured NetBox base URL.
2. Do not add config or cache writes that rely only on system umask for privacy.
3. Sanitize any untrusted string before printing it to the terminal or rendering it in Rich/Textual widgets.
4. Prefer explicit failure over permissive coercion for URL and auth-related inputs.
5. Add or update tests in the security-focused test files whenever a hardening path changes.

## Recommended Verification Commands

Run the focused security coverage:

```bash
pytest -q tests/test_config_profiles.py tests/test_api_auth.py tests/test_api_cache.py tests/test_output_safety.py
```

Run the full suite:

```bash
pytest -q
```

Current known good result at the time of writing (excludes live-network demo tests):

- `100 passed`
