# Geração de documentação

O `netbox-sdk` inclui um sistema de captura integrado que executa comandos `nbx`
selecionados, grava sua saída e gera páginas de referência orientadas a pacote
para as superfícies CLI e TUI.

A saída é dividida de propósito:

- [Saída de comandos da CLI](../reference/cli/command-examples/index.md) cobre `netbox_cli`
- [Saída de lançamento da TUI](../reference/tui/launch-examples/index.md) cobre `netbox_tui`
- `netbox_sdk` permanece documentado por guias manuscritos do SDK, pois não
  expõe superfície de comando direta

## Regra de segurança

A geração de documentação está restrita ao perfil demo apenas. Nunca deve rodar contra
uma instância NetBox de produção.

- capturas de API ao vivo usam `nbx demo ...`
- capturas de ajuda e descoberta de esquema local podem usar comandos raiz como `nbx groups`
- nenhum modo `--live` é suportado

## Início rápido

```bash
cd /path/to/netbox-sdk
uv sync --group docs --group dev --extra cli --extra tui --extra demo
uv run nbx demo init
uv run nbx docs generate-capture
```

## Opções da CLI

| Flag | Padrão | Descrição |
|------|---------|-------------|
| `-o` / `--output` | `docs/generated/nbx-command-capture.md` | Caminho do snapshot Markdown |
| `--raw-dir` | `docs/generated/raw/` | Diretório de artefatos JSON por comando |
| `--markdown` | ligado | Anexar `--markdown` a capturas compatíveis |
| `-j` / `--concurrency` | `4` | Número de workers de captura paralelos |

## Arquivos de saída

| Arquivo | Descrição |
|------|-------------|
| `docs/generated/raw/NNN-<slug>.json` | Artefato completo de captura por comando |
| `docs/generated/raw/index.json` | Metadados resumidos consumidos pelo MkDocs |
| `docs/reference/cli/command-examples/index.md` | Página inicial gerada da saída CLI |
| `docs/reference/tui/launch-examples/index.md` | Página inicial gerada da saída de lançamento TUI |
| `docs/generated/nbx-command-capture.md` | Snapshot Markdown bruto combinado |
| `docs/generated/nbx-command-capture.pt.md` | Espelho em português do snapshot combinado |

## Modelo de captura

Cada comando capturado é declarado em `netbox_cli/docgen_specs.py` como um
`CaptureSpec` com:

- `surface`: `cli` ou `tui`
- `section`: o bucket de página gerada dentro dessa superfície
- `title`: o título mostrado na documentação gerada
- `argv`: os argumentos de comando passados após `nbx`
- `notes`: contexto opcional mostrado acima da saída
- `safe`: se falhas de comando devem abortar a execução ou ser capturadas como saída

O motor de captura grava artefatos JSON brutos primeiro. O hook MkDocs em
`docs/hooks.py` então reconstrói duas árvores geradas separadas antes de cada build
de documentação:

- `docs/reference/cli/command-examples/`
- `docs/reference/tui/launch-examples/`

Cada página `.md` tem um espelho `.pt.md` com rótulos de UI em português.

## Regeneração

```bash
uv run nbx demo init
uv run nbx docs generate-capture
uv run mkdocs build --strict
```

---

## Geração de simulação da TUI

`nbx docs generate-tui-simulation` renderiza capturas SVG com dados de fixture
do navegador principal da TUI NetBox em todos os temas integrados e um conjunto
fixo de estados da aplicação. A saída é usada para visualizações no site e
páginas de documentação que exibem imagens da TUI em estilo interativo sem
requerer um backend ativo.

### Início rápido

```bash
uv sync --group docs --group dev --extra cli --extra tui
uv run nbx docs generate-tui-simulation
```

### Opções da CLI

| Flag | Padrão | Descrição |
|------|---------|-------------|
| `-o` / `--output` | `docs/generated/tui-simulation/main-browser.json` | Destino do JSON de manifesto |
| `--assets-dir` | Diretório pai de `--output` | Diretório de saída dos SVGs |

### Arquivos de saída

| Arquivo | Descrição |
|------|-------------|
| `docs/generated/tui-simulation/main-browser.json` | Manifesto com metadados de tema/estado e caminhos de SVG |
| `docs/generated/tui-simulation/main-browser-<estado>-<tema>.svg` | Um SVG por combinação (estado × tema) |

### Diferenças em relação ao `generate-capture`

| Recurso | `generate-capture` | `generate-tui-simulation` |
|---|---|---|
| Requer NetBox ativo | Sim (perfil demo) | Não — usa dados de fixture |
| Formato de saída | Markdown + artefatos JSON | Manifesto JSON + SVGs |
| O que captura | Saída de comandos CLI | Estados visuais da TUI |
| Controle de estado | `argv` do comando | Fixtures de estado predefinidos em `tui_simulation.py` |

Os fixtures de simulação e as listas de tema/estado são definidos em
`netbox_cli/tui_simulation.py`.
