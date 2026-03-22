"""Tests for demo CLI commands, bootstrap flows, and profile setup behavior."""

from __future__ import annotations

import sys
from types import SimpleNamespace

from typer.testing import CliRunner

from netbox_cli import cli
from netbox_cli.api import ConnectionProbe
from netbox_cli.config import DEMO_BASE_URL, Config

runner = CliRunner()


def _demo_config() -> Config:
    return Config(
        base_url=DEMO_BASE_URL,
        token_version="v1",
        token_key=None,
        token_secret="demo-secret",
        timeout=30.0,
    )


def test_demo_config_command(monkeypatch) -> None:
    monkeypatch.setattr(
        cli.demo,
        "load_profile_config",
        lambda profile: _demo_config().model_copy(
            update={"demo_username": "demo-user", "demo_password": "demo-pass"}
        ),
    )

    result = runner.invoke(cli.app, ["demo", "config"])

    assert result.exit_code == 0
    assert DEMO_BASE_URL in result.stdout
    assert '"profile": "demo"' in result.stdout
    assert '"demo_username": "demo-user"' in result.stdout
    assert '"demo_password": "set"' in result.stdout


def test_demo_config_allows_legacy_v2_profile(monkeypatch) -> None:
    monkeypatch.setattr(
        cli,
        "load_profile_config",
        lambda profile: Config(
            base_url=DEMO_BASE_URL,
            token_version="v2",
            token_key="legacy-key",
            token_secret="legacy-secret",
            timeout=30.0,
        ),
    )

    result = runner.invoke(cli.app, ["demo", "config"])

    assert result.exit_code == 0
    assert '"token_version": "v2"' in result.output


def test_demo_test_command_success(monkeypatch) -> None:
    class _FakeClient:
        async def probe_connection(self) -> ConnectionProbe:
            return ConnectionProbe(status=200, version="4.2", ok=True, error=None)

    monkeypatch.setattr(cli, "_ensure_demo_runtime_config", _demo_config)
    monkeypatch.setattr(cli, "_get_client_for_config", lambda cfg: _FakeClient())

    result = runner.invoke(cli.app, ["demo", "test"])

    assert result.exit_code == 0
    assert "Demo connection OK" in result.output
    assert "status=200" in result.output
    assert "api_version=4.2" in result.output


def test_demo_test_command_failure(monkeypatch) -> None:
    class _FakeClient:
        async def probe_connection(self) -> ConnectionProbe:
            return ConnectionProbe(
                status=401,
                version="",
                ok=False,
                error="Invalid token",
            )

    monkeypatch.setattr(cli, "_ensure_demo_runtime_config", _demo_config)
    monkeypatch.setattr(cli, "_get_client_for_config", lambda cfg: _FakeClient())

    result = runner.invoke(cli.app, ["demo", "test"])

    assert result.exit_code == 1
    assert "Demo connection failed: Invalid token" in result.output


def test_demo_callback_initializes_when_missing(monkeypatch) -> None:
    called: dict[str, bool] = {}

    monkeypatch.setattr(cli, "load_profile_config", lambda profile: Config(base_url=DEMO_BASE_URL))

    def _fake_init(
        *,
        force: bool,
        headless: bool = False,
        token_key: str | None = None,
        token_secret: str | None = None,
    ) -> Config:
        called["force"] = force
        return _demo_config()

    monkeypatch.setattr(cli, "_initialize_demo_profile", _fake_init)

    result = runner.invoke(cli.app, ["demo"])

    assert result.exit_code == 0
    assert called["force"] is True


def test_demo_dynamic_command_uses_demo_profile(monkeypatch) -> None:
    calls: dict[str, object] = {}

    async def _fake_run_dynamic_command(**kwargs):
        calls.update(kwargs)

        class _Response:
            status = 200
            text = '{"count":0,"results":[]}'

        return _Response()

    monkeypatch.setattr(cli, "_ensure_demo_runtime_config", _demo_config)
    monkeypatch.setattr(cli, "_get_index", lambda: object())
    monkeypatch.setattr(cli, "run_dynamic_command", _fake_run_dynamic_command)

    result = runner.invoke(cli.app, ["demo", "dcim", "devices", "list"])

    assert result.exit_code == 0
    assert calls["group"] == "dcim"
    assert calls["resource"] == "devices"
    assert calls["action"] == "list"
    assert calls["client"].config.base_url == DEMO_BASE_URL


def test_demo_init_bootstraps_and_saves_profile(monkeypatch) -> None:
    prompts = iter(["demo-user", "demo-pass"])
    saved: dict[str, object] = {}

    monkeypatch.setitem(sys.modules, "playwright", SimpleNamespace())
    monkeypatch.setattr(cli.typer, "prompt", lambda *args, **kwargs: next(prompts))
    monkeypatch.setattr(
        cli,
        "load_profile_config",
        lambda profile: Config(base_url=DEMO_BASE_URL, timeout=42.0),
    )
    monkeypatch.setattr(
        "netbox_cli.demo_auth.bootstrap_demo_profile",
        lambda **kwargs: Config(
            base_url=DEMO_BASE_URL,
            token_key="fresh-key",
            token_secret="fresh-secret",
            timeout=kwargs["timeout"],
        ),
    )
    monkeypatch.setattr(
        cli,
        "save_profile_config",
        lambda profile, cfg: saved.update({"profile": profile, "cfg": cfg}),
    )
    monkeypatch.setattr(cli, "_verify_runtime_config", lambda cfg, context: None)

    result = runner.invoke(cli.app, ["demo", "init"])

    assert result.exit_code == 0
    assert saved["profile"] == "demo"
    assert saved["cfg"].token_key == "fresh-key"
    assert saved["cfg"].timeout == 42.0
    assert saved["cfg"].demo_username == "demo-user"
    assert saved["cfg"].demo_password == "demo-pass"


def test_demo_init_defaults_to_headless(monkeypatch) -> None:
    prompts = iter(["demo-user", "demo-pass"])
    called: dict[str, object] = {}

    monkeypatch.setitem(sys.modules, "playwright", SimpleNamespace())
    monkeypatch.setattr(cli.typer, "prompt", lambda *args, **kwargs: next(prompts))
    monkeypatch.setattr(
        cli,
        "load_profile_config",
        lambda profile: Config(base_url=DEMO_BASE_URL, timeout=42.0),
    )
    monkeypatch.setattr(
        "netbox_cli.demo_auth.bootstrap_demo_profile",
        lambda **kwargs: (
            called.update(kwargs)
            or Config(
                base_url=DEMO_BASE_URL,
                token_key="fresh-key",
                token_secret="fresh-secret",
                timeout=kwargs["timeout"],
            )
        ),
    )
    monkeypatch.setattr(cli, "save_profile_config", lambda profile, cfg: None)
    monkeypatch.setattr(cli, "_verify_runtime_config", lambda cfg, context: None)

    result = runner.invoke(cli.app, ["demo", "init"])

    assert result.exit_code == 0
    assert called["headless"] is True


def test_demo_direct_token_setup(monkeypatch) -> None:
    saved: dict[str, object] = {}

    monkeypatch.setattr(
        cli,
        "load_profile_config",
        lambda profile: Config(base_url=DEMO_BASE_URL, timeout=33.0),
    )
    monkeypatch.setattr(
        cli.typer,
        "confirm",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(
        cli,
        "save_profile_config",
        lambda profile, cfg: saved.update({"profile": profile, "cfg": cfg}),
    )
    monkeypatch.setattr(cli, "_verify_runtime_config", lambda cfg, context: None)

    result = runner.invoke(
        cli.app,
        ["demo", "--token-key", "provided-key", "--token-secret", "provided-secret"],
    )

    assert result.exit_code == 0
    assert saved["profile"] == "demo"
    assert saved["cfg"].token_key == "provided-key"
    assert saved["cfg"].token_secret == "provided-secret"
    assert saved["cfg"].base_url == DEMO_BASE_URL


def test_demo_direct_token_requires_both_values() -> None:
    result = runner.invoke(cli.app, ["demo", "--token-key", "provided-key"])

    assert result.exit_code != 0
    assert "Use both --token-key and --token-secret together." in result.output


def test_demo_direct_token_setup_rejects_invalid_token(monkeypatch) -> None:
    monkeypatch.setattr(
        cli,
        "load_profile_config",
        lambda profile: Config(base_url=DEMO_BASE_URL, timeout=33.0),
    )
    monkeypatch.setattr(cli.typer, "confirm", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        cli,
        "_verify_runtime_config",
        lambda cfg, context: (_ for _ in ()).throw(
            cli.typer.BadParameter("Demo token verification failed: Invalid v1 token")
        ),
    )

    result = runner.invoke(
        cli.app,
        ["demo", "--token-key", "provided-key", "--token-secret", "provided-secret"],
    )

    assert result.exit_code != 0
    assert "Demo token verification failed: Invalid v1 token" in result.output


def test_demo_override_confirmation_can_abort(monkeypatch) -> None:
    monkeypatch.setattr(cli, "load_profile_config", lambda profile: _demo_config())
    monkeypatch.setattr(cli.typer, "confirm", lambda *args, **kwargs: False)

    result = runner.invoke(
        cli.app,
        ["demo", "--token-key", "provided-key", "--token-secret", "provided-secret"],
    )

    assert result.exit_code == 1
    assert "Demo configuration saved." not in result.output


def test_demo_init_reports_playwright_error(monkeypatch) -> None:
    prompts = iter(["demo-user", "demo-pass"])

    monkeypatch.setitem(sys.modules, "playwright", SimpleNamespace())
    monkeypatch.setattr(cli.typer, "prompt", lambda *args, **kwargs: next(prompts))
    monkeypatch.setattr(
        cli,
        "load_profile_config",
        lambda profile: Config(base_url=DEMO_BASE_URL, timeout=42.0),
    )
    monkeypatch.setattr(cli.typer, "confirm", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        "netbox_cli.demo_auth.bootstrap_demo_profile",
        lambda **kwargs: (_ for _ in ()).throw(
            RuntimeError(
                "Playwright is required for `nbx demo init`. Install it with:\n"
                "  pip install playwright\n"
                "  playwright install chromium"
            )
        ),
    )

    result = runner.invoke(cli.app, ["demo", "init"])

    assert result.exit_code == 1
    assert "Playwright is required for `nbx demo init`." in result.output
    assert "pip install playwright" in result.output


def test_demo_init_rejects_unverified_token(monkeypatch) -> None:
    prompts = iter(["demo-user", "demo-pass"])

    monkeypatch.setitem(sys.modules, "playwright", SimpleNamespace())
    monkeypatch.setattr(cli.typer, "prompt", lambda *args, **kwargs: next(prompts))
    monkeypatch.setattr(
        cli,
        "load_profile_config",
        lambda profile: Config(base_url=DEMO_BASE_URL, timeout=42.0),
    )
    monkeypatch.setattr(
        "netbox_cli.demo_auth.bootstrap_demo_profile",
        lambda **kwargs: Config(
            base_url=DEMO_BASE_URL,
            token_version="v1",
            token_key=None,
            token_secret="invalid-token",
            timeout=kwargs["timeout"],
        ),
    )
    monkeypatch.setattr(
        cli,
        "_verify_runtime_config",
        lambda cfg, context: (_ for _ in ()).throw(
            cli.typer.BadParameter("Demo token verification failed: Invalid v1 token")
        ),
    )

    result = runner.invoke(cli.app, ["demo", "init"])

    assert result.exit_code == 1
    assert "Demo token verification failed: Invalid v1 token" in result.output


def test_demo_init_reports_missing_system_libraries(monkeypatch) -> None:
    prompts = iter(["demo-user", "demo-pass"])

    monkeypatch.setitem(sys.modules, "playwright", SimpleNamespace())
    monkeypatch.setattr(cli.typer, "prompt", lambda *args, **kwargs: next(prompts))
    monkeypatch.setattr(
        cli,
        "load_profile_config",
        lambda profile: Config(base_url=DEMO_BASE_URL, timeout=42.0),
    )
    monkeypatch.setattr(cli.typer, "confirm", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        "netbox_cli.demo_auth.bootstrap_demo_profile",
        lambda **kwargs: (_ for _ in ()).throw(
            RuntimeError(
                "Playwright Chromium could not start because system libraries are missing.\n"
                "Install browser dependencies with:\n"
                "  playwright install --with-deps chromium\n"
                "If that is unavailable on your system, install the missing shared libraries and retry."
            )
        ),
    )

    result = runner.invoke(cli.app, ["demo", "init"])

    assert result.exit_code == 1
    assert "playwright install --with-deps chromium" in result.output


def test_demo_init_reports_missing_x_server_for_headed(monkeypatch) -> None:
    prompts = iter(["demo-user", "demo-pass"])

    monkeypatch.setitem(sys.modules, "playwright", SimpleNamespace())
    monkeypatch.setattr(cli.typer, "prompt", lambda *args, **kwargs: next(prompts))
    monkeypatch.setattr(
        cli,
        "load_profile_config",
        lambda profile: Config(base_url=DEMO_BASE_URL, timeout=42.0),
    )
    monkeypatch.setattr(cli.typer, "confirm", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        "netbox_cli.demo_auth.bootstrap_demo_profile",
        lambda **kwargs: (_ for _ in ()).throw(
            RuntimeError(
                "Playwright was started in headed mode, but no X server is available.\n"
                "Use headless mode, or run the command under xvfb.\n"
                "Examples:\n"
                "  nbx demo\n"
                "  xvfb-run nbx demo --headed"
            )
        ),
    )

    result = runner.invoke(cli.app, ["demo", "init", "--headed"])

    assert result.exit_code == 1
    assert "no X server is available" in result.output
    assert "xvfb-run nbx demo --headed" in result.output


def test_demo_missing_playwright_fails_before_prompt(monkeypatch) -> None:
    monkeypatch.setattr(
        cli,
        "load_profile_config",
        lambda profile: Config(base_url=DEMO_BASE_URL, timeout=42.0),
    )
    monkeypatch.setattr(cli.typer, "confirm", lambda *args, **kwargs: True)

    prompted = {"called": False}

    def _fail_prompt(*args, **kwargs):
        prompted["called"] = True
        raise AssertionError("prompt should not run before Playwright preflight")

    monkeypatch.setattr(cli.typer, "prompt", _fail_prompt)

    import builtins

    real_import = builtins.__import__

    def _fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "playwright":
            raise ModuleNotFoundError("No module named 'playwright'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _fake_import)

    result = runner.invoke(cli.app, ["demo"])

    assert result.exit_code == 1
    assert prompted["called"] is False
    assert "uv sync --dev" in result.output
    assert "uv tool run --from playwright playwright install chromium --with-deps" in result.output
