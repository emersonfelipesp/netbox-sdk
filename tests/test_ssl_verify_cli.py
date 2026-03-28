"""Tests for CLI TLS verification prompts and probe retry."""

from __future__ import annotations

import pytest
import typer

from netbox_sdk.client import ConnectionProbe
from netbox_sdk.config import DEFAULT_PROFILE, Config, load_profile_config

pytestmark = pytest.mark.suite_cli


def test_prompt_ssl_verify_if_unset_disable_persists(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    from netbox_cli.runtime import _prompt_ssl_verify_if_unset

    cfg = Config(
        base_url="https://example.com",
        token_key="k",
        token_secret="s",
        ssl_verify=None,
    )
    monkeypatch.setattr("netbox_cli.runtime.typer.confirm", lambda *a, **k: True)
    monkeypatch.setattr("netbox_cli.runtime.typer.echo", lambda *a, **k: None)
    _prompt_ssl_verify_if_unset(cfg, DEFAULT_PROFILE)
    assert cfg.ssl_verify is False
    assert load_profile_config(DEFAULT_PROFILE).ssl_verify is False


def test_prompt_ssl_verify_if_unset_keep_exits(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    from netbox_cli.runtime import _prompt_ssl_verify_if_unset

    cfg = Config(
        base_url="https://example.com",
        token_key="k",
        token_secret="s",
        ssl_verify=None,
    )
    monkeypatch.setattr("netbox_cli.runtime.typer.confirm", lambda *a, **k: False)
    monkeypatch.setattr("netbox_cli.runtime.typer.echo", lambda *a, **k: None)
    with pytest.raises(typer.Exit) as excinfo:
        _prompt_ssl_verify_if_unset(cfg, DEFAULT_PROFILE)
    assert excinfo.value.exit_code == 1
    assert cfg.ssl_verify is True
    assert load_profile_config(DEFAULT_PROFILE).ssl_verify is True


def test_prompt_ssl_verify_if_unset_noop_when_already_set(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    from netbox_cli.runtime import _prompt_ssl_verify_if_unset

    cfg = Config(
        base_url="https://example.com",
        token_key="k",
        token_secret="s",
        ssl_verify=False,
    )
    called: list[bool] = []

    def _no_confirm(*a: object, **k: object) -> bool:
        called.append(True)
        return True

    monkeypatch.setattr("netbox_cli.runtime.typer.confirm", _no_confirm)
    _prompt_ssl_verify_if_unset(cfg, DEFAULT_PROFILE)
    assert called == []


def test_retry_probe_after_ssl_prompt_repokes_on_disable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    from netbox_cli import runtime as rt

    cfg = Config(
        base_url="https://example.com",
        token_key="k",
        token_secret="s",
        ssl_verify=None,
    )
    bad = ConnectionProbe(
        status=0,
        version="",
        ok=False,
        error="certificate verify failed: self-signed certificate",
    )
    ok = ConnectionProbe(status=200, version="4.0", ok=True, error=None)

    def _fake_run(coro: object) -> ConnectionProbe:
        close = getattr(coro, "close", None)
        if callable(close):
            close()
        return ok

    monkeypatch.setattr(rt, "run_with_spinner", _fake_run)
    monkeypatch.setattr(rt.typer, "confirm", lambda *a, **k: True)
    monkeypatch.setattr(rt.typer, "echo", lambda *a, **k: None)
    out = rt._retry_probe_after_ssl_prompt(cfg, DEFAULT_PROFILE, bad)
    assert out is ok
    assert cfg.ssl_verify is False


def test_retry_probe_after_ssl_prompt_skips_when_not_cert_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from netbox_cli import runtime as rt

    cfg = Config(
        base_url="https://example.com",
        token_key="k",
        token_secret="s",
        ssl_verify=None,
    )
    probe = ConnectionProbe(status=0, version="", ok=False, error="connection refused")
    monkeypatch.setattr(rt, "run_with_spinner", lambda _c: (_ for _ in ()).throw(AssertionError))
    out = rt._retry_probe_after_ssl_prompt(cfg, DEFAULT_PROFILE, probe)
    assert out is probe
