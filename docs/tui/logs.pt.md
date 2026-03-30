# Visualizador de logs

O `netbox-sdk` expõe duas visões de log:

- `nbx tui logs` lança o visualizador de logs Textual em tela cheia
- `nbx logs` imprime um tail simples na CLI do mesmo arquivo de log compartilhado

Ambos leem o log JSON estruturado gravado pelo runtime do SDK, CLI e TUI.

## Lançamento

```bash
nbx tui logs
nbx tui logs --theme dracula
nbx logs
nbx logs --limit 500
```

## O que mostra

- timestamp
- nível
- nome do logger
- corpo da mensagem
- detalhes opcionais de exceção

Use `nbx logs --source` na visão CLI simples quando também quiser módulo,
função e informação de linha. Use `nbx tui logs --theme` para listar temas
disponíveis para o visualizador Textual.

## Armazenamento

O visualizador de logs lê do diretório de log compartilhado sob a raiz de config do NetBox SDK.
Novas instalações usam `~/.config/netbox-sdk/logs/netbox-sdk.log`, enquanto arquivos de log
antigos do `netbox-cli` ainda são lidos automaticamente por compatibilidade.

## Capturas de tela

- [Galeria do visualizador de logs](screenshots-logs.md)
- [Saída de comando de lançamento](../reference/tui/launch-examples/index.md)
