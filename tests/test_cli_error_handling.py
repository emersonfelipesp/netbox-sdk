"""Tests for user-facing CLI error handling and unexpected command failures."""

from __future__ import annotations

from netbox_cli import cli
from netbox_cli.config import Config


def _mock_config() -> Config:
    return Config(
        base_url="https://netbox.example.com",
        token_key="abc",
        token_secret="def",
        timeout=30.0,
    )


def test_main_handles_unknown_command_without_traceback(capsys) -> None:
    exit_code = cli.main(["cli"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "No such command 'cli'" in captured.out
    assert "Run 'nbx --help' to see available commands." in captured.out
    assert "Traceback" not in captured.out
    assert "Traceback" not in captured.err


def test_main_handles_unexpected_command_exception(capsys, monkeypatch) -> None:
    monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)

    def _boom():
        raise RuntimeError("boom")

    monkeypatch.setattr(cli, "_get_client", _boom)

    exit_code = cli.main(["tui"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Unexpected failure: boom." in captured.out
    assert "Traceback" not in captured.out
    assert "Traceback" not in captured.err
