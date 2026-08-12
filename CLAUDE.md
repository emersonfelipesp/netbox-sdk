# netbox-sdk — Project Guide

## Workspace Context

This file lives at `/root/personal-context/nmulticloud-context/netbox-sdk/CLAUDE.md` inside the `personal-context` workspace.
Workspace guidance: `/root/personal-context/CLAUDE.md`.
Per-repo deep-dive: `/root/personal-context/claude-reference/netbox-sdk.md`.
Submodule layout and cross-repo links: `/root/personal-context/claude-reference/dependency-map.md`.

---

## Codebase Index

| Path | CLAUDE.md | What's there |
|---|---|---|
| `netbox_sdk/` | [→](netbox_sdk/CLAUDE.md) | Standalone SDK package: client, config, schema, services, cache, shared formatting/logging/output helpers |
| `netbox_tui/` | [→](netbox_tui/CLAUDE.md) | Textual TUI package: apps, chrome, widgets, navigation, state, TCSS, theme registry |
| `netbox_tui/themes/` | [→](netbox_tui/themes/CLAUDE.md) | JSON theme files auto-discovered by the TUI |
| `netbox_cli/` | [→](netbox_cli/CLAUDE.md) | Typer CLI package: root app, runtime, dynamic commands, demo/dev/docgen wiring |
| `netbox_mcp/` | [→](netbox_mcp/CLAUDE.md) | Optional schema-driven MCP package: validated tools, stdio/HTTP transports, auth, mutation gate |
| `netbox_cli/reference/` | [→](netbox_cli/reference/CLAUDE.md) | Bundled CLI-local OpenAPI reference copy (schema driving dynamic commands) |
| `netbox_sdk/reference/` | [→](netbox_sdk/reference/CLAUDE.md) | Bundled SDK OpenAPI assets for supported NetBox release lines |
| `tests/` | [→](tests/CLAUDE.md) | pytest suite |
| `docs/` | [→](docs/CLAUDE.md) | MkDocs sources |
| `.github/` | [→](.github/CLAUDE.md) | GitHub Actions workflows |
| `reference/` | [→](reference/CLAUDE.md) | Design, Textual, and prior-art client references |
| `reference/PYNETBOX.md` | n/a | Maintainer reference for `pynetbox` architecture and prior-art client behavior |

## Architecture In One Page

```
netbox_sdk/   standalone runtime-independent API layer
    ├── branching.py
    ├── config.py
    ├── client.py
    ├── decorators.py
    ├── exceptions.py
    ├── proxbox.py
    ├── proxbox_sync.py
    ├── http_cache.py
    ├── http_ssl.py
    ├── telemetry.py
    ├── mock_main.py
    ├── schema.py
    ├── services.py
    ├── plugin_discovery.py
    ├── plugin_bridge.py
    ├── formatting.py
    ├── logging_runtime.py
    ├── output_safety.py
    ├── trace_ascii.py
    ├── demo_auth.py
    ├── facade.py
    ├── typed_api.py
    ├── typed_runtime.py
    ├── versioning.py
    ├── mock/
    ├── models/
    ├── typed_versions/
    ├── django_models/
    └── reference/openapi/

netbox_tui/   optional Textual layer
    ├── app.py / dev_app.py / cli_tui.py / logs_app.py / django_model_app.py / graphql_app.py / proxbox_app.py
    ├── branch_screen.py / filter_overlay.py / login_modal.py / ssl_verify_support.py
    ├── chrome.py / widgets.py / navigation.py / nav_blueprint.py / panels.py / state.py
    ├── cli_completions.py / dev_rendering.py / lifecycle.py / logo_render.py
    ├── theme_registry.py
    ├── *.tcss
    └── themes/*.json

netbox_cli/   optional Typer layer
    ├── __init__.py   root app + entrypoint
    ├── branching.py  NetBox Branching commands
    ├── decorators.py reusable Typer decorator factories
    ├── runtime.py    config/index/client factories
    ├── dynamic.py    OpenAPI command registration/execution
    ├── proxbox.py    netbox-proxbox catalog, CRUD, TUI, and sync commands
    ├── support.py    shared CLI rendering/error helpers
    ├── demo.py       demo profile command tree
    ├── dev.py        dev command tree
    ├── django_model.py
    ├── markdown_output.py
    └── docgen*/ docgen/

netbox_mcp/   optional Model Context Protocol layer
    ├── __init__.py   entrypoint + transport selection
    ├── app.py        explicit FastMCP tool registration
    ├── models.py     strict tool argument schemas
    └── service.py    SDK-backed dispatch + mutation gate
```

Data flow:
1. `netbox_sdk` owns API behavior and shared data transformation.
2. `netbox_cli` imports `netbox_sdk` and lazy-loads `netbox_tui` where needed.
3. `netbox_tui` imports `netbox_sdk` directly and only reaches into `netbox_cli` for CLI app/runtime callbacks where required.
4. `netbox_mcp` imports only `netbox_sdk`; it shares introspection and request
   resolution contracts with the CLI without importing the CLI package.

## Contributor Workflow

Initial setup:

```bash
uv sync --dev --extra cli --extra tui --extra demo --extra mcp
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
```

Day-to-day:

```bash
uv run pre-commit run --all-files
uv run pytest
uv run pytest -m suite_sdk
uv run pytest -m suite_cli
uv run pytest -m suite_tui
uv run pytest -m suite_mcp
```

If you need a minimal install boundary check:

```bash
pip install -e .
pip install -e '.[cli]'
pip install -e '.[tui]'
pip install -e '.[mcp]'
pip install -e '.[all]'
```

## CLI Dynamic Command Surface

The CLI exposes NetBox API resources through `nbx <group> <resource> <action>`. Static command registration is network-free and defaults to the bundled NetBox 4.6 schema; command execution, discovery helpers, and TUI launch use `_get_runtime_index()` to honor `--netbox-version` / `NETBOX_SDK_NETBOX_VERSION` or detect the configured instance release line.

| Action | HTTP | Path | Notes |
|---|---|---|---|
| `list` | GET | list path | Supports `--all` for auto-pagination |
| `get` | GET | detail path | Requires `--id` |
| `create` | POST | list path | |
| `update` | PUT | detail path | Requires `--id` |
| `patch` | PATCH | detail path | Requires `--id` |
| `delete` | DELETE | detail path | Requires `--id` |
| `bulk-update` | PUT | list path | Array body; no `--id` |
| `bulk-patch` | PATCH | list path | Array body; no `--id` |
| `bulk-delete` | DELETE | list path | Array body; no `--id` |
| `filters` | — | local only | Prints available filter parameters from schema |

Every dynamic action that resolves to `POST`, `PUT`, `PATCH`, or `DELETE`
(including a raw HTTP-method action spelling), write-method `nbx call` and
`nbx dev http` requests, every mutating `nbx branching`/`nbx branch` verb,
and Proxbox CRUD/sync scheduling or TUI launch require `--confirm` or
`NETBOX_SDK_CONFIRM_WRITE=1`. Dry-run previews do not require confirmation;
the shared dev/Proxbox request workbench also presents a separate confirmation
dialog before every POST, PUT, PATCH, or DELETE dispatch.

**Auto-pagination** (`--all` / `--max-records`): When `--all` is passed for a `list` action, `list_all_pages` in `netbox_sdk/services.py` follows the `next` URL chain and returns a single synthesised response. It raises `PaginationError` on malformed result arrays, repeated page targets, or a page that supplies another link without adding records. `--max-records N` (default 10 000) remains the hard ceiling on accumulated records.

**Query/header forwarding**: `parse_key_value_pairs()` preserves repeated query keys as list values so filters like `tag=a&tag=b` survive through `aiohttp`. Dynamic commands, `nbx call`, and `nbx dev http` accept `-H` / `--header` in either `Header=Value` or `Header: Value` form for ETag/conditional request workflows.

**Bulk routing**: `bulk-update`, `bulk-patch`, and `bulk-delete` always target the list path, never the detail path. The `--id` option is silently ignored for bulk actions.

**Filter discovery**: `filters` is a synthetic local action that calls `SchemaIndex.filter_params()` and prints the available query parameters without making an HTTP request.

**Plugin auto-discovery** (`netbox_sdk/plugin_discovery.py`): when `dynamic.py` is asked to act on a `group/resource` pair that is absent from the bundled schema (`index.resource_paths(group, resource) is None`), it lazily calls `enrich_schema_index_with_runtime_resources(index, client)`. That function does a BFS walk starting at `GET /api/plugins/` and follows every URL found in API root responses, collecting collection and detail path pairs into the live `SchemaIndex`. Any installed NetBox plugin that exposes a `NetBoxRouter` root is therefore automatically reachable via `nbx plugins <plugin> <resource> <action>` — no CLI rebuild or SDK configuration required.

Plugin auto-discovery also runs unconditionally in `runtime.py::_get_enriched_index()`, which is used when the CLI needs a fully populated index without a prior resource-miss trigger.

**What a plugin needs to be auto-discovered:**
1. Register a `NetBoxRouter` with `APIRootView` in its `api/urls.py`.
2. Return a JSON dict of collection URLs from `GET /api/plugins/<plugin>/`.
3. Each collection URL must serve a paginated `{"count": …, "results": […]}` response.

Sub-namespaced endpoints (e.g. `endpoints/proxmox/`, `endpoints/pbs/`) are discovered through the same BFS as long as the plugin root links to the sub-namespace root, which `NetBoxRouter` includes automatically. `netbox-proxbox` satisfies all three requirements across all 29 of its ViewSets.

## Proxbox Surface

`netbox_sdk.proxbox` owns the stable catalog for the dedicated Proxbox command
surface. It registers Proxbox plugin resources into a `SchemaIndex` without a
live schema probe, marks read-only plugin resources as read-only, and feeds the
generated `nbx proxbox <family> <resource> <action>` commands plus the
Proxbox-only TUI.

`netbox_sdk.client.NetBoxApiClient.stream_sse()` is the transport-only primitive
for long-running Server-Sent Event streams. It bypasses HTTP cache and token
retry logic, keeps the aiohttp response context open while yielding raw SSE
blocks, and is intentionally generic. It does **not** follow redirects
(`allow_redirects=False`) and raises `RequestError` on any `>=400`, any `3xx`, or
any success whose `Content-Type` is not `text/event-stream`, so a non-SSE body
(login/redirect/interstitial) can never be silently parsed as an empty stream.

`netbox_sdk.proxbox_sync.ProxboxSyncClient` owns the netbox-proxbox contract:
scheduling `POST /api/plugins/proxbox/sync/schedule/`, resolving Proxmox
endpoint names through `/api/plugins/proxbox/endpoints/proxmox/`, parsing SSE
blocks into `SseFrame`, streaming `/plugins/proxbox/jobs/{job_id}/stream/`, and
fetching `/api/core/jobs/{job_id}/` after the stream for authoritative status
and error log entries. `ProxboxSyncError` preserves a known scheduled `job_id`
when that authoritative fetch fails so automation can inspect the existing job
instead of blindly scheduling a duplicate.

`netbox_cli.proxbox` owns all Rich/Typer behavior for `nbx proxbox resources`,
`ops`, generated CRUD commands, the confirmation-gated Proxbox TUI launcher,
`sync`, and `sync-types`. Keep Rich rendering out of the SDK; final CLI sync results must
merge streamed errors with post-stream Job `error` and error-level `log_entries`
because server-side SSE throttling can drop granular errors. After a stream
failure, the fetched job status is authoritative: poll the same job within the
remaining timeout when necessary, keep terminal success successful, and report
the transport loss as a warning rather than a job error.

## Core Rules

- SDK code in `netbox_sdk/` must not import `netbox_cli` or `netbox_tui`.
- CLI code in `netbox_cli/` must lazy-import TUI entrypoints so `import netbox_cli` works without `textual`.
- TUI code in `netbox_tui/` may depend on `netbox_sdk` and `textual`, not on old `netbox_cli/ui` paths.
- MCP code in `netbox_mcp/` may depend on `netbox_sdk` and `mcp`, never on `netbox_cli` or `netbox_tui`.
- Use absolute imports only: `netbox_sdk.*`, `netbox_tui.*`, `netbox_cli.*`, `netbox_mcp.*`.
- Never use pynetbox or direct NetBox model access. Use `aiohttp` via `netbox_sdk.client`.
- Semantic plugin discovery and dispatch must use `NetBoxApiClient.request_bounded()` so contracts are current, uncached, non-redirecting, and body-bounded; never authorize a plugin tool from the ordinary stale-if-error cache.
- Filesystem-cache invalidation failures (lock timeouts and other `OSError`s alike) are a per-path bypass state: reads must not trust or populate existing entries until a failed invalidation has been completed, and portable stale-lock reclamation must preserve exclusive ownership across racing reclaimers. A cache entry proven stale by a generation mismatch (the 304-concurrent-write race) must not be resurrected by a later stale-if-error fallback in the same request if the follow-up refetch itself fails. A corrupted per-path index recovers into the same per-path bypass state, not a trustable generation `0`: `_load_index_state_or_purge()` marks the path unavailable on corruption, and `_purge_all_entries()` publishes digest-keyed markers for every secondary corrupted index it discovers, so `load()`/`save()`/`refresh()`/`path_generation()` never let a stale captured `expected_generation=0` match a freshly reset index's `0`. On POSIX, `_locked_index()`'s `fcntl` branch polls `flock(LOCK_EX | LOCK_NB)` on the same bounded timeout `_portable_lock` uses (never a blocking `flock(LOCK_EX)`), retrying only `EAGAIN`/`EACCES`; `NetBoxApiClient` runs every synchronous cache-store operation through `asyncio.to_thread()` so the required wait-then-succeed locking semantics do not stall its event loop.
- The SDK now exposes three public layers: raw `NetBoxApiClient`, async facade `api()`, and versioned typed client `typed_api()`.
- OpenTelemetry request tracing is opt-in and lives in `netbox_sdk.telemetry`; keep
  all `opentelemetry.*` imports lazy/guarded so base `import netbox_sdk` works
  without the `otel` extra.
- Bundled typed and OpenAPI support currently targets NetBox release lines `4.6`, `4.5`, `4.4`, and `4.3`; CLI defaults to 4.6 and can be pinned to 4.5/4.6 via `--netbox-version` or `NETBOX_SDK_NETBOX_VERSION`. The CI live-NetBox suite exercises `v4.6.6`, `v4.6.3`, `v4.6.2`, and `v4.5.10`.
- Never hardcode colors in TCSS. Use theme variables and JSON theme definitions.
- Consult [`reference/PYNETBOX.md`](reference/PYNETBOX.md) when evaluating prior-art NetBox client patterns or interoperability expectations.

## TUI Design Rules

- Consult `reference/design/NETBOX-DARK-PATTERNS.md` first, then `reference/design/TOAD-DESIGN-GUIDE.md`.
- Theme changes must propagate through nested Textual internals, not only parent widgets.
- Keep visual state in TCSS classes, not Python conditionals.

## Continuous Integration

`.gitea/workflows/ci.yml` is the secret-free Gitea-first review gate. It runs
the complete locked offline environment on the isolated
`ci-untrusted-python312` label: workflow policy, ty, Pyright, all-files
pre-commit, the full mocked suite, SDK/CLI/TUI/MCP security regressions, strict
documentation, lifecycle/package evidence, distribution metadata, and an
installed-wheel smoke check. Pull-request jobs have read-only repository
permissions and must never receive credentials, publish, deploy, push, or
contact a live NetBox service.

The Gitea workflow supplements rather than replaces GitHub's Python 3.11–3.13
and live-NetBox matrices. A workflow file alone is not a merge gate: require an
eligible runner, terminal successful contexts, protected-branch requirements,
and a PR branch current with its base. Gitea evaluates `refs/pull/<N>/head`, not
a synthetic merge commit; a queued job with `runner_id: 0` is missing evidence,
not a pass.

`.gitea/workflows/publish-package.yml` is the private package-registry release
path. It accepts only an exact annotated RC tag at explicitly fetched canonical
`main`; manual dispatch is forbidden. Candidate code builds twice without
credentials on `ci-untrusted-python312`, canonicalizes archive metadata from the
validated commit epoch, and must produce byte-identical wheel/sdist pairs. A
credential-free `mirror-host` job performs all Git/archive/metadata parsing and
independently canonicalizes private copies, requires byte equality with the
untouched incoming artifacts, and emits a private exact seal. A separate
package-write job checks out its helper at `${{ github.sha }}`, rejects any
verify-job source-SHA mismatch, changes to that exact tool root, and only
validates the bounded seal, re-hashes the two files, and performs bounded
registry/Twine operations. Only its final step
receives the ephemeral job token. GitHub Actions remains the sole TestPyPI and
PyPI publisher.

## Verification Before Done

- Run `uv run pre-commit run --all-files`.
- Run `uv run pyright netbox_sdk netbox_cli netbox_tui netbox_mcp` alongside
  `ty check`. Both gates must pass. All four packages ship `py.typed` PEP 561
  markers.
- Run the package-specific marker suite for the package(s) you changed.
- Run `uv run pytest` when shared files or release/main validation paths are involved.
- For packaging changes, verify extras and import boundaries.

## Release Process

### Merging `main` into version branches (e.g. `v0.0.7.post1`)

When updating a release or topic branch from `main`, **`main` has priority on merge conflicts**: resolve by keeping the `main` side. With `git merge origin/main` checked out on the release branch, that is **`git checkout --theirs -- <path>`** (then review and `git add`). Re-port any branch-only work onto the post-merge tree if still needed.

- Use the Git tag as `vX.Y.Z` (including post-releases such as `v0.0.7.post1` when applicable).
- Use the GitHub release title as `netbox-sdk vX.Y.Z`.
- Do not mix bare tags and package-prefixed titles across releases.
- Example: tag `v0.0.7.post1`, title `netbox-sdk v0.0.7.post1`.
- When bumping the source candidate, update **`docs/snippets/package-version.txt`**, **`mkdocs.yml`** → **`extra.package_version`**, **`metadata.json`** → **`release`**, **`llms.txt`** → **Current project version**, and the release-tag examples in **`README.md`**, then run **`uv lock`**. Keep normal-index pins (`pip-pinned-*.txt`, `uv-pinned-cli.txt`, and the README pinned install) aligned separately with **`docs/snippets/published-package-version.txt`**; advance that final-release value only after the package is verified on the default PyPI index. **`tests/test_docs_alignment.py`** guards both contracts.
- Generate **`metadata.json`** only with a full SHA that identifies a commit object in candidate ancestry whose `pyproject.toml` contains the same project version and whose tree matches the candidate outside the deliberate `metadata.json` follow-up; annotated tag-object SHAs are invalid provenance. `scripts/build_metadata.py` accepts `SOURCE_COMMIT` or `GITHUB_SHA`, falls back to the checked-out `HEAD`, and fails on missing, unrelated, wrong-object, version-mismatched, or materially different provenance. Because a commit cannot contain its own SHA, first commit the two-parent release-lineage integration, then immediately regenerate metadata with that integration commit SHA and create a follow-up metadata commit before pushing or opening review.
- The immutable `v0.0.10` annotated tag object must remain **`e104bdd554ac2becf7abd38b238d8fb5509651f4`** and peel to commit **`3bcc86481f60f0f2d6fb1913c42d1561f5d5b77e`**. If it is on a divergent lineage, integrate that exact commit through a reviewed merge with exactly two parents and the published commit as the second parent. The final Gitea integration must preserve that merge commit (merge-commit or fast-forward of the already-two-parent commit); squash, rebase, and octopus merges are forbidden. Before any release, fetch Gitea's tag into an isolated validation ref, verify the exact tag object and commit are present there, and require the release commit to be an ancestor of explicitly fetched canonical Gitea `main`. Never move the tag, discard its unique commits, force-push a default branch, or rebase published history.
- Credentialed release workflows must pin every action to a reviewed full commit SHA. Build and publish with only the `publish` dependency group locked in `uv.lock`; validate and capture exactly one correctly identified wheel plus one sdist before any network-installed smoke dependency runs; smoke only a downstream artifact copy; and upload only fresh directories populated by the artifact validator. Immediately re-fetch/revalidate canonical Gitea plus the exact TestPyPI filename/hash set, then stage only verified-missing PyPI files so partial uploads resume without `--skip-existing`; revalidate the approved filename/digest manifest in the Twine step and require a bounded final exact-set/hash check on PyPI. Metadata generation is read-only; a separate minimal `main`-only writer keeps its automatic token read-only and exposes the fine-grained `METADATA_WRITE_TOKEN` secret only to the guarded clone/commit/push step.
- The private-registry publisher builds twice from independent source worktrees, canonicalizes wheel/sdist archive metadata from the validated source-commit epoch, and requires byte equality. All Git/archive/core-metadata/README validation happens in a separate credential-free job that emits only a private exact seal; the package-write job checks out the trusted helper at that same immutable source SHA, uses `token: ''` for checkout, and exposes `${{ github.token }}` only to the final timeout-bounded seal-rehash/registry/Twine step. It accepts only an absent version or the exact two-file set with matching bytes and repository association. Partial, extra, mismatched, redirected, oversized, timed-out, or wrongly associated states fail closed; ambiguous upload/link responses recover only after an independent exact-state GET.
- Every private-publisher stage requires the exact complete pinned uv identity, including `x86_64-unknown-linux-gnu`; shortened, suffixed, wrong-version, or wrong-platform output fails before candidate processing.
- Before creating any release tag, capture `GET /repos/emersonfelipesp/netbox-sdk/tag_protections` with `nms git api --output`, then run `python -m scripts.gitea_release validate-tag-protection --policy-file .gitea/release-tag-policy.json --evidence-file <file>`. The server must expose exactly the repository-owned `v*` rule with only `emersonfelipesp` allowlisted and no teams. This external authorization is not self-verified by the tag-triggered workflow.
- Treat a partial private-registry version as terminal and immutable: never delete, overwrite, or retry that version; fix the cause and advance to the next unused `rcN` through the complete release preflight.
- Direct Git tag pushes are authorized only for exact `v*rc*` candidates and publish to TestPyPI. Final and post-release PyPI publication is authorized only by a published GitHub Release whose tag exactly matches the project version; never create a GitHub Release for an RC or directly push a final/post tag as the publishing trigger.
- `scripts/release_policy.py` is the single PEP 440 authority for registry routing. Final and post-release versions may reach the default PyPI index; prerelease, development, and local versions remain TestPyPI/source-only.
