# .github — GitHub Actions Workflows

## Local Equivalents

Lint/local style check:

```bash
uv sync --dev --extra cli --extra tui --extra demo --locked
uv run pre-commit run --all-files --show-diff-on-failure --color=always
```

Test suite:

```bash
uv sync --dev --extra cli --extra tui --extra demo --locked
uv run pytest -v --tb=short
uv run pytest -v --tb=short -m suite_sdk
uv run pytest -v --tb=short -m suite_cli
uv run pytest -v --tb=short -m suite_tui
```

Docs build:

```bash
uv sync --group docs --group dev --extra cli --extra tui --extra demo --locked
uv run mkdocs build --strict
```

## Workflow Summary

- `workflows/lint.yml`
  - installs dev dependencies plus `cli`, `tui`, and `demo` extras
  - runs pre-commit as the formatting/lint gate
- `workflows/test.yml`
  - detects whether a change affects `netbox_sdk`, `netbox_cli`, `netbox_tui`, or shared repo-wide validation inputs
  - runs `suite_sdk`, `suite_cli`, or `suite_tui` on Python 3.11, 3.12, and 3.13 for branch/PR changes
  - escalates to a full `pytest` matrix when shared files change or when the push targets `main`
- `workflows/docs.yml`
  - builds docs with docs+dev groups plus CLI/TUI/demo extras
  - optionally regenerates captured docs when demo secrets are available
- `workflows/main-post-merge.yml`
  - validates the published `netbox-sdk[cli]` install
  - then runs source-based full-suite pytest coverage with full extras
- `workflows/django-model-builds.yml`
  - installs `netbox-sdk[cli]` from PyPI and rebuilds cached Django model graphs
- `workflows/publish-testpypi.yml`
  - validates metadata and version tags
  - builds and uploads the single `netbox-sdk` distribution to TestPyPI and optionally PyPI
  - runs the full pytest matrix as release validation before publish
