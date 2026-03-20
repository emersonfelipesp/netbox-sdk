from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from typer.testing import CliRunner

from netbox_cli import cli
from netbox_cli.api import ApiResponse
from netbox_cli.config import DEMO_BASE_URL, Config

runner = CliRunner()


def _demo_config() -> Config:
    return Config(
        base_url=DEMO_BASE_URL,
        token_version="v1",
        token_secret="demo-secret",
        timeout=30.0,
    )


def test_demo_interfaces_get_trace_renders_ascii(monkeypatch) -> None:
    client = MagicMock()
    client.request = AsyncMock(
        return_value=ApiResponse(
            status=200,
            text=json.dumps(
                [
                    [
                        [
                            {
                                "id": 4,
                                "display": "GigabitEthernet0/1/1",
                                "name": "GigabitEthernet0/1/1",
                                "device": {
                                    "id": 1,
                                    "display": "dmi01-akron-rtr01",
                                    "name": "dmi01-akron-rtr01",
                                },
                            }
                        ],
                        {"id": 36, "display": "Cable #36", "status": "connected"},
                        [
                            {
                                "id": 171,
                                "display": "GigabitEthernet1/0/2",
                                "name": "GigabitEthernet1/0/2",
                                "device": {
                                    "id": 14,
                                    "display": "dmi01-akron-sw01",
                                    "name": "dmi01-akron-sw01",
                                },
                            }
                        ],
                    ]
                ]
            ),
        )
    )

    async def _fake_run_dynamic_command(**kwargs):
        return ApiResponse(
            status=200,
            text=json.dumps(
                {
                    "id": 4,
                    "display": "GigabitEthernet0/1/1",
                    "name": "GigabitEthernet0/1/1",
                    "cable": {"id": 36, "display": "#36"},
                }
            ),
        )

    monkeypatch.setattr(cli, "_ensure_demo_runtime_config", _demo_config)
    monkeypatch.setattr(cli, "_get_client_for_config", lambda cfg: client)
    monkeypatch.setattr(cli, "run_dynamic_command", _fake_run_dynamic_command)
    monkeypatch.setattr(
        cli,
        "_get_index",
        lambda: SimpleNamespace(
            trace_path=lambda group, resource: "/api/dcim/interfaces/{id}/trace/"
        ),
    )

    result = runner.invoke(
        cli.app,
        ["demo", "dcim", "interfaces", "get", "--id", "4", "--trace"],
    )

    assert result.exit_code == 0
    assert "Status: 200" in result.output
    assert "Cable Trace:" in result.output
    assert "dmi01-akron-rtr01" in result.output
    assert "Cable #36" in result.output
    assert "Trace Completed - 1 segment(s)" in result.output
    client.request.assert_awaited_once_with("GET", "/api/dcim/interfaces/4/trace/")


def test_demo_interfaces_get_trace_reports_missing_connection(monkeypatch) -> None:
    client = MagicMock()
    client.request = AsyncMock(
        return_value=ApiResponse(
            status=404,
            text=json.dumps({"detail": "No connected path found."}),
        )
    )

    async def _fake_run_dynamic_command(**kwargs):
        return ApiResponse(
            status=200,
            text=json.dumps({"id": 4, "display": "GigabitEthernet0/1/1"}),
        )

    monkeypatch.setattr(cli, "_ensure_demo_runtime_config", _demo_config)
    monkeypatch.setattr(cli, "_get_client_for_config", lambda cfg: client)
    monkeypatch.setattr(cli, "run_dynamic_command", _fake_run_dynamic_command)
    monkeypatch.setattr(
        cli,
        "_get_index",
        lambda: SimpleNamespace(
            trace_path=lambda group, resource: "/api/dcim/interfaces/{id}/trace/"
        ),
    )

    result = runner.invoke(
        cli.app,
        ["demo", "dcim", "interfaces", "get", "--id", "4", "--trace"],
    )

    assert result.exit_code == 0
    assert "No connected cable trace found." in result.output


def test_demo_interfaces_get_trace_only_suppresses_detail_table(monkeypatch) -> None:
    client = MagicMock()
    client.request = AsyncMock(
        return_value=ApiResponse(
            status=200,
            text=json.dumps(
                [
                    [
                        [
                            {
                                "id": 4,
                                "display": "GigabitEthernet0/1/1",
                                "name": "GigabitEthernet0/1/1",
                                "device": {
                                    "id": 1,
                                    "display": "dmi01-akron-rtr01",
                                    "name": "dmi01-akron-rtr01",
                                },
                            }
                        ],
                        {"id": 36, "display": "Cable #36", "status": "connected"},
                        [
                            {
                                "id": 171,
                                "display": "GigabitEthernet1/0/2",
                                "name": "GigabitEthernet1/0/2",
                                "device": {
                                    "id": 14,
                                    "display": "dmi01-akron-sw01",
                                    "name": "dmi01-akron-sw01",
                                },
                            }
                        ],
                    ]
                ]
            ),
        )
    )

    async def _fake_run_dynamic_command(**kwargs):
        return ApiResponse(
            status=200,
            text=json.dumps(
                {
                    "id": 4,
                    "display": "GigabitEthernet0/1/1",
                    "name": "GigabitEthernet0/1/1",
                }
            ),
        )

    monkeypatch.setattr(cli, "_ensure_demo_runtime_config", _demo_config)
    monkeypatch.setattr(cli, "_get_client_for_config", lambda cfg: client)
    monkeypatch.setattr(cli, "run_dynamic_command", _fake_run_dynamic_command)
    monkeypatch.setattr(
        cli,
        "_get_index",
        lambda: SimpleNamespace(
            trace_path=lambda group, resource: "/api/dcim/interfaces/{id}/trace/"
        ),
    )

    result = runner.invoke(
        cli.app,
        ["demo", "dcim", "interfaces", "get", "--id", "4", "--trace-only"],
    )

    assert result.exit_code == 0
    assert "Cable Trace:" in result.output
    assert "dmi01-akron-rtr01" in result.output
    assert "Field" not in result.output
    assert "Status: 200" not in result.output


def test_demo_interfaces_get_rejects_trace_and_trace_only_together(monkeypatch) -> None:
    monkeypatch.setattr(cli, "_ensure_demo_runtime_config", _demo_config)

    result = runner.invoke(
        cli.app,
        [
            "demo",
            "dcim",
            "interfaces",
            "get",
            "--id",
            "4",
            "--trace",
            "--trace-only",
        ],
    )

    assert result.exit_code != 0
    assert "Use either --trace or --trace-only, not both." in result.output
