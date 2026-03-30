# Capturas de tela da TUI

O `netbox-sdk` inclui seis aplicações Textual, cada uma voltada a um fluxo
diferente. Esta galeria reúne capturas temáticas para cada uma.

## Aplicações TUI disponíveis

| TUI | Descrição | Comando de lançamento |
|-----|-------------|-----------------|
| [TUI padrão](screenshots-default.md) | Interface principal de navegação por recursos NetBox | `nbx tui` / `nbx demo tui` |
| [Dev TUI](screenshots-dev.md) | Bancada de requisições do desenvolvedor para exploração da API | `nbx dev tui` / `nbx demo dev tui` |
| [TUI GraphQL](screenshots-graphql.md) | Explorador GraphQL interativo, editor de consultas e visualizador de resposta | `nbx graphql tui` / `nbx demo graphql tui` |
| [Visualizador de logs](screenshots-logs.md) | Visualizador de log estruturado para depuração e diagnóstico | `nbx tui logs` |
| [Construtor de CLI](screenshots-cli.md) | Composição guiada de comandos para `nbx` | `nbx cli tui` / `nbx demo cli tui` |
| [Navegador de modelos Django](screenshots-django.md) | Navegador dos modelos Django internos do NetBox | `nbx dev django-model tui` |

## Temas disponíveis

Todas as aplicações TUI suportam 5 temas integrados:

- **NetBox Dark** — Tema escuro alinhado à aparência padrão do NetBox
- **NetBox Light** — Tema claro para uso diurno
- **Dracula** — Tema escuro popular com acentos roxos
- **Tokyo Night** — Tema escuro sereno com tons azuis
- **One Dark Pro** — Port do tema One Dark do Atom

## Capturar novas capturas de tela

Para capturar capturas novas de todas as TUIs com todos os temas, execute:

```bash
python scripts/tui_screenshots.py
```

Este script usa o perfil demo para a conexão NetBox compartilhada, enquanto as
capturas da TUI GraphQL usam introspecção e respostas de consulta mockadas determinísticas
para a galeria permanecer estável entre execuções e temas. Garanta que o perfil demo
esteja configurado primeiro:

```bash
nbx demo init
```

As capturas são salvas em `docs/assets/screenshots/`. Cada arquivo segue o padrão de nome `tui-{app}-{theme}.svg`.

Para a saída não visual de lançamento/ajuda dessas aplicações, veja
[Saída de lançamento da TUI](../reference/tui/launch-examples/index.md).
