# RPC Plugin

`netbox_sdk.rpc` provides the maintained Python contract for the officially
supported `netbox-rpc` plugin. `netbox_sdk.plugins` identifies `netbox-rpc` and
`netbox-proxbox` as first-class integrations; other plugins remain available
through runtime discovery when standard REST operations are sufficient.

## Official support registry

```python
from netbox_sdk import official_plugin, official_plugins

assert [plugin.package for plugin in official_plugins()] == [
    "netbox-rpc",
    "netbox-proxbox",
]
rpc_plugin = official_plugin("rpc")
assert rpc_plugin is not None
assert rpc_plugin.sdk_module == "netbox_sdk.rpc"
```

The registry is descriptive and immutable. It does not disable generic plugin
discovery or imply that every discovered plugin has maintained workflow methods.

## Collection specifications

`rpc_resources()` returns eight frozen `RPCResourceSpec` values for settings,
backends, procedures, procedure commands, intents, the Linux service allowlist,
executions, and execution events. Each specification owns its list/detail paths
and allowed methods; `supported_actions` derives the SDK and CLI actions.

Use `build_rpc_schema_index()` for an isolated RPC-only index, or
`register_rpc_resources(index)` to add the fixed contract to an existing
`SchemaIndex`. This avoids a network probe and prevents generic discovery from
guessing workflow semantics.

## Standard and bulk requests

```python
import asyncio

from netbox_sdk import Config, NetBoxApiClient, RPCClient


async def main() -> None:
    config = Config(
        base_url="https://netbox.example.com",
        token_version="v1",
        token_secret="token",
    )
    async with NetBoxApiClient(config) as transport:
        rpc = RPCClient(transport)
        backends = await rpc.request("backends", "list", query={"limit": 50})
        backend = await rpc.request("backends", "get", object_id=7)
        updated = await rpc.request(
            "backends", "patch", object_id=7, payload={"verify_ssl": True}
        )
        batch = await rpc.request(
            "backends", "bulk-patch", payload=[{"id": 7, "verify_ssl": True}]
        )


asyncio.run(main())
```

Unsupported resource/action pairs fail before HTTP dispatch. Bulk actions take
an array payload and target the collection path.

## Workflow methods

```python
import asyncio

from netbox_sdk import Config, NetBoxApiClient, RPCClient


async def main() -> None:
    config = Config(
        base_url="https://netbox.example.com",
        token_version="v1",
        token_secret="token",
    )
    async with NetBoxApiClient(config) as transport:
        rpc = RPCClient(transport)
        available = await rpc.available_procedures(target_type="dcim.device")
        commands = await rpc.procedure_commands(6)
        command_result = await rpc.procedure_commands(6, payload={"argv": ["true"]})
        execution = await rpc.run_intent(
            2,
            assigned_object_type="dcim.device",
            assigned_object_id=42,
            params={"service_slug": "nginx"},
        )
        approved = await rpc.execution_action(100, "approve", reason="reviewed")
        rejected = await rpc.execution_action(101, "reject", reason="unsafe")
        cancelled = await rpc.execution_action(102, "cancel")
        events = await rpc.execution_events(100)
        terminal = await rpc.wait_for_execution(100, timeout=300, interval=2)


asyncio.run(main())
```

`execution_action()` accepts only `cancel`, `approve`, and `reject`.
`wait_for_execution()` requires finite positive bounds and stops on `succeeded`,
`failed`, `cancelled`, `rejected`, or `expired`; `approved` remains nonterminal.
HTTP errors return immediately. A nonterminal or malformed successful response
is polled until the deadline and then raises `TimeoutError`.

## Safety and maintenance

NetBox owns permissions, target restrictions, JSON Schema admission, approval
requirements, and audit records. Callers own confirmation for mutations; the
`nbx rpc` layer enforces it before client construction. Do not log tokens,
credential-bearing parameters, or secret response bodies.

When the plugin contract changes, update `RPC_RESOURCES`, semantic methods, the
exact SDK and CLI transport tests, both bilingual RPC guides, and the root and
subsystem agent files in one reviewed change.
