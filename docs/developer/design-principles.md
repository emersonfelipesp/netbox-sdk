# Design principles (SOLID-aligned)

This project does not enforce SOLID through tooling; these are conventions for contributors and for embedding the library.

## Single responsibility (S)

- **HTTP, auth, cache, token retry** live in `api.py` and `http_cache.py`.
- **OpenAPI indexing** lives in `schema.py`.
- **Request resolution** from user-facing actions lives in `services.py`.
- **Typer** lives under `cli/`; **Textual** under `ui/`.
- **Theme JSON** and validation live in `theme_registry.py` and `themes/*.json`.

Avoid growing “god modules” when adding features; prefer a new small module or extending the closest existing owner.

## Open/closed (O)

Dynamic CLI commands are generated from the bundled OpenAPI schema. New NetBox resources appear in the CLI/TUI when the schema is updated, without hand-maintaining per-resource command tables.

## Liskov substitution (L)

Shared contracts between layers are plain types: `Config`, `ApiResponse`, `SchemaIndex`, `NetBoxApiClient`. Code that accepts a `NetBoxApiClient` should work with test doubles that implement `request()` and `probe_connection()` consistently.

## Interface segregation (I)

Prefer small, focused helpers over wide “context” objects. Where tests need seams, use `typing.Protocol` or duck typing for “client-like” objects rather than subclassing `NetBoxApiClient`.

## Dependency inversion (D)

- **Preferred:** TUIs and tools receive `client` and `index` from the caller, or use `app_runtime` (`get_schema_index`, `client_for_config`, `get_default_client`) instead of reaching into `cli.runtime` internals.
- **CLI package:** Command bodies resolve `_get_client`, `_ensure_runtime_config`, and related hooks via lazy imports from `netbox_cli.cli` so tests can patch `cli.*` reliably.
- **Documented exceptions:**
  - `ui/cli_tui.py` imports the real Typer `app` for `CliRunner` parity with `nbx`.
  - `get_default_client()` in `app_runtime` intentionally calls into `netbox_cli.cli` for interactive profile completion.

## Quality gates

- `uv run pre-commit run --all-files`
- `uv run pytest`

New cross-layer imports that violate the [package integration](package-integration.md) table should be documented here or avoided.
