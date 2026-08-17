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

### NetBox 4.7 (preview) — mapeamentos de porta de serviços

O NetBox 4.7 adiciona `port_mappings`, permitindo que um serviço exponha vários
protocolos ao mesmo tempo (DNS em `tcp/53` e `udp/53`). O par legado
`protocol` + `ports` continua válido na escrita: o serializer compartilhado do
upstream documenta que *"either format is accepted"*, traduzindo o par legado
para `port_mappings` quando `port_mappings` não é informado. Informar ambos só é
aceito quando concordam; um conflito real é rejeitado como ambíguo.

```python
# Ainda aceito no 4.7 — traduzido no servidor para port_mappings
api.ipam.services.create({"name": "ssh", "protocol": "tcp", "ports": [22], ...})

# Forma nativa do 4.7, e a única maneira de expressar múltiplos protocolos
api.ipam.services.create({"name": "dns", "port_mappings": ["tcp/53", "udp/53"], ...})
```

Na leitura, um serviço de protocolo único reporta `port_mappings` **e** os campos
legados `protocol`/`ports`; um serviço multiprotocolo reporta `null` para ambos,
pois não pode ser expresso no formato antigo.

> **Nota de geração.** O `drf-spectacular` omite `protocol` do bloco
> `properties` dos modelos *graváveis* de serviço, embora o contrato de escrita
> documentado o aceite. O `netbox-sdk` o restaura com um overlay determinístico
> de geração (`scripts/generate_typed_sdk.py::apply_write_compat_overlay`)
> aplicado apenas em memória — o bundle OpenAPI versionado permanece fiel byte a
> byte ao artefato upstream fixado. Sem ele, um PATCH de
> `{"protocol": "udp", "ports": [53]}` seria enviado como `{"ports": [53]}` e o
> NetBox repreencheria o protocolo armazenado, ignorando silenciosamente a
> alteração.
