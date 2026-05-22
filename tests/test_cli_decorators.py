"""Tests for internal CLI command decorators."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import pytest
import typer
from typer.testing import CliRunner

from netbox_cli.decorators import (
    json_result,
    no_result,
    raise_branching_cli_error,
    resource_command,
)
from netbox_sdk.exceptions import (
    BranchConflictError,
    BranchingPluginUnavailableError,
    BranchJobTimeoutError,
)

pytestmark = pytest.mark.suite_cli


class _Resource:
    def __init__(self) -> None:
        self.closed = False

    async def close(self) -> None:
        self.closed = True


def test_resource_command_preserves_typer_signature_and_renders_json() -> None:
    app = typer.Typer()
    runner = CliRunner()
    resource = _Resource()

    def _factory() -> tuple[_Resource, _Resource]:
        return resource, resource

    @app.command("sample")
    @resource_command(resource_factory=_factory, renderer=json_result())
    def sample(
        name: str = typer.Argument(...),
        enabled: bool = typer.Option(False, "--enabled"),
    ) -> Callable[[_Resource], Awaitable[dict[str, Any]]]:
        async def _operation(_resource: _Resource) -> dict[str, Any]:
            return {"name": name, "enabled": enabled}

        return _operation

    help_result = runner.invoke(app, ["--help"])
    assert help_result.exit_code == 0
    assert "--enabled" in help_result.stdout

    result = runner.invoke(app, ["branch-a", "--enabled"])
    assert result.exit_code == 0
    assert '"name": "branch-a"' in result.stdout
    assert '"enabled": true' in result.stdout
    assert resource.closed is True


def test_resource_command_closes_resource_on_failure() -> None:
    resource = _Resource()

    def _factory() -> tuple[_Resource, _Resource]:
        return resource, resource

    @resource_command(resource_factory=_factory, renderer=no_result())
    def command() -> Callable[[_Resource], Awaitable[None]]:
        async def _operation(_resource: _Resource) -> None:
            raise RuntimeError("boom")

        return _operation

    with pytest.raises(RuntimeError, match="boom"):
        command()
    assert resource.closed is True


@pytest.mark.parametrize(
    ("exc", "exit_code"),
    (
        (BranchingPluginUnavailableError(), 2),
        (BranchConflictError([{"id": 1}]), 3),
        (BranchJobTimeoutError(42, "pending"), 4),
    ),
)
def test_raise_branching_cli_error_maps_exit_codes(exc: Exception, exit_code: int) -> None:
    with pytest.raises(typer.Exit) as raised:
        raise_branching_cli_error(exc)

    assert raised.value.exit_code == exit_code
