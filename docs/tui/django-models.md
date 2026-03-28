# Django Models Browser

The Django model browser is the most specialized TUI in the repository. It is
intended for contributors and advanced operators who need to inspect NetBox's
internal Django model graph rather than interact with the REST API.

## Commands

```bash
nbx dev django-model build
nbx dev django-model tui

nbx demo dev django-model tui
```

## Workflow

1. Build or fetch a model graph cache.
2. Launch the TUI against that cache.
3. Inspect models, relationships, and source excerpts interactively.

The cache is written under the NetBox SDK config root on new installs, with
compatibility support for older `netbox-cli` cache paths.

## Best use cases

- contributor-oriented model inspection
- schema and relationship debugging
- validating how NetBox source models map to API behavior

## Screenshots

- [Django Models Browser gallery](screenshots-django.md)
