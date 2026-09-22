"""First-class ``nbx openbao`` commands."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import typer

from netbox_cli.dynamic import _build_action_command
from netbox_cli.runtime import _get_client
from netbox_cli.support import print_response, run_with_spinner
from netbox_cli.write_confirmation import require_write_confirmation
from netbox_sdk.client import NetBoxApiClient
from netbox_sdk.openbao import (
    DEFAULT_SNAPSHOT_LIMIT,
    OpenBaoClient,
    build_openbao_schema_index,
    openbao_actions,
    openbao_resources,
)
from netbox_sdk.schema import SchemaIndex
from netbox_sdk.services import load_json_payload, parse_header_pairs, parse_key_value_pairs

openbao_app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Manage credentials and reviewed OpenBao administration through NetBox.",
)
actions_app = typer.Typer(no_args_is_help=True, help="Maintained custom REST actions.")
snapshot_app = typer.Typer(no_args_is_help=True, help="Bounded Raft snapshot transfer.")


class _OpenBaoOneShotClient:
    """Present the dynamic CLI client API while forcing one-shot dispatch."""

    def __init__(self, client: Any) -> None:
        self._client = client

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        kwargs.pop("use_cache", None)
        return await self._client.request_one_shot(method, path, **kwargs)

    async def close(self) -> None:
        await self._client.close()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)


def _get_openbao_client() -> _OpenBaoOneShotClient:
    return _OpenBaoOneShotClient(_get_client())


def _write_private_exclusive(path: Path, data: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError as exc:
        raise typer.BadParameter(
            "Output already exists; refusing to overwrite", param_hint="--output"
        ) from exc
    identity = os.fstat(descriptor)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        try:
            current = path.lstat()
            if (current.st_dev, current.st_ino) == (identity.st_dev, identity.st_ino):
                path.unlink()
        except FileNotFoundError:
            pass
        raise


def _index() -> SchemaIndex:
    return build_openbao_schema_index()


def _load_object(body_json: str | None, body_file: str | None) -> dict[str, Any] | None:
    value = load_json_payload(body_json, body_file)
    if value is not None and not isinstance(value, dict):
        raise typer.BadParameter("OpenBao action bodies must be JSON objects")
    return value


def _run(coro: Any) -> Any:
    client = _get_client()
    return run_with_spinner(coro(client), close=client)


@openbao_app.command("resources")
def list_resources() -> None:
    """Print the fixed collection and action catalog without a client."""
    for spec in openbao_resources():
        typer.echo(f"resource {spec.command}: {', '.join(spec.supported_actions)}")
    for spec in openbao_actions():
        suffix = " (planned)" if spec.planned else ""
        typer.echo(f"action {spec.command}: {'|'.join(spec.methods)} {spec.path_template}{suffix}")


def _action_command(action_key: str, *, binary: str, default_method: str, material: bool) -> Any:
    def command(
        object_id: int | None = typer.Option(None, "--id", min=1),
        path_param: list[str] | None = typer.Option(
            None, "--path-param", help="Path key=value (repeatable)."
        ),
        method: str | None = typer.Option(None, "--method"),
        query: list[str] | None = typer.Option(None, "-q", "--query"),
        header: list[str] | None = typer.Option(None, "-H", "--header"),
        body_json: str | None = typer.Option(None, "--body-json"),
        body_file: str | None = typer.Option(None, "--body-file"),
        confirm: bool = typer.Option(False, "--confirm"),
        as_json: bool = typer.Option(False, "--json"),
    ) -> None:
        if binary != "none":
            raise typer.BadParameter("Use the openbao snapshot download/upload commands")
        try:
            parsed_path_values = parse_key_value_pairs(path_param or [])
            query_values = parse_key_value_pairs(query or [])
            headers = parse_header_pairs(header or [])
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc
        if any(isinstance(value, list) for value in parsed_path_values.values()):
            raise typer.BadParameter(
                "OpenBao path parameters cannot be repeated", param_hint="--path-param"
            )
        path_values: dict[str, str | int] = {
            key: str(value) for key, value in parsed_path_values.items()
        }
        if object_id is not None:
            path_values["id"] = str(object_id)
        selected_method = (method or default_method).upper()
        if material or selected_method not in {"GET", "HEAD"}:
            require_write_confirmation(confirmed=confirm)
        payload = _load_object(body_json, body_file)

        async def invoke(client: Any) -> Any:
            return await OpenBaoClient(client).request_action(
                action_key,
                method=selected_method,
                path_parameters=path_values,
                query=query_values or None,
                payload=payload,
                headers=headers or None,
            )

        response = _run(invoke)
        print_response(response.status, response.text, as_json=as_json)

    return command


def _register_commands() -> None:
    for spec in openbao_resources():
        leaf = typer.Typer(no_args_is_help=True, help=f"OpenBao {spec.command} records.")
        openbao_app.add_typer(leaf, name=spec.command)
        for action in spec.supported_actions:
            leaf.command(action)(
                _build_action_command(
                    group="plugins",
                    resource=spec.resource,
                    action=action,
                    client_factory=cast(Callable[[], NetBoxApiClient], _get_openbao_client),
                    index_factory=_index,
                    dry_run_index_factory=_index,
                )
            )
    for spec in openbao_actions():
        actions_app.command(spec.command)(
            _action_command(
                spec.key,
                binary=spec.binary,
                default_method=spec.methods[0],
                material=spec.material,
            )
        )


@snapshot_app.command("download")
def download_snapshot(
    cluster_id: int = typer.Option(..., "--id", min=1),
    output: Path = typer.Option(..., "--output"),
    method: str = typer.Option("GET", "--method"),
    body_json: str | None = typer.Option(None, "--body-json"),
    body_file: str | None = typer.Option(None, "--body-file"),
    max_bytes: int = typer.Option(DEFAULT_SNAPSHOT_LIMIT, "--max-bytes", min=1),
    confirm: bool = typer.Option(False, "--confirm"),
) -> None:
    selected = method.upper()
    if selected not in {"GET", "POST"}:
        raise typer.BadParameter(
            "Snapshot download method must be GET or POST", param_hint="--method"
        )
    require_write_confirmation(confirmed=confirm)
    payload = _load_object(body_json, body_file)

    async def invoke(client: Any) -> bytes:
        return await OpenBaoClient(client).download_snapshot(
            cluster_id, method=selected, payload=payload, max_bytes=max_bytes
        )

    data = _run(invoke)
    _write_private_exclusive(output, data)
    typer.echo(f"Wrote {len(data)} bytes to {output}")


@snapshot_app.command("upload")
def upload_snapshot(
    cluster_id: int = typer.Option(..., "--id", min=1),
    source: Path = typer.Option(..., "--input"),
    force: bool = typer.Option(False, "--force"),
    reason: str = typer.Option(..., "--reason"),
    confirmation: str = typer.Option(..., "--confirmation"),
    openbao_cluster_id: str = typer.Option(..., "--openbao-cluster-id"),
    configuration_index: int = typer.Option(..., "--raft-index", min=0),
    header: list[str] | None = typer.Option(None, "-H", "--header"),
    max_bytes: int = typer.Option(DEFAULT_SNAPSHOT_LIMIT, "--max-bytes", min=1),
    confirm: bool = typer.Option(False, "--confirm"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    require_write_confirmation(confirmed=confirm)
    try:
        headers = parse_header_pairs(header or [])
    except ValueError as exc:
        raise typer.BadParameter(str(exc), param_hint="--header") from exc

    async def invoke(client: Any) -> Any:
        return await OpenBaoClient(client).upload_snapshot(
            cluster_id,
            source,
            force=force,
            reason=reason,
            confirmation=confirmation,
            openbao_cluster_id=openbao_cluster_id,
            configuration_index=configuration_index,
            headers=headers or None,
            max_bytes=max_bytes,
        )

    response = _run(invoke)
    print_response(response.status, response.text, as_json=as_json)


openbao_app.add_typer(actions_app, name="actions")
openbao_app.add_typer(snapshot_app, name="snapshot")
_register_commands()

__all__ = ["openbao_app"]
