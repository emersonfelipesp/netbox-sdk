# CLI

`nbx` is the command-line interface for NetBox SDK. It shares configuration,
schema discovery, and request logic with the Python SDK and the TUI layer.

It supports four complementary interaction modes:

| Mode | Example | When to use |
|------|---------|-------------|
| **Dynamic** | `nbx dcim devices list` | Day-to-day operations — auto-discovered from OpenAPI |
| **Explicit HTTP** | `nbx call GET /api/status/` | Custom paths, bulk API exploration |
| **Discovery** | `nbx groups` / `nbx resources dcim` | Learning what's available |
| **GraphQL** | `nbx graphql "{ sites { name } }"` | Cross-resource queries and schema experimentation |

---

## Command tree overview

```
nbx
├── init                    configure the default profile
├── config                  show current configuration
├── groups                  list all OpenAPI app groups
├── resources GROUP         list resources for a group
├── ops GROUP RESOURCE      list operations for a resource
├── graphql                 execute GraphQL queries
├── call METHOD PATH        explicit HTTP request
├── tui                     launch the main Textual browser
├── logs                    show recent structured application logs
├── cli                     CLI-specific helpers
│   └── tui                 launch guided command builder
├── docs                    documentation generation tools
│   └── generate-capture    capture CLI output to docs/generated/
├── demo                    demo.netbox.dev profile
│   ├── init                authenticate with demo.netbox.dev
│   ├── config              show demo profile config
│   ├── reset               remove saved demo credentials
│   ├── tui                 launch TUI with demo profile
│   ├── cli                 command builder against demo profile
│   │   └── tui             launch guided command builder on demo profile
│   ├── dev                 developer tools with demo profile
│   │   ├── tui             launch Dev TUI with demo profile
│   │   └── django-model    inspect NetBox Django models
│   └── <group> <resource>  same command tree as root, using demo profile
├── dev                     developer tools and experimental interfaces
│   ├── tui                 launch developer request workbench
│   ├── http                direct HTTP helpers for arbitrary API paths
│   └── django-model        build/fetch/browse NetBox Django models
└── <group>                 OpenAPI app group (dcim, ipam, …)
    └── <resource>          resource (devices, prefixes, …)
        ├── list            GET list endpoint
        ├── get             GET detail endpoint (requires --id)
        ├── create          POST
        ├── update          PUT (requires --id)
        ├── patch           PATCH (requires --id)
        └── delete          DELETE (requires --id)
```

---

- [Commands](commands.md) for the top-level command set
- [Dynamic Commands](dynamic-commands.md) for OpenAPI-driven resource operations
- [GraphQL](graphql.md) for GraphQL-specific usage
- [Demo Profile](demo-profile.md) for the `nbx demo` command tree
- [Command Examples](../reference/command-examples/index.md) for captured CLI output
