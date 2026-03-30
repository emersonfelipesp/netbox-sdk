# Fazendo requisições

O `netbox_sdk` suporta dois estilos assíncronos de requisição:

- o `NetBoxApiClient` de baixo nível para chamadas HTTP diretas
- a fachada de alto nível retornada por `api()` para fluxos no estilo PyNetBox
- o cliente tipado versionado retornado por `typed_api()` para E/S Pydantic validada

Ambas as camadas são assíncronas e podem ser usadas no mesmo projeto.

---

## Uso da fachada

A fachada é o caminho mais curto para operações comuns do NetBox SDK:

```python
from netbox_sdk import api

nb = api("https://netbox.example.com", token="mytoken")
```

### Obter um único registro

```python
device = await nb.dcim.devices.get(42)
if device is not None:
    print(device.name)
```

### Filtrar e iterar

```python
devices = nb.dcim.devices.filter(site="lon", role="leaf-switch")

async for device in devices:
    print(device.name)
```

### Criar, modificar e salvar

```python
device = await nb.dcim.devices.create(
    name="sw-lon-01",
    site={"id": 1},
    role={"id": 2},
    device_type={"id": 3},
)

device.name = "sw-lon-01-renamed"
await device.save()
```

### Usar endpoints de detalhe

```python
prefix = await nb.ipam.prefixes.get(123)

available = await prefix.available_ips.list()
new_ip = await prefix.available_ips.create({})
new_prefix = await prefix.available_prefixes.create({"prefix_length": 28})
```

### Elevação de rack JSON vs SVG

```python
rack = await nb.dcim.racks.get(5)
units = await rack.elevation.list()
svg = await rack.elevation.list(render="svg")
```

### Plugins

```python
plugins = await nb.plugins.installed_plugins()

async for olt in nb.plugins.gpon.olts.filter(status="active"):
    print(olt.name)
```

---

## Uso do cliente tipado

Use o cliente tipado quando quiser payloads de requisição validados, payloads de
resposta validados e modelos de endpoint específicos da versão.

```python
from netbox_sdk import typed_api

nb = typed_api(
    "https://netbox.example.com",
    token="mytoken",
    netbox_version="4.5",
)
```

### Obter um registro tipado

```python
device = await nb.dcim.devices.get(42)
if device is not None:
    print(device.name)
```

### Validar uma requisição antes do HTTP

```python
from netbox_sdk import TypedRequestValidationError

try:
    await nb.ipam.prefixes.available_ips.create(7, body=[{"prefix_length": "invalid"}])
except TypedRequestValidationError as exc:
    print(exc)
```

### Seleção de versão

```python
typed_api("https://netbox.example.com", token="tok", netbox_version="4.5")
typed_api("https://netbox.example.com", token="tok", netbox_version="4.5.5")
```

O cliente tipado suporta NetBox `4.5`, `4.4` e `4.3`. Modelos gerados para
essas linhas de release estão versionados no repositório e acompanham o pacote.

---

## Uso do cliente de baixo nível

Todas as chamadas HTTP passam por `NetBoxApiClient.request()`.

## Uso básico

```python
from netbox_sdk import Config, NetBoxApiClient

cfg = Config(base_url="https://netbox.example.com", token_version="v1", token_secret="mytoken")
client = NetBoxApiClient(cfg)
```

### HTTPS e verificação TLS

`Config` aceita `ssl_verify` opcional:

- Omitido ou `None`: verifica certificados HTTPS (padrão), com prompts da CLI/TUI no primeiro erro de verificação se você ainda não armazenou preferência.
- `True` / `False`: sempre verificar ou desativar verificação para HTTPS (sem prompt interativo em falha).

```python
cfg = Config(
    base_url="https://netbox.example.com",
    token_version="v1",
    token_secret="mytoken",
    ssl_verify=False,  # apenas para labs confiáveis; inseguro em redes não confiáveis
)
client = NetBoxApiClient(cfg)
```

Para variáveis de ambiente, perfis salvos e recuperação interativa, veja [Configuração — HTTPS e verificação TLS](../getting-started/configuration.md#https-and-tls-verification).

### GET — listar recursos

```python
response = await client.request("GET", "/api/dcim/devices/")
data = response.json()

print(data["count"])    # número total de resultados
print(data["results"])  # lista de objetos device
```

### GET — filtrar resultados

```python
response = await client.request(
    "GET",
    "/api/dcim/devices/",
    query={"site": "lon", "role": "leaf-switch", "limit": "50"},
)
```

### GET — obter objeto único

```python
response = await client.request("GET", "/api/dcim/devices/42/")
device = response.json()
print(device["name"])
```

### POST — criar

```python
response = await client.request(
    "POST",
    "/api/dcim/devices/",
    payload={
        "name": "sw-lon-01",
        "device_type": {"id": 3},
        "site": {"id": 1},
        "role": {"id": 2},
    },
)
if response.status == 201:
    new_device = response.json()
    print(f"Created device ID {new_device['id']}")
```

### PUT — atualização completa

```python
response = await client.request(
    "PUT",
    "/api/dcim/devices/42/",
    payload={
        "name": "sw-lon-01-renamed",
        "device_type": {"id": 3},
        "site": {"id": 1},
        "role": {"id": 2},
    },
)
```

### PATCH — atualização parcial

```python
response = await client.request(
    "PATCH",
    "/api/dcim/devices/42/",
    payload={"name": "sw-lon-01-renamed"},
)
```

### DELETE

```python
response = await client.request("DELETE", "/api/dcim/devices/42/")
if response.status == 204:
    print("Deleted")
```

---

## Objeto de resposta

`request()` sempre retorna `ApiResponse`:

```python
class ApiResponse(BaseModel):
    status: int               # código de status HTTP
    text: str                 # corpo bruto da resposta
    headers: dict[str, str]   # cabeçalhos da resposta

    def json(self) -> Any: ...  # analisa text como JSON
```

Verifique o código de status antes de analisar:

```python
response = await client.request("GET", "/api/dcim/devices/99/")
if response.status == 404:
    print("Device not found")
elif response.status == 200:
    device = response.json()
```

---

## Paginação

Endpoints de lista do NetBox retornam resultados paginados. Itere páginas manualmente:

```python
async def list_all_devices(client: NetBoxApiClient) -> list[dict]:
    results = []
    offset = 0
    limit = 100
    while True:
        response = await client.request(
            "GET",
            "/api/dcim/devices/",
            query={"limit": str(limit), "offset": str(offset)},
        )
        data = response.json()
        results.extend(data["results"])
        if not data.get("next"):
            break
        offset += limit
    return results
```

---

## GraphQL

```python
query = """
{
  device_list(site: "lon") {
    id
    name
    device_type { model }
    primary_ip4 { address }
  }
}
"""
response = await client.graphql(query)
data = response.json()["data"]["device_list"]
```

Com variáveis:

```python
query = "query($id: Int!) { device(id: $id) { name status } }"
response = await client.graphql(query, variables={"id": 42})
```

---

## Verificação de saúde da conexão

Antes de chamadas à API, verifique conectividade:

```python
from netbox_sdk import ConnectionProbe

probe = await client.probe_connection()

if probe.ok:
    print(f"Connected — NetBox API {probe.version}")
else:
    print(f"Failed (HTTP {probe.status}): {probe.error}")
```

`probe_connection()` retorna `ok=True` para qualquer status acessível abaixo de 400, ou 403 (URL válida mas token incorreto — ainda acessível).

---

## Cache HTTP

Requisições GET para caminhos `/api/...` são automaticamente cacheadas em disco sob a
raiz de config do NetBox SDK, tipicamente `~/.config/netbox-sdk/http-cache/`. O
cabeçalho de resposta `X-NBX-Cache` indica o resultado do cache:

| Valor | Significado |
|-------|-------------|
| `MISS` | Primeira busca, armazenada no cache |
| `HIT` | Servida a partir de cache fresco |
| `REVALIDATED` | Servidor retornou 304, TTL do cache estendido |
| `STALE` | Erro de rede; dados obsoletos servidos |

Ajuste a política de cache:

```python
from netbox_sdk.http_cache import CachePolicy, HttpCacheStore
from netbox_sdk.config import cache_dir

# Padrão: 60s fresco, 300s stale-if-error para endpoints de lista
store = HttpCacheStore(cache_dir())
```

Requisições POST/PUT/PATCH/DELETE **nunca** são cacheadas.

---

## Requisições orientadas por esquema

Use `netbox_sdk.services` para resolver nomes de ação em chamadas HTTP:

```python
from netbox_sdk import build_schema_index
from netbox_sdk.services import resolve_dynamic_request, run_dynamic_command

idx = build_schema_index()

# Resolve para ResolvedRequest
req = resolve_dynamic_request(
    idx, "dcim", "devices", "list",
    object_id=None, query={"site": "lon"}, payload=None,
)
# req.method == "GET", req.path == "/api/dcim/devices/", req.query == {"site": "lon"}

# Ou executa diretamente
response = await run_dynamic_command(
    client, idx, "dcim", "devices", "list",
    object_id=None,
    query_pairs=["site=lon"],
    body_json=None,
    body_file=None,
)
```

Ações suportadas: `list`, `get`, `create`, `update`, `patch`, `delete`.

---

## Uploads multipart

`NetBoxApiClient.request()` muda automaticamente para multipart quando um
payload contém valores semelhantes a arquivo:

```python
with open("rack-photo.png", "rb") as handle:
    response = await client.request(
        "POST",
        "/api/extras/image-attachments/",
        payload={
            "object_type": "dcim.device",
            "object_id": 42,
            "name": "Front view",
            "image": ("rack-photo.png", handle, "image/png"),
        },
    )
```

Entradas de arquivo suportadas incluem objetos de arquivo simples e tuplas na forma
`(filename, file_obj)` ou `(filename, file_obj, content_type)`.

---

## Auxiliares de status e OpenAPI

O cliente de baixo nível expõe auxiliares para metadados comuns da API:

```python
status = await client.status()
version = await client.get_version()
spec = await client.openapi()
```

Provisionamento de token também está disponível:

```python
token_response = await client.create_token("admin", "password")
print(token_response.json()["key"])
```
