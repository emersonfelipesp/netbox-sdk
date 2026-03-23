# CLI Reference

`nbx` is the entry point for all command-line operations. It supports three complementary interaction modes:

| Mode | Example | When to use |
|------|---------|-------------|
| **Dynamic** | `nbx dcim devices list` | Day-to-day operations — auto-discovered from OpenAPI |
| **Explicit HTTP** | `nbx call GET /api/status/` | Custom paths, bulk API exploration |
| **Discovery** | `nbx groups` / `nbx resources dcim` | Learning what's available |

---

## Command tree overview

```
nbx
├── init                    configure the default profile
├── config                  show current configuration
├── groups                  list all OpenAPI app groups
├── resources GROUP         list resources for a group
├── ops GROUP RESOURCE      list operations for a resource
├── call METHOD PATH        explicit HTTP request
├── tui                     launch Textual TUI
├── logs                    view structured application logs in a TUI log viewer
├── docs                    documentation generation tools
│   └── generate-capture    capture CLI output to docs/generated/
├── demo                    demo.netbox.dev profile
│   ├── init                authenticate with demo.netbox.dev
│   ├── config              show demo profile config
│   ├── reset               remove saved demo credentials
│   ├── tui                 launch TUI with demo profile
│   ├── dev                 developer tools with demo profile
│   │   └── tui             launch Dev TUI with demo profile
│   └── <group> <resource>  same command tree as root, using demo profile
├── dev                     developer tools and experimental interfaces
│   ├── tui                 launch developer request workbench
│   └── http                direct HTTP helpers for arbitrary API paths
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

- [Commands](commands.md) — all top-level commands with options
- [Dynamic Commands](dynamic-commands.md) — how OpenAPI-driven resource commands work
- [Demo Profile](demo-profile.md) — the `nbx demo` subcommand tree
