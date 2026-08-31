# netbox-sdk

**SDK-first NetBox integration package for Python automation, terminal workflows, and Textual UIs.**

`netbox-sdk` is an SDK-first NetBox toolkit with terminal interfaces built on
one shared runtime:

- `netbox_cli` — Typer command-line interface
- `netbox_tui` — Textual terminal applications
- `netbox_mcp` — schema-driven Model Context Protocol server
- `netbox_sdk` — standalone REST API SDK shared by both

Published package name: `netbox-sdk`. `netbox-console` was a legacy alias published in earlier releases and is no longer shipped from this project.

## Integration Package Details

`netbox-sdk` is an integration package, not a NetBox plugin. It is not installed
into NetBox with `PLUGINS`, does not add Django models or views, and does not
need a plugin config name. Its certification evidence therefore focuses on the
same quality criteria that apply to ecosystem packages: open-source licensing,
package metadata, API compatibility, tests, documentation, support channels, and
release maintainability.

| Area | Evidence |
| --- | --- |
| License | Apache-2.0 in `LICENSE.txt` and `pyproject.toml` package metadata |
| Package | `netbox-sdk` on PyPI, with `netbox_sdk`, `netbox_cli`, `netbox_tui`, and `netbox_mcp` import packages |
| Python | Python `3.11`, `3.12`, and `3.13` |
| NetBox API compatibility | Typed clients for NetBox `4.6`, `4.5`, `4.4`, and `4.3`, plus `4.7` as a preview line (upstream `v4.7.0-beta2`, opt-in); live CI against `v4.7.0-beta2`, `v4.6.6`, `v4.6.3`, `v4.6.2`, and `v4.5.10` |
| Tests | Mock API suite, live NetBox suite, security tests, type checks, package metadata checks, and strict docs builds in GitHub Actions |
| Support | GitHub issues for bugs/features/docs requests; docs at <https://emersonfelipesp.github.io/netbox-sdk/> |

## Quick Start with the Demo Instance

Install:

```bash
pip install 'netbox-sdk[all]'
```

Authenticate against the public demo instance:

```bash
nbx demo init
```

Try a few commands:

```bash
nbx demo dcim devices list
nbx demo ipam prefixes list
nbx demo tui
nbx demo dev tui
```

## Install

The source candidate documented on the site matches **`docs/snippets/package-version.txt`**
(aligned with `pyproject.toml`). The latest final release available from the
default PyPI index is tracked separately in
**`docs/snippets/published-package-version.txt`**. Omit a pin for the latest
published final, or use that published-version value for a reproducible install.

Minimal SDK only:

```bash
pip install netbox-sdk
```

CLI:

```bash
pip install 'netbox-sdk[cli]'
```

TUI:

```bash
pip install 'netbox-sdk[tui]'
```

MCP server:

```bash
pip install 'netbox-sdk[mcp]'
```

OpenTelemetry tracing:

```bash
pip install 'netbox-sdk[otel]'
```

Everything:

```bash
pip install 'netbox-sdk[all]'
```

Pinned to the latest final release on the default package index:

```bash
pip install 'netbox-sdk[all]==0.0.11'
```

With `uv` as a user tool:

```bash
uv tool install --force 'netbox-sdk[cli]'
```

Developer checkout:

```bash
git clone https://github.com/emersonfelipesp/netbox-sdk.git
cd netbox-sdk
uv sync --dev --extra cli --extra tui --extra demo --extra mcp
uv run nbx --help
```

## Common Commands

```bash
# Basic CRUD
nbx init
nbx dcim devices list
nbx dcim devices get --id 1
nbx dcim devices create --body-json '{"name":"sw01","site":1}' --confirm
nbx dcim devices patch --id 1 --body-json '{"status":"active"}' --confirm
nbx dcim devices delete --id 1 --confirm

# NetBox version selection
# Default command discovery uses the bundled 4.6 schema; execution detects configured instances.
nbx dcim cable-bundles list --help
nbx --netbox-version 4.5 dcim devices list
NETBOX_SDK_NETBOX_VERSION=4.5 nbx resources dcim

# Auto-pagination — fetch every page in one call
nbx dcim devices list --all
nbx dcim devices list --all --max-records 500

# Filtering
nbx dcim devices list -q status=active -q site=nyc01
nbx dcim devices list -q tag=prod -q tag=edge

# Discover available filter parameters (no HTTP call)
nbx dcim devices filters

# HTTP headers for ETag / conditional update workflows
nbx dcim devices patch --id 1 -H 'If-Match: "etag-value"' --body-json '{"status":"active"}' --confirm
nbx call PATCH /api/dcim/devices/1/ -H 'If-Match: "etag-value"' --body-json '{"status":"active"}' --dry-run
nbx call PATCH /api/dcim/devices/1/ -H 'If-Match: "etag-value"' --body-json '{"status":"active"}' --confirm
nbx dev http patch --path /api/dcim/devices/ --id 1 --body-json '{"status":"active"}' --confirm

# NetBox Branching writes use the same confirmation gate
nbx branching create --name feature-x --confirm
nbx branching sync 7 --confirm

# Bulk operations (array body to list path)
nbx extras tags bulk-patch --body-json '[{"id":1,"color":"aa1409"},{"id":2,"color":"0c7a00"}]' --confirm
nbx extras tags bulk-update --body-json '[{"id":1,"name":"tag-a","slug":"tag-a","color":"ff0000"}]' --confirm
nbx extras tags bulk-delete --body-json '[{"id":1},{"id":2}]' --confirm

# Proxbox plugin catalog, CRUD, TUI, and sync jobs
nbx proxbox resources
nbx proxbox ops firewall/rules
nbx proxbox endpoints proxmox list -q name=pve-prod
nbx proxbox firewall rules patch --id 7 --dry-run --body-json '{"enabled":false}'
nbx proxbox tui --theme
nbx proxbox tui --theme dracula --confirm
nbx proxbox sync --confirm
nbx proxbox sync pve-prod -t virtual-machines -t storage --confirm
nbx proxbox sync-types

# TUI and developer tools
nbx tui
nbx dev tui
nbx cli tui
nbx logs
```

## MCP Server and Agent Safety

Install the `mcp` extra and run the server over stdio (the default):

```bash
pip install 'netbox-sdk[mcp]'
nbx-mcp
```

Streamable HTTP is also available at `/mcp`:

```bash
NETBOX_MCP_AUTH_TOKEN="$NETBOX_MCP_AUTH_TOKEN" nbx-mcp --transport streamable-http --host 127.0.0.1 --port 8000
```

Every Streamable HTTP bind requires a shared-secret bearer token via
`--auth-token` or `NETBOX_MCP_AUTH_TOKEN`; the server refuses to start
without one, including on loopback hosts (`127.0.0.1`/`localhost`/`::1`).
Binding to loopback only restricts *reachability* to this machine — it does
not *authenticate* other local processes or users, who could otherwise reach
the server's loaded NetBox credential (and any active `--allow-mutations`
window) unauthenticated. Prefer `NETBOX_MCP_AUTH_TOKEN` over `--auth-token`
on any shared host: a CLI argument is visible to other local users through
`ps` and `/proc/<pid>/cmdline`, while the environment variable is not:

```bash
NETBOX_MCP_AUTH_TOKEN="$NETBOX_MCP_AUTH_TOKEN" nbx-mcp --transport streamable-http --host 0.0.0.0
```

Every request must then send `Authorization: Bearer <token>`; requests
without it receive `401`.

The server exposes a narrow schema-driven tool set for introspection, reads,
mutations, plugin discovery, and guarded raw calls. It reads the existing
`netbox_sdk.config` profile for stdio credentials and accepts an optional
per-call bearer token. Live mutations are denied by default; enable them only
for a reviewed execution window with `NETBOX_MCP_ALLOW_MUTATIONS=1` or
`--allow-mutations`. A mutation `dry_run=true` only resolves the local request
and does not validate it against NetBox. `NETBOX_SDK_NETBOX_VERSION` pins the
same bundled release line for `nbx-mcp` that it pins for `nbx`; without a pin,
live MCP discovery uses the shared connected-instance resolution policy.

NetBox plugins can also advertise semantic operations through a versioned
manifest under their existing REST API root. The stable `plugin_list_tools`
and `plugin_call_tool` MCP tools discover and invoke those operations through
the same `NetBoxApiClient`; plugin DRF permissions remain authoritative and no
parallel credential or MCP server is created. Plugin-tool dry-runs perform only
the live GETs required for manifest discovery and never dispatch the advertised
write endpoint. Bridge version 1 is a generic descriptor protocol; each plugin
owns its tool-payload snapshot. Validation rejects date-time normalization
overflow and floating-point integers above the lossless JSON safe range so a
rounded number cannot select another object identity. See the [plugin bridge
contract](https://emersonfelipesp.github.io/netbox-sdk/mcp/plugin-bridge/).

Agents can inspect the same JSON capability contract through the CLI:

```bash
nbx groups --json
nbx resources dcim --json
nbx ops dcim devices --json
nbx capabilities --json
```

The `nbx` process itself refuses every dynamic action resolving to a write
method (including raw `POST`/`PUT`/`PATCH`/`DELETE` action spellings),
write-method `nbx call` and `nbx dev http` requests, mutating
`nbx branching`/`nbx branch` verbs, Proxbox CRUD, and Proxbox sync scheduling
unless the invocation includes `--confirm` or its environment contains
`NETBOX_SDK_CONFIRM_WRITE=1`. Dry runs remain available without confirmation.
Repository-local Claude Code and Codex hooks provide an earlier defense-in-depth
denial for recognizable Bash commands, but arbitrary decoded/generated shell
input is ultimately enforced by the CLI gate. The mirrored
`netbox-sdk-operations` Skill in
`.claude/skills/` and `.codex/skills/` documents introspect → preview → execute
→ verify.

See [Agent Client Setup](https://emersonfelipesp.github.io/netbox-sdk/mcp/agent-setup/)
for the step-by-step guide to wiring `nbx-mcp`, the hooks, and the Skill into
Claude Code and Codex CLI.

## Architecture

- `netbox_sdk` owns config, auth, caching, the release-line registry, shared bundled/live schema resolution, request resolution, the versioned plugin bridge, shared formatting, and demo helpers.
- `netbox_cli` owns the `nbx` command tree and lazy-loads `netbox_tui` where needed.
- `netbox_tui` owns all Textual apps, themes, widgets, and TCSS.
- `netbox_mcp` owns the stable validated MCP tools, including plugin bridge discovery/invocation, and imports only `netbox_sdk`.

## Runtime Dependencies

Base SDK installs depend on `aiohttp`, `pydantic`, `jsonschema`,
`email-validator`, `rich`, and `pyyaml`. Optional extras add the terminal
surfaces and local test tools:

- `cli`: Typer-powered `nbx` command tree
- `tui`: Textual terminal applications
- `mcp`: official Python MCP SDK and the `nbx-mcp` server
- `mock`: FastAPI/uvicorn mock NetBox API for integration tests
- `demo`: Playwright-powered demo setup automation
- `branching`: semantic marker for NetBox Branching workflows; no extra runtime
  dependency is required today
- `otel`: OpenTelemetry API, SDK, and OTLP HTTP/protobuf exporter for opt-in
  request tracing

External services are optional at runtime. The Python SDK can target any NetBox
instance reachable over HTTPS/HTTP, and the local mock API can be used for
offline tests.

## OpenTelemetry Request Metrics

Metrics activate **on the presence of an OTLP endpoint alone** — no SDK-specific
toggle. Install the `otel` extra and set either
`OTEL_EXPORTER_OTLP_METRICS_ENDPOINT` or `OTEL_EXPORTER_OTLP_ENDPOINT`, and every
`NetBoxApiClient.request()` records against a counter and a duration histogram.
A deployment that already exports telemetry therefore gets request rates and
latencies with no per-service wiring, which is the difference from tracing:
tracing emits one record per request and asks for an explicit opt-in, metrics
aggregate and do not.

| Instrument | Name | Unit |
| --- | --- | --- |
| Counter | `netbox.client.request.count` | `{request}` |
| Histogram | `netbox.client.request.duration` | `s` |

Attributes are the HTTP method, a **templated** operation path, the response
status, and the server address. The template is what keeps cardinality bounded:
`/api/dcim/devices/17/` is recorded as `/api/dcim/devices/{id}/`, so a metric
attribute never carries an object id. Numeric and UUID segments are both
templated.

A request that raises is still counted, with no status attribute — the failure
path is the one an operator most needs to see. Recording never raises into the
caller: a telemetry failure must not break the call it observes.

An existing global `MeterProvider` configured by the host application is reused,
never replaced. With the `otel` extra absent, or with `OTEL_SDK_DISABLED=true` or
`OTEL_METRICS_EXPORTER=none`, everything degrades to a no-op.

| Variable | Purpose |
| --- | --- |
| `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT` | Metrics-specific OTLP endpoint; activates metrics |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Shared OTLP endpoint; also activates metrics |
| `OTEL_METRICS_EXPORTER` | Use `none` to disable metrics while leaving tracing alone |
| `OTEL_SDK_DISABLED` | Standard kill switch; disables metrics when true |

## OpenTelemetry Request Tracing

Tracing is disabled by default. Install the `otel` extra and enable it with
`NETBOX_OTEL_ENABLED=true` or `Config(otel_enabled=True)` to emit one
OpenTelemetry CLIENT span for each `NetBoxApiClient.request()` call. Spans use
HTTP-client semantic attributes for method, server address, URL path, and final
response status; authorization headers, tokens, and query strings are never added
as span attributes.

The SDK uses an existing global OpenTelemetry provider when the host application
has configured one. Otherwise, when tracing is explicitly enabled, it installs a
provider with a BatchSpanProcessor and the OTLP HTTP/protobuf exporter. Collector
endpoint, headers, service name, resource attributes, sampler, and exporter
selection are controlled by the standard OpenTelemetry environment variables.

| Variable | Purpose |
| --- | --- |
| `NETBOX_OTEL_ENABLED` | SDK-specific opt-in toggle (`true`/`false`) |
| `OTEL_SDK_DISABLED` | Standard OpenTelemetry kill switch; disables SDK tracing when true |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint for the HTTP exporter |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | Must be `http/protobuf` for the bundled HTTP exporter |
| `OTEL_EXPORTER_OTLP_HEADERS` | Standard OTLP exporter headers |
| `OTEL_SERVICE_NAME` | Service name, defaulting to `netbox-sdk` |
| `OTEL_RESOURCE_ATTRIBUTES` | Additional OpenTelemetry resource attributes |
| `OTEL_TRACES_SAMPLER` | Standard OpenTelemetry sampler selection |
| `OTEL_TRACES_EXPORTER` | Use `otlp` or `none` for the SDK-installed provider |

## netbox-sdk vs pynetbox

<img src="comparison-pynetbox-vs-netbox-sdk.svg" alt="pynetbox vs netbox-sdk comparison table" width="760" />

## Contributor Workflow

```bash
uv sync --dev --extra cli --extra tui --extra demo --extra mcp
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
uv run pre-commit run --all-files
uv run ty check netbox_sdk netbox_cli netbox_tui netbox_mcp tests
uv run pytest
```

Gitea pull requests targeting `main` also run a secret-free quality gate on the
isolated `ci-untrusted-python312` runner. It covers workflow policy, both type
checkers, pre-commit, the complete offline mocked suite, SDK/CLI/TUI/MCP security
regressions, strict MkDocs, and wheel/sdist metadata plus an installed-wheel
smoke. GitHub retains the Python 3.11–3.13 and live-NetBox matrices. Do not merge
on queued or missing Gitea evidence; `runner_id: 0` means no eligible runner has
accepted the job.

## IDE Support

Open the repository in VS Code. When prompted, install the recommended
extensions (`ms-python.vscode-pylance`, `ms-python.python`,
`charliermarsh.ruff`). Pylance picks up types from all four packages
automatically — each ships a `py.typed` PEP 561 marker.

Type checking uses two gates: `ty` (Astral, fast, pre-commit + CI) and
`pyright` (Pylance-compatible, pre-commit). Both run at `typeCheckingMode =
"basic"`. To run them manually:

```bash
uv run ty check netbox_sdk netbox_cli netbox_tui netbox_mcp tests
uv run pyright netbox_sdk netbox_cli netbox_tui netbox_mcp
```

## Release Process

Release candidates use an annotated RC tag on the canonical source repository.
The repository-owned workflow publishes the immutable candidate to an
access-controlled package registry; GitHub Actions remains the only authority
that publishes to TestPyPI or the default PyPI index:

The private Gitea workflow pins the maintained Node 20 backports
`actions/upload-artifact` v3.2.2-node20 and
`actions/download-artifact` v3.1.0-node20 by full commit SHA. The installed Gitea
Actions runtime does not implement the artifact service required by v4+, so
upgrading those actions requires an explicit runner-compatibility proof.
`.gitea/workflows/artifact-v3-compatibility.yml` exercises the exact pinned
upload/download pair across separate isolated untrusted jobs on every pull
request; that check must pass before any candidate tag is created. PR code must
never target the credential-bearing `mirror-host` label.
Trusted jobs fetch public canonical source anonymously at exact refs. Every
private publisher downloads the pinned uv 0.11.28 archive directly, verifies
its reviewed SHA-256 before extraction, and uses only that absolute executable
with empty per-run managed-Python and cache directories. Before both install and
sync it clears inherited `UV_*` state, disables discovered uv configuration,
and passes the managed-Python, install, and cache choices explicitly. The
package-write credential comes from the repository `PACKAGE_WRITE_TOKEN` secret
and is introduced only in the final sealed publish step; the upstream Gitea
Actions job token is not a supported package-registry credential.
All three release stages run as separate disposable `ci-untrusted-python312`
jobs. The built-in job token stays package-read-only throughout; package write
authority exists only in the repository secret mapped into the final publish
step. Neither release nor PR code may target persistent `mirror-host`.

```bash
# Static, operator-reviewed release oracle: do not derive this tag from event input.
nms git api GET /repos/emersonfelipesp/netbox-sdk/tag_protections \
  --output /tmp/netbox-sdk-tag-protections.json
python -m scripts.gitea_release validate-tag-protection \
  --policy-file .gitea/release-tag-policy.json \
  --evidence-file /tmp/netbox-sdk-tag-protections.json
git tag -a v0.0.12rc3 -m "Release v0.0.12rc3"
git push gitea v0.0.12rc3
```

The evidence command and validator are a mandatory preflight before creating
any release tag. The repository contract requires one server-side protection
for every `v*` tag, with only `emersonfelipesp` allowlisted and no teams. This
is external repository state: the tag-triggered workflow cannot and does not
self-verify the protection that authorized its own trigger.

Do not create a GitHub Release for an RC. Final and post releases must never be
authorized by a direct tag push; publish them through the GitHub Release event
with the title pattern `netbox-sdk vX.Y.Z`:

```bash
gh release create vX.Y.Z \
  --title "netbox-sdk vX.Y.Z"
```

When cutting a source candidate, bump **`pyproject.toml`** and
**`netbox_sdk.__version__`**, then keep the candidate surfaces in sync:
**`docs/snippets/package-version.txt`**, **`mkdocs.yml`** →
**`extra.package_version`**, **`metadata.json`**, and **`llms.txt`**. Keep
normal-index install examples aligned separately with
**`docs/snippets/published-package-version.txt`** and update that value only
after a PEP 440 final or post-release package is verifiably available on PyPI.
Prerelease, development, and local versions remain source/TestPyPI-only.
**`uv lock`** must reflect the source candidate.
**`scripts/release_policy.py`** and **`tests/test_docs_alignment.py`** guard both
version contracts and registry routing.

The published `v0.0.10` annotated tag object is immutable at
`e104bdd554ac2becf7abd38b238d8fb5509651f4` and must peel to
`3bcc86481f60f0f2d6fb1913c42d1561f5d5b77e`. Preserve its unique history with
a merge with exactly two parents and the published commit as its second parent,
then use a merge-commit (or fast-forward the already-created merge commit) when
integrating the reviewed Gitea PR. Squash, rebase, and octopus merge methods are
forbidden. Verify the exact object and commit, then confirm the release commit
is already an ancestor of explicitly fetched canonical Gitea `main` before
creating any candidate tag or publishing any registry artifact. The release
workflow also fetches Gitea's `v0.0.10` ref into an isolated validation ref and
requires its annotated tag-object SHA and peeled commit to match exactly.

All credentialed publishing workflows pin every action to a reviewed full
commit SHA. Every private-publisher stage also requires the complete pinned uv
identity, including the Linux x86-64 target triple; a shortened, suffixed,
wrong-version, or wrong-platform rendering fails before candidate processing.
The private-registry workflow builds twice in independent,
credential-free source worktrees, derives canonical archive metadata from the
validated source-commit timestamp, and requires both wheel/sdist pairs to be
byte-identical. A separate credential-free job binds the archives and complete
distribution metadata to the exact canonical Git source, then emits only a
private, read-only seal and its two exact files. The package-write job checks out
the helper at the immutable tag-event SHA, rejects any upstream source-SHA
mismatch, parses only the small seal,
re-hashes the two regular files, and accepts only an absent or already-exact
remote set associated with this repository. The public package workflow uses the `publish` dependency group from
`uv.lock` for build and Twine execution, validates exactly one correctly named
wheel plus one sdist, and captures that closed set before any network-installed
smoke dependency can run. Smoke testing consumes a downstream artifact copy.
Immediately before a final PyPI upload, the workflow re-fetches canonical
Gitea, reruns the ancestry/tag policy, matches TestPyPI's exact filename and
SHA-256 set, then compares PyPI's current exact filename/hash set and copies
only verified-missing production files into a fresh directory. Twine receives
only that approved directory after its filename/digest manifest is revalidated
in the upload step, so a partial PyPI upload can resume without
`--skip-existing`. A bounded post-upload check then requires PyPI to expose the
exact wheel/sdist pair and hashes. Publisher jobs install only the audited,
locked `publish` dependency group. Metadata generation runs in a read-only job;
a separate minimal `main`-only writer receives the generated file through a job
output while its automatic token stays read-only. Configure a fine-grained
`METADATA_WRITE_TOKEN` repository secret with contents-write access; it is
exposed only to the guarded clone/commit/push step.

Private-registry versions are immutable. A partial remote version is a terminal
collision for that version: never delete files, overwrite them, or retry the
same version. Diagnose and fix the release source or workflow, advance every
candidate-version surface to the next unused `rcN`, repeat the external
release-tag protection preflight, and publish only the new candidate tag.

Release metadata is a deliberate follow-up commit: first commit the integration,
then run `SOURCE_COMMIT=<integration-sha> python scripts/build_metadata.py` and
commit the resulting `metadata.json` before pushing. Supply the integration
commit SHA, never the annotated tag-object SHA. The generator rejects a
non-commit object, a commit outside candidate ancestry, a commit whose
`pyproject.toml` has a different project version, or a source tree that differs
from the candidate anywhere except the deliberate `metadata.json` follow-up.
