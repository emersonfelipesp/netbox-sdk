# GraphQL

`nbx graphql` é o ponto de entrada CLI para a API GraphQL do NetBox. Use quando
precisar de consultas entre recursos ou quiser prototipar payloads GraphQL sem
escrever código Python.

`nbx graphql tui` é o explorador GraphQL interativo. Usa o mesmo perfil,
transporte e fluxo de autenticação que o comando de consulta CLI, mas adiciona
introspecção de esquema, construção guiada de consultas, edição de variáveis,
histórico e inspeção formatada da resposta.

## Consulta básica

```bash
nbx graphql "{ sites { name } }"
```

## Variáveis

Passe um objeto JSON:

```bash
nbx graphql "query($id: Int!) { device(id: $id) { name } }" --variables '{"id": 1}'
```

Ou repita `-v` / `--variables` com pares `key=value`:

```bash
nbx graphql "query($name: String!) { devices(name: $name) { id } }" -v name=sw01
```

## Formatos de saída

```bash
nbx graphql "{ sites { name } }" --json
nbx graphql "{ sites { name } }" --yaml
```

`--json` e `--yaml` espelham os controles de saída disponíveis em `nbx call` e
comandos dinâmicos.

## Explorador GraphQL interativo

```bash
nbx graphql tui
nbx graphql tui --theme dracula
nbx graphql tui --theme

nbx demo graphql tui
nbx demo graphql tui --theme dracula
```

A TUI GraphQL abre um workspace de três painéis:

- explorador de campos de consulta raiz com introspecção de esquema ao vivo
- editores de consulta e variáveis para texto GraphQL arbitrário
- abas de corpo da resposta, cabeçalhos e resumo para consultas executadas

Quando a introspecção não está disponível, o editor ainda abre em modo de consulta manual
para que você possa enviar requisições GraphQL diretamente.

## Quando usar GraphQL vs REST

- Use `nbx graphql` quando quiser uma única consulta abrangendo vários tipos de
  recurso.
- Use `nbx graphql tui` quando quiser inspecionar o esquema de forma interativa,
  navegar argumentos e tipos de retorno e montar consultas no terminal.
- Use comandos REST dinâmicos como `nbx dcim devices list` quando quiser
  descoberta orientada por esquema e o fluxo REST padrão do NetBox.
- Use `nbx call` quando precisar de controle explícito sobre um caminho REST que não
  está representado na árvore de comandos dinâmicos.
