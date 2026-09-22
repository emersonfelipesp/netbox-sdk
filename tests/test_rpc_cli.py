"""Tests for the first-class ``nbx rpc`` command tree."""

from __future__ import annotations

import json
from typing import Any

import pytest
from typer.main import get_command
from typer.testing import CliRunner

from netbox_cli import app
from netbox_cli import rpc as rpc_mod
from netbox_sdk.client import ApiResponse

pytestmark = pytest.mark.suite_cli
runner = CliRunner()


class _FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, Any]] = []
        self.closed = False

    async def request(
        self,
        method: str,
        path: str,
        *,
        query: Any = None,
        payload: Any = None,
        headers: Any = None,
    ) -> ApiResponse:
        self.calls.append((method, path, payload if payload is not None else query))
        return ApiResponse(status=200, text=json.dumps({"status": "succeeded"}), headers={})

    async def close(self) -> None:
        self.closed = True


def test_rpc_help_exposes_all_collections_and_workflows() -> None:
    result = runner.invoke(app, ["rpc", "--help"])
    assert result.exit_code == 0
    for name in (
        "settings",
        "backends",
        "procedures",
        "procedure-commands",
        "intents",
        "linux-service-allowlist",
        "executions",
        "execution-events",
    ):
        assert name in result.stdout


def _rpc_action_names(resource: str) -> set[str]:
    root = get_command(app)
    return set(root.commands["rpc"].commands[resource].commands)


@pytest.mark.parametrize(
    "resource",
    ["backends", "procedures", "procedure-commands", "intents", "linux-service-allowlist"],
)
def test_rpc_mutable_collections_expose_complete_netbox_router_actions(resource: str) -> None:
    expected = {
        "list",
        "get",
        "create",
        "update",
        "patch",
        "delete",
        "bulk-update",
        "bulk-patch",
        "bulk-delete",
    }
    if resource == "procedures":
        expected.update({"available", "commands"})
    if resource == "intents":
        expected.add("run")
    assert _rpc_action_names(resource) == expected


@pytest.mark.parametrize(
    ("resource", "actions"),
    [
        ("settings", {"list", "get", "patch"}),
        (
            "executions",
            {
                "list",
                "get",
                "create",
                "cancel",
                "approve",
                "reject",
                "events",
                "wait",
            },
        ),
        ("execution-events", {"list", "get"}),
    ],
)
def test_rpc_restricted_collections_expose_exact_actions(resource: str, actions: set[str]) -> None:
    assert _rpc_action_names(resource) == actions


def test_rpc_execution_create_has_client_free_redacted_dry_run() -> None:
    result = runner.invoke(
        app,
        [
            "rpc",
            "executions",
            "create",
            "--dry-run",
            "--body-json",
            '{"procedure_id":1,"assigned_object_type":"dcim.device",'
            '"assigned_object_id":2,"password":"secret"}',
        ],
    )
    assert result.exit_code == 0
    assert "/api/plugins/rpc/executions/" in result.stdout
    assert "[redacted]" in result.stdout
    assert "secret" not in result.stdout


def test_rpc_mutating_custom_action_requires_confirmation_before_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        rpc_mod,
        "_get_client",
        lambda: pytest.fail("client must not be constructed"),
    )
    result = runner.invoke(app, ["rpc", "executions", "cancel", "--id", "7"])
    assert result.exit_code != 0


def test_rpc_custom_actions_forward_exact_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeClient()
    monkeypatch.setattr(rpc_mod, "_get_client", lambda: fake)

    result = runner.invoke(
        app,
        ["rpc", "executions", "approve", "--id", "7", "--reason", "ok", "--confirm"],
    )
    assert result.exit_code == 0
    assert fake.calls == [("POST", "/api/plugins/rpc/executions/7/approve/", {"reason": "ok"})]
    assert fake.closed is True


@pytest.mark.parametrize(
    ("action", "method"),
    [("bulk-update", "PUT"), ("bulk-patch", "PATCH"), ("bulk-delete", "DELETE")],
)
def test_rpc_bulk_cli_dispatches_collection_method_and_array_body(
    monkeypatch: pytest.MonkeyPatch, action: str, method: str
) -> None:
    fake = _FakeClient()
    monkeypatch.setattr(rpc_mod, "_get_client", lambda: fake)
    result = runner.invoke(
        app,
        ["rpc", "backends", action, "--body-json", '[{"id":7}]', "--confirm"],
    )
    assert result.exit_code == 0
    assert fake.calls == [(method, "/api/plugins/rpc/backends/", [{"id": 7}])]


@pytest.mark.parametrize(
    "args",
    [
        ["rpc", "procedures", "commands", "--id", "7", "--body-json", "{}"],
        [
            "rpc",
            "intents",
            "run",
            "--id",
            "2",
            "--assigned-object-type",
            "dcim.device",
            "--assigned-object-id",
            "7",
        ],
        ["rpc", "backends", "bulk-patch", "--body-json", "[]"],
    ],
)
def test_all_rpc_write_families_confirm_before_client(
    monkeypatch: pytest.MonkeyPatch, args: list[str]
) -> None:
    monkeypatch.setattr(
        rpc_mod, "_get_client", lambda: pytest.fail("client must not be constructed")
    )
    result = runner.invoke(app, args)
    assert result.exit_code != 0


@pytest.mark.parametrize("value", ["nan", "inf", "-inf"])
def test_rpc_wait_rejects_nonfinite_bounds_before_client(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setattr(
        rpc_mod, "_get_client", lambda: pytest.fail("client must not be constructed")
    )
    result = runner.invoke(app, ["rpc", "executions", "wait", "--id", "7", "--timeout", value])
    assert result.exit_code != 0
