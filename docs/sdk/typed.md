# Typed API

`netbox_sdk` ships a versioned typed client alongside the raw client and async
facade.

Use `typed_api()` when you want:

- request payload validation before HTTP
- response payload validation after HTTP
- editor and type-checker support for endpoint methods and models
- explicit NetBox version selection

## Entry point

```python
from netbox_sdk import typed_api

nb = typed_api(
    "https://netbox.example.com",
    token="your-token",
    netbox_version="4.5",
)
```

Supported release lines:

- `4.6`
- `4.5`
- `4.4`
- `4.3`

Patch versions normalize to their release line, so `4.4.10` selects the `4.4`
typed client.

Continuous integration exercises the live-NetBox suite against
`v4.7.0-beta2`, `v4.6.6`, `v4.6.3`, `v4.6.2`, and `v4.5.10`.

## Example

```python
import asyncio

from netbox_sdk import typed_api


async def main() -> None:
    nb = typed_api(
        "https://netbox.example.com",
        token="your-token",
        netbox_version="4.5",
    )
    device = await nb.dcim.devices.get(42)
    if device is not None:
        print(device.name)


asyncio.run(main())
```

## Validation behavior

- Request bodies are validated before HTTP and raise `TypedRequestValidationError`
- Response bodies are validated after HTTP and raise `TypedResponseValidationError`
- Unsupported versions raise `UnsupportedNetBoxVersionError`

### Bulk responses are validated against the shape the server returns

NetBox reuses the collection path for bulk operations. Posting a **single**
object returns that object; posting a **list** commits the batch and returns a
**list**. The upstream OpenAPI document declares only the singular response for
that path, so the generated bindings declare only the singular model:

```python
async def create(self, body: WritableSiteRequest | list[WritableSiteRequest]) -> Site: ...
```

The runtime therefore selects the response model from the shape of the request
payload: a list body is validated as `list[Model]`, a single body as `Model`.
Without this, a committed batch would raise `TypedResponseValidationError`
*after the server had already applied every object* — and the natural reaction,
a retry, would create duplicates.

This applies to `POST`, `PUT` (`bulk-update`) and `PATCH` (`bulk-patch`) alike,
because all of them route through one request path. Bulk `DELETE` answers with a
bodyless `204`, so there is nothing to validate and the call returns `None`.

### Background bulk operations (NetBox 4.7)

NetBox 4.7 accepts `?background=true` on bulk `POST`/`PUT`/`PATCH`/`DELETE`. The
batch is queued instead of executed inline, and the response is `202` carrying a
job reference rather than the committed objects — the feature exists to avoid
proxy timeouts on large batches.

```python
result = await api.dcim.sites.create(
    body=[{"name": "B1", "slug": "b1"}, {"name": "B2", "slug": "b2"}],
    query={"background": True},
)
result.job.id      # 4211
result.job.status  # "pending"
```

The runtime selects the response model from the request: an affirmative
`background` flag yields `BackgroundJobReference`, and that takes precedence over
body shape, because a queued batch returns a job for either a single object or a
list. Without the flag, nothing changes.

> **This is an overlay, pending upstream schema support.** The pinned 4.7
> artifact (`v4.7.0-beta2`) does not describe the parameter, so the generator
> declares it on bulk JSON-array writes while keeping the committed bundle
> byte-faithful to upstream. Singular collection paths such as the extras
> dashboard are not overlaid. A guard test fails once a refreshed 4.7 schema
> describes `background` itself, so the overlay cannot outlive its reason to
> exist.

## Generated artifacts

The repository ships committed OpenAPI bundles, generated Pydantic models, and
generated typed endpoint bindings for the supported release lines. Users do not
need to run code generation locally.

Relevant modules:

- `netbox_sdk.models.v4_6`
- `netbox_sdk.models.v4_7` (preview)
- `netbox_sdk.models.v4_5`
- `netbox_sdk.models.v4_4`
- `netbox_sdk.models.v4_3`
- `netbox_sdk.typed_versions.v4_6`
- `netbox_sdk.typed_versions.v4_7` (preview)
- `netbox_sdk.typed_versions.v4_5`
- `netbox_sdk.typed_versions.v4_4`
- `netbox_sdk.typed_versions.v4_3`

## Choosing between SDK layers

- Use `NetBoxApiClient` for raw request control
- Use `api()` for the async ergonomic facade
- Use `typed_api()` for versioned Pydantic-validated I/O

### NetBox 4.7 (preview) — service port mappings

NetBox 4.7 adds `port_mappings`, letting a service expose several protocols at
once (DNS on both `tcp/53` and `udp/53`). The legacy single-protocol
`protocol` + `ports` pair still works on write: upstream's shared serializer
documents that *"either format is accepted"*, translating the legacy pair into
`port_mappings` when `port_mappings` is not supplied. Supplying both is accepted
only when they agree; a genuine conflict is rejected as ambiguous.

```python
# Still accepted on 4.7 — translated server-side into port_mappings
api.ipam.services.create({"name": "ssh", "protocol": "tcp", "ports": [22], ...})

# 4.7-native, and the only way to express multiple protocols
api.ipam.services.create({"name": "dns", "port_mappings": ["tcp/53", "udp/53"], ...})
```

On read, a single-protocol service reports `port_mappings` **and** the legacy
`protocol`/`ports`; a multi-protocol service reports `null` for both, because it
cannot be expressed in the old format.

> **Generation note.** `drf-spectacular` omits `protocol` from the *writable*
> service models' `properties` block even though the documented write contract
> accepts it. `netbox-sdk` restores it with a deterministic generation overlay
> (`scripts/generate_typed_sdk.py::apply_write_compat_overlay`) applied in memory
> only — the committed OpenAPI bundle stays byte-faithful to the pinned upstream
> artifact. Without it, a PATCH of `{"protocol": "udp", "ports": [53]}` would be
> sent as `{"ports": [53]}` and NetBox would backfill the stored protocol,
> silently ignoring the change.
