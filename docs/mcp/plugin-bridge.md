# NetBox Plugin Bridge

The plugin bridge lets any NetBox plugin advertise a small set of semantic
operations through its existing REST API. `netbox-sdk` discovers and validates
those operations, and `netbox_mcp` exposes them through two stable MCP tools:
`plugin_list_tools` and `plugin_call_tool`.

The bridge does not create a second server inside the plugin. Authentication,
authorization, throttling, request handling, and the operation itself remain in
the plugin's normal Django REST Framework views. The SDK remains the only HTTP
client and reuses the selected NetBox profile or per-call token.

## Advertisement

A participating plugin adds an `mcp` member to its API-root response. For a
plugin named `example`, the only accepted version 1 location is:

```json
{
  "mcp": {
    "schema_version": "1",
    "manifest": "/api/plugins/example/mcp/"
  }
}
```

The manifest link must be same-origin and remain inside the advertising plugin
namespace. NetBox installations below a URL prefix may advertise the prefixed
form (for example `/netbox/api/plugins/example/mcp/`); the SDK normalizes it to
the configured base before dispatch. A plugin that does not advertise this
member is simply ignored.

## Manifest contract

`GET /api/plugins/example/mcp/` returns a versioned document:

```json
{
  "schema_version": "1",
  "plugin": "example",
  "tools": [
    {
      "name": "run_report",
      "title": "Run an inventory report",
      "description": "Build the report visible to the current NetBox principal.",
      "method": "POST",
      "path": "reports/run/",
      "effect": "write",
      "inputSchema": {
        "type": "object",
        "properties": {
          "scope": {"type": "string", "enum": ["active", "all"]}
        },
        "required": ["scope"],
        "additionalProperties": false
      },
      "outputSchema": {
        "type": "object",
        "properties": {"job_id": {"type": "integer", "minimum": 1}},
        "required": ["job_id"],
        "additionalProperties": false
      },
      "annotations": {
        "readOnlyHint": false,
        "destructiveHint": false,
        "idempotentHint": false,
        "openWorldHint": false
      }
    }
  ]
}
```

Version 1 has intentionally narrow rules:

- `plugin` and tool names use lowercase stable identifiers. Tool names are
  unique within one manifest and are presented as `plugin.tool` in catalogs.
- `path` is a fixed relative path below `/api/plugins/<plugin>/`. Absolute
  paths, URLs, query strings, fragments, percent encoding, backslashes, empty
  segments, and dot segments are rejected.
- `GET` and `HEAD` operations declare `effect: read`. Write methods declare
  `write` or `destructive`; `DELETE` must be destructive. MCP annotations must
  agree with the declared effect.
- `inputSchema` is strict Draft 2020-12 JSON Schema with `type: object` and
  `additionalProperties: false`. Version 1 accepts only its documented bounded
  keyword subset and excludes references/definitions, regex patterns and the
  unsupported formats, conditional schemas, and combinators. Version 1 supports
  only the `date-time` format and validates it as RFC 3339, including its
  leap-second syntax. `uniqueItems` is
  allowed only for arrays with one explicitly typed scalar item domain; mixed
  scalar types are rejected. These restrictions prevent remote fetches,
  recursive contracts, silently ignored formats, and avoidable validation
  amplification.
- `GET`/`HEAD` input properties must be scalars or arrays of scalars because
  those are the only values the bridge can encode deterministically as query
  parameters.
- Every response body returned by a target must be strict, finite JSON and is
  size/depth/node bounded even when `outputSchema` is omitted. `HEAD` and HTTP
  204/205 responses are the bodyless exceptions and return `body: null`. When a
  schema is present, successful responses with bodies are additionally
  validated before return. If a write was dispatched but its response is
  non-successful, redirected, unreadable, or invalid, MCP reports that the
  outcome is unknown and warns callers not to retry blindly. Local argument and
  header failures occur before this ambiguity boundary and are safe to correct.
- Manifests, schemas, tool counts, input/output size, nesting, and node counts
  are bounded. One scan accepts at most 128 plugin roots, 512 aggregate tools,
  257 discovery requests, 2 MiB of aggregate discovery bodies, and 30 seconds
  overall. The remaining aggregate allowance is applied while each response is
  streamed using its pre-decoding decompressed byte count, and non-success
  bodies count too. Each manifest is limited to 256 KiB and 64 tools; each
  target body is limited to 256 KiB.

The advertised schema is a caller contract, not an authorization mechanism.
The target DRF view must continue to enforce its normal NetBox permissions and
validate the same request body.

## MCP usage

Discover one plugin or every participating plugin:

```json
{
  "plugin": "example"
}
```

Pass that object to `plugin_list_tools`. The result includes the validated
descriptor, its qualified name, and the resolved request path. During an
all-plugin scan, one invalid advertisement is reported in `problems` without
hiding valid plugins. Selecting that invalid plugin directly fails closed.

Invoke a listed tool with `plugin_call_tool`:

```json
{
  "plugin": "example",
  "tool": "run_report",
  "arguments": {"scope": "active"},
  "dry_run": true
}
```

Reads dispatch immediately after discovery and validation. Writes and
destructive operations remain disabled unless the MCP server was started with
`NETBOX_MCP_ALLOW_MUTATIONS=1` or `--allow-mutations`. A plugin-tool dry-run
does perform the live GET requests needed to discover and validate the current
manifest, but it never dispatches the advertised target operation.

Discovery and target dispatch use the SDK's bounded bridge transport: HTTP
redirects are never followed, `3xx` responses fail closed, discovery bypasses
the ordinary HTTP cache and stale-if-error behavior, `Content-Length` is checked
before reading, and decompressed/chunked bytes are counted while streaming.
Consequently a removed advertisement or write tool cannot remain authorized by
a stale SDK cache, and a redirect cannot forward a mutation outside the fixed
plugin path.

## Plugin author checklist

1. Reuse an existing permission-gated DRF endpoint for the operation.
2. Add a read-only manifest view at `/api/plugins/<plugin>/mcp/`.
3. Advertise that exact path from the plugin API root with schema version `1`.
4. Keep every target path fixed and plugin-local; encode parameters in the
   strict input schema, not in the path template.
5. Match method, effect, annotations, and the endpoint serializer exactly.
6. Add contract tests for the advertisement, manifest, permissions, request
   schema, response schema, and absence of a parallel credential or MCP stack.

Proxbox is the canonical implementation example: it advertises
`list_sync_jobs` and `schedule_sync`, both backed by its existing
`sync/schedule/` API view.
