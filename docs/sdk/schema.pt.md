# Indexação de esquema

O SDK inclui uma cópia integrada do esquema OpenAPI do NetBox em `netbox_sdk/reference/openapi/netbox-openapi.json`. `SchemaIndex` analisa uma vez e expõe auxiliares rápidos de consulta para grupos, recursos, caminhos e parâmetros de filtro.

---

## Construir o índice

```python
from netbox_sdk import build_schema_index

# Usa o esquema integrado (padrão)
idx = build_schema_index()

# Ou forneça um caminho personalizado (JSON ou YAML)
from pathlib import Path
idx = build_schema_index(Path("/path/to/custom-schema.json"))
```

`build_schema_index()` é barato de chamar — analisa JSON uma vez. Compartilhe a mesma instância `SchemaIndex` entre requisições em vez de reconstruir a cada chamada.

---

## Grupos e recursos

```python
idx.groups()
# ["circuits", "dcim", "extras", "ipam", "plugins", "tenancy", "users", "virtualization", "wireless"]

idx.resources("dcim")
# ["cables", "connected-device", "console-ports", "devices", "interfaces", ...]
```

---

## Caminhos de recurso

```python
paths = idx.resource_paths("dcim", "devices")
# ResourcePaths(
#     list_path="/api/dcim/devices/",
#     detail_path="/api/dcim/devices/{id}/"
# )

paths = idx.resource_paths("nonexistent", "thing")
# None
```

Use estes caminhos diretamente com `client.request()`:

```python
paths = idx.resource_paths("dcim", "devices")
if paths and paths.list_path:
    response = await client.request("GET", paths.list_path)
```

---

## Operações

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

## Parâmetros de filtro

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

`q` vem sempre primeiro. Sufixos de lookup (`__ic`, `__n`, `__gt`, etc.) e parâmetros de paginação (`limit`, `offset`, `format`) são excluídos.

Campos de `FilterParam`:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `name` | `str` | Nome do parâmetro de query |
| `label` | `str` | Rótulo legível |
| `type` | `str` | `"string"`, `"integer"`, `"boolean"`, `"enum"`, `"array"` |
| `choices` | `tuple[str, ...]` | Não vazio para tipos `enum` |
| `description` | `str` | Do campo `description` do OpenAPI |

---

## Auxiliares de caminho especiais

```python
# Endpoint de trace de cabo (dcim)
idx.trace_path("dcim", "interfaces")
# "/api/dcim/interfaces/{id}/trace/"

idx.trace_path("dcim", "devices")
# None  (devices não têm endpoint de trace)

# Endpoint de paths de circuito
idx.paths_path("circuits", "circuit-terminations")
# "/api/circuits/circuit-terminations/{id}/paths/"
```

---

## Recursos de plugin

Plugins NetBox expõem recursos REST sob `/api/plugins/`. O esquema integrado inclui plugins enviados com a OVA padrão do NetBox, mas plugins de terceiros precisam de descoberta em tempo de execução.

### Registro manual

```python
idx.add_discovered_resource(
    group="plugins",
    resource="myplugin/widgets",
    list_path="/api/plugins/myplugin/widgets/",
    detail_path="/api/plugins/myplugin/widgets/{id}/",
)
```

Retorna `True` se o índice mudou, `False` se já estava registrado identicamente.

### Descoberta ao vivo

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

### Limpeza

```python
idx.remove_group_resources("plugins")  # remove todas as entradas de plugin do índice
```

---

## Esquema personalizado

Carregue um esquema de um arquivo que você controla:

```python
from netbox_sdk.schema import load_openapi_schema, SchemaIndex

raw = load_openapi_schema(Path("/path/to/schema.json"))   # JSON
raw = load_openapi_schema(Path("/path/to/schema.yaml"))   # YAML (requer pyyaml)

idx = SchemaIndex(raw)
```

Ou mescle rotas de plugin ao vivo no esquema integrado:

```python
idx = build_schema_index()  # começa do integrado
paths = await discover_plugin_resource_paths(client)
for list_path, detail_path in paths:
    ...  # adicione cada recurso descoberto
```
