"""Tests for new CLI options: --select, --columns, --max-columns, --dry-run."""

from __future__ import annotations

import json

import pytest
from click.exceptions import BadParameter
from typer.testing import CliRunner

import netbox_cli.dev as cli_dev
from netbox_cli import cli
from netbox_cli.dynamic import _handle_dynamic_invocation, _parse_dynamic_options
from netbox_cli.support import select_json_path
from netbox_sdk.client import ApiResponse
from netbox_sdk.schema import SchemaIndex

pytestmark = pytest.mark.suite_cli

runner = CliRunner()


def _live_plugin_index() -> SchemaIndex:
    index = SchemaIndex({"openapi": "3.0.0", "paths": {}})
    index.add_discovered_resource(
        group="plugins",
        resource="custom/widgets",
        list_path="/api/plugins/custom/widgets/",
        detail_path="/api/plugins/custom/widgets/{id}/",
        list_methods=("GET", "POST"),
        detail_methods=("GET", "PATCH", "DELETE"),
    )
    return index


def _mock_config() -> cli.Config:
    from netbox_sdk.config import Config

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


class _FakeRuntimeDiscoveryClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def request(self, method: str, path: str, **kwargs: object) -> ApiResponse:
        del kwargs
        self.calls.append((method, path))
        if method == "GET" and path == "/api/plugins/":
            return ApiResponse(status=200, text="{}", headers={})
        if method == "GET" and path == "/api/core/object-types/":
            return ApiResponse(
                status=200,
                text=(
                    '{"count": 1, "next": null, "results": ['
                    '{"public": true, "rest_api_endpoint": "/api/plugins/custom/widgets/"}'
                    "]}"
                ),
                headers={},
            )
        if method == "OPTIONS" and path == "/api/plugins/custom/widgets/":
            return ApiResponse(
                status=200,
                text='{"actions": {"POST": {}}}',
                headers={"Allow": "GET, POST, OPTIONS"},
            )
        if method == "GET" and path == "/api/plugins/custom/widgets/":
            return ApiResponse(status=200, text='{"count": 0, "results": []}', headers={})
        return ApiResponse(status=404, text='{"detail": "not found"}', headers={})


class _CaptureClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def request(self, method: str, path: str, **kwargs: object) -> ApiResponse:
        self.calls.append({"method": method, "path": path, **kwargs})
        return ApiResponse(status=200, text='{"count": 0, "results": []}', headers={})


def _patch_list_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)
    monkeypatch.setattr(
        "netbox_cli.runtime._get_client",
        lambda: _FakeListClient(),
    )


def test_call_command_forwards_headers_and_repeated_query(monkeypatch):
    client = _CaptureClient()
    monkeypatch.setattr(cli, "_get_client", lambda: client)

    result = runner.invoke(
        cli.app,
        [
            "call",
            "GET",
            "/api/dcim/devices/",
            "-q",
            "tag=prod",
            "-q",
            "tag=edge",
            "-H",
            'If-Match: "etag"',
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert client.calls[0]["query"] == {"tag": ["prod", "edge"]}
    assert client.calls[0]["headers"] == {"If-Match": '"etag"'}


def test_dev_http_get_forwards_headers_and_repeated_query(monkeypatch):
    client = _CaptureClient()
    monkeypatch.setattr(cli_dev, "dev_http_api_client", lambda: client)

    result = runner.invoke(
        cli.app,
        [
            "dev",
            "http",
            "get",
            "--path",
            "/api/dcim/devices/",
            "-q",
            "tag=prod",
            "-q",
            "tag=edge",
            "-H",
            "If-Match=etag",
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert client.calls[0]["query"] == {"tag": ["prod", "edge"]}
    assert client.calls[0]["headers"] == {"If-Match": "etag"}


class TestDevHttpInputValidation:
    """Focused checks for the shared dev-http input validation helpers."""

    def test_rejects_empty_path(self):
        with pytest.raises(BadParameter) as raised:
            cli_dev._validate_dev_input(cli_dev._DevHttpGetInput, path=" ")

        assert "--path: cannot be empty" in str(raised.value)

    @pytest.mark.parametrize(
        ("model_cls", "kwargs"),
        (
            (cli_dev._DevHttpGetInput, {"path": "/api/status/", "object_id": 0}),
            (cli_dev._DevHttpBodyInput, {"path": "/api/status/", "object_id": -1}),
            (cli_dev._DevHttpDeleteInput, {"path": "/api/status/", "object_id": 0}),
        ),
    )
    def test_rejects_non_positive_object_ids(self, model_cls, kwargs):
        with pytest.raises(BadParameter) as raised:
            cli_dev._validate_dev_input(model_cls, **kwargs)

        assert "--id: must be a positive integer" in str(raised.value)

    def test_rejects_invalid_query_pair(self):
        with pytest.raises(BadParameter) as raised:
            cli_dev._validate_dev_input(
                cli_dev._DevHttpGetInput,
                path="/api/status/",
                query=["status"],
            )

        message = str(raised.value)
        assert "--query: expected key=value format" in message
        assert "--query site=nyc" in message

    def test_rejects_invalid_argument_pair(self):
        with pytest.raises(BadParameter) as raised:
            cli_dev._validate_dev_input(
                cli_dev._DevHttpBodyInput,
                path="/api/status/",
                arguments=["name"],
            )

        message = str(raised.value)
        assert "--argument: expected key=value format" in message
        assert "--argument name=router1" in message


class TestLiveResourceDiscovery:
    """Tests for live schema enrichment on CLI discovery and free-form commands."""

    def test_groups_command_live_uses_enriched_index(self, monkeypatch):
        monkeypatch.setattr(cli, "_get_enriched_index", _live_plugin_index)
        monkeypatch.setattr(
            cli,
            "_get_index",
            lambda: pytest.fail("groups --live must not use the static index"),
        )

        result = runner.invoke(cli.app, ["groups", "--live"])

        assert result.exit_code == 0
        assert "plugins" in result.output

    def test_resources_command_live_lists_discovered_plugin_resource(self, monkeypatch):
        monkeypatch.setattr(cli, "_get_enriched_index", _live_plugin_index)

        result = runner.invoke(cli.app, ["resources", "plugins", "--live"])

        assert result.exit_code == 0
        assert "custom/widgets" in result.output

    def test_ops_command_live_lists_discovered_methods(self, monkeypatch):
        monkeypatch.setattr(cli, "_get_enriched_index", _live_plugin_index)

        result = runner.invoke(cli.app, ["ops", "plugins", "custom/widgets", "--live"])

        assert result.exit_code == 0
        assert "POST" in result.output
        assert "/api/plugins/custom/widgets/" in result.output

    def test_free_form_dynamic_invocation_enriches_missing_resource(self, capsys):
        client = _FakeRuntimeDiscoveryClient()

        _handle_dynamic_invocation(
            ["plugins", "custom/widgets", "list", "--json"],
            client_factory=lambda: client,  # type: ignore[arg-type, return-value]
            index_factory=lambda: SchemaIndex({"openapi": "3.0.0", "paths": {}}),
        )

        captured = capsys.readouterr()
        assert '"count": 0' in captured.out
        assert ("GET", "/api/core/object-types/") in client.calls
        assert ("GET", "/api/plugins/custom/widgets/") in client.calls


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
        monkeypatch.setattr(
            "netbox_cli.runtime._get_client",
            lambda: _ClientWithRows(),
        )

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
