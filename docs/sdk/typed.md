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
`v4.6.6`, `v4.6.3`, `v4.6.2`, and `v4.5.10`.

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

## Generated artifacts

The repository ships committed OpenAPI bundles, generated Pydantic models, and
generated typed endpoint bindings for the supported release lines. Users do not
need to run code generation locally.

Relevant modules:

- `netbox_sdk.models.v4_6`
- `netbox_sdk.models.v4_5`
- `netbox_sdk.models.v4_4`
- `netbox_sdk.models.v4_3`
- `netbox_sdk.typed_versions.v4_6`
- `netbox_sdk.typed_versions.v4_5`
- `netbox_sdk.typed_versions.v4_4`
- `netbox_sdk.typed_versions.v4_3`

## Choosing between SDK layers

- Use `NetBoxApiClient` for raw request control
- Use `api()` for the async ergonomic facade
- Use `typed_api()` for versioned Pydantic-validated I/O

### NetBox 4.7 (preview) — service write migration

NetBox 4.7 replaces a service's single `protocol` + `ports` pair with
`port_mappings`. Upstream's **writable** service models drop `protocol`
accordingly (the schema marks it "Deprecated; use port_mappings. Reported only
for single-protocol services"), while the **read** models still report it.
`netbox-sdk`'s generated 4.7 bindings mirror that exactly.

The practical consequence when moving a caller from 4.6 to 4.7:

```python
# 4.6 — accepted on write
api.ipam.services.create({"name": "ssh", "protocol": "tcp", "ports": [22], ...})

# 4.7 — `protocol` is NOT part of the write contract and is silently ignored.
# Use port_mappings instead:
api.ipam.services.create({"name": "dns", "port_mappings": ["tcp/53", "udp/53"], ...})
```

Because the generated models use Pydantic's default `extra="ignore"`, passing
`protocol` to a 4.7 write does **not** raise — the field is dropped before the
request is sent. Audit service writes when pinning 4.7. This behaviour is pinned
by `tests/test_typed_sdk.py::test_v47_service_write_contract_matches_upstream_and_v46_migration_is_pinned`.
