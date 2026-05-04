# Guia de captura de comandos

Este repositório inclui um pipeline de captura seguro para documentação do `nbx`. Registra
a entrada e saída exatas de comandos usadas para construir as páginas de referência geradas.

## Regra de operação

A geração de documentação só pode falar com instâncias NetBox demo.

- permitido: `demo.netbox.dev` ou outra instância demo dedicada não produtiva
- não permitido: NetBox de produção real
- exemplos de API gerados devem aparecer como `nbx demo ...` na documentação

## Pontos de entrada principais

| Caminho | Propósito |
|------|---------|
| `docs/generate_command_docs.py` | Shim autônomo para regeneração local |
| `nbx docs generate-capture` | Ponto de entrada CLI preferido |
| `docs/run_capture_in_background.sh` | Inicia docgen sob `nohup` |
| [`generated/nbx-command-capture.md`](generated/nbx-command-capture.md) | Snapshot Markdown combinado |
| [`generated/nbx-command-capture.pt.md`](generated/nbx-command-capture.pt.md) | Espelho em português do snapshot combinado |
| `generated/raw/` | Artefatos JSON completos consumidos pelo hook MkDocs |

## Saída do site público

A documentação pública separa artefatos gerados por superfície de pacote:

- [Saída de comandos da CLI](reference/cli/command-examples/index.md)
- [Saída de lançamento da TUI](reference/tui/launch-examples/index.md)
- Capturas de tela da TUI permanecem na [galeria de capturas da TUI](tui/screenshots.md)

`netbox_sdk` não recebe seção gerada de saída de comando porque é um pacote de API Python
em vez de superfície executável de comando.

## Uso

```bash
uv run nbx demo init
uv run nbx docs generate-capture
uv run mkdocs build --strict
```

## Modelo de saída

Cada spec de captura carrega:

- `surface`: `cli` ou `tui`
- `section`: bucket de página gerada
- `title`: título da página
- `argv`: argumentos de comando
- `notes`: explicação extra mostrada na documentação
- `safe`: se falhas são tratadas como saída capturada válida

O motor grava JSON bruto primeiro; então `docs/hooks.py` converte esses artefatos
em páginas MkDocs específicas da superfície (incluindo espelhos `.pt.md`).
