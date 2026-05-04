---
hide:
  - navigation
  - toc
---

# NetBox SDK

**Kit NetBox com foco no SDK para Python, terminal e UIs Textual.**

O `netbox-sdk` é organizado em três pacotes irmãos:

- `netbox_sdk` — SDK REST NetBox independente
- `netbox_cli` — CLI com Typer
- `netbox_tui` — TUI com Textual

O repositório expõe três superfícies públicas:

- `netbox_sdk` para integrações Python
- `nbx` para fluxos de CLI
- várias TUIs Textual para navegação, depuração e execução guiada de comandos

O próprio pacote SDK expõe três camadas:

- `NetBoxApiClient` para controle HTTP assíncrono de baixo nível
- `api()` / `Api` para a camada de fachada assíncrona
- `typed_api()` para o cliente tipado versionado com modelos Pydantic versionados

As linhas de release tipadas atuais do SDK são NetBox `4.6`, `4.5`, `4.4` e `4.3`.
A integração contínua exercita a suíte live-NetBox contra `v4.6.0-beta2`,
`v4.5.9` e `v4.5.8`.

--8<-- "snippets/documented-release-pt.md"

<div class="grid cards" markdown>

-   :material-api:{ .lg .middle } **SDK**

    ```python
    from netbox_sdk import api, typed_api
    ```

    [:octicons-arrow-right-24: Guia do SDK](sdk/index.md)

-   :material-console:{ .lg .middle } **CLI**

    ```bash
    nbx dcim devices list
    nbx dcim devices get --id 1
    ```

    [:octicons-arrow-right-24: Guia da CLI](cli/index.md)

-   :material-monitor:{ .lg .middle } **TUI**

    ```bash
    nbx tui
    nbx demo tui --theme dracula
    ```

    [:octicons-arrow-right-24: Guia da TUI](tui/index.md)

-   :material-lightning-bolt:{ .lg .middle } **Início rápido**

    ```bash
    pip install 'netbox-sdk[all]'
    --8<-- "snippets/pip-pinned-all.txt"
    nbx init
    nbx dcim devices list
    ```

    [:octicons-arrow-right-24: Início rápido](getting-started/quickstart.md)

</div>

## Divisão do produto

- A documentação do `SDK` cobre APIs Python importáveis, camadas de requisição,
  autenticação e clientes tipados versionados.
- A documentação da `CLI` cobre a árvore de comandos `nbx`, comandos dinâmicos,
  GraphQL, perfil demo e exemplos de comandos capturados.
- A documentação da `TUI` cobre o navegador principal, a bancada do desenvolvedor,
  o construtor de CLI, o visualizador de logs e o navegador de modelos Django.

## Padrão para contribuidores

```bash
uv sync --dev --extra cli --extra tui --extra demo
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
uv run pre-commit run --all-files
uv run pytest
```
