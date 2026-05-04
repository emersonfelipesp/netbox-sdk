# Bancada do desenvolvedor

O `nbx dev tui` lança o workspace de exploração da API para o NetBox SDK. É
voltado à inspeção de requisições, descoberta de caminhos e depuração em vez do
fluxo padrão de navegar e filtrar do `nbx tui`.

## Lançamento

```bash
nbx dev tui
nbx dev tui --theme dracula

nbx demo dev tui
nbx demo dev tui --theme dracula
```

## Melhores casos de uso

- explorar payloads de requisição e resposta ao desenvolver automação
- inspecionar metadados de operação antes de chamar `nbx dev http`
- validar filtros, parâmetros e formas de resposta contra um NetBox ao vivo
- reproduzir comportamento contra o perfil público `demo.netbox.dev`

## Relação com outras interfaces

- `nbx tui` é a TUI de navegação geral
- `nbx dev tui` é a bancada de requisições
- `nbx cli tui` é o construtor de comandos guiado
- `nbx logs` é o visualizador de log estruturado

## Capturas de tela

- [Galeria da bancada do desenvolvedor](screenshots-dev.md)
