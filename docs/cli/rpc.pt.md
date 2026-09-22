# RPC

`nbx rpc` é a superfície de comandos mantida para o plugin oficialmente
suportado `netbox-rpc`. Ela combina operações REST padrão conforme a política
com comandos de workflow que a descoberta OpenAPI genérica não consegue inferir.

## Contrato das coleções

| Coleção | Comandos padrão | Comandos de workflow |
|---|---|---|
| `settings` | `list`, `get`, `patch` | — |
| `backends` | list/get/create/update/patch/delete e as três escritas em lote | — |
| `procedures` | list/get/create/update/patch/delete e as três escritas em lote | `available`, `commands` |
| `procedure-commands` | list/get/create/update/patch/delete e as três escritas em lote | — |
| `intents` | list/get/create/update/patch/delete e as três escritas em lote | `run` |
| `linux-service-allowlist` | list/get/create/update/patch/delete e as três escritas em lote | — |
| `netbox-plugin-allowlist` | list/get/create/update/patch/delete e as três escritas em lote | — |
| `executions` | `list`, `get`, `create` | `cancel`, `approve`, `reject`, `events`, `wait` |
| `execution-events` | `list`, `get` | — |

Os comandos em lote são `bulk-update` (`PUT`), `bulk-patch` (`PATCH`) e
`bulk-delete` (`DELETE`). Eles recebem um array JSON e sempre usam o caminho da
coleção. O POST padrão de coleção do NetBox também aceita um array, portanto o
comando comum `create` cria tanto um registro quanto vários registros em lote.

## Procedimentos e comandos

```bash
nbx rpc procedures create \
  --body-json '{"name":"service-status","handler_id":"linux.service.status","version":"1.0","enabled":true,"target_models":["dcim.device"],"effect":"read","timeout_seconds":30,"approval_required":false,"params_schema":{"type":"object"}}' \
  --confirm --json
nbx rpc procedures get --id 6 --json
nbx rpc procedures patch --id 6 \
  --body-json '{"description":"Read one systemd service state"}' \
  --confirm --json
nbx rpc procedures available --target-type dcim.device -q limit=100 --json
nbx rpc procedures commands --id 6 -q limit=100 --json
nbx rpc procedures commands --id 6 \
  --body-json '{"argv":["systemctl","status","nginx"]}' --confirm --json
nbx rpc procedures delete --id 6 --confirm --json
```

Fornecer `--body-json` ou `--body-file` a `procedures commands` muda a requisição
de GET para POST e, portanto, exige `--confirm`. `-q` / `--query` pode ser
repetido na forma de leitura e preserva chaves repetidas; um POST de criação de
comando rejeita opções de consulta em vez de descartá-las silenciosamente. Os
comandos de procedimento também podem ser gerenciados integralmente pela
coleção independente `procedure-commands`.

## Intents e execuções

```bash
nbx rpc intents create \
  --body-json '{"name":"inspect-service","execution_mode":"sequential","enabled":true,"procedure_ids":[6]}' \
  --confirm --json
nbx rpc intents get --id 2 --json
nbx rpc intents update --id 2 \
  --body-json '{"name":"inspect-service","execution_mode":"parallel","enabled":true,"procedure_ids":[6,7]}' \
  --confirm --json
nbx rpc intents patch --id 2 --body-json '{"enabled":false}' --confirm --json
nbx rpc intents run --id 2 \
  --assigned-object-type dcim.device --assigned-object-id 42 \
  --params-json '{"service_slug":"nginx"}' --confirm --json

nbx rpc executions create \
  --body-json '{"procedure_id":6,"assigned_object_type":"dcim.device","assigned_object_id":42,"params":{}}' \
  --confirm --json
nbx rpc executions approve --id 100 --reason reviewed --confirm --json
nbx rpc executions reject --id 101 --reason unsafe --confirm --json
nbx rpc executions cancel --id 102 --confirm --json
nbx rpc executions events --id 100 -q limit=100 --json
```

`--params-file` e `--body-file` são as alternativas em arquivo ao JSON inline.
O NetBox continua sendo a autoridade para admissão por JSON Schema, restrições
de alvo, permissões e política de aprovação.

Cada POST personalizado e cada escrita padrão confirma antes da construção do
cliente HTTP. Os comandos CRUD padrão também oferecem a visualização
`--dry-run`, sem cliente e com redação recursiva de segredos.

Use os mesmos comandos padrão para `backends`, `procedure-commands`,
`linux-service-allowlist` e `netbox-plugin-allowlist`. A última coleção gerencia
as distribuições, os módulos, os caminhos e os serviços controlados pelo
servidor que os procedimentos RPC de instalação de plugins podem usar; o
servidor continua sendo a autoridade para validação e permissões. O servidor
restringe intencionalmente `settings` a list/get/patch, `executions` a list/get/create e
`execution-events` a list/get; `nbx rpc` não anuncia mutações incompatíveis.

## Espera limitada

```bash
nbx rpc executions wait --id 100 --timeout 300 --interval 2 --json
```

Os dois limites devem ser finitos e maiores que zero. A espera termina em
`succeeded`, `failed`, `cancelled`, `rejected` ou `expired`; `approved` não é
terminal. Uma resposta HTTP de erro retorna imediatamente. Uma resposta de
sucesso não terminal ou malformada é consultada até o prazo e então gera erro
de timeout.
Cada consulta ignora o cache normal de respostas para observar as transições
de estado no intervalo solicitado.

## Regras para automação

- Prefira `--json` em scripts.
- Use payloads em arquivo quando o histórico do shell não puder conter parâmetros.
- Nunca repita uma mutação apenas porque a renderização da resposta falhou;
  inspecione primeiro a execução.
- A descoberta genérica `nbx plugins ...` continua adequada para CRUD padrão de
  plugins de terceiros, mas não substitui os comandos explícitos de workflow RPC.
