# .github — GitHub Actions Workflows — AGENTS.md Mirror

This file mirrors the sibling `CLAUDE.md` guidance for agents that read `AGENTS.md`. Treat `CLAUDE.md` as the source material; the content below preserves the current guide.

## Source

@CLAUDE.md

---

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
  - ignores metadata-only pushes, which are covered by the dedicated provenance validator
- `workflows/test.yml`
  - detects whether a change affects `netbox_sdk`, `netbox_cli`, `netbox_tui`, `netbox_mcp`, or shared repo-wide validation inputs
  - runs `suite_sdk`, `suite_cli`, `suite_tui`, or `suite_mcp` on Python 3.11, 3.12, and 3.13 for branch/PR changes
  - escalates to a full `pytest` matrix when shared files change or when the push targets `main`
  - adds the `mock` extra for mock API coverage and runs live NetBox tests for SDK-affecting branch/PR changes and every mirrored canonical `main` source update against `v4.7.0`, `v4.6.6`, `v4.6.3`, `v4.6.2`, and `v4.5.10`. Metadata-only pushes use the dedicated provenance validator instead. Each source checkout must resolve its tag to the reviewed full commit. The `v4.7.0` image is pulled by reviewed OCI digest and the inspected RepoDigests must contain that exact digest; lines without a reviewed image digest run from their verified source checkout. Provenance-managed lines also verify the upstream tag, commit, source blob, independent source SHA-256, and normalized committed bundle before startup. `/api/status/` must then match the exact matrix version after stripping a leading `v`
  - runs the **bundled release-line matrix** (`test-bundled-release-lines`) on the same trigger: one job per registered NetBox line, pinning `NETBOX_SDK_NETBOX_VERSION`/`NETBOX_MOCK_VERSION` and running the version-sensitive suites plus a CLI-vs-MCP resolution parity check. It needs no live NetBox, so it still covers lines that remain live-exempt for CI cost (`4.3`, `4.4`). The matrix must match `netbox_sdk.versioning.SUPPORTED_NETBOX_VERSIONS`; `tests/test_release_line_coverage.py` fails if it drifts, and also fails if a line has neither a live job nor a documented self-retiring exception
  - fetches full Git history for every SDK/full-suite job because release-lineage tests resolve the immutable `v0.0.10` tag
  - routes release policy, metadata generation, and metadata-workflow changes through the complete suite
- `workflows/security.yml`
  - path-routes SDK, CLI, and TUI security tests
  - runs the relevant `tests/test_security_*.py` module on Python 3.11, 3.12, and 3.13
  - ignores metadata-only pushes, which are covered by the dedicated provenance validator
- `workflows/docs.yml`
  - builds docs with docs+dev groups plus CLI/TUI/demo extras
  - optionally regenerates captured docs when demo secrets are available
  - deploys to the current repository's `gh-pages` branch via `mkdocs gh-deploy`
  - ignores metadata-only pushes and serializes deployments per ref so concurrent `gh-pages` writes cannot race
  - must keep `mkdocs.yml` `site_url` and repo links aligned with `emersonfelipesp/netbox-sdk`
- `workflows/certification.yml`
  - validates `CERTIFICATION.md` evidence with `tests/test_certification_readiness.py`
  - builds the distribution, checks metadata with Twine, and smoke-installs the wheel
  - ignores metadata-only pushes, which are covered by the dedicated provenance validator
- `workflows/main-post-merge.yml`
  - validates the published `netbox-sdk[cli]` install
  - then runs source-based full-suite pytest coverage with full extras
  - ignores metadata-only pushes while still running once for every mirrored canonical source update
- `workflows/django-model-builds.yml`
  - installs `netbox-sdk[cli]` from PyPI and rebuilds cached Django model graphs
- `.gitea/workflows/mirror-github.yml`
  - serializes every canonical `main` push, generates metadata in a credential-free untrusted job, and confirms the event SHA is still the latest canonical tip before publishing
  - gives `SOURCE_MIRROR_TOKEN` only to the canonical fetch step and `GH_MIRROR_TOKEN` only to the GitHub push step; the GitHub push retries a changed lease at most three times
  - creates a freshly generated metadata-only child of each canonical tip before updating GitHub, so the mirror cannot discard the provenance commit
  - implements the weaker mirror-side design because no existing Gitea workflow exposes a repository-content write credential; the metadata follow-up therefore remains absent from canonical Gitea history
  - because that follow-up is absent from canonical history, the provenance test requires the recorded commit to describe the candidate tree but not to be an ancestor of it: a squash merge leaves the recorded commit a same-tree sibling of the released history
- `workflows/publish-metadata.yml`
  - runs only when `metadata.json` changes on GitHub `main`
  - validates the full commit-object SHA, same-version ancestry, and whole-tree equality outside the metadata follow-up through `scripts.build_metadata.validate_source_provenance`
  - uses no write credential; test, lint, security, certification, post-merge, and documentation workflows ignore metadata-only pushes because this dedicated gate covers them
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

The repository also owns `.gitea/workflows/publish-package.yml` for an
access-controlled package registry. It is tag-push RC-only and builds the exact
source twice in a credential-free untrusted job, canonicalizing from the commit
epoch and requiring byte equality. A second credential-free job performs all
Git/archive/metadata validation, independently re-canonicalizes private copies,
requires them to equal the untouched transfer bytes, and transfers only a
private exact seal. The package-write job checks out its helper at the immutable
tag-event SHA, rejects any verify-job source mismatch, runs from that exact tool
root, parses only the bounded seal, re-hashes its files, and confines the ephemeral token to the final
bounded publish step. This does not change GitHub Actions' sole authority over
TestPyPI and PyPI. The final job retains the repository's explicit
`contents: read, packages: write` contract, but its exact-SHA checkout sets
`token: ''`; no pre-publish action or step consumes `${{ github.token }}`.

Release-tag authorization is external state, not a workflow assertion. Before
creating a tag, capture the exact tag-protection list with `nms git api GET
/repos/emersonfelipesp/netbox-sdk/tag_protections --output <file>` and
validate it against `.gitea/release-tag-policy.json`; every `v*` tag must be
protected with only `emersonfelipesp` allowlisted and no teams. This policy is
not self-verified by the tag-triggered workflow. A partial
private-registry version is terminal: never delete, overwrite, or retry it;
advance to the next unused `rcN` after fixing the cause.
