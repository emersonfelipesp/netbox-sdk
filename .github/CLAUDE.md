# .github — GitHub Actions Workflows

## Workflows

### `workflows/lint.yml` — Lint + Format Checks

Runs on every push and pull request.

- **Python:** 3.13
- **Tooling:** `uv sync --dev --locked`
- **Command:** `uv run pre-commit run --all-files --show-diff-on-failure --color=always`

This workflow is the source of truth for Python style enforcement. It executes the same `.pre-commit-config.yaml` hooks contributors should install locally, so local commits, local pushes, and GitHub Actions all use the same Ruff lint/format rules.

---

### `workflows/test.yml` — CI Tests

Runs the full pytest suite on every push and pull request.

- **Matrix:** Python 3.11, 3.12, 3.13
- **fail-fast:** false (all versions run even if one fails)
- **Install:** `uv sync --dev --locked`
- **Command:** `uv run pytest`

Live tests (`test_demo_auth.py`, `test_demo_cli.py`) that require `DEMO_USERNAME` / `DEMO_PASSWORD` skip gracefully when those secrets are absent in a fork or external PR.

---

### `workflows/docs.yml` — Build & Deploy Documentation

Runs on:
- Every push to `main`
- Manual `workflow_dispatch`

**Permissions:** `contents: write` (needed for `mkdocs gh-deploy` to push to the `gh-pages` branch).

**Steps:**

1. **Checkout** — full history (`fetch-depth: 0`) for MkDocs git-committer-date support
2. **Set up Python 3.12** with pip cache
3. **Install** `pip install -e ".[docs,dev]"` — gets `mkdocs-material` + `netbox-cli` itself
4. **Docgen** (conditional) — runs only when both `DEMO_USERNAME` and `DEMO_PASSWORD` secrets are set:
   ```bash
   pip install playwright
   playwright install chromium --with-deps
   nbx demo init --username "$DEMO_USERNAME" --password "$DEMO_PASSWORD" --headless
   nbx docs generate-capture
   ```
   If secrets are absent, prints a message and exits 0 (skips silently).
5. **Configure git identity** — sets `github-actions[bot]` name/email for the push
6. **Deploy** — `mkdocs gh-deploy --force --clean --verbose`

**Required repository secrets:**
| Secret | Value |
|---|---|
| `DEMO_USERNAME` | demo.netbox.dev account username |
| `DEMO_PASSWORD` | demo.netbox.dev account password |

**Important:** Do NOT use `if:` conditions to check secrets in GitHub Actions YAML — it causes "workflow file issue" errors. Always guard with shell-level `[ -z ]` after exporting secrets as `env:` variables.

---

### `workflows/publish-testpypi.yml` — Release Validation and Publishing (TestPyPI → PyPI)

Runs on:
- Push tags matching `v*`
- Manual `workflow_dispatch` (supports `publish_pypi` boolean input)

**Permissions:** `contents: read`

**Pipeline stages (gated):**

1. **Prepare release artifacts**:
   - validate package metadata (`project.name == netbox-console`)
   - validate tag/version match on tag pushes (`v<version>`)
   - build `sdist` + `wheel` once and publish as workflow artifact
2. **Publish to TestPyPI**:
   - Twine upload with `--skip-existing`
3. **Validate TestPyPI release**:
   - pre-CI style checks (`pre-commit` + `pytest` matrix)
   - post-CI style checks (package install + demo TUI tests + full pytest)
4. **Publish to official PyPI** *(only if all TestPyPI validations pass and `publish_pypi=true` on manual dispatch)*:
   - Twine upload with `--skip-existing`
5. **Validate official PyPI release**:
   - pre-CI style checks (`pre-commit` + `pytest` matrix)
   - post-CI style checks (package install + demo TUI tests + full pytest)

**Package install rules in validation:**
- TestPyPI package + official PyPI dependencies:
   - `--index-url https://test.pypi.org/simple/`
   - `--extra-index-url https://pypi.org/simple/`
- Official PyPI package:
   - `--index-url https://pypi.org/simple/`

**Playwright runtime validation** is included in both TestPyPI and PyPI smoke checks:
- `python -m playwright install --with-deps chromium`
- minimal Chromium launch check (`browser = p.chromium.launch(headless=True)`)

**Required repository secrets (TestPyPI):**
| Secret | Value |
|---|---|
| `TEST_PYPI_USERNAME` | usually `__token__` |
| `TEST_PYPI_TOKEN` | TestPyPI API token |
| `TEST_PYPI_REPOSITORY_URL` | `https://test.pypi.org/` |

**Required repository secrets (PyPI):**
| Secret | Value |
|---|---|
| `PYPI_USERNAME` | usually `__token__` |
| `PYPI_TOKEN` | PyPI API token |
| `PYPI_REPOSITORY_URL` | `https://pypi.org/` |
