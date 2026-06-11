"""Tests for bulk operations and filter discovery in the CLI dynamic command layer."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest
import typer

from netbox_sdk.client import ApiResponse
from netbox_sdk.schema import build_schema_index
from tests.conftest import OPENAPI_PATH

pytestmark = pytest.mark.suite_cli


def _index():
    return build_schema_index(OPENAPI_PATH)


# ---- _supported_actions ----


def test_supported_actions_includes_bulk_ops():
    from netbox_cli.dynamic import _supported_actions

    actions = _supported_actions("dcim", "devices", index=_index())
    assert "bulk-update" in actions
    assert "bulk-patch" in actions
    assert "bulk-delete" in actions


def test_supported_actions_includes_filters_for_filterable_resource():
    from netbox_cli.dynamic import _supported_actions

    # dcim/devices has many filter parameters.
    actions = _supported_actions("dcim", "devices", index=_index())
    assert "filters" in actions


def test_supported_actions_bulk_ordering():
    from netbox_cli.dynamic import _supported_actions

    actions = _supported_actions("dcim", "devices", index=_index())
    # Bulk ops appear after the six per-object actions.
    basic = [a for a in actions if a in {"list", "get", "create", "update", "patch", "delete"}]
    bulk = [a for a in actions if a.startswith("bulk-")]
    assert basic
    assert bulk
    assert actions.index("list") < actions.index("bulk-update")


def test_supported_actions_no_extra_bulk_when_only_get():
    from netbox_cli.dynamic import _supported_actions

    # core/background-queues has only GET at the list path — no write ops at all.
    actions = _supported_actions("core", "background-queues", index=_index())
    assert "bulk-update" not in actions
    assert "bulk-patch" not in actions
    assert "bulk-delete" not in actions


# ---- _parse_dynamic_options ----


def test_parse_dynamic_options_all_flag():
    from netbox_cli.dynamic import _parse_dynamic_options

    result = _parse_dynamic_options(["--all"])
    fetch_all = result[-2]
    assert fetch_all is True


def test_parse_dynamic_options_max_records():
    from netbox_cli.dynamic import _parse_dynamic_options

    result = _parse_dynamic_options(["--max-records", "500"])
    max_records = result[-1]
    assert max_records == 500


def test_parse_dynamic_options_all_and_max_records_together():
    from netbox_cli.dynamic import _parse_dynamic_options

    result = _parse_dynamic_options(["--all", "--max-records", "250"])
    fetch_all, max_records = result[-2], result[-1]
    assert fetch_all is True
    assert max_records == 250


def test_parse_dynamic_options_max_records_invalid():
    from netbox_cli.dynamic import _parse_dynamic_options

    with pytest.raises(typer.BadParameter):
        _parse_dynamic_options(["--max-records", "not-a-number"])


def test_parse_dynamic_options_max_records_zero_invalid():
    from netbox_cli.dynamic import _parse_dynamic_options

    with pytest.raises(typer.BadParameter):
        _parse_dynamic_options(["--max-records", "0"])


def test_parse_dynamic_options_defaults():
    from netbox_cli.dynamic import _parse_dynamic_options

    result = _parse_dynamic_options([])
    fetch_all, max_records = result[-2], result[-1]
    assert fetch_all is False
    assert max_records == 10000


# ---- _handle_dynamic_invocation — filters action ----


def test_handle_dynamic_invocation_filters_action(capsys):
    from netbox_cli.dynamic import _handle_dynamic_invocation

    _handle_dynamic_invocation(
        ["dcim", "devices", "filters"],
        client_factory=MagicMock(),
        index_factory=_index,
    )
    captured = capsys.readouterr()
    assert "Filter parameters for dcim/devices" in captured.out
    # Should have at least a few known parameters.
    assert "name" in captured.out or "q" in captured.out


def test_handle_dynamic_invocation_filters_no_params(capsys):
    from netbox_cli.dynamic import _handle_dynamic_invocation

    # Use a resource that has no queryable filter params — fallback to "no params" message.
    # We'll monkeypatch the index to return an empty list for filter_params.
    idx = _index()
    original = idx.filter_params

    def _no_params(group: str, resource: str):
        return []

    idx.filter_params = _no_params  # type: ignore[method-assign]

    _handle_dynamic_invocation(
        ["dcim", "devices", "filters"],
        client_factory=MagicMock(),
        index_factory=lambda: idx,
    )
    captured = capsys.readouterr()
    assert "No filter parameters" in captured.out


# ---- _handle_dynamic_invocation — --all flag validation ----


def test_handle_dynamic_invocation_all_flag_rejected_for_non_list():
    from netbox_cli.dynamic import _handle_dynamic_invocation

    with pytest.raises(typer.BadParameter, match="--all is only supported for the list action"):
        _handle_dynamic_invocation(
            ["dcim", "devices", "get", "--id", "1", "--all"],
            client_factory=MagicMock(),
            index_factory=_index,
        )


# ---- _handle_dynamic_invocation — bulk --dry-run ----


def test_handle_dynamic_invocation_bulk_dry_run(capsys):
    from netbox_cli.dynamic import _handle_dynamic_invocation

    # --dry-run for bulk-update should not raise and should print a preview.
    _handle_dynamic_invocation(
        [
            "dcim",
            "devices",
            "bulk-update",
            "--dry-run",
            "--body-json",
            '[{"id": 1, "name": "x"}]',
        ],
        client_factory=MagicMock(side_effect=AssertionError("client should not be built")),
        index_factory=_index,
    )
    captured = capsys.readouterr()
    assert (
        "PUT" in captured.out
        or "bulk" in captured.out.lower()
        or "/api/dcim/devices/" in captured.out
    )


def test_handle_dynamic_invocation_bulk_dry_run_patch(capsys):
    from netbox_cli.dynamic import _handle_dynamic_invocation

    _handle_dynamic_invocation(
        [
            "dcim",
            "devices",
            "bulk-patch",
            "--dry-run",
            "--body-json",
            '[{"id": 1}]',
        ],
        client_factory=MagicMock(side_effect=AssertionError("client should not be built")),
        index_factory=_index,
    )
    captured = capsys.readouterr()
    assert "PATCH" in captured.out or "/api/dcim/devices/" in captured.out


# ---- _handle_dynamic_invocation — --all flag with mock client ----


def test_handle_dynamic_invocation_all_uses_list_all_pages(monkeypatch):
    """When --all is passed for list, run_with_spinner is called with a list_all_pages coroutine."""
    import inspect

    from netbox_cli import dynamic

    page = {"count": 1, "next": None, "previous": None, "results": [{"id": 42}]}

    # Capture what coroutine run_with_spinner receives and return a fixed response.
    captured_coros: list[Any] = []

    def _fake_run_with_spinner(coro: Any, close: Any = None) -> ApiResponse:
        captured_coros.append(coro)
        # Close the coroutine immediately to prevent "never awaited" warnings.
        if inspect.iscoroutine(coro):
            coro.close()
        return ApiResponse(status=200, text=json.dumps(page))

    monkeypatch.setattr(dynamic, "run_with_spinner", _fake_run_with_spinner)

    mock_client = MagicMock()
    mock_client.close = MagicMock(return_value=None)

    dynamic._handle_dynamic_invocation(
        ["dcim", "devices", "list", "--all"],
        client_factory=lambda: mock_client,
        index_factory=_index,
    )

    # run_with_spinner must have been called with a coroutine (the list_all_pages call).
    assert len(captured_coros) == 1
    assert inspect.iscoroutine(captured_coros[0])
