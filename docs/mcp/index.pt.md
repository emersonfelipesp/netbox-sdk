# Servidor MCP

O `netbox_mcp` oferece uma superfície pequena do Model Context Protocol sobre o
mesmo `SchemaIndex`, resolvedor de requisições, descoberta de plugins,
paginação, cliente e configuração de perfis usados pelo SDK e pela CLI. Ele não
gera uma ferramenta por operação OpenAPI, portanto a lista de ferramentas
permanece estável quando plugins mudam os recursos disponíveis.

## Instalação e execução

```bash
pip install 'netbox-sdk[mcp]'
nbx-mcp
```

stdio é o transporte padrão. Para Streamable HTTP:

```bash
nbx-mcp --transport streamable-http --host 127.0.0.1 --port 8000
```

O endpoint MCP é `/mcp`. Use uma interface confiável e aplique autenticação de
transporte e TLS quando o serviço for exposto além do host local.

## Ferramentas

| Ferramenta | Comportamento |
|---|---|
| `list_groups`, `list_resources`, `describe_operation` | Introspecção JSON estável; `live=true` inclui recursos em runtime |
| `list`, `get` | Leituras resolvidas pelo schema; `list` suporta paginação e filtros repetidos |
| `filters` | Introspecção local sem requisição HTTP |
| `create`, `update`, `patch`, `delete` | Mutações desabilitadas por padrão |
| `bulk_update`, `bulk_patch`, `bulk_delete` | Mutações em lote desabilitadas por padrão |
| `plugin_discover` | Enriquece o schema ativo com descoberta de plugins |
| `call` | Escape hatch relativo a `/api/`; somente GET/HEAD com o gate fechado |

Cada entrada é validada por um schema Pydantic explícito antes do despacho.

## Autenticação

No stdio, o servidor lê o perfil padrão existente de `netbox_sdk.config`; não
há um segundo armazenamento de credenciais. Ferramentas que acessam o NetBox
também aceitam um token bearer por chamada. Não coloque tokens em logs,
transcrições visíveis ao modelo ou configurações versionadas.

## Segurança de mutações

Escritas reais são negadas por padrão. Primeiro visualize a requisição com
`dry_run=true`; depois abra uma janela de execução explícita com:

```bash
NETBOX_MCP_ALLOW_MUTATIONS=1 nbx-mcp
nbx-mcp --allow-mutations
```

`dry_run=true` resolve método, caminho, query e corpo localmente sem construir
um cliente. Não é validação no servidor e não prova que a chamada real terá
sucesso.

Hooks locais do Claude Code e do Codex também bloqueiam operações CLI `nbx` de
criação, atualização, patch, remoção e lote, salvo quando o comando revisado é
prefixado com `NETBOX_SDK_CONFIRM_WRITE=1`.

## Sequência operacional para agentes

1. Inspecione `nbx capabilities --json` ou chame `list_groups`,
   `list_resources` e `describe_operation`.
2. Visualize toda escrita com `--dry-run` ou `dry_run=true`.
3. Habilite/confirme explicitamente apenas a operação revisada e execute-a.
4. Verifique o resultado com `get` ou um `list` filtrado.

O repositório fornece esse procedimento no Skill espelhado
`netbox-sdk-operations`, em `.claude/skills/` e `.codex/skills/`.
