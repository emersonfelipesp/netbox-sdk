"""Tests for new CLI options: --select, --columns, --max-columns, --dry-run."""

from __future__ import annotations

import json

import pytest
from click.exceptions import BadParameter
from typer.testing import CliRunner

from netbox_cli import cli
from netbox_cli.cli.dynamic import _parse_dynamic_options
from netbox_cli.cli.support import select_json_path
from netbox_cli.config import Config

runner = CliRunner()


def _mock_config() -> Config:
    return Config(
        base_url="https://netbox.example.com",
        token_key="abc",
        token_secret="def",
        timeout=30.0,
    )


class _FakeListClient:
    """Minimal async client so list/select/columns tests avoid real HTTP."""

    async def request(self, method: str, path: str, **kwargs: object):
        del method, path, kwargs

        class _Response:
            status = 200
            text = json.dumps({"count": 0, "results": []})

        return _Response()


def _patch_list_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)
    monkeypatch.setattr(cli, "_get_client", lambda: _FakeListClient())


class TestSelectJsonPath:
    """Tests for select_json_path helper function."""

    def test_select_simple_field(self):
        data = {"id": 1, "name": "test"}
        assert select_json_path(data, "name") == "test"

    def test_select_nested_field(self):
        data = {"results": [{"name": "device1"}, {"name": "device2"}]}
        assert select_json_path(data, "results.0.name") == "device1"

    def test_select_array_index(self):
        data = {"results": [{"id": 1}, {"id": 2}]}
        assert select_json_path(data, "results.1.id") == 2

    def test_select_all_items_in_array(self):
        data = {"results": [{"name": "a"}, {"name": "b"}]}
        result = select_json_path(data, "results")
        assert result == [{"name": "a"}, {"name": "b"}]

    def test_select_nonexistent_path(self):
        data = {"id": 1}
        assert select_json_path(data, "nonexistent") is None

    def test_select_empty_path_returns_original(self):
        data = {"id": 1}
        assert select_json_path(data, "") == data

    def test_select_deeply_nested(self):
        data = {"a": {"b": {"c": {"d": "deep"}}}}
        assert select_json_path(data, "a.b.c.d") == "deep"

    def test_select_invalid_array_index(self):
        data = {"results": [{"name": "a"}]}
        assert select_json_path(data, "results.99") is None

    def test_select_array_with_non_numeric(self):
        data = {"results": [{"name": "a"}]}
        assert select_json_path(data, "results.invalid") is None


class TestParseDynamicOptionsNewFlags:
    """Tests for _parse_dynamic_options with new flags."""

    def test_parse_select_flag(self):
        result = _parse_dynamic_options(["--select", "results.0.name"])
        assert result[9] == "results.0.name"

    def test_parse_columns_flag(self):
        result = _parse_dynamic_options(["--columns", "id,name,status"])
        assert result[10] == ["id", "name", "status"]

    def test_parse_columns_flag_with_spaces(self):
        result = _parse_dynamic_options(["--columns", "id, name, status"])
        assert result[10] == ["id", "name", "status"]

    def test_parse_max_columns_flag(self):
        result = _parse_dynamic_options(["--max-columns", "3"])
        assert result[11] == 3

    def test_parse_max_columns_default(self):
        result = _parse_dynamic_options([])
        assert result[11] == 6

    def test_parse_max_columns_invalid(self):
        with pytest.raises(BadParameter):
            _parse_dynamic_options(["--max-columns", "invalid"])

    def test_parse_max_columns_zero_raises(self):
        with pytest.raises(BadParameter):
            _parse_dynamic_options(["--max-columns", "0"])

    def test_parse_dry_run_flag(self):
        result = _parse_dynamic_options(["--dry-run"])
        assert result[12] is True

    def test_parse_dry_run_defaults_false(self):
        result = _parse_dynamic_options([])
        assert result[12] is False

    def test_parse_select_requires_value(self):
        with pytest.raises(BadParameter):
            _parse_dynamic_options(["--select"])

    def test_parse_columns_requires_value(self):
        with pytest.raises(BadParameter):
            _parse_dynamic_options(["--columns"])

    def test_parse_max_columns_requires_value(self):
        with pytest.raises(BadParameter):
            _parse_dynamic_options(["--max-columns"])

    def test_parse_multiple_new_flags(self):
        result = _parse_dynamic_options(
            [
                "--select",
                "results.0.name",
                "--columns",
                "id,name",
                "--max-columns",
                "4",
                "--dry-run",
            ]
        )
        assert result[9] == "results.0.name"
        assert result[10] == ["id", "name"]
        assert result[11] == 4
        assert result[12] is True


class TestDryRunValidation:
    """Tests for --dry-run validation (only write operations)."""

    def test_dry_run_allowed_for_create(self, monkeypatch):
        monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)

        result = runner.invoke(
            cli.app,
            ["dcim", "devices", "create", "--dry-run", "--body-json", '{"name":"test"}'],
        )
        assert result.exit_code == 0
        assert "Dry Run Preview" in result.output

    def test_dry_run_allowed_for_update(self, monkeypatch):
        monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)

        result = runner.invoke(
            cli.app,
            [
                "dcim",
                "devices",
                "update",
                "--id",
                "1",
                "--dry-run",
                "--body-json",
                '{"name":"test"}',
            ],
        )
        assert result.exit_code == 0
        assert "Dry Run Preview" in result.output

    def test_dry_run_allowed_for_patch(self, monkeypatch):
        monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)

        result = runner.invoke(
            cli.app,
            [
                "dcim",
                "devices",
                "patch",
                "--id",
                "1",
                "--dry-run",
                "--body-json",
                '{"name":"test"}',
            ],
        )
        assert result.exit_code == 0
        assert "Dry Run Preview" in result.output

    def test_dry_run_allowed_for_delete(self, monkeypatch):
        monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)

        result = runner.invoke(
            cli.app,
            ["dcim", "devices", "delete", "--id", "1", "--dry-run"],
        )
        assert result.exit_code == 0
        assert "Dry Run Preview" in result.output

    def test_dry_run_rejected_for_list(self, monkeypatch):
        monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)

        result = runner.invoke(
            cli.app,
            ["dcim", "devices", "list", "--dry-run"],
        )
        assert result.exit_code != 0
        assert "write operations" in result.output.lower()

    def test_dry_run_rejected_for_get(self, monkeypatch):
        monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)

        result = runner.invoke(
            cli.app,
            ["dcim", "devices", "get", "--id", "1", "--dry-run"],
        )
        assert result.exit_code != 0
        assert "write operations" in result.output.lower()


class TestColumnControl:
    """Tests for --columns and --max-columns in table rendering."""

    def test_columns_option_accepted(self, monkeypatch):
        """Test that --columns option is accepted by the CLI."""
        _patch_list_client(monkeypatch)

        result = runner.invoke(
            cli.app,
            ["dcim", "devices", "list", "--columns", "id,name"],
        )
        assert result.exit_code == 0

    def test_max_columns_option_accepted(self, monkeypatch):
        """Test that --max-columns option is accepted by the CLI."""
        _patch_list_client(monkeypatch)

        result = runner.invoke(
            cli.app,
            ["dcim", "devices", "list", "--max-columns", "2"],
        )
        assert result.exit_code == 0

    def test_columns_nonexistent_raises_bad_parameter(self, monkeypatch):
        """--columns must match at least one key in the response rows."""

        class _ClientWithRows(_FakeListClient):
            async def request(self, method: str, path: str, **kwargs: object):
                del method, path, kwargs

                class _Response:
                    status = 200
                    text = json.dumps({"count": 1, "results": [{"id": 1, "name": "d1"}]})

                return _Response()

        monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)
        monkeypatch.setattr(cli, "_get_client", lambda: _ClientWithRows())

        result = runner.invoke(
            cli.app,
            ["dcim", "devices", "list", "--columns", "bogus,also_missing"],
        )
        assert result.exit_code != 0
        assert "None of the requested columns" in result.output


class TestSelectOption:
    """Tests for --select field extraction."""

    def test_select_option_accepted(self, monkeypatch):
        """Test that --select option is accepted by the CLI."""
        _patch_list_client(monkeypatch)

        result = runner.invoke(
            cli.app,
            ["dcim", "devices", "list", "--select", "results.0.name"],
        )
        assert result.exit_code == 0
