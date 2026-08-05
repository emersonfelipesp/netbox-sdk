# Configuração de clientes de agente

Esta página conecta os componentes documentados em [Servidor MCP](index.md) a
dois clientes de agente concretos: Claude Code e Codex CLI. Ela pressupõe que
o `netbox-sdk` já está instalado com o extra `mcp`:

```bash
pip install 'netbox-sdk[mcp]'
```

ou, a partir de um checkout deste repositório:

```bash
pipx install '.[mcp]'
```

Qualquer um dos caminhos deve deixar `nbx-mcp` disponível no `PATH` —
confirme com `nbx-mcp --help` antes de continuar.

## O que o repositório já fornece

| Caminho | Finalidade | Cliente |
|---|---|---|
| `.mcp.json` | Registra `nbx-mcp` como servidor MCP stdio com escopo de projeto | Claude Code |
| `.codex/config.toml` | Registra `nbx-mcp` como servidor MCP com escopo de projeto | Codex CLI |
| `.claude/settings.json` | Hook `PreToolUse` que executa `scripts/check_nbx_write.py` antes do Bash | Claude Code |
| `.codex/hooks.json` | Mesmo hook, espelhado para o formato de hooks do Codex | Codex CLI |
| `.claude/skills/netbox-sdk-operations/` | O Skill `netbox-sdk-operations` (inspecionar → visualizar → executar → verificar) | Claude Code |
| `.codex/skills/netbox-sdk-operations/` | Mesmo conteúdo do Skill, espelhado para o Codex | Codex CLI |

Nenhum desses arquivos contém credenciais. O servidor MCP lê as credenciais
do NetBox a partir do perfil existente em `netbox_sdk.config` em tempo de
execução (veja [Autenticação](index.md#autenticacao)); o hook apenas
inspeciona o comando Bash prestes a rodar, sem tocar no NetBox.

## Claude Code

### Servidor MCP

O Claude Code descobre automaticamente servidores MCP com escopo de projeto a
partir de `.mcp.json` assim que o diretório de trabalho de uma sessão está
dentro deste repositório (ou de um de seus worktrees). Descoberta não é o
mesmo que conexão: na primeira vez que uma sessão inicia neste projeto, o
Claude Code pede uma aprovação única antes de efetivamente usar o
`netbox-sdk`. Se esse prompt for dispensado ou rolar para fora da tela, rode
`/mcp` dentro da sessão para aprová-lo explicitamente; se ele já foi
rejeitado antes, rode `claude mcp reset-project-choices` para limpar essa
decisão e fazer o prompt aparecer de novo. Depois de aprovado, confirme que
está registrado e acessível:

```bash
claude mcp list
```

`netbox-sdk` deve aparecer como conectado, não como `⏸ Pending approval`.

O `.mcp.json` foi gerado com `claude mcp add -s project netbox-sdk --
nbx-mcp` e tem este conteúdo:

```json
{
  "mcpServers": {
    "netbox-sdk": {
      "type": "stdio",
      "command": "nbx-mcp",
      "args": [],
      "env": {}
    }
  }
}
```

Para registrar o mesmo servidor fora deste repositório (por exemplo, contra
outro checkout, ou com um transporte diferente do padrão), use `-s user` para
um registro em nível de máquina em vez de `-s project`:

```bash
claude mcp add -s user netbox-sdk -- nbx-mcp
```

### Hooks

O `.claude/settings.json` é carregado automaticamente em qualquer sessão do
Claude Code cujo diretório de trabalho seja este repositório — não há etapa
separada de confiança ou registro. O hook `PreToolUse` roda antes de cada
chamada da ferramenta Bash e bloqueia mutações `nbx` não confirmadas (veja
[Segurança de mutações](index.md#seguranca-de-mutacoes) e
[`scripts/check_nbx_write.py`](https://github.com/emersonfelipesp/netbox-sdk/blob/main/scripts/check_nbx_write.py)).

### Skill

O Skill `netbox-sdk-operations` em `.claude/skills/` é descoberto da mesma
forma — sem etapa de instalação. Invoque-o explicitamente com
`/netbox-sdk-operations` ou deixe o Claude Code selecioná-lo automaticamente
com base no frontmatter `description` quando uma tarefa do NetBox estiver em
escopo.

## Codex CLI

### Servidor MCP

O Codex CLI suporta registro de MCP com escopo de projeto através do
`.codex/config.toml`, espelhando o `.mcp.json` do Claude Code. Este
repositório já traz um:

```toml
[mcp_servers.netbox-sdk]
command = "nbx-mcp"
default_tools_approval_mode = "writes"
```

O `.codex/config.toml`, como qualquer outro arquivo em `.codex/`, só é
carregado quando o diretório do projeto está
[confiável](#hooks-exigem-duas-etapas-de-confianca-separadas). Mantenha o
servidor com escopo de projeto em vez de registrá-lo globalmente: o
`nbx-mcp` lê o perfil do NetBox de quem o chama, e uma entrada global via
`codex mcp add` em `~/.codex/config.toml` fica ativa em todos os projetos do
Codex, inclusive nos não confiáveis, o que amplia desnecessariamente a
exposição da ferramenta. Só recorra ao registro global se você
deliberadamente quiser o `netbox-sdk` disponível fora deste repositório:

```bash
codex mcp add netbox-sdk -- nbx-mcp
codex mcp list
```

### Hooks exigem duas etapas de confiança separadas

O Codex CLI condiciona o `.codex/` à **confiança do projeto** e, separadamente,
condiciona cada definição de hook a uma **revisão baseada em hash** — as duas
etapas precisam passar antes que o `.codex/hooks.json` realmente rode.

1. **Confiança do projeto.** O Codex desabilita configuração local do
   projeto, hooks e políticas de execução para qualquer diretório que não
   esteja marcado como confiável — apenas os Skills continuam carregando em
   um projeto não confiável. A confiança é indexada pelo caminho exato do
   diretório, então um worktree em um caminho diferente do seu clone
   canônico precisa da própria entrada de confiança; confiar apenas no clone
   canônico deixa a camada `.codex/` do worktree sem carregar. Conceda
   confiança de forma interativa no primeiro uso dentro de cada checkout que
   você usar, ou de forma não interativa adicionando uma entrada por caminho
   em `~/.codex/config.toml`:

   ```toml
   [projects."/caminho/para/netbox-sdk"]
   trust_level = "trusted"

   [projects."/caminho/para/netbox-sdk.worktrees/algum-branch"]
   trust_level = "trusted"
   ```

2. **Revisão do hook.** Mesmo em um projeto confiável, o Codex exige que
   você revise e confie no conteúdo exato de um hook de comando não
   gerenciado antes que ele possa rodar, através do comando `/hooks` dentro
   de uma sessão. A confiança é registrada com base no hash do conteúdo
   atual da definição do hook, então qualquer edição futura em
   `.codex/hooks.json` revoga a confiança até que você o revise novamente
   com `/hooks`.

Verifique se as duas etapas foram concluídas executando um comando de
mutação `nbx` reconhecível através do Codex sem `--confirm` — ele deve ser
bloqueado pelo `check_nbx_write.py` com a mensagem de status
`Checking nbx mutation confirmation`, em vez de rodar sem verificação. Se ele
rodar sem verificação, reconfira a confiança do projeto para o caminho exato
em uso e rode `/hooks` para confirmar que o hook está listado como
confiável.

### Skill

`.codex/skills/netbox-sdk-operations/` espelha o Skill do Claude Code byte a
byte e carrega independentemente do nível de confiança do projeto. O arquivo
`agents/openai.yaml` na cópia do Claude Code é metadado próprio do
[marketplace de Agent Skills da Claude](https://docs.claude.com/en/docs/claude-code/skills) —
não tem equivalente no Codex e não precisa ter.

## Verificando a configuração completa

1. `nbx-mcp --help` sai com código 0 — o extra `mcp` está instalado.
2. A partir de dentro deste repositório, `claude mcp list` mostra `netbox-sdk`
   como conectado (aprove via `/mcp` primeiro se ainda aparecer pendente), e
   `codex mcp list` mostra `netbox-sdk` assim que o diretório do projeto
   estiver confiável.
3. `nbx capabilities --json` (ou as ferramentas MCP `list_groups`/
   `list_resources`) retorna o contrato de ferramentas/recursos guiado por
   schema descrito em [Servidor MCP](index.md#ferramentas).
4. Uma mutação não confirmada tentada por uma chamada da ferramenta Bash
   (por exemplo, `nbx dcim devices create ...` sem `--confirm`) é bloqueada
   pelo hook `PreToolUse` em ambos os clientes — veja
   [Segurança de mutações](index.md#seguranca-de-mutacoes) para o gate em
   nível de CLI que esse hook reforça.
