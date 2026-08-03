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
nbx-mcp --transport streamable-http --host 127.0.0.1 --port 8000 --auth-token "$NETBOX_MCP_AUTH_TOKEN"
```

O endpoint MCP é `/mcp`. Todo vínculo Streamable HTTP exige um token bearer
compartilhado via `--auth-token` ou `NETBOX_MCP_AUTH_TOKEN`; o servidor
levanta `RuntimeError` e recusa iniciar sem ele, inclusive em hosts loopback
(`127.0.0.1`, `localhost`, `::1`). Vincular a loopback restringe apenas a
*alcançabilidade* a esta máquina — não *autentica* outros processos ou
usuários locais, que de outra forma poderiam acessar a credencial NetBox
carregada pelo servidor (e qualquer janela `--allow-mutations` ativa) sem
autenticação em um host de desenvolvimento ou bastion compartilhado. Aplique
terminação TLS na frente do serviço quando ele for exposto além do host
local — o token bearer autentica quem chama, não criptografa o transporte.

Esse gate não pode ser contornado chamando o objeto do servidor diretamente
em vez de passar por `run()`: `create_mcp_server()` sempre substitui o
`streamable_http_app` do servidor retornado por um wrapper que aplica o
mesmo `auth_token`, levantando `RuntimeError` inclusive quando nenhum token
foi configurado. Não existe caminho de código — `run("streamable-http")`,
`streamable_http_app()` ou qualquer outro — que produza um app Streamable
HTTP sem autenticação a partir de uma instância criada por
`create_mcp_server()`.

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

Esse token do NetBox por chamada é distinto do token bearer do próprio
transporte Streamable HTTP (`--auth-token`/`NETBOX_MCP_AUTH_TOKEN`, descrito
acima): o token de transporte autentica *quem chama o MCP* perante *este
servidor*, enquanto o token por chamada autentica *este servidor* perante o
*NetBox*.

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
