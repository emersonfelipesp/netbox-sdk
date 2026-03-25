"""Tests for GraphQL command and API method."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from netbox_cli import cli
from netbox_cli.api import NetBoxApiClient
from netbox_cli.config import Config

runner = CliRunner()


def _mock_config() -> Config:
    return Config(
        base_url="https://netbox.example.com",
        token_key="abc",
        token_secret="def",
        timeout=30.0,
    )


class TestGraphQLApiMethod:
    """Tests for NetBoxApiClient.graphql() method."""

    @pytest.fixture
    def client(self):
        return NetBoxApiClient(_mock_config())

    @pytest.mark.asyncio
    async def test_graphql_request_payload(self, client, monkeypatch):
        """Test that graphql sends correct payload to the API."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = '{"data": {"sites": []}}'
        mock_response.headers = {}

        async def mock_request(method, path, **kwargs):
            assert method == "POST"
            assert path == "/api/graphql/"
            assert kwargs.get("payload") == {"query": "query { sites { name } }"}
            return mock_response

        monkeypatch.setattr(client, "request", mock_request)

        result = await client.graphql("query { sites { name } }")
        assert result.status == 200

    @pytest.mark.asyncio
    async def test_graphql_with_variables(self, client, monkeypatch):
        """Test that graphql sends variables correctly."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = '{"data": {"device": {"name": "test"}}}'
        mock_response.headers = {}

        async def mock_request(method, path, **kwargs):
            payload = kwargs.get("payload", {})
            assert payload["query"] == "query($id: Int!) { device(id: $id) { name } }"
            assert payload["variables"] == {"id": 1}
            return mock_response

        monkeypatch.setattr(client, "request", mock_request)

        result = await client.graphql(
            "query($id: Int!) { device(id: $id) { name } }",
            variables={"id": 1},
        )
        assert result.status == 200

    @pytest.mark.asyncio
    async def test_graphql_response_parsing(self, client, monkeypatch):
        """Test that graphql response is properly wrapped."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = '{"data": {"sites": [{"name": "site1"}]}}'
        mock_response.headers = {}

        async def mock_request(method, path, **kwargs):
            return mock_response

        monkeypatch.setattr(client, "request", mock_request)

        result = await client.graphql("{ sites { name } }")
        assert result.status == 200
        assert "sites" in result.text


class TestGraphQLCommand:
    """Tests for nbx graphql CLI command."""

    def test_graphql_help(self):
        result = runner.invoke(cli.app, ["graphql", "--help"])
        if result.exit_code != 0:
            print(f"CLI output: {result.output}")
            print(f"Exception: {result.exception}")
        assert result.exit_code == 0
        assert "GraphQL" in result.output
        assert "--variables" in result.output or "-v" in result.output

    def test_graphql_simple_query(self, monkeypatch):
        """Test simple GraphQL query execution."""

        class _FakeClient:
            async def graphql(self, query, variables=None):
                class _Response:
                    status = 200
                    text = json.dumps({"data": {"sites": [{"name": "test"}]}})

                return _Response()

        monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)
        monkeypatch.setattr(cli, "_get_client", lambda: _FakeClient())

        result = runner.invoke(
            cli.app,
            ["graphql", "{ sites { name } }"],
        )
        assert result.exit_code == 0
        assert "test" in result.output.lower()

    def test_graphql_with_json_variables(self, monkeypatch):
        """Test GraphQL with JSON string variables."""

        class _FakeClient:
            async def graphql(self, query, variables=None):
                assert variables == {"id": 1}

                class _Response:
                    status = 200
                    text = json.dumps({"data": {"device": {"name": "sw01"}}})

                return _Response()

        monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)
        monkeypatch.setattr(cli, "_get_client", lambda: _FakeClient())

        result = runner.invoke(
            cli.app,
            [
                "graphql",
                "query($id: Int!) { device(id: $id) { name } }",
                "--variables",
                '{"id": 1}',
            ],
        )
        assert result.exit_code == 0
        assert "sw01" in result.output.lower()

    def test_graphql_with_key_value_variables(self, monkeypatch):
        """Test GraphQL with key=value variables."""

        class _FakeClient:
            async def graphql(self, query, variables=None):
                assert variables == {"name": "sw01"}

                class _Response:
                    status = 200
                    text = json.dumps({"data": {"devices": []}})

                return _Response()

        monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)
        monkeypatch.setattr(cli, "_get_client", lambda: _FakeClient())

        result = runner.invoke(
            cli.app,
            [
                "graphql",
                "query($name: String!) { devices(name: $name) { id } }",
                "--variables",
                "name=sw01",
            ],
        )
        assert result.exit_code == 0

    def test_graphql_json_output(self, monkeypatch):
        """Test GraphQL with --json output."""

        class _FakeClient:
            async def graphql(self, query, variables=None):
                class _Response:
                    status = 200
                    text = json.dumps({"data": {"sites": [{"name": "test"}]}})

                return _Response()

        monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)
        monkeypatch.setattr(cli, "_get_client", lambda: _FakeClient())

        result = runner.invoke(
            cli.app,
            ["graphql", "{ sites { name } }", "--json"],
        )
        assert result.exit_code == 0
        assert "data" in result.output

    def test_graphql_yaml_output(self, monkeypatch):
        """Test GraphQL with --yaml output."""

        class _FakeClient:
            async def graphql(self, query, variables=None):
                class _Response:
                    status = 200
                    text = json.dumps({"data": {"sites": [{"name": "test"}]}})

                return _Response()

        monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)
        monkeypatch.setattr(cli, "_get_client", lambda: _FakeClient())

        result = runner.invoke(
            cli.app,
            ["graphql", "{ sites { name } }", "--yaml"],
        )
        assert result.exit_code == 0
        assert "sites" in result.output.lower()

    def test_graphql_requires_query_argument(self):
        """Test that graphql requires a query argument."""
        result = runner.invoke(cli.app, ["graphql"])
        assert result.exit_code != 0

    def test_graphql_error_handling(self, monkeypatch):
        """Test GraphQL error response handling."""

        class _FakeClient:
            async def graphql(self, query, variables=None):
                class _Response:
                    status = 400
                    text = json.dumps({"errors": [{"message": "Invalid query"}]})

                return _Response()

        monkeypatch.setattr(cli, "_ensure_runtime_config", _mock_config)
        monkeypatch.setattr(cli, "_get_client", lambda: _FakeClient())

        result = runner.invoke(
            cli.app,
            ["graphql", "invalid query"],
        )
        assert "400" in result.output


class TestGraphQLDemo:
    """Tests for nbx demo graphql command - skip if not available."""

    def test_demo_graphql_help(self):
        result = runner.invoke(cli.app, ["demo", "graphql", "--help"])
        if result.exit_code == 2 and "No such command" in result.output:
            pytest.skip("Demo app does not have graphql command")
        assert result.exit_code == 0
        assert "GraphQL" in result.output
