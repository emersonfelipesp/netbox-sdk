# Arquitetura

O repositório está organizado em quatro pacotes Python irmãos que compartilham um único runtime:

- `netbox_sdk` — camada API/SDK independente (sem dependências de CLI ou TUI)
- `netbox_cli` — camada CLI Typer (requer o extra `[cli]`)
- `netbox_tui` — camada TUI Textual (requer o extra `[tui]`)
- `netbox_mcp` — adaptador estável do Model Context Protocol (requer o extra `[mcp]`)

---

## Direção das dependências

```mermaid
flowchart LR
    CLI["netbox_cli\nTyper CLI"]
    TUI["netbox_tui\nTextual TUI"]
    SDK["netbox_sdk\nCore SDK"]
    MCP["netbox_mcp\nFerramentas MCP estáveis"]

    CLI --> SDK
    TUI --> SDK
    MCP --> SDK
    CLI -. "importação lazy\n(apenas comandos de lançamento de TUI)" .-> TUI
```

`netbox_sdk` é o núcleo estável. Deve permanecer importável sem Typer ou Textual instalados.

---

## Componentes internos do SDK

```mermaid
flowchart TB
    config["config.py\nModelo Config, persistência de perfil\nvars de ambiente, montagem de cabeçalho de auth"]
    cache["http_cache.py\nCache JSON no sistema de arquivos\nTTL · ETag · stale-if-error"]
    client["client.py\nNetBoxApiClient\nasync aiohttp · auth · proteção SSRF"]
    schema["schema.py\nSchemaIndex\nParsing OpenAPI · resolução de recursos"]
    versions["versioning.py\nRegistro de linhas de release\nartefatos · status do ciclo de vida"]
    resolution["schema_resolution.py\nResolução de pin + instância\nembutido · ao vivo · fallback"]
    services["services.py\nresolve_dynamic_request()\nrun_dynamic_command()"]
    facade["facade.py\nApi → App → Endpoint\n→ Record / RecordSet"]
    typed["typed_api.py\ntyped_api()\nClientes tipados por versão"]
    models["models/\nModelos Pydantic gerados\nv4_3 · v4_4 · v4_5 · v4_6"]
    bridge["plugin_bridge.py\nManifestos versionados de plugins\nschema + caminho estritos"]

    config --> client
    cache --> client
    versions --> resolution
    schema --> resolution
    schema --> services
    client --> services
    client --> facade
    schema --> facade
    facade --> typed
    models --> typed
    client --> bridge
```

| Módulo | Função |
|---|---|
| `config.py` | Modelo Pydantic `Config`, persistência de múltiplos perfis, sanitização de tokens, carregamento de variáveis de ambiente |
| `client.py` | `NetBoxApiClient` — cliente HTTP async aiohttp, injeção de auth, integração com cache HTTP, proteção SSRF |
| `http_cache.py` | `HttpCacheStore` — cache JSON em disco com TTL, ETag/If-Modified-Since, stale-if-error |
| `schema.py` | `SchemaIndex` — analisa JSON OpenAPI em grupos, recursos, operações e parâmetros de filtro |
| `versioning.py` | Registro congelado que possui o artefato OpenAPI, o módulo de modelos gerados, o módulo tipado e o status do ciclo de vida de cada linha suportada |
| `schema_resolution.py` | Parsing compartilhado de overrides, índices embutidos cacheados e isolados por clone, detecção da instância, busca de schema ao vivo e fallback padrão |
| `services.py` | `resolve_dynamic_request()` / `run_dynamic_command()` — mapeia ações CLI para chamadas HTTP |
| `plugin_bridge.py` | Descobre manifestos semânticos versionados, valida contratos e payloads hostis e resolve destinos fixos locais ao plugin |
| `facade.py` | `api()` — fachada async estilo PyNetBox: `Api → App → Endpoint → Record/RecordSet` |
| `typed_api.py` | `typed_api()` — clientes tipados por versão com modelos Pydantic de request/response |
| `models/` | Modelos Pydantic gerados para NetBox 4.3, 4.4, 4.5, 4.6 e 4.7 (preview) |

---

## Estrutura dos pacotes

??? note "Árvore completa de pacotes"

    ```
    netbox_sdk/
      __init__.py
      client.py
      config.py
      http_cache.py
      schema.py
      schema_resolution.py
      services.py
      plugin_discovery.py
      plugin_bridge.py
      formatting.py
      logging_runtime.py
      output_safety.py
      trace_ascii.py
      demo_auth.py
      facade.py
      typed_api.py
      typed_runtime.py
      versioning.py
      exceptions.py
      models/
        v4_3.py · v4_4.py · v4_5.py · v4_6.py
      typed_versions/
        v4_3.py · v4_4.py · v4_5.py · v4_6.py
      django_models/
      reference/openapi/
        netbox-openapi.json (alias legado)
        netbox-openapi-4.3.json
        netbox-openapi-4.4.json
        netbox-openapi-4.5.json
        netbox-openapi-4.6.json (padrão)
        netbox-openapi-4.7.json (preview)

    netbox_cli/
      __init__.py
      runtime.py
      dynamic.py
      support.py
      demo.py
      dev.py
      django_model.py
      markdown_output.py
      branching.py
      decorators.py
      tui_simulation.py
      docgen_capture.py
      docgen_specs.py
      docgen/

    netbox_tui/
      __init__.py
      app.py
      cli_tui.py
      dev_app.py
      logs_app.py
      graphql_app.py
      django_model_app.py
      chrome.py
      navigation.py
      nav_blueprint.py
      panels.py
      widgets.py
      state.py
      dev_state.py
      django_model_state.py
      graphql_state.py
      filter_overlay.py
      branch_screen.py
      login_modal.py
      ssl_verify_support.py
      cli_completions.py
      dev_rendering.py
      lifecycle.py
      logo_render.py
      theme_registry.py
      *.tcss
      themes/*.json

    netbox_mcp/
      __init__.py
      __main__.py
      app.py
      models.py
      service.py
      py.typed
    ```

---

## Fluxo de dados

=== "CLI"

    ```mermaid
    flowchart LR
        CMD["nbx dcim devices list"]
        INIT["netbox_cli.__init__\naplicação Typer raiz"]
        DYN["netbox_cli.dynamic\n_register_openapi_subcommands()"]
        SVC["netbox_sdk.services\nresolve_dynamic_request()"]
        CLIENT["netbox_sdk.client\nNetBoxApiClient.request()"]
        OUT["netbox_cli.support\nmarkdown_output"]

        CMD --> INIT --> DYN --> SVC --> CLIENT --> OUT
    ```

    1. `nbx` despacha para a aplicação Typer raiz em `netbox_cli/__init__.py`
    2. `netbox_cli.dynamic` registra todos os comandos `nbx <grupo> <recurso> <ação>` na inicialização a partir do esquema OpenAPI
    3. `netbox_sdk.services.resolve_dynamic_request()` mapeia a ação para `(método, caminho, query, payload)`
    4. `NetBoxApiClient.request()` executa a chamada HTTP com auth, cache e proteção SSRF
    5. `support` / `markdown_output` renderizam a resposta como tabelas Rich ou Markdown

=== "TUI"

    ```mermaid
    flowchart LR
        CMD2["nbx tui"]
        LAZY["netbox_cli\nimporta netbox_tui lazily"]
        APP["netbox_tui.app\nNetBoxTuiApp"]
        SDK2["netbox_sdk\nclient · schema · formatting"]
        TUI2["Textual\nwidgets · TCSS · registro de temas"]

        CMD2 --> LAZY --> APP --> SDK2 --> TUI2
    ```

    1. `nbx tui` em `netbox_cli/__init__.py` importa `netbox_tui` lazily (para que `import netbox_cli` funcione sem Textual)
    2. `NetBoxTuiApp` recebe o `NetBoxApiClient` e `SchemaIndex` ativos do runtime do CLI
    3. Todas as consultas de dados passam por `netbox_sdk.client` e `netbox_sdk.schema`
    4. Formatação (badges, labels, cores) vem de `netbox_sdk.formatting`
    5. Layout da UI é puro Textual: stylesheets TCSS + registro de temas

=== "Ponte MCP para plugins"

    ```mermaid
    flowchart LR
        AGENT["Cliente MCP"]
        TOOLS["plugin_list_tools / plugin_call_tool"]
        BRIDGE["netbox_sdk.plugin_bridge\nvalidação do contrato"]
        CLIENT3["NetBoxApiClient"]
        PLUGIN["View DRF existente do plugin\npermissões + operação"]

        AGENT --> TOOLS --> BRIDGE --> CLIENT3 --> PLUGIN
    ```

    1. As ferramentas MCP estáveis descobrem um anúncio explícito de versão 1
       na raiz da API do plugin.
    2. `plugin_bridge` confina links e caminhos de destino, depois valida o
       manifesto e os schemas da invocação.
    3. `NetBoxApiClient.request_bounded()` executa descoberta atual sem cache e
       requisições de destino com a credencial NetBox normal, redirects
       desativados e limite sobre o corpo descompactado em stream.
    4. O endpoint DRF existente continua responsável pela autorização e pela
       operação; o despacho de escritas também exige o gate de mutações MCP.

---

## Responsabilidades

### `netbox_sdk`

Responsável por:

- Comportamento do cliente API (HTTP, auth, cache, atualização de token, upload de arquivos)
- Carregamento de perfil e config do disco e variáveis de ambiente
- Cache de resposta HTTP (no sistema de arquivos, ETag/If-Modified-Since)
- Indexação do esquema OpenAPI e resolução de recursos
- Metadados de linhas de release e a política compartilhada pin explícito →
  bundle detectado → schema ao vivo → bundle padrão
- Resolução dinâmica de requisições a partir de tuplas `(grupo, recurso, ação)`
- Descoberta OpenAPI de plugins e contratos semânticos versionados da ponte
- Utilitários de formatação e segurança de saída compartilhados
- Helpers de auth para demonstração e parsing/cache de modelos Django
- Todas as três camadas públicas de API: `NetBoxApiClient`, `api()`, `typed_api()`

### `netbox_cli`

Responsável por:

- Entrypoint `nbx` e registro de comandos raiz
- Factories de runtime para config/índice/cliente (`netbox_cli/runtime.py`)
- Cabeamento dinâmico de comandos a partir do esquema OpenAPI (`netbox_cli/dynamic.py`)
- Renderização de saída CLI (`support.py`, `markdown_output.py`)
- Árvores de comandos demo/dev/docgen

Comandos CLI que lançam uma TUI devem importar `netbox_tui` lazily e exibir uma dica de instalação para `pip install 'netbox-sdk[tui]'` quando necessário.

### `netbox_tui`

Responsável por:

- Todas as seis aplicações Textual: `NetBoxTuiApp`, `NbxCliTuiApp`, `NetBoxDevTuiApp`, `NetBoxGraphqlTuiApp`, `NetBoxLogsTuiApp`, `DjangoModelTuiApp`
- Widgets Textual compartilhados, chrome, painéis e gerenciamento de estado
- Stylesheets TCSS e registro de temas

Transformações de dados compartilhadas (`semantic_cell`, `humanize_value`, parsing de linhas) vivem em `netbox_sdk.formatting`, não no pacote TUI.

### `netbox_mcp`

Responsável por:

- Um inventário MCP estável e registrado explicitamente
- Validação Pydantic estrita na fronteira do transporte
- `plugin_list_tools` e `plugin_call_tool` sobre `netbox_sdk.plugin_bridge`
- Autenticação de transporte e gate de mutações desabilitado por padrão

Ferramentas de plugins nunca criam outra credencial ou pilha HTTP. Descoberta e
execução usam `NetBoxApiClient`; o endpoint DRF existente do plugin continua
sendo a fronteira de autorização e da operação.

---

## Empacotamento

| Comando de instalação | O que você obtém |
|---|---|
| `pip install netbox-sdk` | Apenas `netbox_sdk` — SDK, sem CLI ou TUI |
| `pip install 'netbox-sdk[cli]'` | `netbox_sdk` + `netbox_cli` |
| `pip install 'netbox-sdk[tui]'` | `netbox_sdk` + `netbox_tui` |
| `pip install 'netbox-sdk[mcp]'` | `netbox_sdk` + `netbox_mcp` |
| `pip install 'netbox-sdk[all]'` | Tudo, incluindo ferramentas de demonstração |

---

## Verificação

Para mudanças que afetam a arquitetura, execute:

```bash
uv sync --dev --extra cli --extra tui --extra demo --extra mcp
uv run pre-commit run --all-files
uv run pytest
```
