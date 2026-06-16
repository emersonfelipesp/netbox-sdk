# .github — GitHub Actions Workflows

## Workspace Context

This file lives at `/root/personal-context/nmulticloud-context/netbox-sdk/.github/CLAUDE.md` inside the `personal-context` workspace.
Workspace guidance: `/root/personal-context/CLAUDE.md`.
Per-repo deep-dive: `/root/personal-context/claude-reference/netbox-sdk.md`.
Submodule layout and cross-repo links: `/root/personal-context/claude-reference/dependency-map.md`.

---

## Local Equivalents

Lint/local style check:

```bash
uv sync --dev --extra cli --extra tui --extra demo --locked
uv run ty check netbox_sdk netbox_cli netbox_tui tests
uv run pre-commit run --all-files --show-diff-on-failure --color=always
```

Test suite:

```bash
uv sync --dev --extra cli --extra tui --extra demo --extra mock --locked
uv run pytest -v --tb=short -p no:randomly
uv run pytest -v --tb=short -p no:randomly -m suite_sdk
uv run pytest -v --tb=short -p no:randomly -m suite_cli
uv run pytest -v --tb=short -p no:randomly -m suite_tui
```

Docs build:

```bash
uv sync --group docs --group dev --extra cli --extra tui --extra demo --locked
uv run mkdocs build --strict
```

## Workflow Summary

- `workflows/lint.yml`
  - installs dev dependencies plus `cli`, `tui`, and `demo` extras
  - runs `ty check` as the type-check gate
  - runs pre-commit as the formatting/lint gate
- `workflows/test.yml`
  - detects whether a change affects `netbox_sdk`, `netbox_cli`, `netbox_tui`, or shared repo-wide validation inputs
  - runs `suite_sdk`, `suite_cli`, or `suite_tui` on Python 3.11, 3.12, and 3.13 for branch/PR changes
  - escalates to a full `pytest` matrix when shared files change or when the push targets `main`
  - adds the `mock` extra for mock API coverage and runs live NetBox tests on `main` against `v4.6.3`, `v4.6.2`, and `v4.5.10`
- `workflows/security.yml`
  - path-routes SDK, CLI, and TUI security tests
  - runs the relevant `tests/test_security_*.py` module on Python 3.11, 3.12, and 3.13
- `workflows/docs.yml`
  - builds docs with docs+dev groups plus CLI/TUI/demo extras
  - optionally regenerates captured docs when demo secrets are available
  - deploys to the current repository's `gh-pages` branch via `mkdocs gh-deploy`
  - must keep `mkdocs.yml` `site_url` and repo links aligned with `emersonfelipesp/netbox-sdk`
- `workflows/certification.yml`
  - validates `CERTIFICATION.md` evidence with `tests/test_certification_readiness.py`
  - builds the distribution, checks metadata with Twine, and smoke-installs the wheel
- `workflows/main-post-merge.yml`
  - validates the published `netbox-sdk[cli]` install
  - then runs source-based full-suite pytest coverage with full extras
- `workflows/django-model-builds.yml`
  - installs `netbox-sdk[cli]` from PyPI and rebuilds cached Django model graphs
- `workflows/publish-metadata.yml`
  - regenerates `metadata.json` from `scripts/build_metadata.py` on relevant `main` updates and tags
- `workflows/publish-testpypi.yml`
  - validates metadata and version tags
  - builds and uploads the single `netbox-sdk` distribution to TestPyPI and optionally PyPI
  - runs `ty check` on Python 3.13 during release validation
  - runs the full pytest matrix as release validation before publish
