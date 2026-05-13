# Branching

NetBox 4.x can host the [`netbox-branching`](https://github.com/netboxlabs/netbox-branching)
plugin to give every change a git-like branch, review, and merge workflow. The
SDK ships a high-level `BranchingClient` plus first-class header plumbing so
SDK / CLI / TUI consumers can target a branch with one call.

Install the optional extra to make this an explicit dependency:

```bash
pip install 'netbox-sdk[branching]'
```

The extra is currently a marker — it does not add runtime dependencies — but
pinning it documents intent and lets us add helpers without breaking lean
installs later.

## Feature detection

```python
from netbox_sdk import api
from netbox_sdk.branching import BranchingClient

nb = api(base_url="https://netbox.example.com", token="…")
branching = BranchingClient(nb)

if not await branching.is_available():
    raise RuntimeError("netbox-branching is not installed on this NetBox")
```

`is_available()` issues `GET /api/plugins/branching/` and returns `True` when
the plugin responds.

## CRUD

```python
branches = await branching.list()                       # all branches
branch   = await branching.get("td5smq0f")              # by schema_id
branch   = await branching.create(name="feature-x")
await branching.update("td5smq0f", description="…")
await branching.delete("td5smq0f")
```

Every action accepts either the integer primary key or the 8-character
`schema_id`.

## Actions

`sync`, `merge`, and `revert` return a queued `Job`. Pass `wait=True` to poll
`/api/core/jobs/{id}/` until completion.

```python
job = await branching.sync("td5smq0f", commit=True, wait=True)
job = await branching.merge("td5smq0f", commit=True, wait=True,
                            acknowledge_conflicts=False)
job = await branching.revert("td5smq0f", wait=True)
branch = await branching.archive("td5smq0f")
```

If the server returns `409` with a conflict body, the SDK raises
`BranchConflictError(conflicts=…)`, which exposes the raw conflict list so
callers can render them.

## Activating a branch

The plugin scopes every request that carries the `X-NetBox-Branch` header to
that branch. The async facade exposes two patterns:

```python
# Scoped, async-context-local — auto-cleared at exit, safe under concurrency.
async with nb.activate_branch("td5smq0f"):
    devices = await nb.dcim.devices.list()

# Long-lived, applied to every request until cleared.
nb.client.persistent_headers["X-NetBox-Branch"] = "td5smq0f"
```

`activate_branch()` accepts a `Branch`, a `schema_id`, or a branch name (the
SDK resolves the name to a `schema_id` automatically).

## Read-only collections

```python
events  = await branching.events()           # /branch-events/
changes = await branching.changes()          # /changes/
models  = await branching.branchable_models()
```

## Typed clients

The same surface is reachable through the versioned typed client:

```python
from netbox_sdk import typed_api

nb = typed_api("4.6", base_url="…", token="…")
branches = await nb.plugins.branching.branches.list()
```

`PluginsApp.branching` is wired for NetBox 4.4, 4.5, and 4.6.
