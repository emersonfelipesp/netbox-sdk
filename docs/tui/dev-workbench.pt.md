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

## Confirmação de escrita

Cada envio `POST`, `PUT`, `PATCH` ou `DELETE` abre um diálogo de confirmação que
mostra método, caminho e payload resolvidos. A requisição só é enviada após a
escolha explícita de **Confirm write**; cancelar ou pressionar Escape não altera
o NetBox. Esse gate por requisição também vale quando a bancada compartilhada é
aberta por `nbx proxbox tui`.

## Capturas de tela

- [Galeria da bancada do desenvolvedor](screenshots-dev.md)
