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

### `workflows/publish-testpypi.yml` — Build & Publish to TestPyPI

Runs on:
- Manual `workflow_dispatch`
- Push tags matching `v*`

**Permissions:** `contents: read`

**Steps:**

1. **Checkout** repository
2. **Set up Python 3.13**
3. **Set up uv**
4. **Validate package metadata** — fails if `project.name` in `pyproject.toml` is not `netbox-cli`
5. **Build artifacts** — `sdist` + `wheel` via `python -m build`
6. **Publish** — Twine upload to TestPyPI legacy endpoint with `--skip-existing` (safe reruns)
7. **Smoke test install** — installs `netbox-cli==<project version>` using:
   - `--index-url https://test.pypi.org/simple/`
   - `--extra-index-url https://pypi.org/simple/`

**Required repository secrets:**
| Secret | Value |
|---|---|
| `TEST_PYPI_USERNAME` | usually `__token__` |
| `TEST_PYPI_TOKEN` | TestPyPI API token |
| `TEST_PYPI_REPOSITORY_URL` | `https://test.pypi.org/` |
