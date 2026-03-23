"""Tests for markdown output rendering and output-format flag handling."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from netbox_cli import cli
from netbox_cli.cli.dynamic import _parse_dynamic_options
from netbox_cli.cli.support import OUTPUT_FORMAT_CONFLICT_MESSAGE, resolve_output_format
from netbox_cli.config import Config
from netbox_cli.markdown_output import render_markdown

runner = CliRunner()


def _mock_config() -> Config:
    return Config(
        base_url="https://netbox.example.com",
        token_key="abc",
        token_secret="def",
        timeout=30.0,
    )


def test_render_markdown_paginated_results_table() -> None:
    payload = {
        "count": 2,
        "results": [
            {"id": 1, "name": "r1", "status": "active"},
            {"id": 2, "name": "r2", "status": "planned"},
        ],
    }

    rendered = render_markdown(payload)

    assert "| ID | Name | Status |" in rendered
    assert "| 1 | r1 | active |" in rendered
    assert "| 2 | r2 | planned |" in rendered


def test_render_markdown_list_of_dicts_table() -> None:
    payload = [{"id": 7, "display": "edge-1"}, {"id": 8, "display": "edge-2"}]

    rendered = render_markdown(payload)

    assert "| ID | Display |" in rendered
    assert "| 7 | edge-1 |" in rendered
    assert "| 8 | edge-2 |" in rendered


def test_render_markdown_single_dict_field_value_table() -> None:
    payload = {"id": 42, "name": "sw-42"}

    rendered = render_markdown(payload)

    assert "| Field | Value |" in rendered
    assert "| ID | 42 |" in rendered
    assert "| Name | sw-42 |" in rendered


def test_render_markdown_nested_values_are_serialized_and_escaped() -> None:
    payload = {
        "id": 1,
        "meta": {"a": "x|y", "note": "line1\nline2"},
        "tags": ["core", "leaf"],
    }

    rendered = render_markdown(payload)

    assert '{"a":"x\\|y","note":"line1\\nline2"}' in rendered
    assert '| Tags | ["core","leaf"] |' in rendered


def test_render_markdown_empty_payload_behaviors() -> None:
    assert render_markdown([]) == "No results."
    assert render_markdown({"count": 0, "results": []}) == "No results."


def test_resolve_output_format_rejects_mixed_flags() -> None:
    with pytest.raises(ValueError, match=OUTPUT_FORMAT_CONFLICT_MESSAGE):
        resolve_output_format(as_json=True, as_markdown=True, error_factory=ValueError)


def test_parse_dynamic_options_accepts_markdown() -> None:
    parsed = _parse_dynamic_options(["--markdown"])
    assert parsed[6] is True


def test_nbx_call_rejects_conflicting_output_flags(monkeypatch) -> None:
    monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)

    result = runner.invoke(
        cli.app,
        ["call", "GET", "/api/status/", "--json", "--markdown"],
    )

    assert result.exit_code != 0
    import re

    cleaned = re.sub(r"[│╭╮╰╯─]", "", result.output)
    normalized_output = re.sub(r"\s+", " ", cleaned)
    assert OUTPUT_FORMAT_CONFLICT_MESSAGE in normalized_output


def test_dev_http_rejects_conflicting_output_flags(monkeypatch) -> None:
    monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)

    result = runner.invoke(
        cli.app,
        ["dev", "http", "get", "--path", "/api/status/", "--yaml", "--markdown"],
    )

    assert result.exit_code != 0
    import re

    cleaned = re.sub(r"[│╭╮╰╯─]", "", result.output)
    normalized_output = re.sub(r"\s+", " ", cleaned)
    assert OUTPUT_FORMAT_CONFLICT_MESSAGE in normalized_output


def test_nbx_call_markdown_outputs_table(monkeypatch) -> None:
    monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)

    class _FakeClient:
        async def request(self, method: str, path: str, **kwargs: object):
            del method, path, kwargs

            class _Response:
                status = 200
                text = json.dumps({"id": 9, "name": "sw9"})

            return _Response()

    monkeypatch.setattr(cli, "_get_client", lambda: _FakeClient())

    result = runner.invoke(
        cli.app,
        ["call", "GET", "/api/dcim/devices/9/", "--markdown"],
    )

    assert result.exit_code == 0
    assert "Status: 200" in result.output
    assert "| Field | Value |" in result.output
    assert "| ID | 9 |" in result.output
