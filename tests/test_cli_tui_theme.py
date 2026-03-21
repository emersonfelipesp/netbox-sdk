from __future__ import annotations

from typer.testing import CliRunner

from netbox_cli import cli
from netbox_cli.config import Config

runner = CliRunner()


def _mock_config() -> Config:
    return Config(
        base_url="https://netbox.example.com",
        token_key="abc",
        token_secret="def",
        timeout=30.0,
    )


def test_tui_theme_list(monkeypatch) -> None:
    monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)

    result = runner.invoke(cli.app, ["tui", "--theme"])

    assert result.exit_code == 0
    assert "Available themes:" in result.stdout
    assert "- default" in result.stdout
    assert "- dracula" in result.stdout
    assert "- netbox-dark" in result.stdout
    assert "- netbox-light" in result.stdout


def test_tui_theme_dracula(monkeypatch) -> None:
    monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)
    monkeypatch.setattr(cli, "_get_client", lambda: object())
    monkeypatch.setattr(cli, "_get_index", lambda: object())

    called: dict[str, object] = {}

    def _fake_run_tui(*, client, index, theme_name: str, demo_mode: bool) -> None:
        called["theme_name"] = theme_name
        called["demo_mode"] = demo_mode

    import netbox_cli.tui as tui_module

    monkeypatch.setattr(tui_module, "run_tui", _fake_run_tui)

    result = runner.invoke(cli.app, ["tui", "--theme", "dracula"])

    assert result.exit_code == 0
    assert called["theme_name"] == "dracula"
    assert called["demo_mode"] is False


def test_tui_theme_unknown(monkeypatch) -> None:
    monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)

    result = runner.invoke(cli.app, ["tui", "--theme", "unknown-theme"])

    assert result.exit_code != 0
    assert "Unknown theme 'unknown-theme'" in result.output


def test_tui_theme_list_does_not_require_runtime_config(monkeypatch) -> None:
    def _fail_config():
        raise AssertionError("runtime config should not be requested for theme listing")

    monkeypatch.setattr(cli, "_ensure_runtime_config", _fail_config)

    result = runner.invoke(cli.app, ["tui", "--theme"])

    assert result.exit_code == 0
    assert "Available themes:" in result.stdout


def test_tui_theme_alias_netbox_dark(monkeypatch) -> None:
    monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)
    monkeypatch.setattr(cli, "_get_client", lambda: object())
    monkeypatch.setattr(cli, "_get_index", lambda: object())

    called: dict[str, object] = {}

    def _fake_run_tui(
        *, client, index, theme_name: str | None, demo_mode: bool
    ) -> None:
        called["theme_name"] = str(theme_name)
        called["demo_mode"] = demo_mode

    import netbox_cli.tui as tui_module

    monkeypatch.setattr(tui_module, "run_tui", _fake_run_tui)

    result = runner.invoke(cli.app, ["tui", "--theme", "netbox-dark"])

    assert result.exit_code == 0
    assert called["theme_name"] == "netbox-dark"
    assert called["demo_mode"] is False


def test_tui_theme_alias_netbox(monkeypatch) -> None:
    monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)
    monkeypatch.setattr(cli, "_get_client", lambda: object())
    monkeypatch.setattr(cli, "_get_index", lambda: object())

    called: dict[str, object] = {}

    def _fake_run_tui(
        *, client, index, theme_name: str | None, demo_mode: bool
    ) -> None:
        called["theme_name"] = str(theme_name)
        called["demo_mode"] = demo_mode

    import netbox_cli.tui as tui_module

    monkeypatch.setattr(tui_module, "run_tui", _fake_run_tui)

    result = runner.invoke(cli.app, ["tui", "--theme", "netbox"])

    assert result.exit_code == 0
    assert called["theme_name"] == "netbox-dark"
    assert called["demo_mode"] is False


def test_demo_tui_sets_demo_mode(monkeypatch) -> None:
    monkeypatch.setattr(cli, "_ensure_demo_runtime_config", _mock_config)
    monkeypatch.setattr(cli, "_get_demo_client", lambda: object())
    monkeypatch.setattr(cli, "_get_index", lambda: object())

    called: dict[str, object] = {}

    def _fake_run_tui(
        *, client, index, theme_name: str | None, demo_mode: bool
    ) -> None:
        called["theme_name"] = str(theme_name)
        called["demo_mode"] = demo_mode

    import netbox_cli.tui as tui_module

    monkeypatch.setattr(tui_module, "run_tui", _fake_run_tui)

    result = runner.invoke(cli.app, ["demo", "tui", "--theme", "dracula"])

    assert result.exit_code == 0
    assert called["theme_name"] == "dracula"
    assert called["demo_mode"] is True
