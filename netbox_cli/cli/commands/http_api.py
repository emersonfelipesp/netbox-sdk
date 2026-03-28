"""Raw HTTP and GraphQL CLI commands."""

from __future__ import annotations

import json
from typing import Any

import typer

from ...services import load_json_payload, parse_key_value_pairs
from ..support import print_response, resolve_output_format, run_with_spinner
from ._wiring import get_bound_client


def register_http_api_commands(app: typer.Typer) -> None:
    @app.command("graphql")
    def graphql_command(
        query: str = typer.Argument(..., help="GraphQL query string"),
        variables: list[str] = typer.Option(
            None,
            "--variables",
            "-v",
            help="GraphQL variables: one JSON object, or repeat for multiple key=value pairs",
        ),
        output_json: bool = typer.Option(False, "--json", help="Output raw JSON"),
        output_yaml: bool = typer.Option(False, "--yaml", help="Output YAML"),
    ) -> None:
        """Execute a GraphQL query against the NetBox API."""
        client = get_bound_client()

        vars_dict: dict[str, Any] | None = None
        pairs = variables or []
        if pairs:
            if len(pairs) == 1:
                raw = pairs[0]
                try:
                    decoded = json.loads(raw)
                except json.JSONDecodeError:
                    try:
                        vars_dict = parse_key_value_pairs(pairs)
                    except ValueError as exc:
                        raise typer.BadParameter(str(exc)) from exc
                else:
                    if not isinstance(decoded, dict):
                        raise typer.BadParameter("GraphQL variables JSON must decode to an object")
                    vars_dict = decoded
            else:
                try:
                    vars_dict = parse_key_value_pairs(pairs)
                except ValueError as exc:
                    raise typer.BadParameter(str(exc)) from exc

        response = run_with_spinner(client.graphql(query, vars_dict))
        print_response(
            response.status,
            response.text,
            as_json=output_json,
            as_yaml=output_yaml,
        )

    @app.command("call")
    def call_command(
        method: str = typer.Argument(...),
        path: str = typer.Argument(...),
        query: list[str] = typer.Option(None, "-q", "--query", help="Query parameter key=value"),
        body_json: str | None = typer.Option(None, "--body-json", help="Inline JSON request body"),
        body_file: str | None = typer.Option(
            None,
            "--body-file",
            help="Path to JSON request body file",
        ),
        output_json: bool = typer.Option(False, "--json", help="Output raw JSON"),
        output_yaml: bool = typer.Option(False, "--yaml", help="Output YAML"),
        output_markdown: bool = typer.Option(
            False,
            "--markdown",
            help="Output Markdown (mutually exclusive with --json/--yaml)",
        ),
    ) -> None:
        """Call an arbitrary NetBox API path."""
        resolve_output_format(
            as_json=output_json,
            as_yaml=output_yaml,
            as_markdown=output_markdown,
        )
        query_pairs = query or []
        query_dict = parse_key_value_pairs(query_pairs)
        payload = load_json_payload(body_json, body_file)
        response = run_with_spinner(
            get_bound_client().request(method, path, query=query_dict, payload=payload)
        )
        print_response(
            response.status,
            response.text,
            as_json=output_json,
            as_yaml=output_yaml,
            as_markdown=output_markdown,
        )
