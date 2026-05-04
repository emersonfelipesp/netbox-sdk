# NetBox SDK

O `netbox_sdk` é uma biblioteca Python independente para conectar ao NetBox via API REST. É o núcleo compartilhado pela CLI e pela TUI, mas também pode ser importado sozinho em qualquer projeto Python.

O SDK expõe três camadas:

- `NetBoxApiClient` para controle assíncrono de requisições de baixo nível
- `api()` / `Api` para uma fachada assíncrona de alto nível com fluxos no estilo PyNetBox
- `typed_api()` para um cliente tipado versionado com modelos Pydantic versionados

## Módulos

| Módulo | Responsabilidade |
|---|---|
| `netbox_sdk.config` | Modelo de config, persistência de perfis, construção do cabeçalho de auth |
| `netbox_sdk.client` | Cliente HTTP assíncrono e sonda de conexão |
| `netbox_sdk.facade` | API assíncrona conveniente para apps, endpoints, registros e rotas de detalhe |
| `netbox_sdk.typed_api` | Fábrica do cliente tipado versionado |
| `netbox_sdk.models` | Modelos Pydantic gerados versionados para releases NetBox suportadas |
| `netbox_sdk.typed_versions` | Bindings tipados de endpoints gerados versionados |
| `netbox_sdk.http_cache` | Cache em disco com TTL / stale-if-error |
| `netbox_sdk.schema` | Carregamento e indexação do esquema OpenAPI |
| `netbox_sdk.services` | Resolução dinâmica de requisições |
| `netbox_sdk.plugin_discovery` | Descoberta de API de plugins / objetos customizados em tempo de execução |

## Instalação

```bash
pip install netbox-sdk
```

Você não precisa dos extras opcionais de CLI ou TUI para usar `netbox_sdk` como
dependência Python.

## Início rápido

```python
import asyncio
from netbox_sdk import api


async def main():
    nb = api("https://netbox.example.com", token="your-token")

    device = await nb.dcim.devices.get(42)
    if device is not None:
        print(device.name)

asyncio.run(main())
```

Se quiser controle HTTP bruto em vez da fachada, use `NetBoxApiClient` diretamente.

## Plugins e objetos customizados

Use `async_api()` quando quiser que a fachada selecione o esquema da instância
NetBox conectada e o enriqueça com recursos em tempo de execução. Ela descobre
coleções REST de plugins sob `/api/plugins/` e recursos públicos de ObjectType
anunciados por `/api/core/object-types/`.

```python
from netbox_sdk import async_api

nb = await async_api("https://netbox.example.com", token="your-token")
widgets = await nb.plugins.custom.widgets.all().to_list()
```

O SDK suporta objetos de plugins / customizados que expõem endpoints REST
padrão de lista e detalhe. Modelos privados ou dados de plugins sem endpoint
REST são ignorados.

## SDK tipado

Use `typed_api()` quando quiser validação de requisição e resposta e modelos de
endpoint visíveis no IDE.

```python
from netbox_sdk import typed_api

nb = typed_api(
    "https://netbox.example.com",
    token="your-token",
    netbox_version="4.5",
)
```

Linhas de release suportadas:

- `4.5`
- `4.4`
- `4.3`

Versões de patch normalizam para a linha de release correspondente, por exemplo `4.5.5` mapeia
para `4.5`.
