# Princípios de design (alinhados a SOLID)

Este projeto não impõe SOLID por ferramentas; estas são convenções para contribuidores e para embutir a biblioteca.

## Responsabilidade única (S)

- **HTTP, auth, cache, retry de token** ficam em `netbox_sdk/client.py` e `netbox_sdk/http_cache.py`.
- **Indexação OpenAPI** fica em `netbox_sdk/schema.py`.
- **Resolução de requisições** a partir de ações voltadas ao usuário fica em `netbox_sdk/services.py`.
- **Typer** fica em `netbox_cli/`; **Textual** em `netbox_tui/`.
- **JSON de tema** e validação ficam em `netbox_tui/theme_registry.py` e `netbox_tui/themes/*.json`.

Evite crescer “módulos deus” ao adicionar recursos; prefira um módulo pequeno novo ou estender o dono existente mais próximo.

## Aberto/fechado (O)

Comandos CLI dinâmicos são gerados a partir do esquema OpenAPI integrado. Novos recursos NetBox aparecem na CLI/TUI quando o esquema é atualizado, sem manter tabelas de comando por recurso à mão.

## Substituição de Liskov (L)

Contratos compartilhados entre camadas são tipos simples: `Config`, `ApiResponse`, `SchemaIndex`, `NetBoxApiClient`. Código que aceita `NetBoxApiClient` deve funcionar com doubles de teste que implementam `request()` e `probe_connection()` de forma consistente.

## Segregação de interface (I)

Prefira auxiliares pequenos e focados a objetos “contexto” largos. Onde testes precisam de costuras, use `typing.Protocol` ou duck typing para objetos “parecidos com cliente” em vez de subclassificar `NetBoxApiClient`.

## Inversão de dependência (D)

- **Preferido:** TUIs e ferramentas recebem `client` e `index` do chamador em vez de alcançar internos da CLI.
- **CLI:** Corpos de comando resolvem `_get_client`, `_ensure_runtime_config` e hooks relacionados via `netbox_cli` / `netbox_cli.runtime` para testes poderem patchar `netbox_cli.*` de forma confiável.
- **Exceções documentadas:**
  - `netbox_tui/cli_tui.py` importa o `app` Typer real para paridade `CliRunner` com `nbx`.
  - `_get_client()` em `netbox_cli.runtime` usa import tardio de `netbox_cli` para completar perfil interativo em um só lugar.

## Portões de qualidade

- `uv run pre-commit run --all-files`
- `uv run pytest`

Novos imports entre camadas que violam a tabela de [integração de pacotes](package-integration.md) devem ser documentados aqui ou evitados.
