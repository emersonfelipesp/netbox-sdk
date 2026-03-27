# Schema Indexing

The SDK ships a bundled copy of the NetBox OpenAPI schema at `netbox_sdk/reference/openapi/netbox-openapi.json`. `SchemaIndex` parses it once and exposes fast query helpers for groups, resources, paths, and filter parameters.

---

## Building the index

```python
from netbox_sdk import build_schema_index

# Uses the bundled schema (default)
idx = build_schema_index()

# Or supply a custom path (JSON or YAML)
from pathlib import Path
idx = build_schema_index(Path("/path/to/custom-schema.json"))
```

`build_schema_index()` is cheap to call — it parses JSON once. Share the same `SchemaIndex` instance across requests rather than rebuilding it per call.

---

## Groups and resources

```python
idx.groups()
# ["circuits", "dcim", "extras", "ipam", "plugins", "tenancy", "users", "virtualization", "wireless"]

idx.resources("dcim")
# ["cables", "connected-device", "console-ports", "devices", "interfaces", ...]
```

---

## Resource paths

```python
paths = idx.resource_paths("dcim", "devices")
# ResourcePaths(
#     list_path="/api/dcim/devices/",
#     detail_path="/api/dcim/devices/{id}/"
# )

paths = idx.resource_paths("nonexistent", "thing")
# None
```

Use these paths directly with `client.request()`:

```python
paths = idx.resource_paths("dcim", "devices")
if paths and paths.list_path:
    response = await client.request("GET", paths.list_path)
```

---

## Operations

```python
ops = idx.operations_for("dcim", "devices")
# [
#   Operation(group="dcim", resource="devices", method="GET",  path="/api/dcim/devices/",       ...),
#   Operation(group="dcim", resource="devices", method="POST", path="/api/dcim/devices/",       ...),
#   Operation(group="dcim", resource="devices", method="GET",  path="/api/dcim/devices/{id}/",  ...),
#   ...
# ]

for op in ops:
    print(f"{op.method:6} {op.path}")
```

---

## Filter parameters

```python
params = idx.filter_params("dcim", "devices")
# [
#   FilterParam(name="q",    label="Q",    type="string"),
#   FilterParam(name="id",   label="Id",   type="integer"),
#   FilterParam(name="name", label="Name", type="string"),
#   FilterParam(name="role", label="Role", type="string"),
#   ...
# ]
```

`q` is always first. Lookup suffixes (`__ic`, `__n`, `__gt`, etc.) and pagination params (`limit`, `offset`, `format`) are excluded.

`FilterParam` fields:

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Query parameter name |
| `label` | `str` | Human-readable label |
| `type` | `str` | `"string"`, `"integer"`, `"boolean"`, `"enum"`, `"array"` |
| `choices` | `tuple[str, ...]` | Non-empty for `enum` types |
| `description` | `str` | From OpenAPI `description` field |

---

## Special path helpers

```python
# Cable trace endpoint (dcim)
idx.trace_path("dcim", "interfaces")
# "/api/dcim/interfaces/{id}/trace/"

idx.trace_path("dcim", "devices")
# None  (devices don't have a trace endpoint)

# Circuit paths endpoint
idx.paths_path("circuits", "circuit-terminations")
# "/api/circuits/circuit-terminations/{id}/paths/"
```

---

## Plugin resources

NetBox plugins expose REST resources under `/api/plugins/`. The bundled schema includes any plugins shipped with the standard NetBox OVA, but third-party plugins need runtime discovery.

### Manual registration

```python
idx.add_discovered_resource(
    group="plugins",
    resource="myplugin/widgets",
    list_path="/api/plugins/myplugin/widgets/",
    detail_path="/api/plugins/myplugin/widgets/{id}/",
)
```

Returns `True` if the index changed, `False` if already registered identically.

### Live discovery

```python
from netbox_sdk.plugin_discovery import discover_plugin_resource_paths

paths = await discover_plugin_resource_paths(client)
# [("/api/plugins/gpon/olts/", "/api/plugins/gpon/olts/{id}/"), ...]

for list_path, detail_path in paths:
    group_parts = list_path.strip("/").split("/")
    # group_parts: ["api", "plugins", "gpon", "olts"]
    plugin_name = group_parts[2]
    resource_name = group_parts[3]
    idx.add_discovered_resource(
        group="plugins",
        resource=f"{plugin_name}/{resource_name}",
        list_path=list_path,
        detail_path=detail_path,
    )
```

### Cleanup

```python
idx.remove_group_resources("plugins")  # removes all plugin entries from the index
```

---

## Custom schema

Load a schema from a file you control:

```python
from netbox_sdk.schema import load_openapi_schema, SchemaIndex

raw = load_openapi_schema(Path("/path/to/schema.json"))   # JSON
raw = load_openapi_schema(Path("/path/to/schema.yaml"))   # YAML (requires pyyaml)

idx = SchemaIndex(raw)
```

Or merge live plugin routes into the bundled schema:

```python
idx = build_schema_index()  # start from bundled
paths = await discover_plugin_resource_paths(client)
for list_path, detail_path in paths:
    ...  # add each discovered resource
```
