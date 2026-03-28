# GraphQL TUI

`nbx graphql tui` launches a dedicated Textual interface for exploring NetBox's
GraphQL schema and executing real GraphQL queries from the terminal.

It complements the one-shot `nbx graphql QUERY` command. The CLI path is best
for direct execution and scripting; the TUI is best when you need to inspect
schema structure, browse arguments, and iteratively refine queries.

## Launch

```bash
nbx graphql tui
nbx graphql tui --theme dracula
nbx graphql tui --theme

nbx demo graphql tui
nbx demo graphql tui --theme dracula
```

The demo entry point uses the same demo-profile authentication flow as the rest
of the SDK. Query execution goes through the shared `NetBoxApiClient.graphql()`
path, so demo token refresh and production-profile behavior stay aligned.

## Layout

The GraphQL TUI is split into three working areas:

- a root-field explorer with search and saved-query history
- a query builder with query and variables editors
- a response panel with body, headers, and execution summary tabs

The top bar also exposes theme selection, connection status, field context,
support, and close controls.

## Schema exploration

On startup the app runs a GraphQL introspection query against the connected
instance and builds an explorer model from the returned schema.

The explorer surfaces:

- root query fields
- field arguments, types, defaults, and descriptions
- return types for selected fields
- nested object selection hints
- input object fields used by filters and pagination arguments
- union and interface possible types for inline fragment scaffolding

Use `/` to focus the field search box and narrow the root-field list in real
time.

## Guided query building

The GraphQL TUI never locks you into a builder-only flow. The query editor is
plain editable GraphQL text, but the action bar can insert helpful skeletons:

- `Build Field` generates a minimal query for the selected root field
- `Insert Args` inserts all field arguments with type-aware placeholders
- `Insert Filters` inserts a `filters:` object when available
- `Insert Pagination` inserts a `pagination:` object when available
- `Insert Fragments` inserts inline fragments for union or interface returns

These snippets are intentionally minimal so you can keep refining them manually.

## Variables and execution

The Variables tab accepts one JSON object. Leave it blank when the query does
not use variables.

Running a query shows:

- HTTP status and GraphQL error state
- request duration
- response size
- formatted JSON response body
- response headers
- a short execution summary including data keys and GraphQL errors

GraphQL errors are surfaced even when the HTTP status is `200`.

## History and persistence

The TUI saves per-instance state under the NetBox SDK config root. That state
includes:

- selected theme
- last query text
- last variables text
- selected root field
- recent query history

History is scoped by NetBox base URL, so demo and production instances keep
their own query sets.

## Introspection fallback

Some NetBox deployments may disable introspection or return schema errors. When
that happens the GraphQL TUI still opens in editor-first mode. You can continue
to send manual GraphQL queries, and the sidebar shows that schema browsing is
currently unavailable.

## Relationship to other interfaces

- `nbx graphql QUERY` is the direct CLI runner for GraphQL requests
- `nbx graphql tui` is the interactive GraphQL explorer
- `nbx dev tui` is the REST-focused developer workbench
- `nbx tui` is the general resource browser backed by the REST/OpenAPI surface

## Screenshots and generated launch output

- [GraphQL TUI screenshot gallery](screenshots-graphql.md)
- [TUI launch output reference](../reference/tui/launch-examples/index.md)
