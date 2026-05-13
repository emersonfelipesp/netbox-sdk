# Suporte de IDE

Todos os três pacotes — `netbox_sdk`, `netbox_cli` e `netbox_tui` — incluem um
marcador `py.typed` ([PEP 561](https://peps.python.org/pep-0561/)) e estão
listados em `package-data` da wheel. Editores que leem PEP 561 (VS Code via
Pylance, PyCharm, Pyright na linha de comando) resolvem tipos a partir de uma
instalação de `netbox-sdk` sem configuração adicional.

## VS Code

O repositório versiona um workspace mínimo em `.vscode/` para que um clone novo
já tenha uma IDE funcional no primeiro abrir. Quando o VS Code sugerir
instalar as extensões recomendadas, aceite:

- `ms-python.python`
- `ms-python.vscode-pylance`
- `charliermarsh.ruff`

O `.vscode/settings.json` aponta o interpretador para
`${workspaceFolder}/.venv/bin/python`, ativa indexação e auto-import do
Pylance, e usa o Ruff como formatador no save.
`python.analysis.typeCheckingMode` é `basic` para casar com o bloco
`[tool.pyright]` do `pyproject.toml`, então os diagnósticos ao vivo do editor
batem com o gate do pre-commit.

## Gates de checagem de tipo

Dois type checkers rodam sobre a mesma árvore de código, no mesmo nível
`basic`:

- **`ty`** (Astral) — usado pelo hook `ty-check` no pre-commit e na CI;
  feedback rápido sobre SDK e pacotes CLI/TUI.
- **`pyright`** (compatível com Pylance) — usado pelo hook `pyright-check`
  no pre-commit, então o que o Pylance mostra no VS Code é o que falha nos
  hooks de commit.

Para rodar manualmente:

```bash
uv run ty check netbox_sdk netbox_cli netbox_tui tests
uv run pyright netbox_sdk netbox_cli netbox_tui
```

Ambos os gates precisam passar antes do commit. O hook `pyright-check` fica
junto do `ty-check` em `.pre-commit-config.yaml`; `uv run pre-commit run --all-files`
exercita os dois.

### Caminhos excluídos

Código gerado e em bundle é excluído de ambos os checkers para manter as
verificações rápidas e evitar ruído de bindings gerados:

- `netbox_sdk/models/**`
- `netbox_sdk/typed_versions/**`
- `tests/**` (para `pyright`; o `ty` checa testes mas silencia `all` no
  bloco de overrides)

### Severidade de regras

`[tool.pyright]` rebaixa um conjunto pequeno de regras para `warning` para
que elas apareçam no editor sem quebrar o gate do pre-commit. Essas regras
espelham o que o `ty` já silencia, mais os análogos do pyright que apareceram
no código existente:

- `reportAttributeAccessIssue`
- `reportArgumentType`
- `reportAssignmentType`
- `reportRedeclaration`
- `reportInvalidTypeArguments`

Corrigir a dívida de tipos correspondente é uma tarefa separada de fazer a
IDE funcionar; tratar esses warnings não deve acontecer como efeito colateral
de outras mudanças.

## Consumidores

Se você instalar `netbox-sdk` do PyPI em outro projeto, o Pylance pega os
type hints empacotados automaticamente — não há nada para habilitar no
repositório que consome. A wheel inclui:

- `netbox_sdk/py.typed`
- `netbox_cli/py.typed`
- `netbox_tui/py.typed`

Passar o mouse em `NetBoxApiClient`, `api()` ou `typed_api()` em um código
consumidor resolve para os tipos reais.
