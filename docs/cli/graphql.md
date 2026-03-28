# GraphQL

`nbx graphql` is the CLI entry point for NetBox's GraphQL API. Use it when you
need cross-resource queries or want to prototype GraphQL payloads without
writing Python code.

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

## When to use GraphQL vs REST

- Use `nbx graphql` when you want a single query spanning multiple resource
  types.
- Use dynamic REST commands like `nbx dcim devices list` when you want
  schema-driven discovery and the standard NetBox REST workflow.
- Use `nbx call` when you need explicit control over a REST path that is not
  represented by the dynamic command tree.
