# Design principles (SOLID-aligned)

This project does not enforce SOLID through tooling; these are conventions for contributors and for embedding the library.

## Single responsibility (S)

- **HTTP, auth, cache, token retry** live in `netbox_sdk/client.py` and `netbox_sdk/http_cache.py`.
- **OpenAPI indexing** lives in `netbox_sdk/schema.py`.
- **Request resolution** from user-facing actions lives in `netbox_sdk/services.py`.
- **Typer** lives in `netbox_cli/`; **Textual** in `netbox_tui/`.
- **Theme JSON** and validation live in `netbox_tui/theme_registry.py` and `netbox_tui/themes/*.json`.

Avoid growing “god modules” when adding features; prefer a new small module or extending the closest existing owner.

## Open/closed (O)

Dynamic CLI commands are generated from the bundled OpenAPI schema. New NetBox resources appear in the CLI/TUI when the schema is updated, without hand-maintaining per-resource command tables.

## Liskov substitution (L)

Shared contracts between layers are plain types: `Config`, `ApiResponse`, `SchemaIndex`, `NetBoxApiClient`. Code that accepts a `NetBoxApiClient` should work with test doubles that implement `request()` and `probe_connection()` consistently.

## Interface segregation (I)

Prefer small, focused helpers over wide “context” objects. Where tests need seams, use `typing.Protocol` or duck typing for “client-like” objects rather than subclassing `NetBoxApiClient`.

## Dependency inversion (D)

- **Preferred:** TUIs and tools receive `client` and `index` from the caller instead of reaching into CLI internals.
- **CLI:** Command bodies resolve `_get_client`, `_ensure_runtime_config`, and related hooks via `netbox_cli` / `netbox_cli.runtime` so tests can patch `netbox_cli.*` reliably.
- **Documented exceptions:**
  - `netbox_tui/cli_tui.py` imports the real Typer `app` for `CliRunner` parity with `nbx`.
  - `_get_client()` in `netbox_cli.runtime` uses a late import of `netbox_cli` so interactive profile completion stays in one place.

## Quality gates

- `uv run pre-commit run --all-files`
- `uv run pytest`

New cross-layer imports that violate the [package integration](package-integration.md) table should be documented here or avoided.
