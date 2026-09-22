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
        self.calls: list[dict[str, Any]] = []
        self.closed = False

    async def request(
        self,
        method: str,
        path: str,
        *,
        query: Any = None,
        payload: Any = None,
        headers: Any = None,
        use_cache: bool = True,
    ) -> ApiResponse:
        del headers
        self.calls.append(
            {
                "method": method,
                "path": path,
                "query": query,
                "payload": payload,
                "use_cache": use_cache,
            }
        )
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


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (
            [
                "rpc",
                "procedures",
                "available",
                "--target-type",
                "DCIM.Device",
                "--query",
                "tag=edge",
                "--query",
                "tag=managed",
            ],
            {
                "method": "GET",
                "path": "/api/plugins/rpc/procedures/available/",
                "query": {"tag": ["edge", "managed"], "target_type": "dcim.device"},
                "payload": None,
                "use_cache": True,
            },
        ),
        (
            [
                "rpc",
                "procedures",
                "commands",
                "--id",
                "7",
                "--query",
                "limit=25",
                "-q",
                "tag=managed",
            ],
            {
                "method": "GET",
                "path": "/api/plugins/rpc/procedures/7/commands/",
                "query": {"limit": "25", "tag": "managed"},
                "payload": None,
                "use_cache": True,
            },
        ),
        (
            [
                "rpc",
                "procedures",
                "commands",
                "--id",
                "7",
                "--body-json",
                '{"argv":["true"]}',
                "--confirm",
            ],
            {
                "method": "POST",
                "path": "/api/plugins/rpc/procedures/7/commands/",
                "query": None,
                "payload": {"argv": ["true"]},
                "use_cache": True,
            },
        ),
        (
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
                "--params-json",
                '{"service_slug":"nginx"}',
                "--confirm",
            ],
            {
                "method": "POST",
                "path": "/api/plugins/rpc/intents/2/run/",
                "query": None,
                "payload": {
                    "assigned_object_type": "dcim.device",
                    "assigned_object_id": 7,
                    "params": {"service_slug": "nginx"},
                },
                "use_cache": True,
            },
        ),
        (
            ["rpc", "executions", "cancel", "--id", "7", "--confirm"],
            {
                "method": "POST",
                "path": "/api/plugins/rpc/executions/7/cancel/",
                "query": None,
                "payload": {},
                "use_cache": True,
            },
        ),
        (
            [
                "rpc",
                "executions",
                "approve",
                "--id",
                "7",
                "--reason",
                "reviewed",
                "--confirm",
            ],
            {
                "method": "POST",
                "path": "/api/plugins/rpc/executions/7/approve/",
                "query": None,
                "payload": {"reason": "reviewed"},
                "use_cache": True,
            },
        ),
        (
            [
                "rpc",
                "executions",
                "reject",
                "--id",
                "7",
                "--reason",
                "unsafe",
                "--confirm",
            ],
            {
                "method": "POST",
                "path": "/api/plugins/rpc/executions/7/reject/",
                "query": None,
                "payload": {"reason": "unsafe"},
                "use_cache": True,
            },
        ),
        (
            [
                "rpc",
                "executions",
                "events",
                "--id",
                "7",
                "--query",
                "level=warning",
                "--query",
                "level=error",
            ],
            {
                "method": "GET",
                "path": "/api/plugins/rpc/executions/7/events/",
                "query": {"level": ["warning", "error"]},
                "payload": None,
                "use_cache": True,
            },
        ),
        (
            ["rpc", "executions", "wait", "--id", "7", "--timeout", "1"],
            {
                "method": "GET",
                "path": "/api/plugins/rpc/executions/7/",
                "query": None,
                "payload": None,
                "use_cache": False,
            },
        ),
    ],
)
def test_rpc_custom_actions_forward_exact_contract(
    monkeypatch: pytest.MonkeyPatch,
    args: list[str],
    expected: dict[str, Any],
) -> None:
    fake = _FakeClient()
    monkeypatch.setattr(rpc_mod, "_get_client", lambda: fake)
    result = runner.invoke(app, args)
    assert result.exit_code == 0
    assert fake.calls == [expected]
    assert fake.closed is True


@pytest.mark.parametrize(
    ("action", "method"),
    [("bulk-update", "PUT"), ("bulk-patch", "PATCH"), ("bulk-delete", "DELETE")],
)
@pytest.mark.parametrize(
    ("resource", "collection_path"),
    [
        ("backends", "/api/plugins/rpc/backends/"),
        ("procedures", "/api/plugins/rpc/procedures/"),
        ("procedure-commands", "/api/plugins/rpc/procedure-commands/"),
        ("intents", "/api/plugins/rpc/intents/"),
        ("linux-service-allowlist", "/api/plugins/rpc/linux-service-allowlist/"),
    ],
)
def test_rpc_bulk_cli_dispatches_collection_method_and_array_body(
    monkeypatch: pytest.MonkeyPatch,
    resource: str,
    collection_path: str,
    action: str,
    method: str,
) -> None:
    fake = _FakeClient()
    monkeypatch.setattr(rpc_mod, "_get_client", lambda: fake)
    result = runner.invoke(
        app,
        ["rpc", resource, action, "--body-json", '[{"id":7}]', "--confirm"],
    )
    assert result.exit_code == 0
    assert fake.calls == [
        {
            "method": method,
            "path": collection_path,
            "query": {},
            "payload": [{"id": 7}],
            "use_cache": True,
        }
    ]


@pytest.mark.parametrize(
    ("resource", "collection_path"),
    [
        ("backends", "/api/plugins/rpc/backends/"),
        ("procedures", "/api/plugins/rpc/procedures/"),
        ("procedure-commands", "/api/plugins/rpc/procedure-commands/"),
        ("intents", "/api/plugins/rpc/intents/"),
        ("linux-service-allowlist", "/api/plugins/rpc/linux-service-allowlist/"),
    ],
)
@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (["list"], ("GET", "/", {})),
        (["get", "--id", "7"], ("GET", "/7/", {})),
        (
            ["create", "--body-json", '{"name":"single"}', "--confirm"],
            ("POST", "/", {"name": "single"}),
        ),
        (
            ["create", "--body-json", '[{"name":"first"}]', "--confirm"],
            ("POST", "/", [{"name": "first"}]),
        ),
        (
            ["update", "--id", "7", "--body-json", '{"name":"replacement"}', "--confirm"],
            ("PUT", "/7/", {"name": "replacement"}),
        ),
        (
            ["patch", "--id", "7", "--body-json", '{"name":"partial"}', "--confirm"],
            ("PATCH", "/7/", {"name": "partial"}),
        ),
        (["delete", "--id", "7", "--confirm"], ("DELETE", "/7/", {})),
    ],
)
def test_rpc_mutable_collection_cli_dispatch_exact_crud(
    monkeypatch: pytest.MonkeyPatch,
    resource: str,
    collection_path: str,
    args: list[str],
    expected: tuple[str, str, Any],
) -> None:
    fake = _FakeClient()
    monkeypatch.setattr(rpc_mod, "_get_client", lambda: fake)

    result = runner.invoke(app, ["rpc", resource, *args])

    method, suffix, body = expected
    assert result.exit_code == 0
    assert fake.calls == [
        {
            "method": method,
            "path": f"{collection_path.rstrip('/')}{suffix}",
            "query": {},
            "payload": body if body != {} else None,
            "use_cache": True,
        }
    ]
    assert fake.closed is True


@pytest.mark.parametrize(
    ("resource", "args", "method", "path", "query", "payload"),
    [
        ("settings", ["list"], "GET", "/api/plugins/rpc/settings/", {}, None),
        ("settings", ["get", "--id", "1"], "GET", "/api/plugins/rpc/settings/1/", {}, None),
        (
            "settings",
            ["patch", "--id", "1", "--body-json", '{"enabled":true}', "--confirm"],
            "PATCH",
            "/api/plugins/rpc/settings/1/",
            {},
            {"enabled": True},
        ),
        ("executions", ["list"], "GET", "/api/plugins/rpc/executions/", {}, None),
        (
            "executions",
            ["get", "--id", "7"],
            "GET",
            "/api/plugins/rpc/executions/7/",
            {},
            None,
        ),
        (
            "executions",
            ["create", "--body-json", '{"procedure_id":2}', "--confirm"],
            "POST",
            "/api/plugins/rpc/executions/",
            {},
            {"procedure_id": 2},
        ),
        (
            "execution-events",
            ["list"],
            "GET",
            "/api/plugins/rpc/execution-events/",
            {},
            None,
        ),
        (
            "execution-events",
            ["get", "--id", "9"],
            "GET",
            "/api/plugins/rpc/execution-events/9/",
            {},
            None,
        ),
    ],
)
def test_rpc_restricted_collection_cli_dispatch_exact_transport(
    monkeypatch: pytest.MonkeyPatch,
    resource: str,
    args: list[str],
    method: str,
    path: str,
    query: dict[str, Any],
    payload: dict[str, Any] | None,
) -> None:
    fake = _FakeClient()
    monkeypatch.setattr(rpc_mod, "_get_client", lambda: fake)

    result = runner.invoke(app, ["rpc", resource, *args])

    assert result.exit_code == 0
    assert fake.calls == [
        {
            "method": method,
            "path": path,
            "query": query,
            "payload": payload,
            "use_cache": True,
        }
    ]
    assert fake.closed is True


def test_rpc_procedure_commands_rejects_query_with_post_before_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        rpc_mod,
        "_get_client",
        lambda: pytest.fail("client must not be constructed"),
    )

    result = runner.invoke(
        app,
        [
            "rpc",
            "procedures",
            "commands",
            "--id",
            "7",
            "--query",
            "limit=25",
            "--body-json",
            "{}",
            "--confirm",
        ],
    )

    assert result.exit_code != 0
    assert "query parameters are only supported for GET" in result.output


@pytest.mark.parametrize(
    "args",
    [
        ["rpc", "procedures", "available", "--query", "invalid"],
        ["rpc", "procedures", "commands", "--id", "7", "--query", "invalid"],
        ["rpc", "executions", "events", "--id", "7", "--query", "invalid"],
    ],
)
def test_rpc_query_options_reject_invalid_pairs_before_client(
    monkeypatch: pytest.MonkeyPatch,
    args: list[str],
) -> None:
    monkeypatch.setattr(
        rpc_mod,
        "_get_client",
        lambda: pytest.fail("client must not be constructed"),
    )

    result = runner.invoke(app, args)

    assert result.exit_code != 0
    assert "Expected key=value format" in result.output


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
