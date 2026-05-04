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

## Notas

- A fachada é async-first. Use-a dentro de funções `async def`.
- Reutiliza o cliente de baixo nível; `NetBoxApiClient` permanece disponível quando você quer controle direto de requisições.
- A implementação é intencionalmente explícita. Não tenta reproduzir exatamente o comportamento síncrono ou lazy-fetch implícito do PyNetBox.
