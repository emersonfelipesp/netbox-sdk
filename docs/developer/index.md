# Developer Guide

Technical documentation for contributors and anyone building on top of `netbox-sdk`.

- [Architecture](architecture.md) — module map, three-package dependency direction, data flow, and packaging
- [SDK Internals](sdk-internals.md) — how the client, config, schema, facade, cache, and services modules work internally
- [Integration with proxbox-api](integration-with-proxbox-api.md) — session factory, REST helpers, concurrency, caching, retry, and real-world integration patterns
- [Package integration](package-integration.md) — PyPI extras, `netbox_sdk` / `netbox_cli` / `netbox_tui`, import rules
- [Design principles](design-principles.md) — SOLID-aligned conventions for this repo
- [Textual Composition Pattern](textual-composition.md) — React-style composition guideline for Textual widgets
- [Documentation Generation](docgen.md) — the command capture system and CI workflow
- [IDE Support](ide-support.md) — VS Code workspace, Pylance via PEP 561 markers, and the dual `ty` + `pyright` checker gates

## Pull-request quality gates

Gitea pull requests targeting `main` run `.gitea/workflows/ci.yml` without
secrets on the isolated `ci-untrusted-python312` runner. The gate verifies the
locked environment, workflow policy, ty, Pyright, all-files pre-commit, the
complete offline mocked suite, all SDK/CLI/TUI security modules, strict MkDocs,
distribution metadata, and an installed-wheel smoke. It cannot publish, deploy,
push, or contact a live NetBox service.

GitHub continues to own the Python 3.11–3.13 and live-NetBox matrices. Gitea
validates `refs/pull/<N>/head`; branch protection must require the PR head to be
current with `main` as well as requiring all terminal contexts. A queued job
with `runner_id: 0` is missing evidence and must never be treated as a pass.
