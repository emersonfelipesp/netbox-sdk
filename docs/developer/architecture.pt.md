# Arquitetura

O repositório está organizado em três pacotes Python irmãos:

- `netbox_sdk` — camada API/SDK independente
- `netbox_cli` — camada CLI Typer
- `netbox_tui` — camada TUI Textual

## Direção das dependências

```text
netbox_cli  -> netbox_sdk
netbox_tui  -> netbox_sdk
netbox_cli  -> netbox_tui   apenas via imports preguiçosos para comandos que lançam TUI
netbox_sdk  -/-> netbox_cli, netbox_tui
```

`netbox_sdk` é o núcleo estável. Deve permanecer importável sem Typer ou Textual instalados.

## Layout dos pacotes

```text
netbox_sdk/
  __init__.py
  client.py
  config.py
  http_cache.py
  schema.py
  services.py
  plugin_discovery.py
  formatting.py
  logging_runtime.py
  output_safety.py
  trace_ascii.py
  demo_auth.py
  django_models/
  reference/openapi/netbox-openapi.json

netbox_cli/
  __init__.py
  runtime.py
  dynamic.py
  support.py
  demo.py
  dev.py
  django_model.py
  markdown_output.py
  docgen_capture.py
  docgen_specs.py
  docgen/

netbox_tui/
  __init__.py
  app.py
  cli_tui.py
  dev_app.py
  logs_app.py
  django_model_app.py
  chrome.py
  navigation.py
  nav_blueprint.py
  panels.py
  widgets.py
  state.py
  dev_state.py
  django_model_state.py
  filter_overlay.py
  theme_registry.py
  *.tcss
  themes/*.json
```

## Responsabilidades

### `netbox_sdk`

Possui:
- comportamento do cliente API
- carregamento de perfil/config
- cache HTTP
- indexação do esquema OpenAPI
- resolução de requisições
- auxiliares de descoberta de plugins
- formatação compartilhada e segurança de saída
- auxiliares de auth demo
- auxiliares de análise/cache de modelos Django

### `netbox_cli`

Possui:
- entrypoint `nbx`
- registro de comandos de nível superior
- fábricas de runtime config/index/client
- ligação dinâmica de comandos a partir do OpenAPI
- renderização de saída CLI e saída Markdown
- árvores de comandos demo/dev/docgen

Comandos CLI que lançam TUI devem importar `netbox_tui` preguiçosamente e mostrar dica de instalação para `pip install 'netbox-sdk[tui]'` quando necessário.

### `netbox_tui`

Possui:
- todas as aplicações Textual
- widgets/chrome/panels/state Textual compartilhados
- assets TCSS
- registro de temas e catálogo JSON de temas

Transformação de dados compartilhada como `semantic_cell`, `humanize_value` e análise de linhas fica em `netbox_sdk.formatting`, não no pacote TUI.

## Fluxo de dados

### CLI

```text
nbx dcim devices list
  -> netbox_cli.__init__.py root app
  -> netbox_cli.dynamic
  -> netbox_sdk.services.resolve_dynamic_request
  -> netbox_sdk.client.NetBoxApiClient.request
  -> netbox_cli.support / markdown_output
```

### TUI

```text
nbx tui
  -> netbox_cli importa preguiçosamente netbox_tui
  -> netbox_tui.app.NetBoxTuiApp
  -> netbox_sdk.client / schema / formatting
  -> widgets Textual + TCSS + registro de temas
```

## Empacotamento

- Instalação núcleo: `pip install netbox-sdk`
- Instalação CLI: `pip install 'netbox-sdk[cli]'`
- Instalação TUI: `pip install 'netbox-sdk[tui]'`
- Instalação completa: `pip install 'netbox-sdk[all]'`

## Verificação

Para mudanças que afetam arquitetura, execute:

```bash
uv sync --dev --extra cli --extra tui --extra demo
uv run pre-commit run --all-files
uv run pytest
```
