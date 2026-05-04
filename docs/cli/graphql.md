# GraphQL

`nbx graphql` is the CLI entry point for NetBox's GraphQL API. Use it when you
need cross-resource queries or want to prototype GraphQL payloads without
writing Python code.

`nbx graphql tui` is the interactive GraphQL explorer. It uses the same
profile, transport, and authentication flow as the CLI query command, but adds
schema introspection, guided query building, variables editing, history, and
formatted response inspection.

## Basic query

```bash
nbx graphql "{ sites { name } }"
```

## Variables

Pass one JSON object:

```bash
nbx graphql "query($id: Int!) { device(id: $id) { name } }" --variables '{"id": 1}'
```

Or repeat `-v` / `--variables` with `key=value` pairs:

```bash
nbx graphql "query($name: String!) { devices(name: $name) { id } }" -v name=sw01
```

## Output formats

```bash
nbx graphql "{ sites { name } }" --json
nbx graphql "{ sites { name } }" --yaml
```

`--json` and `--yaml` mirror the output controls available on `nbx call` and
dynamic commands.

## Interactive GraphQL explorer

```bash
nbx graphql tui
nbx graphql tui --theme dracula
nbx graphql tui --theme

nbx demo graphql tui
nbx demo graphql tui --theme dracula
```

The GraphQL TUI opens a three-pane workspace:

- root query field explorer backed by live schema introspection
- query and variables editors for arbitrary GraphQL text
- response body, headers, and summary tabs for executed queries

When introspection is unavailable, the editor still opens in manual-query mode
so you can send GraphQL requests directly.

## When to use GraphQL vs REST

- Use `nbx graphql` when you want a single query spanning multiple resource
  types.
- Use `nbx graphql tui` when you want to inspect the schema interactively,
  browse arguments and return types, and assemble queries in-terminal.
- Use dynamic REST commands like `nbx dcim devices list` when you want
  schema-driven discovery and the standard NetBox REST workflow.
- Use `nbx call` when you need explicit control over a REST path that is not
  represented by the dynamic command tree.
