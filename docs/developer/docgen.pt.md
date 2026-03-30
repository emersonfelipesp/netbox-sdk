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
