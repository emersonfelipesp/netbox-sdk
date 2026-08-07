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
uv sync --dev --extra cli --extra tui --extra demo --extra mcp --locked
uv run ty check netbox_sdk netbox_cli netbox_tui netbox_mcp tests
uv run pre-commit run --all-files --show-diff-on-failure --color=always
```

Test suite:

```bash
uv sync --dev --extra cli --extra tui --extra demo --extra mock --extra mcp --locked
uv run pytest -v --tb=short -p no:randomly
uv run pytest -v --tb=short -p no:randomly -m suite_sdk
uv run pytest -v --tb=short -p no:randomly -m suite_cli
uv run pytest -v --tb=short -p no:randomly -m suite_tui
uv run pytest -v --tb=short -p no:randomly -m suite_mcp
```

Docs build:

```bash
uv sync --group docs --group dev --extra cli --extra tui --extra demo --extra mcp --locked
uv run mkdocs build --strict
```

## Gitea Feature Gate

`.gitea/workflows/ci.yml` mirrors the secret-free pull-request requirements on
the isolated `ci-untrusted-python312` runner. Its four bounded jobs cover static
and workflow policy, the complete offline mocked suite, all three package
security modules, and strict docs/package/installed-wheel validation. All
third-party actions are pinned to reviewed commit SHAs and repository
permissions are read-only.

This does not replace the GitHub Python-version or live-NetBox matrices. Do not
treat the Gitea contexts as authoritative until an eligible runner and required
branch checks exist. Gitea tests the PR head ref, so branch protection must also
require the head to be current with its base before merge.

## Workflow Summary

- `.gitea/workflows/ci.yml`
  - runs on pushes and pull requests targeting `main`
  - consumes no secrets and has no publish, deploy, repository-write, or live-NetBox authority
  - runs the full locked offline, security, documentation, and package evidence gates

- `workflows/lint.yml`
  - installs dev dependencies plus `cli`, `tui`, `demo`, and `mcp` extras
  - runs `ty check` as the type-check gate
  - runs pre-commit as the formatting/lint gate
- `workflows/test.yml`
  - detects whether a change affects `netbox_sdk`, `netbox_cli`, `netbox_tui`, `netbox_mcp`, or shared repo-wide validation inputs
  - runs `suite_sdk`, `suite_cli`, `suite_tui`, or `suite_mcp` on Python 3.11, 3.12, and 3.13 for branch/PR changes
  - escalates to a full `pytest` matrix when shared files change or when the push targets `main`
  - adds the `mock` extra for mock API coverage and runs live NetBox tests for SDK-affecting branch/PR changes and every `main` push against `v4.6.6`, `v4.6.3`, `v4.6.2`, and `v4.5.10`
  - fetches full Git history for every SDK/full-suite job because release-lineage tests resolve the immutable `v0.0.10` tag
  - routes release policy, metadata generation, and metadata-workflow changes through the complete suite
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
  - regenerates `metadata.json` from `scripts/build_metadata.py` only on relevant `main` updates
  - passes a full commit-object SHA; metadata generation rejects tag objects, empty or abbreviated provenance
  - generates in a read-only job, then hands the file through a job output to a separate minimal `main`-only writer whose automatic token stays read-only; the fine-grained `METADATA_WRITE_TOKEN` secret is exposed only to the guarded clone/commit/push step, and every action is pinned
- `workflows/publish-testpypi.yml`
  - authorizes direct pushes only for exact `v*rc*` candidates and authorizes final/post PyPI publication only from `release: published`
  - builds and uploads the single `netbox-sdk` distribution to TestPyPI and optionally PyPI
  - runs full-history type, pre-commit, and complete pytest preflight before any registry upload
  - retains the Python 3.11–3.13 full pytest matrix as post-TestPyPI validation
  - validates exactly one correctly identified wheel plus one sdist and captures them immediately after the locked build/check; network-installed wheel smoke dependencies run only against a downstream copy
  - compares the exact registry filename set and SHA-256 digests before upload, uploads only validator-approved files from fresh directories without `--skip-existing`, and rejects collisions or unexpected local/remote artifacts
  - installs the exact TestPyPI-only wheel URL with its verified SHA-256 fragment and checks its distribution/import version on every supported Python
  - pins every action to a reviewed full commit SHA and builds, verifies, and publishes with only the `publish` dependency group locked in `uv.lock`
  - requires the release commit to already be in explicitly fetched canonical Gitea `main` and verifies Gitea retains the exact immutable `v0.0.10` annotated tag object
  - re-fetches canonical Gitea, rechecks the exact TestPyPI artifact set, then validates PyPI and stages only verified-missing files so partial production uploads resume without `--skip-existing`; the Twine step revalidates the approved digest manifest and a bounded final check requires the exact PyPI set
  - uses one PEP 440 policy for final and post-release publication; prerelease, development, and local versions remain TestPyPI-only
