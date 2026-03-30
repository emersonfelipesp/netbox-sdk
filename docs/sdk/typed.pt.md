# API tipada

O `netbox_sdk` inclui um cliente tipado versionado junto ao cliente bruto e à
fachada assíncrona.

Use `typed_api()` quando quiser:

- validação do corpo da requisição antes do HTTP
- validação do corpo da resposta depois do HTTP
- suporte de editor e type-checker para métodos de endpoint e modelos
- seleção explícita da versão do NetBox

## Ponto de entrada

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

Versões de patch normalizam para sua linha de release, então `4.4.10` seleciona o
cliente tipado `4.4`.

## Exemplo

```python
import asyncio

from netbox_sdk import typed_api


async def main() -> None:
    nb = typed_api(
        "https://netbox.example.com",
        token="your-token",
        netbox_version="4.5",
    )
    device = await nb.dcim.devices.get(42)
    if device is not None:
        print(device.name)


asyncio.run(main())
```

## Comportamento de validação

- Corpos de requisição são validados antes do HTTP e levantam `TypedRequestValidationError`
- Corpos de resposta são validados depois do HTTP e levantam `TypedResponseValidationError`
- Versões não suportadas levantam `UnsupportedNetBoxVersionError`

## Artefatos gerados

O repositório inclui bundles OpenAPI versionados, modelos Pydantic gerados e
bindings tipados de endpoints gerados para as linhas de release suportadas. Não é
necessário executar geração de código localmente.

Módulos relevantes:

- `netbox_sdk.models.v4_5`
- `netbox_sdk.models.v4_4`
- `netbox_sdk.models.v4_3`
- `netbox_sdk.typed_versions.v4_5`
- `netbox_sdk.typed_versions.v4_4`
- `netbox_sdk.typed_versions.v4_3`

## Escolhendo entre camadas do SDK

- Use `NetBoxApiClient` para controle bruto de requisições
- Use `api()` para a fachada assíncrona ergonômica
- Use `typed_api()` para E/S validada por Pydantic versionada
