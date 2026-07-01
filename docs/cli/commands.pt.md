# Comandos

Todos os comandos `nbx` de nível superior. Execute qualquer comando com `--help` para a lista completa de opções.

---

## `nbx init`

Configuração interativa do perfil default. Solicita URL NetBox, chave do token,
segredo do token e timeout. Salva em `~/.config/netbox-sdk/config.json`.

Arquivos antigos `~/.config/netbox-cli/config.json` ainda são lidos automaticamente se uma
nova config NetBox SDK ainda não foi gravada.

```bash
nbx init
```

Qualquer comando que precise de conexão também dispara esse prompt automaticamente se a config estiver ausente.

---

## `nbx config`

Exibe a configuração do perfil default atual.

```bash
nbx config
nbx config --show-token   # revela chave e segredo do token
```

**Opções**

| Flag | Descrição |
|------|-------------|
| `--show-token` | Inclui chave e segredo do token na saída (texto plano) |

---

## `nbx test`

Testa a conectividade com a instância NetBox configurada (perfil default). Também
verifica se existe um build do grafo de modelos Django para a versão NetBox detectada,
usado pelo `nbx dev django-model`.

```bash
nbx test
nbx test --fetch    # clonar e construir do GitHub se nenhum build correspondente for encontrado
```

**Opções**

| Flag | Descrição |
|------|-------------|
| `--fetch` / `-f` | Se não existir um build de modelo Django para a versão detectada, clonar do GitHub e construí-lo automaticamente |

---

## `nbx groups`

Lista todos os grupos de app OpenAPI disponíveis no esquema integrado.

```bash
nbx groups
```

A saída é um nome de grupo por linha: `circuits`, `core`, `dcim`, `extras`, `ipam`, `plugins`, `tenancy`, `users`, `virtualization`, `vpn`, `wireless`.

---

## `nbx resources GROUP`

Lista todos os recursos dentro de um grupo de app.

```bash
nbx resources dcim
nbx resources ipam
```

---

## `nbx ops GROUP RESOURCE`

Mostra todas as operações HTTP (método, caminho, ID da operação) para um recurso específico.

```bash
nbx ops dcim devices
nbx ops ipam prefixes
```

A saída é uma tabela Rich com colunas: **Method**, **Path**, **Operation ID**.

---

## `nbx call METHOD PATH`

Faz uma requisição HTTP explícita a qualquer caminho da API NetBox.

```bash
nbx call GET /api/status/
nbx call GET /api/dcim/sites/ --json
nbx call GET /api/dcim/sites/ --markdown
nbx call POST /api/ipam/ip-addresses/ --body-json '{"address":"192.0.2.1/24","status":"active"}'
nbx call PUT /api/dcim/devices/1/ --body-file ./device.json
```

**Opções**

| Flag | Descrição |
|------|-------------|
| `-q` / `--query KEY=VALUE` | Parâmetro de query string (repetível) |
| `--body-json TEXT` | Corpo JSON inline da requisição |
| `--body-file PATH` | Caminho para arquivo JSON como corpo |
| `--json` | Saída JSON bruta em vez de tabela Rich |
| `--yaml` | Saída YAML |
| `--markdown` | Respostas da API como Markdown com tabelas primeiro |

`--json`, `--yaml` e `--markdown` são mutuamente exclusivos.

---

## `nbx proxbox sync [ENDPOINT]`

Dispara um job de sincronização pelo plugin `netbox-proxbox` e transmite
Server-Sent Events até o job reportar conclusão. `ENDPOINT` é opcional; pode ser
a chave primária de um endpoint Proxmox ou o nome exato do endpoint. Omita para
sincronizar todos os endpoints Proxmox configurados.

```bash
nbx proxbox sync
nbx proxbox sync pve-prod -t virtual-machines -t storage
nbx proxbox sync 12 -t all --job-name nightly-proxbox-sync
nbx proxbox sync --json
```

A visão ao vivo mostra o job agendado, barras de progresso por fase, eventos
recentes do stream e um resumo final autoritativo. Depois que o stream termina,
a CLI busca `/api/core/jobs/{job_id}/` e combina erros do job e entradas de log
em nível de erro com erros transmitidos para não perder mensagens SSE removidas
por throttling no servidor.

**Opções**

| Flag | Descrição |
|------|-------------|
| `-t` / `--type TEXT` | Slug de tipo de sync Proxbox. Repita para múltiplos tipos. Padrão: `all` |
| `--job-name TEXT` | Nome opcional do job NetBox |
| `--timeout FLOAT` | Segundos máximos para manter o stream SSE aberto (padrão: `7200`) |
| `--json` | Ignora a UI ao vivo e emite JSON `{job_id,status,ok,errors,summary}` |

Tipos válidos: `virtual-machines`, `storage`, `vm-disks`, `vm-backups`,
`vm-snapshots`, `devices`, `network-interfaces`, `vm-interfaces`,
`ip-addresses`, `sdn`, `backup-routines`, `replications`, `task-history` e
`all`. O tipo `all` não pode ser combinado com nenhum outro tipo.

---

## `nbx proxbox sync-types`

Imprime os slugs de tipo de sync aceitos por `nbx proxbox sync`.

```bash
nbx proxbox sync-types
```

---

## `nbx graphql QUERY`

Executa uma consulta GraphQL contra a API NetBox.

```bash
# Consulta simples
nbx graphql "{ sites { name } }"

# Consulta com variáveis
nbx graphql "query($id: Int!) { device(id: $id) { name } }" --variables '{"id": 1}'

# Consulta com variáveis key=value
nbx graphql "query($name: String!) { devices(name: $name) { id } }" --variables name=sw01

# Várias variáveis (repita -v / --variables)
nbx graphql "query($a: Int!, $b: Int!) { __typename }" -v a=1 -v b=2

# Saída JSON
nbx graphql "{ sites { name } }" --json
```

**Opções**

| Flag | Descrição |
|------|-------------|
| `--variables` / `-v TEXT` | Variáveis GraphQL: um objeto JSON, ou repita para vários pares `key=value` |
| `--json` | Saída JSON bruta em vez de tabela formatada |
| `--yaml` | Saída YAML |

Veja [GraphQL](graphql.md) para exemplos e orientação focados.

---

## `nbx graphql tui`

Lança o explorador GraphQL interativo dedicado e executor de consultas.

```bash
nbx graphql tui
nbx graphql tui --theme dracula
nbx graphql tui --theme

nbx demo graphql tui
nbx demo graphql tui --theme dracula
```

Esta TUI carrega introspecção de esquema GraphQL da instância NetBox atual,
permite navegar campos raiz e seus argumentos, inserir esqueletos de consulta/filtro/paginação
no editor e executar consultas GraphQL arbitrárias com variáveis JSON opcionais.

**Opções**

| Flag | Descrição |
|------|-------------|
| `--theme` | Listar temas (sem argumento) ou lançar com nome de tema específico |

Veja [GraphQL](graphql.md) e [TUI GraphQL](../tui/graphql.md) para o fluxo completo.

---

## `nbx tui`

Lança o navegador Textual interativo principal.

```bash
nbx tui
nbx tui --theme dracula
nbx tui --theme          # listar temas disponíveis
```

**Opções**

| Flag | Descrição |
|------|-------------|
| `--theme` | Listar temas (sem argumento) ou lançar com nome de tema específico |

Veja [Guia da TUI](../tui/index.md) para o fluxo do navegador principal.

---

## `nbx logs`

Imprime logs estruturados recentes da aplicação a partir do arquivo de log compartilhado.

```bash
nbx logs
nbx logs --limit 500     # carregar até 500 entradas (padrão: 200)
nbx logs --source
```

**Opções**

| Flag | Padrão | Descrição |
|------|---------|-------------|
| `--limit` | `200` | Número máximo de entradas de log a carregar |
| `--source` | desligado | Incluir detalhes módulo/função/linha |

Novas instalações gravam logs em `~/.config/netbox-sdk/logs/netbox-sdk.log`, com
leituras de compatibilidade de arquivos de log antigos do `netbox-cli` quando presentes.

Para o visualizador de logs Textual em tela cheia, use `nbx tui logs`.

---

## `nbx dev tui`

Lança a TUI de bancada de requisições do desenvolvedor contra seu perfil default.

```bash
nbx dev tui
nbx dev tui --theme dracula
nbx dev tui --theme          # listar temas disponíveis
```

Esta visão é voltada à exploração da API e construção de requisições em vez do fluxo padrão de navegação/resultados.
Quando você lança a mesma visão via `nbx demo dev tui`, a CLI atualiza automaticamente tokens v1 demo expirados se credenciais demo foram salvas durante `nbx demo init`.

**Opções**

| Flag | Descrição |
|------|-------------|
| `--theme` | Listar temas (sem argumento) ou lançar com nome de tema específico |

---

## `nbx dev http`

Auxiliares HTTP orientados ao desenvolvedor para explorar caminhos e operações arbitrários da API.

```bash
nbx dev http paths
nbx dev http ops --path /api/dcim/devices/
nbx dev http get --path /api/status/
```

Use `nbx dev http --help` e os helps dos subcomandos para a matriz completa de opções.

---

## `nbx cli tui`

Lança a TUI de construtor de comandos guiado.

```bash
nbx cli tui
nbx demo cli tui
```

Útil quando você quer explorar a árvore de comandos visualmente e executar um
comando `nbx` montado sem sair do terminal.

---

## `nbx dev django-model`

Auxiliares para contribuidores: analisar, cachear, buscar e navegar
os modelos Django internos do NetBox.

```bash
nbx dev django-model build
nbx dev django-model fetch --auto
nbx dev django-model tui
```

---

## `nbx docs generate-capture`

Gera os artefatos de captura de comandos seguros para documentação usados pelas páginas de referência MkDocs.
A geração de documentação só usa o perfil demo e nunca deve rodar contra produção.

```bash
nbx docs generate-capture
```

**Opções**

| Flag | Padrão | Descrição |
|------|---------|-------------|
| `-o` / `--output` | `docs/generated/nbx-command-capture.md` | Caminho de saída Markdown |
| `--raw-dir` | `docs/generated/raw/` | Diretório para arquivos JSON por comando |
| `--markdown` | ligado | Anexar `--markdown` a capturas compatíveis |
| `-j` / `--concurrency` | `4` | Número de workers de captura paralelos |

Veja [Geração de documentação](../developer/docgen.md) para o guia completo.

---

## `nbx docs generate-tui-simulation`

Gera capturas SVG com dados de fixture do navegador principal da TUI NetBox em
múltiplos temas e estados. A saída é usada pelo site e páginas de documentação
que incorporam visualizações da TUI em estilo interativo.

```bash
nbx docs generate-tui-simulation
```

**Opções**

| Flag | Padrão | Descrição |
|------|---------|-------------|
| `-o` / `--output` | `docs/generated/tui-simulation/main-browser.json` | Destino do JSON de manifesto |
| `--assets-dir` | Diretório pai de `--output` | Diretório de destino dos SVGs |

O comando grava um arquivo JSON de manifesto e um arquivo SVG por combinação
`(tema × estado)` em `docs/generated/tui-simulation/`. Os temas e estados
renderizados são definidos em `netbox_cli/tui_simulation.py`. Diferente do
`generate-capture`, este comando usa dados de fixture e não requer uma instância
NetBox ativa nem credenciais demo.

Veja [Geração de documentação](../developer/docgen.md) para o pipeline completo.
