"""Tests for user-facing CLI error handling and unexpected command failures."""

from __future__ import annotations

import pytest

from netbox_cli import cli
from netbox_cli.support import run_with_spinner
from netbox_sdk.config import Config

pytestmark = pytest.mark.suite_cli


def _mock_config() -> Config:
    return Config(
        base_url="https://netbox.example.com",
        token_key="abc",
        token_secret="def",
        timeout=30.0,
    )


def test_main_handles_unknown_command_without_traceback(capsys) -> None:
    exit_code = cli.main(["__no_such_command__"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "No such command '__no_such_command__'" in captured.out
    assert "Run 'nbx --help' to see available commands." in captured.out
    assert "Traceback" not in captured.out
    assert "Traceback" not in captured.err


def test_main_handles_unexpected_command_exception(capsys, monkeypatch) -> None:
    monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)

    def _boom():
        raise RuntimeError("boom")

    monkeypatch.setattr(cli, "_get_client_for_tui", _boom)

    exit_code = cli.main(["tui"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Unexpected failure: boom." in captured.out
    assert "Traceback" not in captured.out
    assert "Traceback" not in captured.err


def test_run_with_spinner_closes_resource_on_success() -> None:
    class Resource:
        closed = False

        async def close(self) -> None:
            self.closed = True

    async def work() -> str:
        return "ok"

    resource = Resource()

    assert run_with_spinner(work(), close=resource) == "ok"
    assert resource.closed is True


def test_run_with_spinner_closes_resource_on_failure() -> None:
    class Resource:
        closed = False

        async def close(self) -> None:
            self.closed = True

    async def work() -> None:
        raise RuntimeError("boom")

    resource = Resource()

    with pytest.raises(RuntimeError, match="boom"):
        run_with_spinner(work(), close=resource)
    assert resource.closed is True
