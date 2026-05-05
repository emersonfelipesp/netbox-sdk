# API de fachada

O `netbox_sdk` inclui uma camada assíncrona conveniente para fluxos comuns do NetBox.

É equivalente em recursos ao modelo de navegação PyNetBox familiar, mas é
implementada sobre o `NetBoxApiClient` assíncrono existente e os internos do SDK
orientados por esquema. Não é um clone síncrono do `pynetbox`.

---

## Ponto de entrada

Use `api()` para criar um objeto `Api`:

```python
import asyncio
from netbox_sdk import api


async def main():
    nb = api("https://netbox.example.com", token="my-token")
    version = await nb.version()
    print(version)


asyncio.run(main())
```

Apps de nível superior são expostos como atributos:

```python
nb.dcim
nb.ipam
nb.virtualization
nb.plugins
```

---

## CRUD e filtragem

Recuperar um único objeto:

```python
device = await nb.dcim.devices.get(42)
if device is not None:
    print(device.name)
```

Filtrar uma coleção:

```python
devices = nb.dcim.devices.filter(site="lon", role="leaf-switch")

async for device in devices:
    print(device.name)
```

`Endpoint.all()` aceita os mesmos argumentos nomeados de filtro que `filter()`,
portanto as duas chamadas abaixo são equivalentes:

```python
async for device in nb.dcim.devices.all(role="leaf-switch"):
    ...

async for device in nb.dcim.devices.filter(role="leaf-switch"):
    ...
```

Contar linhas correspondentes:

```python
count = await nb.dcim.devices.count(site="lon")
print(count)
```

Criar:

```python
device = await nb.dcim.devices.create(
    name="sw-lon-01",
    site={"id": 1},
    role={"id": 2},
    device_type={"id": 3},
)
print(device.id)
```

Atualização em massa:

```python
result = await nb.dcim.devices.update(
    [
        {"id": 10, "name": "sw-lon-10"},
        {"id": 11, "name": "sw-lon-11"},
    ]
)
```

Exclusão em massa:

```python
await nb.dcim.devices.delete([10, 11, 12])
```

---

## Auxiliares de registro

Objetos retornados pela fachada são registros leves com contexto de endpoint.

Atualizar detalhes completos:

```python
device = await nb.dcim.devices.get(42)
await device.full_details()
print(device.serial)
```

Salvar apenas campos alterados:

```python
device.name = "sw-lon-01-renamed"
print(device.updates())  # {"name": "sw-lon-01-renamed"}
await device.save()
```

Excluir um único registro:

```python
await device.delete()
```

---

## Endpoints de detalhe

A fachada expõe sub-recursos comuns do NetBox diretamente a partir de registros.

IPs e prefixos disponíveis:

```python
prefix = await nb.ipam.prefixes.get(123)

available_ips = await prefix.available_ips.list()
new_ip = await prefix.available_ips.create({})

new_prefix = await prefix.available_prefixes.create({"prefix_length": 28})
```

Elevação de rack:

```python
rack = await nb.dcim.racks.get(5)

units = await rack.elevation.list()
svg = await rack.elevation.list(render="svg")
```

NAPALM e render-config:

```python
device = await nb.dcim.devices.get(42)
facts = await device.napalm.list(method="get_facts")
rendered = await device.render_config.create()
```

---

## Auxiliares de trace e path

Registros rastreáveis expõem `trace()`:

```python
interface = await nb.dcim.interfaces.get(100)
trace = await interface.trace()
```

Registros com path expõem `paths()`:

```python
termination = await nb.circuits.circuit_terminations.get(7)
paths = await termination.paths()
```

---

## Plugins e config de app

Metadados de plugins instalados:

```python
plugins = await nb.plugins.installed_plugins()
```

Recursos de plugin:

```python
olts = nb.plugins.gpon.olts.filter(status="active")
async for olt in olts:
    print(olt.name)
```

Config por app:

```python
user_config = await nb.users.config()
```

---

## Ativação de branch

Requisições com escopo de branch podem ser feitas com `activate_branch()`:

```python
branch = type("Branch", (), {"schema_id": "feature-x"})()

with nb.activate_branch(branch):
    device = await nb.dcim.devices.get(42)
```

Isso define `X-NetBox-Branch` nas requisições feitas dentro do contexto.

---

## Filtros estritos

Ative validação de filtros respaldada pelo OpenAPI na construção da API:

```python
nb = api(
    "https://netbox.example.com",
    token="my-token",
    strict_filters=True,
)
```

Ou substitua por consulta:

```python
devices = nb.dcim.devices.filter(site="lon", strict_filters=True)
```

Filtros desconhecidos levantam `ParameterValidationError`.

---

## Paginação

A fachada pagina iterações de lista de forma transparente. O NetBox 4.6 introduziu
paginação baseada em cursor com `start=<pk>&limit=<n>`, significativamente mais rápida
que a paginação por offset em grandes conjuntos de resultados. O SDK detecta a versão
do NetBox em execução e escolhe a estratégia adequada:

- NetBox `>= 4.6`: modo cursor (padrão).
- NetBox `< 4.6`: modo offset (legado).

### Matriz de parâmetros

Todo método paginado aceita o conjunto completo de argumentos de paginação do
NetBox, além de argumentos arbitrários de filtro:

| Método | `limit` | `offset` | `start` | `mode` | filtros `**kwargs` |
|---|:---:|:---:|:---:|:---:|:---:|
| `Endpoint.all(...)` | sim | sim | sim | sim | sim |
| `Endpoint.filter(...)` | sim | sim | sim | sim | sim |
| `Endpoint.get(...)` | — | — | — | — | sim |
| `Endpoint.count(...)` | — | — | — | — | sim |

`mode` aceita `"cursor"`, `"offset"` ou `"auto"`. `start` e `offset` são mutuamente
exclusivos; passar ambos levanta `ValueError`. `ordering` é rejeitado em modo
cursor (o NetBox aplica essa restrição no servidor).

### Modo cursor (padrão)

```python
nb = api("https://netbox.example.com", token="meu-token")

# Cursor por padrão no NetBox >= 4.6 (filtros e paginação combinam livremente):
async for device in nb.dcim.devices.all(role="leaf-switch", limit=100):
    print(device.id)

# Iniciar em um cursor explícito:
async for device in nb.dcim.devices.all(limit=100, start=0):
    print(device.id)
```

### Usando o método offset (legado)

O paginador offset legado continua totalmente suportado. Force-o para o cliente
inteiro ou para uma consulta específica:

```python
# Cliente inteiro:
nb = api("https://netbox.example.com", token="meu-token", pagination_mode="offset")

# Por consulta:
async for device in nb.dcim.devices.all(mode="offset", limit=100):
    print(device.id)

devices = nb.dcim.devices.filter(role="leaf-switch", mode="offset")
```

A variável de ambiente `NETBOX_SDK_PAGINATION_MODE` (`cursor` / `offset` / `auto`)
sobrescreve o padrão do construtor — útil ao isolar problemas contra uma versão
específica do NetBox. No modo cursor, o servidor retorna `count: null` por desempenho,
então `Endpoint.count()` emite um probe explícito em modo offset para obter o total —
`count()` funciona independente do modo configurado.

---

## Notas

- A fachada é async-first. Use-a dentro de funções `async def`.
- Reutiliza o cliente de baixo nível; `NetBoxApiClient` permanece disponível quando você quer controle direto de requisições.
- A implementação é intencionalmente explícita. Não tenta reproduzir exatamente o comportamento síncrono ou lazy-fetch implícito do PyNetBox.
