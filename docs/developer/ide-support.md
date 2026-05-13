# IDE support

All three packages — `netbox_sdk`, `netbox_cli`, and `netbox_tui` — ship a
[PEP 561](https://peps.python.org/pep-0561/) `py.typed` marker and are included
in the wheel's `package-data`. Editors that read PEP 561 (VS Code via Pylance,
PyCharm, Pyright on the command line) resolve types from an installed
`netbox-sdk` without extra configuration.

## VS Code

The repository commits a minimal workspace under `.vscode/` so a fresh clone
gets a working IDE on first open. When VS Code prompts to install the
recommended extensions, accept:

- `ms-python.python`
- `ms-python.vscode-pylance`
- `charliermarsh.ruff`

`.vscode/settings.json` pins the interpreter to `${workspaceFolder}/.venv/bin/python`,
turns on Pylance indexing and import completions, and runs Ruff as the
formatter on save. `python.analysis.typeCheckingMode` is set to `basic` to
match the `[tool.pyright]` block in `pyproject.toml`, so the live diagnostics
in your editor agree with the pre-commit gate.

## Type checking gates

Two type checkers run from the same source tree, at the same `basic` level:

- **`ty`** (Astral) — used by `ty-check` in pre-commit and CI; fast feedback
  on the SDK plus the CLI/TUI packages.
- **`pyright`** (Pylance-compatible) — used by `pyright-check` in pre-commit
  so what Pylance shows in VS Code matches what fails in commit hooks.

To run them manually:

```bash
uv run ty check netbox_sdk netbox_cli netbox_tui tests
uv run pyright netbox_sdk netbox_cli netbox_tui
```

Both gates must pass before commit. The `pyright-check` hook sits next to
`ty-check` in `.pre-commit-config.yaml`; `uv run pre-commit run --all-files`
exercises both.

### Excluded paths

Generated and bundled code is excluded from both checkers to keep them fast
and to avoid noise from generated bindings:

- `netbox_sdk/models/**`
- `netbox_sdk/typed_versions/**`
- `tests/**` (for `pyright`; `ty` checks tests but silences `all` via its
  overrides block)

### Rule severity

`[tool.pyright]` downgrades a small set of rules to `warning` so they surface
in the editor without failing the pre-commit gate. These mirror what `ty`
already silences plus the pyright analogs that surfaced on existing code:

- `reportAttributeAccessIssue`
- `reportArgumentType`
- `reportAssignmentType`
- `reportRedeclaration`
- `reportInvalidTypeArguments`

Fixing the underlying typing debt is a separate concern from making the IDE
work; addressing those warnings should not happen as a side effect of
unrelated changes.

## Consumers

If you install `netbox-sdk` from PyPI into another project, Pylance picks up
the bundled type hints automatically — there is nothing to enable in the
consuming repository. The wheel includes:

- `netbox_sdk/py.typed`
- `netbox_cli/py.typed`
- `netbox_tui/py.typed`

Hovering `NetBoxApiClient`, `api()`, or `typed_api()` in a consumer codebase
resolves to the real types.
