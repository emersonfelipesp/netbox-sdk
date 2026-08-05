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
dentro deste repositório (ou de um de seus worktrees) — nenhuma etapa extra é
necessária além de deixar `nbx-mcp` no `PATH`. Para confirmar que está
registrado e acessível:

```bash
claude mcp list
```

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

O Codex CLI não tem um arquivo de registro de MCP com escopo de projeto
equivalente ao `.mcp.json`; servidores MCP são sempre registrados
globalmente em `~/.codex/config.toml`:

```bash
codex mcp add netbox-sdk -- nbx-mcp
codex mcp list
```

### Hooks exigem confiança do projeto

Diferente do Claude Code, o Codex CLI desabilita **configuração local do
projeto, hooks e políticas de execução** para qualquer diretório que não
esteja marcado como confiável — apenas os Skills continuam carregando em um
projeto não confiável. Isso significa que `.codex/hooks.json` silenciosamente
não faz nada até que o diretório do projeto seja marcado como confiável.
Conceda confiança de forma interativa no primeiro uso dentro do repositório,
ou de forma não interativa adicionando uma entrada em
`~/.codex/config.toml`:

```toml
[projects."/caminho/para/netbox-sdk"]
trust_level = "trusted"
```

Use o caminho do seu checkout real (o clone canônico, não um worktree
descartável). Verifique se o hook está ativo executando um comando de mutação
`nbx` reconhecível através do Codex sem `--confirm` — ele deve ser bloqueado
pelo `check_nbx_write.py` com a mensagem de status
`Checking nbx mutation confirmation`, em vez de rodar sem verificação.

### Skill

`.codex/skills/netbox-sdk-operations/` espelha o Skill do Claude Code byte a
byte e carrega independentemente do nível de confiança do projeto. O arquivo
`agents/openai.yaml` na cópia do Claude Code é metadado próprio do
[marketplace de Agent Skills da Claude](https://docs.claude.com/en/docs/claude-code/skills) —
não tem equivalente no Codex e não precisa ter.

## Verificando a configuração completa

1. `nbx-mcp --help` sai com código 0 — o extra `mcp` está instalado.
2. `claude mcp list` (a partir de dentro deste repositório) e `codex mcp list`
   mostram `netbox-sdk` como `enabled`.
3. `nbx capabilities --json` (ou as ferramentas MCP `list_groups`/
   `list_resources`) retorna o contrato de ferramentas/recursos guiado por
   schema descrito em [Servidor MCP](index.md#ferramentas).
4. Uma mutação não confirmada tentada por uma chamada da ferramenta Bash
   (por exemplo, `nbx dcim devices create ...` sem `--confirm`) é bloqueada
   pelo hook `PreToolUse` em ambos os clientes — veja
   [Segurança de mutações](index.md#seguranca-de-mutacoes) para o gate em
   nível de CLI que esse hook reforça.
