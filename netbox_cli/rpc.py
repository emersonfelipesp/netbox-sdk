"""``nbx rpc`` commands for the complete netbox-rpc API contract."""

from __future__ import annotations

import math
from typing import Any

import typer

from netbox_cli.dynamic import _build_action_command
from netbox_cli.runtime import _get_client
from netbox_cli.support import print_response, run_with_spinner
from netbox_cli.write_confirmation import require_write_confirmation
from netbox_sdk.rpc import RPCClient, build_rpc_schema_index, rpc_resources
from netbox_sdk.schema import SchemaIndex
from netbox_sdk.services import load_json_payload

rpc_app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Manage the netbox-rpc catalog and audited execution lifecycle.",
)


def _rpc_index_factory() -> SchemaIndex:
    return build_rpc_schema_index()


def _print(response: Any, *, as_json: bool) -> None:
    print_response(response.status, response.text, as_json=as_json)


def _load_object(body_json: str | None, body_file: str | None) -> dict[str, Any]:
    value = load_json_payload(body_json, body_file)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise typer.BadParameter("RPC action bodies must be JSON objects")
    return value


def _run_rpc(coro: Any) -> Any:
    client = _get_client()
    return run_with_spinner(coro(client), close=client)


procedures_app = typer.Typer(no_args_is_help=True, help="RPC procedure catalog.")
intents_app = typer.Typer(no_args_is_help=True, help="Grouped RPC intents.")
executions_app = typer.Typer(no_args_is_help=True, help="RPC execution lifecycle.")


@procedures_app.command("available")
def available_procedures(
    target_type: str | None = typer.Option(None, "--target-type"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    async def invoke(client: Any) -> Any:
        return await RPCClient(client).available_procedures(target_type=target_type)

    _print(_run_rpc(invoke), as_json=as_json)


@procedures_app.command("commands")
def procedure_commands(
    procedure_id: int = typer.Option(..., "--id", min=1),
    body_json: str | None = typer.Option(None, "--body-json"),
    body_file: str | None = typer.Option(None, "--body-file"),
    confirm: bool = typer.Option(False, "--confirm"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    payload = None
    if body_json is not None or body_file is not None:
        require_write_confirmation(confirmed=confirm)
        payload = _load_object(body_json, body_file)

    async def invoke(client: Any) -> Any:
        return await RPCClient(client).procedure_commands(procedure_id, payload=payload)

    _print(_run_rpc(invoke), as_json=as_json)


@intents_app.command("run")
def run_intent(
    intent_id: int = typer.Option(..., "--id", min=1),
    assigned_object_type: str = typer.Option(..., "--assigned-object-type"),
    assigned_object_id: int = typer.Option(..., "--assigned-object-id", min=1),
    params_json: str | None = typer.Option(None, "--params-json"),
    params_file: str | None = typer.Option(None, "--params-file"),
    confirm: bool = typer.Option(False, "--confirm"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    require_write_confirmation(confirmed=confirm)
    params = _load_object(params_json, params_file)

    async def invoke(client: Any) -> Any:
        return await RPCClient(client).run_intent(
            intent_id,
            assigned_object_type=assigned_object_type,
            assigned_object_id=assigned_object_id,
            params=params,
        )

    _print(_run_rpc(invoke), as_json=as_json)


def _execution_action_command(action: str) -> Any:
    def command(
        execution_id: int = typer.Option(..., "--id", min=1),
        reason: str | None = typer.Option(None, "--reason"),
        confirm: bool = typer.Option(False, "--confirm"),
        as_json: bool = typer.Option(False, "--json"),
    ) -> None:
        require_write_confirmation(confirmed=confirm)

        async def invoke(client: Any) -> Any:
            return await RPCClient(client).execution_action(execution_id, action, reason=reason)

        _print(_run_rpc(invoke), as_json=as_json)

    return command


for _action in ("cancel", "approve", "reject"):
    executions_app.command(_action)(_execution_action_command(_action))


@executions_app.command("events")
def execution_events(
    execution_id: int = typer.Option(..., "--id", min=1),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    async def invoke(client: Any) -> Any:
        return await RPCClient(client).execution_events(execution_id)

    _print(_run_rpc(invoke), as_json=as_json)


@executions_app.command("wait")
def wait_for_execution(
    execution_id: int = typer.Option(..., "--id", min=1),
    timeout: float = typer.Option(300.0, "--timeout", min=0.1),
    interval: float = typer.Option(2.0, "--interval", min=0.1),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    if not math.isfinite(timeout) or not math.isfinite(interval):
        raise typer.BadParameter("--timeout and --interval must be finite")

    async def invoke(client: Any) -> Any:
        return await RPCClient(client).wait_for_execution(
            execution_id, timeout=timeout, interval=interval
        )

    _print(_run_rpc(invoke), as_json=as_json)


def _register_rpc_resource_commands() -> None:
    apps = {
        "procedures": procedures_app,
        "intents": intents_app,
        "executions": executions_app,
    }
    for spec in rpc_resources():
        leaf = apps.get(spec.command)
        if leaf is None:
            leaf = typer.Typer(no_args_is_help=True, help=f"RPC {spec.command} records.")
            rpc_app.add_typer(leaf, name=spec.command)
        for action in spec.supported_actions:
            leaf.command(action)(
                _build_action_command(
                    group="plugins",
                    resource=spec.resource,
                    action=action,
                    client_factory=lambda: _get_client(),
                    index_factory=_rpc_index_factory,
                    dry_run_index_factory=_rpc_index_factory,
                )
            )


rpc_app.add_typer(procedures_app, name="procedures")
rpc_app.add_typer(intents_app, name="intents")
rpc_app.add_typer(executions_app, name="executions")
_register_rpc_resource_commands()

__all__ = ["rpc_app"]
