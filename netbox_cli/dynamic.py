"""Dynamic command resolution and OpenAPI-driven subcommand registration.

Handles ``nbx <group> <resource> <action>`` free-form invocations as well as
the ``_register_openapi_subcommands`` builder that wires up all schema-derived
Typer command trees at startup.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from importlib import import_module
from typing import Any

import typer

from netbox_cli.support import (
    print_response,
    print_trace_output,
    resolve_output_format,
    run_with_spinner,
)
from netbox_sdk.client import ApiResponse, NetBoxApiClient
from netbox_sdk.schema import SchemaIndex

logger = logging.getLogger(__name__)


def _runtime_get_client() -> NetBoxApiClient:
    from netbox_cli.runtime import (
        _get_client,  # noqa: PLC0415 — call-time import so tests can patch runtime._get_client
    )

    return _get_client()


def _runtime_get_index() -> SchemaIndex:
    from netbox_cli.runtime import _get_index  # noqa: PLC0415

    return _get_index()


def _run_dynamic_command(
    *,
    client: NetBoxApiClient,
    index: SchemaIndex,
    group: str,
    resource: str,
    action: str,
    object_id: int | None,
    query_pairs: list[str],
    body_json: str | None,
    body_file: str | None,
) -> Any:
    """Invoke :func:`netbox_sdk.services.run_dynamic_command` (or patched CLI hook)."""
    cli_module = import_module("netbox_cli")
    fn = getattr(cli_module, "run_dynamic_command", None)
    if fn is None:
        from netbox_sdk.services import run_dynamic_command  # noqa: PLC0415

        fn = run_dynamic_command
    logger.debug(
        "dynamic command dispatch",
        extra={
            "nbx_event": "cli_dynamic_run",
            "group": group,
            "resource": resource,
            "action": action,
        },
    )
    return fn(
        client=client,
        index=index,
        group=group,
        resource=resource,
        action=action,
        object_id=object_id,
        query_pairs=query_pairs,
        body_json=body_json,
        body_file=body_file,
    )


def _handle_dynamic_invocation(
    raw_args: list[str],
    *,
    client_factory: Callable[[], NetBoxApiClient] = _runtime_get_client,
    index_factory: Callable[[], SchemaIndex] = _runtime_get_index,
) -> None:
    """Parse ``nbx <group> <resource> <action> ...`` argv tail and execute the resolved request."""
    if len(raw_args) < 3:
        raise typer.BadParameter(
            "Dynamic invocation requires: nbx <group> <resource> <action> [options]"
        )

    group, resource, action = raw_args[0], raw_args[1], raw_args[2]
    option_args = raw_args[3:]

    (
        object_id,
        query_pairs,
        body_json,
        body_file,
        as_json,
        as_yaml,
        as_markdown,
        trace,
        trace_only,
        select_path,
        columns,
        max_columns,
        dry_run,
    ) = _parse_dynamic_options(option_args)
    resolve_output_format(as_json=as_json, as_yaml=as_yaml, as_markdown=as_markdown)
    if trace and trace_only:
        raise typer.BadParameter("Use either --trace or --trace-only, not both.")
    if dry_run and action.lower() not in {"create", "update", "patch", "delete"}:
        raise typer.BadParameter(
            "--dry-run is only supported for write operations (create, update, patch, delete)"
        )
    action_lower = action.lower()
    write_actions = {"create", "update", "patch", "delete"}
    # Dry-run previews only need the OpenAPI index; avoid building an API client (and loading config).
    skip_client = bool(dry_run and action_lower in write_actions)
    index = index_factory()
    client = None if skip_client else client_factory()
    if client is not None and index.resource_paths(group, resource) is None:
        from netbox_sdk.plugin_discovery import (  # noqa: PLC0415
            enrich_schema_index_with_runtime_resources,
        )

        run_with_spinner(enrich_schema_index_with_runtime_resources(index, client))
    response = _execute_dynamic_action(
        group=group,
        resource=resource,
        action=action,
        object_id=object_id,
        query_pairs=query_pairs,
        body_json=body_json,
        body_file=body_file,
        select_path=select_path,
        columns=columns,
        max_columns=max_columns,
        dry_run=dry_run,
        client=client,
        index=index,
    )
    if not trace_only:
        if response is None:
            pass
        else:
            print_response(
                response.status,
                response.text,
                as_json=as_json,
                as_yaml=as_yaml,
                as_markdown=as_markdown,
                select_path=select_path,
                columns=columns,
                max_columns=max_columns,
            )
    if trace or trace_only:
        print_trace_output(
            group=group,
            resource=resource,
            action=action,
            object_id=object_id,
            client=client_factory(),
            index=index_factory(),
        )


def _parse_dynamic_options(
    args: list[str],
) -> tuple[
    int | None,
    list[str],
    str | None,
    str | None,
    bool,
    bool,
    bool,
    bool,
    bool,
    str | None,
    list[str] | None,
    int,
    bool,
]:
    object_id: int | None = None
    query_pairs: list[str] = []
    body_json: str | None = None
    body_file: str | None = None
    as_json: bool = False
    as_yaml: bool = False
    as_markdown: bool = False
    trace: bool = False
    trace_only: bool = False
    select_path: str | None = None
    columns: list[str] | None = None
    max_columns: int = 6
    dry_run: bool = False

    i = 0
    while i < len(args):
        token = args[i]
        if token in {"--id"}:
            if i + 1 >= len(args):
                raise typer.BadParameter("--id requires a value")
            object_id = int(args[i + 1])
            i += 2
            continue
        if token in {"-q", "--query"}:
            if i + 1 >= len(args):
                raise typer.BadParameter(f"{token} requires key=value")
            query_pairs.append(args[i + 1])
            i += 2
            continue
        if token == "--body-json":
            if i + 1 >= len(args):
                raise typer.BadParameter("--body-json requires a value")
            body_json = args[i + 1]
            i += 2
            continue
        if token == "--body-file":
            if i + 1 >= len(args):
                raise typer.BadParameter("--body-file requires a path")
            body_file = args[i + 1]
            i += 2
            continue
        if token == "--json":
            as_json = True
            i += 1
            continue
        if token == "--yaml":
            as_yaml = True
            i += 1
            continue
        if token == "--markdown":
            as_markdown = True
            i += 1
            continue
        if token == "--trace":
            trace = True
            i += 1
            continue
        if token == "--trace-only":
            trace_only = True
            i += 1
            continue
        if token == "--select":
            if i + 1 >= len(args):
                raise typer.BadParameter("--select requires a value")
            select_path = args[i + 1]
            i += 2
            continue
        if token == "--columns":
            if i + 1 >= len(args):
                raise typer.BadParameter("--columns requires a comma-separated list")
            columns = [c.strip() for c in args[i + 1].split(",") if c.strip()]
            i += 2
            continue
        if token == "--max-columns":
            if i + 1 >= len(args):
                raise typer.BadParameter("--max-columns requires a number")
            try:
                max_columns = int(args[i + 1])
                if max_columns < 1:
                    raise typer.BadParameter("--max-columns must be at least 1")
            except ValueError:
                raise typer.BadParameter("--max-columns must be a number")
            i += 2
            continue
        if token == "--dry-run":
            dry_run = True
            i += 1
            continue
        raise typer.BadParameter(f"Unknown option: {token}")

    return (
        object_id,
        query_pairs,
        body_json,
        body_file,
        as_json,
        as_yaml,
        as_markdown,
        trace,
        trace_only,
        select_path,
        columns,
        max_columns,
        dry_run,
    )


def _execute_dynamic_action(
    *,
    group: str,
    resource: str,
    action: str,
    object_id: int | None,
    query_pairs: list[str],
    body_json: str | None,
    body_file: str | None,
    select_path: str | None = None,
    columns: list[str] | None = None,
    max_columns: int = 6,
    dry_run: bool = False,
    client: NetBoxApiClient | None = None,
    index: SchemaIndex | None = None,
) -> ApiResponse | None:
    """Run OpenAPI-resolved request, or print dry-run preview when ``dry_run`` is True."""
    action_lower = action.lower()
    write_actions = {"create", "update", "patch", "delete"}

    if dry_run and action_lower in write_actions:
        from netbox_cli.support import print_dry_run
        from netbox_sdk.services import load_json_payload, resolve_dynamic_request

        resolved = resolve_dynamic_request(
            index or _runtime_get_index(),
            group,
            resource,
            action,
            object_id=object_id,
            query={},
            payload=None,
        )
        body = load_json_payload(body_json, body_file)
        return print_dry_run(
            method=resolved.method,
            path=resolved.path,
            body=body,
        )

    return run_with_spinner(
        _run_dynamic_command(
            client=client or _runtime_get_client(),
            index=index or _runtime_get_index(),
            group=group,
            resource=resource,
            action=action,
            object_id=object_id,
            query_pairs=query_pairs,
            body_json=body_json,
            body_file=body_file,
        )
    )


def _supported_actions(group: str, resource: str, *, index: SchemaIndex | None = None) -> list[str]:
    active_index = index or _runtime_get_index()
    rows = active_index.operations_for(group, resource)
    by_pair = {(item.path, item.method.upper()) for item in rows}
    paths = active_index.resource_paths(group, resource)
    if paths is None:
        return []

    actions: list[str] = []
    if paths.list_path and (paths.list_path, "GET") in by_pair:
        actions.append("list")
    if paths.detail_path and (paths.detail_path, "GET") in by_pair:
        actions.append("get")
    if paths.list_path and (paths.list_path, "POST") in by_pair:
        actions.append("create")
    if paths.detail_path and (paths.detail_path, "PUT") in by_pair:
        actions.append("update")
    if paths.detail_path and (paths.detail_path, "PATCH") in by_pair:
        actions.append("patch")
    if paths.detail_path and (paths.detail_path, "DELETE") in by_pair:
        actions.append("delete")
    return actions


def _build_action_command(
    *,
    group: str,
    resource: str,
    action: str,
    client_factory: Callable[[], NetBoxApiClient] = _runtime_get_client,
    index_factory: Callable[[], SchemaIndex] = _runtime_get_index,
) -> Callable[..., None]:
    requires_id = action in {"get", "update", "patch", "delete"}
    allows_body = action in {"create", "update", "patch"}

    def _command(
        object_id: int | None = typer.Option(None, "--id", help="Object ID for detail operations"),
        query: list[str] | None = typer.Option(
            None, "-q", "--query", help="Query parameter key=value"
        ),
        body_json: str | None = typer.Option(None, "--body-json", help="Inline JSON request body"),
        body_file: str | None = typer.Option(
            None, "--body-file", help="Path to JSON request body file"
        ),
        output_json: bool = typer.Option(False, "--json", help="Output raw JSON"),
        output_yaml: bool = typer.Option(False, "--yaml", help="Output YAML"),
        output_markdown: bool = typer.Option(
            False,
            "--markdown",
            help="Output Markdown (mutually exclusive with --json/--yaml)",
        ),
        trace: bool = typer.Option(
            False,
            "--trace",
            help="Fetch and render the cable trace as ASCII when supported.",
        ),
        trace_only: bool = typer.Option(
            False,
            "--trace-only",
            help="Render only the cable trace ASCII output when supported.",
        ),
        select_path: str | None = typer.Option(
            None, "--select", help="JSON dot-path to extract specific field from response"
        ),
        columns: str | None = typer.Option(
            None, "--columns", help="Comma-separated list of columns to display"
        ),
        max_columns: int = typer.Option(
            6, "--max-columns", help="Maximum number of columns to display"
        ),
        dry_run: bool = typer.Option(
            False,
            "--dry-run",
            help="Preview write operation without executing (create/update/patch/delete only)",
        ),
    ) -> None:
        if requires_id and object_id is None:
            raise typer.BadParameter("--id is required for this action")
        if not allows_body and (body_json is not None or body_file is not None):
            raise typer.BadParameter("This action does not accept a request body")
        resolve_output_format(
            as_json=output_json,
            as_yaml=output_yaml,
            as_markdown=output_markdown,
        )
        if trace and trace_only:
            raise typer.BadParameter("Use either --trace or --trace-only, not both.")
        if (trace or trace_only) and action != "get":
            raise typer.BadParameter("--trace and --trace-only are only supported for get actions")

        write_actions = {"create", "update", "patch", "delete"}
        if dry_run and action.lower() not in write_actions:
            raise typer.BadParameter(
                "--dry-run is only supported for write operations (create, update, patch, delete)"
            )

        client = None if dry_run else client_factory()
        index = index_factory()
        columns_list = [c.strip() for c in columns.split(",")] if columns else None
        response = _execute_dynamic_action(
            group=group,
            resource=resource,
            action=action,
            object_id=object_id,
            query_pairs=query or [],
            body_json=body_json,
            body_file=body_file,
            select_path=select_path,
            columns=columns_list,
            max_columns=max_columns,
            dry_run=dry_run,
            client=client,
            index=index,
        )
        if not trace_only:
            if response is None:
                pass
            else:
                print_response(
                    response.status,
                    response.text,
                    as_json=output_json,
                    as_yaml=output_yaml,
                    as_markdown=output_markdown,
                    select_path=select_path,
                    columns=columns_list,
                    max_columns=max_columns,
                )
        if trace or trace_only:
            print_trace_output(
                group=group,
                resource=resource,
                action=action,
                object_id=object_id,
                client=client or _runtime_get_client(),
                index=index,
            )

    return _command


def _register_openapi_subcommands(
    target_app: typer.Typer,
    *,
    client_factory: Callable[[], NetBoxApiClient] = _runtime_get_client,
    index_factory: Callable[[], SchemaIndex] = _runtime_get_index,
) -> None:
    """Attach ``<group>/<resource>/<action>`` Typer commands from the OpenAPI index."""
    index = index_factory()
    logger.info(
        "registering openapi subcommands",
        extra={"nbx_event": "cli_openapi_register", "group_count": len(index.groups())},
    )
    for group in index.groups():
        group_typer = typer.Typer(
            no_args_is_help=True,
            help=f"OpenAPI app group: {group}",
        )
        target_app.add_typer(group_typer, name=group)

        for resource in index.resources(group):
            resource_typer = typer.Typer(
                no_args_is_help=True,
                help=f"Resource: {group}/{resource}",
            )
            group_typer.add_typer(resource_typer, name=resource)

            for action in _supported_actions(group, resource, index=index):
                cmd = _build_action_command(
                    group=group,
                    resource=resource,
                    action=action,
                    client_factory=client_factory,
                    index_factory=index_factory,
                )
                resource_typer.command(name=action, help=f"{action} {group}/{resource}")(cmd)
