"""Tests for the ``nbx branching`` Typer subapp.

Covers:
- Subcommand registration (``nbx branching --help`` lists every verb).
- ``nbx branch`` alias (same subapp under a second name).
- ``nbx --branch ...`` global option seeds the ``X-NetBox-Branch`` header.
- ``nbx branching status`` short-circuits to a JSON payload when the SDK
  reports the plugin missing.
- ``nbx branching list`` round-trips through a fake SDK client.

These tests do not spin up a live server; they patch the runtime client
factory or the BranchingClient methods directly.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pytest
from typer.testing import CliRunner

from netbox_cli import app as nbx_app
from netbox_cli import runtime as nbx_runtime
from netbox_sdk.client import _scoped_headers
from netbox_sdk.config import Config

pytestmark = pytest.mark.suite_cli


runner = CliRunner()

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _plain(text: str) -> str:
    """Strip ANSI escapes so assertions are styling-agnostic."""
    return _ANSI_RE.sub("", text)


@pytest.fixture(autouse=True)
def _isolate_scoped_headers():
    """Reset the shared ``_scoped_headers`` ContextVar around every test.

    The root CLI callback writes ``X-NetBox-Branch`` into this var when
    ``--branch`` is passed, and CliRunner.invoke runs synchronously in
    the current task — so the value persists across tests within a
    pytest-xdist worker if we don't reset it explicitly.
    """
    token = _scoped_headers.set({})
    try:
        yield
    finally:
        _scoped_headers.reset(token)


class _NoopClient:
    """Stand-in for NetBoxApiClient — only needs ``request`` and ``close``."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def request(self, method: str, path: str, **kwargs: Any):  # noqa: ARG002
        self.calls.append((method, path))

        class _R:
            status = 200
            text = json.dumps({"count": 0, "results": []})
            headers: dict[str, str] = {}

            def json(self) -> Any:
                return {"count": 0, "results": []}

        return _R()

    async def close(self) -> None:
        return None


@pytest.fixture
def fake_client(monkeypatch):
    client = _NoopClient()

    def _get_client(*_a: Any, **_kw: Any):
        return client

    monkeypatch.setattr(nbx_runtime, "_get_client", _get_client)
    # The CLI module imports the helper at module load time; patch the
    # rebinding inside netbox_cli.branching too.
    import netbox_cli.branching as branching_mod

    monkeypatch.setattr(branching_mod, "_get_client", _get_client)
    return client


def test_branching_help_lists_all_verbs():
    result = runner.invoke(nbx_app, ["branching", "--help"])
    assert result.exit_code == 0
    for verb in (
        "status",
        "list",
        "show",
        "create",
        "update",
        "delete",
        "sync",
        "merge",
        "revert",
        "archive",
        "events",
        "changes",
        "models",
    ):
        assert verb in result.stdout


def test_branch_alias_also_registered():
    result = runner.invoke(nbx_app, ["branch", "list", "--help"])
    assert result.exit_code == 0
    assert "List branches" in result.stdout


def test_root_help_shows_branch_global_option():
    result = runner.invoke(nbx_app, ["--help"])
    assert result.exit_code == 0
    assert "--branch" in _plain(result.stdout)


def test_global_branch_option_sets_header(monkeypatch):
    """Passing --branch should seed _scoped_headers via the root callback."""
    captured: dict[str, dict[str, str] | None] = {}

    # Monkeypatch the runtime client factory so we can capture the headers
    # ContextVar at the time a downstream command would run.
    def _get_client(*_a: Any, **_kw: Any):
        captured["headers"] = dict(_scoped_headers.get() or {})

        class _NoClient:
            async def request(self, *a: Any, **kw: Any):  # noqa: ARG002
                class _R:
                    status = 404
                    text = ""
                    headers: dict[str, str] = {}

                    def json(self) -> Any:
                        return {}

                return _R()

            async def close(self) -> None:
                return None

        return _NoClient()

    monkeypatch.setattr(nbx_runtime, "_get_client", _get_client)
    import netbox_cli.branching as branching_mod

    monkeypatch.setattr(branching_mod, "_get_client", _get_client)

    result = runner.invoke(nbx_app, ["--branch", "td5smq0f", "branching", "status"])
    # Exit may be 0 (plugin reported missing) or non-zero — what we care
    # about is that the header reached the runtime layer.
    assert captured.get("headers", {}).get("X-NetBox-Branch") == "td5smq0f"
    assert result is not None


def test_branching_list_renders_empty(fake_client):
    result = runner.invoke(nbx_app, ["branching", "list"])
    assert result.exit_code == 0


def test_branching_status_when_plugin_missing(monkeypatch):
    """A 404 from /api/plugins/branching/ should produce a JSON 'available: false'."""

    class _ClientReturning404:
        async def request(self, method: str, path: str, **kwargs: Any):  # noqa: ARG002
            class _R:
                status = 404
                text = ""
                headers: dict[str, str] = {}

                def json(self) -> Any:
                    return {}

            return _R()

        async def close(self) -> None:
            return None

    def _get_client(*_a: Any, **_kw: Any):
        return _ClientReturning404()

    monkeypatch.setattr(nbx_runtime, "_get_client", _get_client)
    import netbox_cli.branching as branching_mod

    monkeypatch.setattr(branching_mod, "_get_client", _get_client)

    result = runner.invoke(nbx_app, ["branching", "status"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout.strip())
    assert payload == {"available": False}


def test_config_is_loadable_for_assertions():
    # Sanity check: Config remains importable without optional extras.
    cfg = Config(base_url="http://x", token="t", ssl_verify=False)
    assert cfg.base_url == "http://x"
