from __future__ import annotations

import typer
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

    def _fake_run_tui(*, client, index, theme_name: str | None, demo_mode: bool) -> None:
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

    def _fake_run_tui(*, client, index, theme_name: str | None, demo_mode: bool) -> None:
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

    def _fake_run_tui(*, client, index, theme_name: str | None, demo_mode: bool) -> None:
        called["theme_name"] = str(theme_name)
        called["demo_mode"] = demo_mode

    import netbox_cli.tui as tui_module

    monkeypatch.setattr(tui_module, "run_tui", _fake_run_tui)

    result = runner.invoke(cli.app, ["demo", "tui", "--theme", "dracula"])

    assert result.exit_code == 0
    assert called["theme_name"] == "dracula"
    assert called["demo_mode"] is True


def test_dev_tui_theme_list(monkeypatch) -> None:
    monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)

    result = runner.invoke(cli.app, ["dev", "tui", "--theme"])

    assert result.exit_code == 0
    assert "Available themes:" in result.stdout
    assert "- netbox-dark" in result.stdout


def test_dev_tui_theme_dispatch(monkeypatch) -> None:
    monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)
    monkeypatch.setattr(cli, "_get_client", lambda: object())
    monkeypatch.setattr(cli, "_get_index", lambda: object())

    called: dict[str, object] = {}

    def _fake_run_dev_tui(*, client, index, theme_name: str | None) -> None:
        called["theme_name"] = str(theme_name)

    import netbox_cli.dev_tui as dev_tui_module

    monkeypatch.setattr(dev_tui_module, "run_dev_tui", _fake_run_dev_tui)

    result = runner.invoke(cli.app, ["dev", "tui", "--theme", "dracula"])

    assert result.exit_code == 0
    assert called["theme_name"] == "dracula"


def test_register_openapi_subcommands_uses_injected_index_factory(monkeypatch) -> None:
    class _FakeOperation:
        def __init__(self, method: str, path: str) -> None:
            self.method = method
            self.path = path
            self.operation_id = f"{method.lower()}-widgets"

    class _FakePaths:
        list_path = "/api/lab/widgets/"
        detail_path = "/api/lab/widgets/{id}/"

    class _InjectedIndex:
        def groups(self) -> list[str]:
            return ["lab"]

        def resources(self, group: str) -> list[str]:
            assert group == "lab"
            return ["widgets"]

        def operations_for(self, group: str, resource: str) -> list[_FakeOperation]:
            assert (group, resource) == ("lab", "widgets")
            return [_FakeOperation("GET", "/api/lab/widgets/")]

        def resource_paths(self, group: str, resource: str) -> _FakePaths:
            assert (group, resource) == ("lab", "widgets")
            return _FakePaths()

    class _GlobalIndex:
        def groups(self) -> list[str]:
            return []

        def resources(self, group: str) -> list[str]:
            raise AssertionError("global index should not be used")

        def operations_for(self, group: str, resource: str) -> list[object]:
            raise AssertionError("global index should not be used")

        def resource_paths(self, group: str, resource: str) -> object:
            raise AssertionError("global index should not be used")

    monkeypatch.setattr(cli, "_get_index", lambda: _GlobalIndex())
    target = typer.Typer(no_args_is_help=True)
    cli._register_openapi_subcommands(
        target,
        client_factory=lambda: object(),
        index_factory=lambda: _InjectedIndex(),
    )

    result = runner.invoke(target, ["lab", "widgets", "list", "--help"])

    assert result.exit_code == 0
    assert "list lab/widgets" in result.stdout
