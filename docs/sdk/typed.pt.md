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

A integração contínua exercita a suíte live-NetBox contra `v4.7.0-beta2`, `v4.6.6`, `v4.6.3`, `v4.6.2` e `v4.5.10`.

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

### Respostas em lote são validadas conforme o formato retornado pelo servidor

O NetBox reutiliza o caminho da coleção para operações em lote. Enviar um
objeto **único** retorna aquele objeto; enviar uma **lista** confirma o lote e
retorna uma **lista**. O documento OpenAPI upstream declara apenas a resposta
singular para esse caminho, então os bindings gerados declaram apenas o modelo
singular:

```python
async def create(self, body: WritableSiteRequest | list[WritableSiteRequest]) -> Site: ...
```

Por isso o runtime seleciona o modelo de resposta a partir do formato do corpo
da requisição: um corpo de lista é validado como `list[Model]`, e um corpo único
como `Model`. Sem isso, um lote já confirmado levantaria
`TypedResponseValidationError` *depois de o servidor já ter aplicado todos os
objetos* — e a reação natural, tentar de novo, criaria duplicatas.

Isso vale igualmente para `POST`, `PUT` (`bulk-update`) e `PATCH`
(`bulk-patch`), pois todos passam pelo mesmo caminho de requisição. O `DELETE`
em lote responde com `204` sem corpo, então não há nada a validar e a chamada
retorna `None`.

### Operações em lote em segundo plano (NetBox 4.7)

O NetBox 4.7 aceita `?background=true` em `POST`/`PUT`/`PATCH`/`DELETE` em lote.
O lote é enfileirado em vez de executado na hora, e a resposta é um `202` com uma
referência de job em vez dos objetos confirmados — o recurso existe para evitar
timeouts de proxy em lotes grandes.

```python
result = await api.dcim.sites.create(
    body=[{"name": "B1", "slug": "b1"}, {"name": "B2", "slug": "b2"}],
    query={"background": True},
)
result.job.id      # 4211
result.job.status  # "pending"
```

O runtime seleciona o modelo de resposta a partir da requisição: um `background`
afirmativo resulta em `BackgroundJobReference`, e isso tem precedência sobre o
formato do corpo, porque um lote enfileirado retorna um job tanto para um objeto
único quanto para uma lista. Sem a flag, nada muda.

> **Isto é um overlay, enquanto o schema upstream não descreve o recurso.** O
> artefato 4.7 fixado (`v4.7.0-beta2`) não descreve o parâmetro, então o gerador
> o declara em escritas bulk com corpo JSON em array, mantendo o bundle
> versionado fiel byte a byte ao upstream. Caminhos de coleção singulares, como
> o dashboard de extras, não recebem o overlay. Um teste de guarda falha assim
> que um schema 4.7 atualizado descrever `background`, de modo que o overlay
> não sobreviva ao seu motivo de existir.

## Artefatos gerados

O repositório inclui bundles OpenAPI versionados, modelos Pydantic gerados e
bindings tipados de endpoints gerados para as linhas de release suportadas. Não é
necessário executar geração de código localmente.

Módulos relevantes:

- `netbox_sdk.models.v4_6`
- `netbox_sdk.models.v4_7` (preview)
- `netbox_sdk.models.v4_5`
- `netbox_sdk.models.v4_4`
- `netbox_sdk.models.v4_3`
- `netbox_sdk.typed_versions.v4_6`
- `netbox_sdk.typed_versions.v4_7` (preview)
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
