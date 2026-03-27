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

- `4.5`
- `4.4`
- `4.3`

Patch versions normalize to their release line, so `4.4.10` selects the `4.4`
typed client.

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

- `netbox_sdk.models.v4_5`
- `netbox_sdk.models.v4_4`
- `netbox_sdk.models.v4_3`
- `netbox_sdk.typed_versions.v4_5`
- `netbox_sdk.typed_versions.v4_4`
- `netbox_sdk.typed_versions.v4_3`

## Choosing between SDK layers

- Use `NetBoxApiClient` for raw request control
- Use `api()` for the async ergonomic facade
- Use `typed_api()` for versioned Pydantic-validated I/O
