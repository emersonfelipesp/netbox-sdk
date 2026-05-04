# Tratamento de erros

---

## RequestError

`request()` **não** levanta em códigos de status não-2xx por padrão — retorna um `ApiResponse` com o código de status. Inspecione o status você mesmo:

```python
response = await client.request("GET", "/api/dcim/devices/99/")

if response.status == 404:
    print("Device not found")
elif response.status == 403:
    print("Forbidden — check your token")
elif response.status >= 500:
    print(f"Server error: {response.text}")
elif response.status == 200:
    device = response.json()
```

`RequestError` é levantada apenas por `get_version()`:

```python
from netbox_sdk import RequestError

try:
    version = await client.get_version()
except RequestError as exc:
    print(f"HTTP {exc.response.status}: {exc.response.text}")
```

A camada de fachada levanta `RequestError` para operações de endpoint falhas como
`await nb.dcim.devices.get(1)` quando a resposta não é um caso de sucesso tratado.

---

## Exceções específicas da fachada

A fachada de alto nível adiciona algumas exceções explícitas para fluxos comuns do NetBox SDK.

### ParameterValidationError

Levantada quando validação estrita de filtro está habilitada e um nome de filtro não está presente
no esquema OpenAPI:

```python
from netbox_sdk import ParameterValidationError, api

nb = api("https://netbox.example.com", token="tok", strict_filters=True)

try:
    nb.dcim.devices.filter(not_a_real_filter="value")
except ParameterValidationError as exc:
    print(exc)
```

### AllocationError

Levantada para endpoints de detalhe de alocação quando o NetBox retorna HTTP 409:

```python
from netbox_sdk import AllocationError

prefix = await nb.ipam.prefixes.get(123)

try:
    await prefix.available_prefixes.create({"prefix_length": 28})
except AllocationError as exc:
    print(exc)
```

### ContentError

Levantada quando a fachada espera JSON mas o servidor retorna conteúdo inválido:

```python
from netbox_sdk import ContentError

try:
    plugins = await nb.plugins.installed_plugins()
except ContentError:
    print("NetBox returned invalid JSON")
```

---

## ConnectionProbe

Use `probe_connection()` antes de chamadas à API para validar conectividade e expor erros legíveis:

```python
probe = await client.probe_connection()

if not probe.ok:
    # Casos comuns:
    # probe.status == 0  → rede inacessível (falha DNS, TCP, TLS)
    # probe.status == 404 → base_url aponta para caminho errado
    # probe.status == 401 → auth rejeitada (token inválido)
    print(f"Cannot reach NetBox (HTTP {probe.status}): {probe.error}")
    return

print(f"NetBox API version: {probe.version}")
```

Campos de `ConnectionProbe`:

| Campo | Tipo | Significado |
|-------|------|-------------|
| `ok` | `bool` | `True` se NetBox acessível (status < 400, ou 403) |
| `status` | `int` | Código HTTP; `0` em falha de rede |
| `version` | `str` | Valor do cabeçalho de resposta `API-Version` |
| `error` | `str \| None` | Erro legível, ou `None` se `ok` é `True` |

Nota: 403 conta como `ok=True` porque significa URL válida — apenas o token está errado.

---

## Erros de rede

Falhas de nível de rede (falha DNS, timeout TCP, erro TLS) são levantadas como exceções de `request()`. O cliente as captura internamente quando existe entrada de cache obsoleta; caso contrário propagam:

```python
import aiohttp

try:
    response = await client.request("GET", "/api/dcim/devices/")
except aiohttp.ClientConnectorError as exc:
    print(f"Cannot connect: {exc}")
except TimeoutError:
    print("Request timed out")
```

Se existir entrada de cache obsoleta para a requisição falha, `request()` retorna a resposta obsoleta com `X-NBX-Cache: STALE` em vez de levantar.

---

## Configuração de timeout

O timeout padrão é 30 segundos. Ajuste por conexão:

```python
from netbox_sdk import Config

cfg = Config(
    base_url="https://netbox.example.com",
    token_version="v1",
    token_secret="tok",
    timeout=10.0,   # 10 segundos
)
```

---

## Configuração ausente

Verifique completude antes de chamadas:

```python
from netbox_sdk.config import is_runtime_config_complete

cfg = Config(base_url="https://nb.example.com", token_version="v2", token_secret="s")
if not is_runtime_config_complete(cfg):
    # Para v2: falta token_key
    # Para v1: falta token_secret
    # Para ambos: falta base_url
    raise RuntimeError("Incomplete configuration")
```

`build_url()` levanta `RuntimeError("NetBox base URL is not configured")` se `base_url` for `None`.

---

## Erros de resolução de esquema

```python
from netbox_sdk.services import resolve_dynamic_request

try:
    req = resolve_dynamic_request(idx, "dcim", "typo", "list", ...)
except ValueError as exc:
    print(exc)   # "Resource not found: dcim/typo"

try:
    req = resolve_dynamic_request(idx, "dcim", "devices", "get", object_id=None, ...)
except ValueError as exc:
    print(exc)   # "Action 'get' requires --id"
```

---

## Erros de análise JSON

`ApiResponse.json()` levanta `json.JSONDecodeError` se o corpo da resposta não for JSON válido. Sempre verifique o código de status primeiro — respostas de erro (4xx/5xx) às vezes são HTML:

```python
response = await client.request("GET", "/api/dcim/devices/")
if response.status == 200:
    data = response.json()
else:
    print(f"Error {response.status}: {response.text[:200]}")
```

A fachada envolve este caso como `ContentError` quando uma operação de alto nível
exige decodificação JSON.

---

## Erros de validação do SDK tipado

O cliente tipado adiciona falhas de validação explícitas com Pydantic.

### TypedRequestValidationError

Levantada antes do HTTP quando o corpo da requisição não corresponde ao modelo de requisição
versionado para a linha de release NetBox selecionada.

```python
from netbox_sdk import TypedRequestValidationError, typed_api

nb = typed_api("https://netbox.example.com", token="tok", netbox_version="4.5")

try:
    await nb.ipam.prefixes.available_ips.create(7, body=[{"prefix_length": "invalid"}])
except TypedRequestValidationError as exc:
    print(exc)
```

### TypedResponseValidationError

Levantada depois do HTTP quando o NetBox retorna JSON que não corresponde ao modelo de
resposta tipado esperado.

```python
from netbox_sdk import TypedResponseValidationError

try:
    await nb.dcim.devices.get(42)
except TypedResponseValidationError as exc:
    print(exc)
```
