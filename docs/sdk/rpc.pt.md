# Plugin RPC

`netbox_sdk.rpc` fornece o contrato Python mantido para o plugin oficialmente
suportado `netbox-rpc`. `netbox_sdk.plugins` identifica `netbox-rpc` e
`netbox-proxbox` como integrações de primeira classe; outros plugins continuam
disponíveis por descoberta em tempo de execução quando operações REST padrão
são suficientes.

## Registro de suporte oficial

```python
from netbox_sdk import official_plugin, official_plugins

assert [plugin.package for plugin in official_plugins()] == [
    "netbox-rpc",
    "netbox-proxbox",
]
rpc_plugin = official_plugin("rpc")
assert rpc_plugin is not None
assert rpc_plugin.sdk_module == "netbox_sdk.rpc"
```

O registro é descritivo e imutável. Ele não desativa a descoberta genérica de
plugins nem implica que cada plugin descoberto tenha métodos de workflow mantidos.

## Especificações das coleções

`rpc_resources()` retorna nove valores imutáveis `RPCResourceSpec` para
configurações, backends, procedimentos, comandos de procedimento, intents, a
lista de serviços Linux permitidos, a lista de plugins NetBox permitidos,
execuções e eventos de execução. Cada especificação possui caminhos de
lista/detalhe e métodos permitidos; `supported_actions` deriva as ações do SDK e
da CLI. As duas coleções de listas permitidas expõem toda a superfície padrão de
escrita REST do NetBox; a validação e as permissões do servidor continuam sendo
autoritativas.

Use `build_rpc_schema_index()` para um índice isolado somente de RPC ou
`register_rpc_resources(index)` para adicionar o contrato fixo a um
`SchemaIndex` existente. Isso evita uma sondagem de rede e impede que a
descoberta genérica tente adivinhar semânticas de workflow.

## Requisições padrão e em lote

```python
import asyncio

from netbox_sdk import Config, NetBoxApiClient, RPCClient


async def main() -> None:
    config = Config(
        base_url="https://netbox.example.com",
        token_version="v1",
        token_secret="token",
    )
    async with NetBoxApiClient(config) as transport:
        rpc = RPCClient(transport)
        backends = await rpc.request("backends", "list", query={"limit": 50})
        backend = await rpc.request("backends", "get", object_id=7)
        updated = await rpc.request(
            "backends", "patch", object_id=7, payload={"verify_ssl": True}
        )
        batch = await rpc.request(
            "backends", "bulk-patch", payload=[{"id": 7, "verify_ssl": True}]
        )
        procedure = await rpc.request(
            "procedures",
            "create",
            payload={
                "name": "service-status",
                "handler_id": "linux.service.status",
                "version": "1.0",
                "target_models": ["dcim.device"],
                "effect": "read",
                "params_schema": {"type": "object"},
            },
        )
        intents = await rpc.request(
            "intents",
            "create",
            payload=[
                {
                    "name": "inspect-service",
                    "execution_mode": "sequential",
                    "procedure_ids": [6],
                }
            ],
        )


asyncio.run(main())
```

Pares recurso/ação incompatíveis falham antes do envio HTTP. Ações em lote
recebem um array e usam o caminho da coleção. O `create` da coleção aceita um
objeto ou um array, conforme o POST individual ou em lote padrão do NetBox.

## Métodos de workflow

```python
import asyncio

from netbox_sdk import Config, NetBoxApiClient, RPCClient


async def main() -> None:
    config = Config(
        base_url="https://netbox.example.com",
        token_version="v1",
        token_secret="token",
    )
    async with NetBoxApiClient(config) as transport:
        rpc = RPCClient(transport)
        available = await rpc.available_procedures(
            target_type="dcim.device", query={"limit": 100}
        )
        commands = await rpc.procedure_commands(6, query={"limit": 100})
        command_result = await rpc.procedure_commands(6, payload={"argv": ["true"]})
        execution = await rpc.run_intent(
            2,
            assigned_object_type="dcim.device",
            assigned_object_id=42,
            params={"service_slug": "nginx"},
        )
        approved = await rpc.execution_action(100, "approve", reason="reviewed")
        rejected = await rpc.execution_action(101, "reject", reason="unsafe")
        cancelled = await rpc.execution_action(102, "cancel")
        events = await rpc.execution_events(100, query={"limit": 100})
        terminal = await rpc.wait_for_execution(100, timeout=300, interval=2)


asyncio.run(main())
```

`execution_action()` aceita somente `cancel`, `approve` e `reject`.
`wait_for_execution()` exige limites finitos e positivos e termina em
`succeeded`, `failed`, `cancelled`, `rejected` ou `expired`; `approved` continua
não terminal. Erros HTTP retornam imediatamente. Uma resposta de sucesso não
terminal ou malformada é consultada até o prazo e então gera `TimeoutError`.
Cada consulta ignora o cache HTTP normal. As consultas personalizadas aceitam
mapeamentos com chaves repetidas; o POST de comando de procedimento rejeita
parâmetros de consulta em vez de ignorá-los silenciosamente.

## Segurança e manutenção

O NetBox controla permissões, restrições de alvo, admissão por JSON Schema,
exigências de aprovação e registros de auditoria. O chamador controla a
confirmação de mutações; a camada `nbx rpc` a exige antes da construção do
cliente. Não registre tokens, parâmetros com credenciais nem corpos secretos.

Quando o contrato do plugin mudar, atualize `RPC_RESOURCES`, os métodos
semânticos, os testes exatos de transporte do SDK e da CLI, os dois guias RPC
bilingues e os arquivos de agente raiz e de subsistema na mesma mudança revisada.
