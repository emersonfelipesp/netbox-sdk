"""Developer command group for the nbx CLI.

Registers ``nbx dev`` and its subcommands including the ``nbx dev http``
sub-app for direct HTTP operations against any OpenAPI path.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from pydantic import BaseModel, ValidationError, field_validator, model_validator
from rich.table import Table

from netbox_cli.runtime import _get_client, _get_index, dev_http_api_client
from netbox_cli.support import (
    console,
    emit_cli_error,
    load_tui_callables,
    print_response,
    resolve_output_format,
    resolve_requested_theme,
    rethrow_theme_catalog_error,
    run_with_spinner,
)
from netbox_sdk.schema import HTTP_METHODS
from netbox_sdk.services import load_json_payload, parse_key_value_pairs

dev_app = typer.Typer(
    add_completion=False,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    help="Developer-focused tools and experimental interfaces.",
    no_args_is_help=True,
)

dev_http_app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Direct HTTP operations mapped from OpenAPI paths (nbx dev http <method> --path ...).",
)


def _normalize_api_path(path: str, object_id: int | None = None) -> str:
    """Normalize a user-supplied path to /api/... and optionally inject an ID segment."""
    p = path.strip()
    if p.startswith("api/"):
        p = "/" + p
    if not p.startswith("/api/"):
        p = "/api" + p if p.startswith("/") else "/api/" + p
    if object_id is not None:
        if "{id}" in p:
            p = p.replace("{id}", str(object_id))
        else:
            p = p.rstrip("/") + f"/{object_id}/"
    if not p.endswith("/"):
        p += "/"
    return p


# ── Pydantic models for dev http input/output ────────────────────────────────


class _DevHttpGetInput(BaseModel):
    path: str
    object_id: int | None = None
    query: list[str] = []
    output_json: bool = False
    output_yaml: bool = False
    output_markdown: bool = False
    extra: dict[str, Any] = {}

    @field_validator("path")
    @classmethod
    def path_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("cannot be empty")
        return v

    @field_validator("object_id")
    @classmethod
    def id_positive(cls, v: int | None) -> int | None:
        if v is not None and v <= 0:
            raise ValueError("must be a positive integer")
        return v

    @field_validator("query")
    @classmethod
    def query_key_value(cls, v: list[str]) -> list[str]:
        for item in v:
            if "=" not in item:
                raise ValueError(
                    f"expected key=value format, got {item!r}  (example: --query site=nyc)"
                )
        return v

    @model_validator(mode="after")
    def output_exclusive(self) -> _DevHttpGetInput:
        resolve_output_format(
            as_json=self.output_json,
            as_yaml=self.output_yaml,
            as_markdown=self.output_markdown,
            error_factory=ValueError,
        )
        return self


class _DevHttpBodyInput(BaseModel):
    path: str
    object_id: int | None = None
    arguments: list[str] = []
    body_json: str | None = None
    body_file: str | None = None
    output_json: bool = False
    output_yaml: bool = False
    output_markdown: bool = False
    extra: dict[str, Any] = {}

    @field_validator("path")
    @classmethod
    def path_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("cannot be empty")
        return v

    @field_validator("object_id")
    @classmethod
    def id_positive(cls, v: int | None) -> int | None:
        if v is not None and v <= 0:
            raise ValueError("must be a positive integer")
        return v

    @field_validator("arguments")
    @classmethod
    def arguments_key_value(cls, v: list[str]) -> list[str]:
        for item in v:
            if "=" not in item:
                raise ValueError(
                    f"expected key=value format, got {item!r}  (example: --argument name=router1)"
                )
        return v

    @field_validator("body_file")
    @classmethod
    def body_file_exists(cls, v: str | None) -> str | None:
        if v is not None and not Path(v).is_file():
            raise ValueError(f"file not found: {v}")
        return v

    @model_validator(mode="after")
    def validate_body_sources(self) -> _DevHttpBodyInput:
        has_explicit = bool(self.body_json or self.body_file)
        has_fields = bool(self.arguments or self.extra)
        if self.body_json and self.body_file:
            raise ValueError("--body-json and --body-file are mutually exclusive; pick one")
        if has_explicit and has_fields:
            raise ValueError(
                "--body-json / --body-file cannot be combined with --argument or direct field flags"
            )
        if self.body_json:
            try:
                json.loads(self.body_json)
            except json.JSONDecodeError as exc:
                raise ValueError(f"--body-json is not valid JSON: {exc}") from exc
        resolve_output_format(
            as_json=self.output_json,
            as_yaml=self.output_yaml,
            as_markdown=self.output_markdown,
            error_factory=ValueError,
        )
        return self


class _DevHttpDeleteInput(BaseModel):
    path: str
    object_id: int
    output_json: bool = False
    output_yaml: bool = False
    output_markdown: bool = False

    @field_validator("path")
    @classmethod
    def path_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("cannot be empty")
        return v

    @field_validator("object_id")
    @classmethod
    def id_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("must be a positive integer")
        return v

    @model_validator(mode="after")
    def output_exclusive(self) -> _DevHttpDeleteInput:
        resolve_output_format(
            as_json=self.output_json,
            as_yaml=self.output_yaml,
            as_markdown=self.output_markdown,
            error_factory=ValueError,
        )
        return self


class DevHttpResult(BaseModel):
    """Structured representation of a dev-http API response."""

    status: int
    ok: bool
    data: Any = None
    error: str | None = None

    @classmethod
    def from_response(cls, status: int, text: str) -> DevHttpResult:
        ok = 200 <= status < 300
        data: Any = None
        error: str | None = None
        stripped = text.strip()
        if stripped:
            try:
                data = json.loads(stripped)
            except json.JSONDecodeError:
                data = stripped
        if not ok:
            if isinstance(data, dict):
                detail = data.get("detail") or data.get("non_field_errors")
                if detail:
                    error = str(detail)
                elif data:
                    # field-level errors: {"name": ["This field is required."]}
                    parts = []
                    for field, msgs in data.items():
                        msg = msgs[0] if isinstance(msgs, list) and msgs else str(msgs)
                        parts.append(f"  {field}: {msg}")
                    error = "\n".join(parts) if parts else f"HTTP {status}"
                else:
                    error = f"HTTP {status}"
            elif isinstance(data, str):
                error = data[:500]
            else:
                error = f"HTTP {status}"
        return cls(status=status, ok=ok, data=data, error=error)


_FIELD_TO_CLI: dict[str, str] = {
    "path": "--path",
    "object_id": "--id",
    "query": "--query",
    "arguments": "--argument",
    "body_json": "--body-json",
    "body_file": "--body-file",
    "output_json": "--json",
    "output_yaml": "--yaml",
    "output_markdown": "--markdown",
    "extra": "field flags",
}


def _validate_dev_input(model_cls: type, **kwargs: Any) -> Any:
    """Instantiate a Pydantic model and convert ValidationError into a user-facing message."""
    try:
        return model_cls(**kwargs)
    except ValidationError as exc:
        lines: list[str] = []
        for err in exc.errors():
            loc = err.get("loc", ())
            raw = ".".join(str(s) for s in loc if s not in ("", "__root__"))
            label = _FIELD_TO_CLI.get(raw, f"--{raw}") if raw else None
            msg = err["msg"].removeprefix("Value error, ")
            lines.append(f"  {label}: {msg}" if label else f"  {msg}")
        raise typer.BadParameter("Invalid input:\n" + "\n".join(lines)) from exc


def _resolve_body(inp: _DevHttpBodyInput) -> dict[str, Any] | list[Any] | None:
    """Build the request payload from a validated _DevHttpBodyInput."""
    if inp.body_json:
        return json.loads(inp.body_json)
    if inp.body_file:
        return load_json_payload(None, inp.body_file)
    body: dict[str, Any] = {}
    for arg in inp.arguments:
        key, _, raw_value = arg.partition("=")
        try:
            body[key.strip()] = json.loads(raw_value)
        except json.JSONDecodeError:
            body[key.strip()] = raw_value
    body.update(inp.extra)
    return body or None


_DEV_HTTP_CTX = {"allow_extra_args": True, "ignore_unknown_options": True}

# Known option names consumed by the commands themselves — not forwarded as field args.
_DEV_HTTP_RESERVED = frozenset(
    {
        "path",
        "p",
        "id",
        "q",
        "query",
        "argument",
        "a",
        "body-json",
        "body-file",
        "json",
        "yaml",
        "markdown",
        "help",
    }
)


def _parse_extra_args(args: list[str]) -> dict[str, Any]:
    """Parse free-form ``--key value`` / ``--key=value`` pairs from leftover ctx.args.

    Values that parse as valid JSON are decoded (so ``--active true`` → ``True``,
    ``--count 5`` → ``5``).  Bare flags (no following value) become ``True``.
    Reserved option names are silently skipped.
    """
    result: dict[str, Any] = {}
    i = 0
    while i < len(args):
        token = args[i]
        if not token.startswith("-"):
            i += 1
            continue
        # Strip leading dashes to get the raw key (supports both - and --)
        raw_key = token.lstrip("-")
        if "=" in raw_key:
            key, _, raw_value = raw_key.partition("=")
            if key in _DEV_HTTP_RESERVED:
                i += 1
                continue
            try:
                result[key] = json.loads(raw_value)
            except json.JSONDecodeError:
                result[key] = raw_value
            i += 1
        else:
            key = raw_key
            if key in _DEV_HTTP_RESERVED:
                # skip the value token too if present
                i += 2 if i + 1 < len(args) and not args[i + 1].startswith("-") else 1
                continue
            # Peek at the next token: if it looks like a value, consume it
            if i + 1 < len(args) and not args[i + 1].startswith("-"):
                raw_value = args[i + 1]
                try:
                    result[key] = json.loads(raw_value)
                except json.JSONDecodeError:
                    result[key] = raw_value
                i += 2
            else:
                result[key] = True
                i += 1
    return result


def _run_http(method: str, inp: _DevHttpGetInput | _DevHttpBodyInput | _DevHttpDeleteInput) -> None:
    """Execute a validated dev-http request and print the result."""
    try:
        normalized = _normalize_api_path(inp.path, inp.object_id)
    except ValueError as exc:
        raise typer.BadParameter(f"Invalid path: {exc}") from exc

    query_dict: dict[str, str] = {}
    payload: dict[str, Any] | list[Any] | None = None

    if isinstance(inp, _DevHttpGetInput):
        try:
            query_dict = parse_key_value_pairs(inp.query)
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc
        for k, v in inp.extra.items():
            query_dict.setdefault(k, str(v) if not isinstance(v, str) else v)
    elif isinstance(inp, _DevHttpBodyInput):
        try:
            payload = _resolve_body(inp)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise typer.BadParameter(f"Body error: {exc}") from exc
        if method in {"POST", "PUT", "PATCH"} and inp.extra:
            if payload is None:
                payload = {}
            if isinstance(payload, dict):
                payload.update(inp.extra)

    try:
        response = run_with_spinner(
            dev_http_api_client().request(method, normalized, query=query_dict, payload=payload)
        )
    except RuntimeError as exc:
        raise typer.BadParameter(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise typer.Exit(emit_cli_error(f"Request failed: {exc}")) from exc

    result = DevHttpResult.from_response(response.status, response.text)

    if not result.ok:
        typer.echo(f"Status: {result.status}")
        raise typer.Exit(emit_cli_error(result.error or f"HTTP {result.status}"))

    print_response(
        result.status,
        response.text,
        as_json=inp.output_json,
        as_yaml=inp.output_yaml,
        as_markdown=inp.output_markdown,
    )


@dev_http_app.command("get", context_settings=_DEV_HTTP_CTX)
def dev_http_get(
    ctx: typer.Context,
    path: str = typer.Option(..., "--path", "-p", help="API path, e.g. /dcim/devices/"),
    object_id: int | None = typer.Option(None, "--id", help="Object ID for detail endpoint"),
    query: list[str] | None = typer.Option(
        None, "-q", "--query", help="Query filter as key=value (repeatable)"
    ),
    output_json: bool = typer.Option(False, "--json", help="Output raw JSON"),
    output_yaml: bool = typer.Option(False, "--yaml", help="Output YAML"),
    output_markdown: bool = typer.Option(
        False,
        "--markdown",
        help="Output Markdown (mutually exclusive with --json/--yaml)",
    ),
) -> None:
    """GET a list or detail endpoint. Use --id for a single object.

    Any unrecognised --flag is forwarded as a query filter:
      nbx dev http get --path /dcim/devices/ --status active --site mysite
    """
    inp = _validate_dev_input(
        _DevHttpGetInput,
        path=path,
        object_id=object_id,
        query=query or [],
        output_json=output_json,
        output_yaml=output_yaml,
        output_markdown=output_markdown,
        extra=_parse_extra_args(ctx.args),
    )
    _run_http("GET", inp)


@dev_http_app.command("post", context_settings=_DEV_HTTP_CTX)
def dev_http_post(
    ctx: typer.Context,
    path: str = typer.Option(..., "--path", "-p", help="API path, e.g. /dcim/devices/"),
    argument: list[str] | None = typer.Option(
        None, "--argument", "-a", help="Body field as key=value (repeatable)"
    ),
    body_json: str | None = typer.Option(None, "--body-json", help="Inline JSON request body"),
    body_file: str | None = typer.Option(None, "--body-file", help="Path to JSON body file"),
    output_json: bool = typer.Option(False, "--json", help="Output raw JSON"),
    output_yaml: bool = typer.Option(False, "--yaml", help="Output YAML"),
    output_markdown: bool = typer.Option(
        False,
        "--markdown",
        help="Output Markdown (mutually exclusive with --json/--yaml)",
    ),
) -> None:
    """POST to create a new object.

    Pass body fields directly as flags or with --argument:
      nbx dev http post --path /dcim/devices/ --name router1 --site 3 --device-type 1
    """
    inp = _validate_dev_input(
        _DevHttpBodyInput,
        path=path,
        object_id=None,
        arguments=argument or [],
        body_json=body_json,
        body_file=body_file,
        output_json=output_json,
        output_yaml=output_yaml,
        output_markdown=output_markdown,
        extra=_parse_extra_args(ctx.args),
    )
    _run_http("POST", inp)


@dev_http_app.command("put", context_settings=_DEV_HTTP_CTX)
def dev_http_put(
    ctx: typer.Context,
    path: str = typer.Option(..., "--path", "-p", help="API path, e.g. /dcim/devices/"),
    object_id: int = typer.Option(..., "--id", help="Object ID (required for PUT)"),
    argument: list[str] | None = typer.Option(
        None, "--argument", "-a", help="Body field as key=value (repeatable)"
    ),
    body_json: str | None = typer.Option(None, "--body-json", help="Inline JSON request body"),
    body_file: str | None = typer.Option(None, "--body-file", help="Path to JSON body file"),
    output_json: bool = typer.Option(False, "--json", help="Output raw JSON"),
    output_yaml: bool = typer.Option(False, "--yaml", help="Output YAML"),
    output_markdown: bool = typer.Option(
        False,
        "--markdown",
        help="Output Markdown (mutually exclusive with --json/--yaml)",
    ),
) -> None:
    """PUT to fully replace an existing object. Requires --id.

    Pass body fields directly as flags:
      nbx dev http put --path /dcim/devices/ --id 42 --name router1-renamed
    """
    inp = _validate_dev_input(
        _DevHttpBodyInput,
        path=path,
        object_id=object_id,
        arguments=argument or [],
        body_json=body_json,
        body_file=body_file,
        output_json=output_json,
        output_yaml=output_yaml,
        output_markdown=output_markdown,
        extra=_parse_extra_args(ctx.args),
    )
    _run_http("PUT", inp)


@dev_http_app.command("patch", context_settings=_DEV_HTTP_CTX)
def dev_http_patch(
    ctx: typer.Context,
    path: str = typer.Option(..., "--path", "-p", help="API path, e.g. /dcim/devices/"),
    object_id: int = typer.Option(..., "--id", help="Object ID (required for PATCH)"),
    argument: list[str] | None = typer.Option(
        None, "--argument", "-a", help="Body field as key=value (repeatable)"
    ),
    body_json: str | None = typer.Option(None, "--body-json", help="Inline JSON request body"),
    body_file: str | None = typer.Option(None, "--body-file", help="Path to JSON body file"),
    output_json: bool = typer.Option(False, "--json", help="Output raw JSON"),
    output_yaml: bool = typer.Option(False, "--yaml", help="Output YAML"),
    output_markdown: bool = typer.Option(
        False,
        "--markdown",
        help="Output Markdown (mutually exclusive with --json/--yaml)",
    ),
) -> None:
    """PATCH to partially update an existing object. Requires --id.

    Pass only the fields you want to change:
      nbx dev http patch --path /dcim/devices/ --id 42 --status active
    """
    inp = _validate_dev_input(
        _DevHttpBodyInput,
        path=path,
        object_id=object_id,
        arguments=argument or [],
        body_json=body_json,
        body_file=body_file,
        output_json=output_json,
        output_yaml=output_yaml,
        output_markdown=output_markdown,
        extra=_parse_extra_args(ctx.args),
    )
    _run_http("PATCH", inp)


@dev_http_app.command("delete")
def dev_http_delete(
    path: str = typer.Option(..., "--path", "-p", help="API path, e.g. /dcim/devices/"),
    object_id: int = typer.Option(..., "--id", help="Object ID (required for DELETE)"),
    output_json: bool = typer.Option(False, "--json", help="Output raw JSON"),
    output_yaml: bool = typer.Option(False, "--yaml", help="Output YAML"),
    output_markdown: bool = typer.Option(
        False,
        "--markdown",
        help="Output Markdown (mutually exclusive with --json/--yaml)",
    ),
) -> None:
    """DELETE an object by ID. Requires --id."""
    inp = _validate_dev_input(
        _DevHttpDeleteInput,
        path=path,
        object_id=object_id,
        output_json=output_json,
        output_yaml=output_yaml,
        output_markdown=output_markdown,
    )
    _run_http("DELETE", inp)


@dev_http_app.command("paths")
def dev_http_paths(
    search: str | None = typer.Argument(None, help="Optional substring filter on path"),
    method: str | None = typer.Option(
        None, "--method", "-m", help="Filter by HTTP method (GET, POST, PUT, PATCH, DELETE)"
    ),
    group: str | None = typer.Option(None, "--group", "-g", help="Filter by API group, e.g. dcim"),
) -> None:
    """List all OpenAPI paths from the bundled NetBox schema."""
    index = _get_index()
    schema_paths = index.schema.get("paths", {})

    rows: list[tuple[str, str]] = []
    for p, path_item in schema_paths.items():
        if not isinstance(path_item, dict):
            continue
        if search and search.lower() not in p.lower():
            continue
        if group and f"/{group}/" not in p:
            continue
        methods = sorted(m.upper() for m in path_item if m.lower() in HTTP_METHODS)
        if method and method.upper() not in methods:
            continue
        rows.append((p, ", ".join(methods)))

    if not rows:
        typer.echo("No matching paths.")
        return

    table = Table(title=f"{len(rows)} path(s)", show_header=True)
    table.add_column("Path", no_wrap=True)
    table.add_column("Methods")
    for p, methods_str in sorted(rows):
        table.add_row(p, methods_str)
    console.print(table)


@dev_http_app.command("ops")
def dev_http_ops(
    path: str = typer.Option(..., "--path", "-p", help="API path to inspect"),
) -> None:
    """Show available HTTP operations for a specific OpenAPI path."""
    index = _get_index()
    p = path.strip()
    if p.startswith("api/"):
        p = "/" + p
    if not p.startswith("/api/"):
        p = "/api" + p if p.startswith("/") else "/api/" + p
    if not p.endswith("/"):
        p += "/"

    schema_paths = index.schema.get("paths", {})
    path_item = schema_paths.get(p) or schema_paths.get(p.rstrip("/"))

    if not isinstance(path_item, dict):
        typer.echo(f"Path not found in schema: {p}", err=True)
        raise typer.Exit(code=1)

    table = Table(title=f"Operations: {p}", show_header=True)
    table.add_column("Method", no_wrap=True)
    table.add_column("Operation ID")
    table.add_column("Summary")
    for m, operation in path_item.items():
        if m.lower() not in HTTP_METHODS:
            continue
        if not isinstance(operation, dict):
            continue
        table.add_row(
            m.upper(),
            str(operation.get("operationId") or "-"),
            str(operation.get("summary") or "-"),
        )
    console.print(table)


@dev_app.command("tui", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def dev_tui_command(
    ctx: typer.Context,
    theme: bool = typer.Option(
        False,
        "--theme",
        help="Theme selector. Use '--theme' to list available themes or '--theme <name>' to launch with one.",
    ),
) -> None:
    """Launch the developer request workbench TUI."""
    available_theme_names, resolve_theme_name, run_dev_tui = load_tui_callables(
        "netbox_tui.dev_app",
        "available_theme_names",
        "resolve_theme_name",
        "run_dev_tui",
    )

    selected_theme = resolve_requested_theme(
        ctx,
        theme=theme,
        available_theme_names=available_theme_names,
        resolve_theme_name=resolve_theme_name,
        usage="nbx dev tui --theme <name>",
    )
    if theme and not ctx.args:
        return

    try:
        run_dev_tui(
            client=_get_client(),
            index=_get_index(),
            theme_name=selected_theme,
        )
    except Exception as exc:
        rethrow_theme_catalog_error(exc)


dev_app.add_typer(dev_http_app, name="http")

from netbox_cli.django_model import django_model_app as _django_model_app  # noqa: E402, PLC0415

dev_app.add_typer(_django_model_app, name="django-model")
