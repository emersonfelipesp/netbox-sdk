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

- `4.6`
- `4.5`
- `4.4`
- `4.3`

Versões de patch normalizam para sua linha de release, então `4.4.10` seleciona o
cliente tipado `4.4`.

A integração contínua exercita a suíte live-NetBox contra `v4.6.6`, `v4.6.3`, `v4.6.2` e `v4.5.10`.

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

- `netbox_sdk.models.v4_6`
- `netbox_sdk.models.v4_5`
- `netbox_sdk.models.v4_4`
- `netbox_sdk.models.v4_3`
- `netbox_sdk.typed_versions.v4_6`
- `netbox_sdk.typed_versions.v4_5`
- `netbox_sdk.typed_versions.v4_4`
- `netbox_sdk.typed_versions.v4_3`

## Escolhendo entre camadas do SDK

- Use `NetBoxApiClient` para controle bruto de requisições
- Use `api()` para a fachada assíncrona ergonômica
- Use `typed_api()` para E/S validada por Pydantic versionada

### NetBox 4.7 (preview) — migração de escrita de serviços

O NetBox 4.7 substitui o par `protocol` + `ports` de um serviço por
`port_mappings`. Os modelos **graváveis** do upstream removem `protocol` (o
schema o marca como "Deprecated; use port_mappings. Reported only for
single-protocol services"), enquanto os modelos de **leitura** continuam a
reportá-lo. Os bindings 4.7 gerados pelo `netbox-sdk` espelham isso exatamente.

Consequência prática ao migrar um chamador de 4.6 para 4.7:

```python
# 4.6 — aceito na escrita
api.ipam.services.create({"name": "ssh", "protocol": "tcp", "ports": [22], ...})

# 4.7 — `protocol` NÃO faz parte do contrato de escrita e é ignorado
# silenciosamente. Use port_mappings:
api.ipam.services.create({"name": "dns", "port_mappings": ["tcp/53", "udp/53"], ...})
```

Como os modelos gerados usam o padrão `extra="ignore"` do Pydantic, passar
`protocol` numa escrita 4.7 **não** levanta erro — o campo é descartado antes do
envio. Audite as escritas de serviço ao fixar a linha 4.7.
