# Developer Guide

Technical documentation for contributors and anyone building on top of `netbox-sdk`.

- [Architecture](architecture.md) — module map, three-package dependency direction, data flow, and packaging
- [SDK Internals](sdk-internals.md) — how the client, config, schema, facade, cache, and services modules work internally
- [Integration with proxbox-api](integration-with-proxbox-api.md) — session factory, REST helpers, concurrency, caching, retry, and real-world integration patterns
- [Package integration](package-integration.md) — PyPI extras, `netbox_sdk` / `netbox_cli` / `netbox_tui`, import rules
- [Design principles](design-principles.md) — SOLID-aligned conventions for this repo
- [Textual Composition Pattern](textual-composition.md) — React-style composition guideline for Textual widgets
- [Documentation Generation](docgen.md) — the command capture system and CI workflow
