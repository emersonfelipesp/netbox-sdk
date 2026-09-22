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
| `executions` | `list`, `get`, `create` | `cancel`, `approve`, `reject`, `events`, `wait` |
| `execution-events` | `list`, `get` | — |

Os comandos em lote são `bulk-update` (`PUT`), `bulk-patch` (`PATCH`) e
`bulk-delete` (`DELETE`). Eles recebem um array JSON e sempre usam o caminho da
coleção.

## Procedimentos e comandos

```bash
nbx rpc procedures available --target-type dcim.device --json
nbx rpc procedures commands --id 6 --json
nbx rpc procedures commands --id 6 \
  --body-json '{"argv":["systemctl","status","nginx"]}' --confirm --json
```

Fornecer `--body-json` ou `--body-file` a `procedures commands` muda a requisição
de GET para POST e, portanto, exige `--confirm`.

## Intents e execuções

```bash
nbx rpc intents run --id 2 \
  --assigned-object-type dcim.device --assigned-object-id 42 \
  --params-json '{"service_slug":"nginx"}' --confirm --json

nbx rpc executions create \
  --body-json '{"procedure_id":6,"assigned_object_type":"dcim.device","assigned_object_id":42,"params":{}}' \
  --confirm --json
nbx rpc executions approve --id 100 --reason reviewed --confirm --json
nbx rpc executions reject --id 101 --reason unsafe --confirm --json
nbx rpc executions cancel --id 102 --confirm --json
nbx rpc executions events --id 100 --json
```

`--params-file` e `--body-file` são as alternativas em arquivo ao JSON inline.
O NetBox continua sendo a autoridade para admissão por JSON Schema, restrições
de alvo, permissões e política de aprovação.

Cada POST personalizado e cada escrita padrão confirma antes da construção do
cliente HTTP. Os comandos CRUD padrão também oferecem a visualização
`--dry-run`, sem cliente e com redação recursiva de segredos.

## Espera limitada

```bash
nbx rpc executions wait --id 100 --timeout 300 --interval 2 --json
```

Os dois limites devem ser finitos e maiores que zero. A espera termina em
`succeeded`, `failed`, `cancelled`, `rejected` ou `expired`; `approved` não é
terminal. Uma resposta HTTP de erro retorna imediatamente. Uma resposta de
sucesso não terminal ou malformada é consultada até o prazo e então gera erro
de timeout.

## Regras para automação

- Prefira `--json` em scripts.
- Use payloads em arquivo quando o histórico do shell não puder conter parâmetros.
- Nunca repita uma mutação apenas porque a renderização da resposta falhou;
  inspecione primeiro a execução.
- A descoberta genérica `nbx plugins ...` continua adequada para CRUD padrão de
  plugins de terceiros, mas não substitui os comandos explícitos de workflow RPC.
