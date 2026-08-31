"""Tests for the ``nbx proxbox jobs`` Typer command group.

These drive the real :class:`~netbox_sdk.proxbox_jobs.ProxboxJobsClient` over a
path-routed fake transport, so the assertions cover the whole chain — option
parsing, window resolution, server-parameter construction, the client-side
predicate, and rendering — rather than a stub of the layer under test.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import click
import pytest
from conftest import cli_json, strip_terminal_control
from typer.main import get_command
from typer.testing import CliRunner

from netbox_cli import app as nbx_app
from netbox_cli import proxbox_jobs as jobs_mod
from netbox_sdk.client import ApiResponse

pytestmark = pytest.mark.suite_cli

runner = CliRunner()


class _FakeTransport:
    """Serves canned pages keyed by request path prefix, and records every call."""

    def __init__(self, routes: dict[str, list[Any]]) -> None:
        self.routes = routes
        self.calls: list[dict[str, Any]] = []
        self.closed = False

    async def request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        payload: Any = None,
        headers: dict[str, str] | None = None,
        expect_json: bool = True,
    ) -> ApiResponse:
        self.calls.append({"method": method, "path": path, "query": dict(query or {})})
        for prefix, pages in self.routes.items():
            if path.startswith(prefix):
                body = pages.pop(0) if len(pages) > 1 else pages[0]
                return ApiResponse(status=200, text=json.dumps(body), headers={})
        raise AssertionError(f"no fake route for {path}")

    async def close(self) -> None:
        self.closed = True

    def job_list_calls(self) -> list[dict[str, Any]]:
        return [call for call in self.calls if call["path"].startswith("/api/core/jobs/")]


def _envelope(results: list[dict[str, Any]], *, next_url: str | None = None) -> dict[str, Any]:
    return {"count": len(results), "next": next_url, "previous": None, "results": results}


def _job_row(**overrides: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": 24422,
        "name": "Proxbox Sync: Full update",
        "status": {"value": "errored", "label": "Errored"},
        "created": "2026-08-28T13:52:17.932733Z",
        "scheduled": None,
        "started": "2026-08-28T13:52:18.000000Z",
        "completed": "2026-08-28T14:27:56.121738Z",
        "interval": None,
        "user": {"id": 2, "username": "emersonfelipesp"},
        "queue_name": "default",
        "job_id": "1cef3888-d5ef-4dcd-9821-1bda20db1015",
        "error": "RuntimeError(\"Stage 'network-interfaces' failed (HTTP 503)\")",
        "object_type": None,
        "object_id": None,
        "data": {
            "proxbox_sync": {
                "params": {
                    "sync_types": ["all"],
                    "proxmox_endpoint_ids": ["5", "11"],
                    "run_id": "91d88672-3098-4b31-96c6-c85fc5efe1cc",
                },
                "runtime_seconds": 2138.2,
            }
        },
        "log_entries": [
            {"level": "info", "message": "Starting Proxbox sync stages", "timestamp": "t0"},
            {"level": "warning", "message": "Cluster/node sync failed", "timestamp": "t1"},
        ],
    }
    row.update(overrides)
    return row


_FOREIGN_ROW = {
    "id": 24418,
    "name": "RPC Execution: status_service",
    "status": {"value": "completed", "label": "Completed"},
    "queue_name": "default",
    "data": {},
    "log_entries": [],
}


@pytest.fixture
def transport(monkeypatch: pytest.MonkeyPatch) -> _FakeTransport:
    fake = _FakeTransport(
        {
            "/api/core/jobs/": [_envelope([_job_row(), _FOREIGN_ROW])],
            "/api/plugins/proxbox/proxmox-clusters/": [
                _envelope([{"id": 3, "name": "PVE-CLUSTER-02", "endpoint": {"id": 2}}])
            ],
            "/api/plugins/proxbox/proxmox-nodes/": [
                _envelope([{"id": 7, "name": "pve01proxbox", "endpoint": {"id": 9}}])
            ],
            "/api/plugins/proxbox/endpoints/proxmox/": [_envelope([{"id": 5, "name": "vPVE"}])],
        }
    )
    monkeypatch.setattr(jobs_mod, "_get_client", lambda: fake)
    return fake


def _run(*args: str):
    return runner.invoke(nbx_app, ["proxbox", "jobs", *args])


def _job_query(transport: _FakeTransport) -> dict[str, Any]:
    return transport.job_list_calls()[0]["query"]


# --------------------------------------------------------------------------
# Listing
# --------------------------------------------------------------------------


def test_list_returns_only_proxbox_jobs_and_reports_the_scan(transport: _FakeTransport) -> None:
    result = _run("list", "--json")

    assert result.exit_code == 0, result.output
    payload = cli_json(result.output)
    assert [job["id"] for job in payload["jobs"]] == [24422]
    assert payload["scanned"] == 2
    assert payload["matched"] == 1
    assert payload["truncated"] is False
    assert transport.closed is True


def test_list_applies_the_default_window_when_none_is_given(transport: _FakeTransport) -> None:
    result = _run("list", "--json")

    assert result.exit_code == 0, result.output
    query = _job_query(transport)
    assert "created__after" in query
    payload = cli_json(result.output)
    assert [bound[0] for bound in payload["window"]["bounds"]] == ["created"]


def test_all_time_drops_the_default_window(transport: _FakeTransport) -> None:
    result = _run("list", "--all-time", "--json")

    assert result.exit_code == 0, result.output
    assert "created__after" not in _job_query(transport)
    assert cli_json(result.output)["window_display"] == "all time"


def test_explicit_ids_suppress_the_default_window(transport: _FakeTransport) -> None:
    result = _run("list", "--id", "24422", "--json")

    assert result.exit_code == 0, result.output
    query = _job_query(transport)
    assert query["id"] == ["24422"]
    assert "created__after" not in query


def test_since_and_until_apply_to_the_selected_date_field(transport: _FakeTransport) -> None:
    result = _run("list", "--since", "7d", "--until", "1d", "--date-field", "completed", "--json")

    assert result.exit_code == 0, result.output
    query = _job_query(transport)
    assert "completed__after" in query
    assert "completed__before" in query
    assert "created__after" not in query
    payload = cli_json(result.output)
    assert {bound[0] for bound in payload["window"]["bounds"]} == {"completed"}
    assert {bound[1] for bound in payload["window"]["bounds"]} == {">=", "<="}


def test_explicit_field_bounds_are_pushed_down_untouched(transport: _FakeTransport) -> None:
    result = _run("list", "--started-after", "2026-08-01T00:00:00Z", "--json")

    assert result.exit_code == 0, result.output
    query = _job_query(transport)
    assert query["started__after"] == "2026-08-01T00:00:00Z"
    assert "created__after" not in query


def test_all_time_conflicts_with_since(transport: _FakeTransport) -> None:
    result = _run("list", "--all-time", "--since", "7d")

    assert result.exit_code != 0
    assert "--all-time cannot be combined" in strip_terminal_control(result.output)


def test_status_and_errored_filters_reach_the_server(transport: _FakeTransport) -> None:
    assert _run("list", "--status", "errored", "--json").exit_code == 0
    assert _job_query(transport)["status"] == ["errored"]


def test_unknown_status_is_rejected_before_any_request(transport: _FakeTransport) -> None:
    result = _run("list", "--status", "borked")

    assert result.exit_code != 0
    assert "Unknown job status" in strip_terminal_control(result.output)
    assert transport.job_list_calls() == []


def test_unknown_sync_type_is_rejected_before_any_request(transport: _FakeTransport) -> None:
    result = _run("list", "--type", "storag")

    assert result.exit_code != 0
    assert "Unknown Proxbox sync type" in strip_terminal_control(result.output)
    assert transport.job_list_calls() == []


def test_unknown_ordering_is_rejected(transport: _FakeTransport) -> None:
    result = _run("list", "--order", "-nonsense")

    assert result.exit_code != 0
    assert "Unknown sort field" in strip_terminal_control(result.output)


def test_ordering_is_pushed_down(transport: _FakeTransport) -> None:
    assert _run("list", "--order", "id", "--json").exit_code == 0
    assert _job_query(transport)["ordering"] == "id"


def test_sync_type_filter_matches_an_all_job(transport: _FakeTransport) -> None:
    result = _run("list", "--type", "storage", "--json")

    assert result.exit_code == 0, result.output
    assert [job["id"] for job in cli_json(result.output)["jobs"]] == [24422]


def test_endpoint_filter_resolves_a_name_then_matches(transport: _FakeTransport) -> None:
    result = _run("list", "--endpoint", "vPVE", "--json")

    assert result.exit_code == 0, result.output
    assert [job["id"] for job in cli_json(result.output)["jobs"]] == [24422]


def test_cluster_filter_resolves_through_the_clusters_endpoint(
    transport: _FakeTransport,
) -> None:
    """The cluster's endpoint (2) is not in the job's ``[5, 11]``, so it drops out."""
    result = _run("list", "--cluster", "PVE-CLUSTER-02", "--json")

    assert result.exit_code == 0, result.output
    assert cli_json(result.output)["jobs"] == []
    assert any(
        call["path"].startswith("/api/plugins/proxbox/proxmox-clusters/")
        for call in transport.calls
    )


def test_node_filter_reports_an_unknown_node_as_an_error(transport: _FakeTransport) -> None:
    result = _run("list", "--node", "pve99", "--json")

    assert result.exit_code == 1
    assert cli_json(result.output)["ok"] is False
    assert transport.closed is True


def test_limit_truncation_is_reported_in_json_and_table(transport: _FakeTransport) -> None:
    transport.routes["/api/core/jobs/"] = [_envelope([_job_row(), _job_row(id=24421)])]

    payload = cli_json(_run("list", "--limit", "1", "--json").output)
    assert payload["truncated"] is True
    assert "limit of 1" in payload["truncation_reason"]

    transport.routes["/api/core/jobs/"] = [_envelope([_job_row(), _job_row(id=24421)])]
    table = strip_terminal_control(_run("list", "--limit", "1").output)
    assert "TRUNCATED" in table


def test_table_output_shows_the_scan_footer(transport: _FakeTransport) -> None:
    output = strip_terminal_control(_run("list").output)

    assert "Proxbox Sync Jobs" in output
    assert "scanned" in output
    assert "matched" in output


def test_fields_selects_columns_and_rejects_unknown_ones(transport: _FakeTransport) -> None:
    payload = cli_json(_run("list", "--fields", "id,status,run_id", "--json").output)
    assert payload["columns"] == ["id", "status", "run_id"]

    result = _run("list", "--fields", "id,nope")
    assert result.exit_code != 0
    assert "Unknown column" in strip_terminal_control(result.output)


def test_wide_uses_the_extended_column_set(transport: _FakeTransport) -> None:
    payload = cli_json(_run("list", "--wide", "--json").output)
    assert payload["columns"] == list(jobs_mod.WIDE_COLUMNS)


def test_json_rows_carry_every_parameter_field(transport: _FakeTransport) -> None:
    job = cli_json(_run("list", "--json").output)["jobs"][0]

    for key in (
        "sync_types",
        "proxmox_endpoint_ids",
        "netbox_endpoint_ids",
        "netbox_vm_ids",
        "batch_object_type",
        "batch_object_ids",
        "fastapi_endpoint_id",
        "run_id",
        "runtime_seconds",
        "error",
        "log_entry_count",
    ):
        assert key in job
    assert job["run_id"] == "91d88672-3098-4b31-96c6-c85fc5efe1cc"
    assert job["runtime_seconds"] == pytest.approx(2138.2)


# --------------------------------------------------------------------------
# Detail
# --------------------------------------------------------------------------


def test_get_emits_the_complete_record(transport: _FakeTransport) -> None:
    transport.routes["/api/core/jobs/"] = [_job_row()]

    payload = cli_json(_run("get", "24422", "--json").output)

    assert payload["id"] == 24422
    assert payload["raw"]["job_id"] == "1cef3888-d5ef-4dcd-9821-1bda20db1015"
    assert len(payload["log_entries"]) == 2


def test_get_can_filter_log_entries_by_level(transport: _FakeTransport) -> None:
    transport.routes["/api/core/jobs/"] = [_job_row()]

    payload = cli_json(_run("get", "24422", "--log-level", "warning", "--json").output)

    assert [entry["level"] for entry in payload["log_entries"]] == ["warning"]


def test_get_rejects_an_unknown_log_level(transport: _FakeTransport) -> None:
    transport.routes["/api/core/jobs/"] = [_job_row()]

    result = _run("get", "24422", "--log-level", "chatty")

    assert result.exit_code != 0
    assert "Unknown log level" in strip_terminal_control(result.output)


def test_get_without_logs_omits_them(transport: _FakeTransport) -> None:
    transport.routes["/api/core/jobs/"] = [_job_row()]

    payload = cli_json(_run("get", "24422", "--no-logs", "--json").output)

    assert payload["log_entries"] == []


def test_get_table_renders_the_detail_and_logs(transport: _FakeTransport) -> None:
    transport.routes["/api/core/jobs/"] = [_job_row()]

    output = strip_terminal_control(_run("get", "24422").output)

    assert "Proxbox Sync Job 24422" in output
    assert "Log Entries" in output


def test_get_surfaces_a_permission_error_with_exit_code_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Denied(_FakeTransport):
        async def request(self, method: str, path: str, **kwargs: Any) -> ApiResponse:
            self.calls.append({"method": method, "path": path, "query": {}})
            return ApiResponse(
                status=403, text=json.dumps({"detail": "You do not have permission."}), headers={}
            )

    denied = _Denied({})
    monkeypatch.setattr(jobs_mod, "_get_client", lambda: denied)

    result = _run("get", "1", "--json")

    assert result.exit_code == 1
    payload = cli_json(result.output)
    assert payload["ok"] is False
    assert "permission" in payload["error"]["message"].lower()
    assert denied.closed is True


# --------------------------------------------------------------------------
# Static surface
# --------------------------------------------------------------------------


def test_statuses_command_lists_every_core_status() -> None:
    output = strip_terminal_control(runner.invoke(nbx_app, ["proxbox", "jobs", "statuses"]).output)

    for value in ("pending", "scheduled", "running", "completed", "errored", "failed"):
        assert value in output


def test_jobs_group_is_registered_under_proxbox() -> None:
    output = strip_terminal_control(runner.invoke(nbx_app, ["proxbox", "--help"]).output)
    assert "jobs" in output


def test_command_registration_makes_no_network_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """The Typer tree must build without a client; --help must never dial out."""

    def _explode() -> Any:
        raise AssertionError("--help must not construct an API client")

    monkeypatch.setattr(jobs_mod, "_get_client", _explode)
    result = runner.invoke(nbx_app, ["proxbox", "jobs", "list", "--help"])

    assert result.exit_code == 0
    assert "--max-scan" in strip_terminal_control(result.output)


def test_default_window_expression_is_a_real_offset() -> None:
    from netbox_sdk.proxbox_jobs import DEFAULT_WINDOW, parse_time_expression

    now = datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC)
    assert parse_time_expression(DEFAULT_WINDOW, now=now) == "2026-07-29T12:00:00Z"


# --------------------------------------------------------------------------
# Table layout
# --------------------------------------------------------------------------


@pytest.mark.parametrize("width", [60, 80, 100, 140, 200])
@pytest.mark.parametrize("columns", ["default", "wide", "all"])
def test_no_column_is_ever_collapsed_to_zero_width(width: int, columns: str) -> None:
    """Every column keeps at least its floor at every terminal width.

    Rich's own fallback reduces all columns by the same ratio and clamps at
    zero, which silently deletes `id` and `status` — the narrowest columns and
    the two most worth keeping — while a long error message keeps its width.
    The listing therefore assigns fixed widths itself; this pins that.
    """
    selected = {
        "default": jobs_mod.DEFAULT_COLUMNS,
        "wide": jobs_mod.WIDE_COLUMNS,
        "all": jobs_mod.AVAILABLE_COLUMNS,
    }[columns]

    widths = jobs_mod._column_widths(selected, width)

    assert set(widths) == set(selected)
    for column, value in widths.items():
        floor = jobs_mod._COLUMN_MIN_WIDTH.get(column, jobs_mod._DEFAULT_COLUMN_MIN_WIDTH)
        assert value >= floor, f"{column} fell below its floor at width {width}"


def test_slack_goes_to_the_weighted_columns_and_fills_the_line() -> None:
    columns = jobs_mod.DEFAULT_COLUMNS
    widths = jobs_mod._column_widths(columns, 200)

    overhead = 3 * len(columns) + 1
    assert sum(widths.values()) == 200 - overhead
    assert widths["error"] > jobs_mod._COLUMN_MIN_WIDTH["error"]
    assert widths["name"] > jobs_mod._COLUMN_MIN_WIDTH["name"]
    assert widths["id"] == jobs_mod._COLUMN_MIN_WIDTH["id"]


def test_default_columns_fit_a_hundred_column_terminal() -> None:
    """The default set is sized to fit; an extra column would cost `id`/`status`."""
    columns = jobs_mod.DEFAULT_COLUMNS
    floors = sum(
        jobs_mod._COLUMN_MIN_WIDTH.get(column, jobs_mod._DEFAULT_COLUMN_MIN_WIDTH)
        for column in columns
    )
    assert floors + 3 * len(columns) + 1 <= 100


def test_timestamps_render_compactly_in_tables_but_not_in_json(
    transport: _FakeTransport,
) -> None:
    table = strip_terminal_control(_run("list").output)
    # The column may be ellipsized at a narrow width, so assert on the prefix —
    # what matters is the space separator, i.e. that it is not raw ISO-8601.
    assert "2026-08-28 1" in table
    assert "2026-08-28T13:52" not in table

    payload = cli_json(_run("list", "--json").output)
    assert payload["jobs"][0]["created"] == "2026-08-28T13:52:17.932733Z"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-08-28T13:52:17.932733Z", "2026-08-28 13:52"),
        ("2026-08-28 13:52:17", "2026-08-28 13:52"),
        ("", ""),
        (None, ""),
        ("not-a-timestamp", "not-a-timestamp"),
    ],
)
def test_compact_timestamp_passes_through_unrecognised_values(value: Any, expected: str) -> None:
    assert jobs_mod._compact_timestamp(value) == expected


def test_object_type_and_object_id_filters_reach_the_server(transport: _FakeTransport) -> None:
    result = _run(
        "list", "--object-type", "netbox_proxbox.proxmoxendpoint", "--object-id", "5", "--json"
    )

    assert result.exit_code == 0, result.output
    query = _job_query(transport)
    assert query["object_type"] == "netbox_proxbox.proxmoxendpoint"
    assert query["object_id"] == "5"


def test_every_documented_filter_flag_is_wired(transport: _FakeTransport) -> None:
    """Guard against a documented flag never being registered on the command.

    Rich help ellipsizes long option names (``--batch-object-type`` becomes
    ``--batch-object-ty…``) even when ``COLUMNS`` is wide, so this inspects the
    Click parameter table rather than the rendered help panel.
    """
    del transport
    jobs_click = get_command(jobs_mod.jobs_app)
    list_cmd = jobs_click.get_command(click.Context(jobs_click), "list")
    assert list_cmd is not None
    option_names = {
        name for param in list_cmd.params for name in (*param.opts, *param.secondary_opts)
    }
    for flag in (
        "--status",
        "--type",
        "--endpoint",
        "--cluster",
        "--node",
        "--vm",
        "--run-id",
        "--batch-object-type",
        "--id",
        "--user",
        "--name",
        "--name-contains",
        "--queue",
        "--rq-job-id",
        "--object-type",
        "--object-id",
        "--since",
        "--until",
        "--date-field",
        "--all-time",
        "--created-after",
        "--completed-before",
        "--errored",
        "--recurring",
        "--limit",
        "--max-scan",
        "--page-size",
        "--order",
        "--fields",
        "--wide",
        "--json",
    ):
        assert flag in option_names, f"{flag} is missing from the command surface"


def test_list_json_rows_include_the_response_summary(transport: _FakeTransport) -> None:
    transport.routes["/api/core/jobs/"] = [
        _envelope(
            [
                _job_row(
                    data={
                        "proxbox_sync": {
                            "params": {"sync_types": ["all"]},
                            "response": {"clusters_updated": 1},
                        }
                    }
                )
            ]
        )
    ]

    job = cli_json(_run("list", "--json").output)["jobs"][0]

    assert job["response"] == {"clusters_updated": 1}
    # log_entries stay out of the listing: they are the heavy part of a job row.
    assert "log_entries" not in job


def test_get_flags_a_core_job_that_is_not_a_proxbox_sync(transport: _FakeTransport) -> None:
    transport.routes["/api/core/jobs/"] = [dict(_FOREIGN_ROW)]

    payload = cli_json(_run("get", "24418", "--json").output)
    assert payload["is_proxbox_sync_job"] is False

    transport.routes["/api/core/jobs/"] = [dict(_FOREIGN_ROW)]
    table = strip_terminal_control(_run("get", "24418").output)
    assert "not a Proxbox sync job" in table


def test_get_does_not_flag_a_real_proxbox_sync(transport: _FakeTransport) -> None:
    transport.routes["/api/core/jobs/"] = [_job_row()]

    payload = cli_json(_run("get", "24422", "--json").output)
    assert payload["is_proxbox_sync_job"] is True

    transport.routes["/api/core/jobs/"] = [_job_row()]
    table = strip_terminal_control(_run("get", "24422").output)
    assert "not a Proxbox sync job" not in table


# --------------------------------------------------------------------------
# Round-1 review regressions
# --------------------------------------------------------------------------


def test_errored_scans_instead_of_narrowing_to_failure_statuses(
    transport: _FakeTransport,
) -> None:
    """A run can finish `completed` while recording a stage error.

    Pushing `status=errored,failed` discarded exactly that row before the
    client-side error check could see it.
    """
    completed_with_error = _job_row(
        id=900,
        status={"value": "completed", "label": "Completed"},
        error="RuntimeError(\"Stage 'sdn' failed\")",
    )
    clean = _job_row(id=901, status={"value": "completed", "label": "Completed"}, error="")
    transport.routes["/api/core/jobs/"] = [_envelope([completed_with_error, clean])]

    payload = cli_json(_run("list", "--errored", "--json").output)

    assert [job["id"] for job in payload["jobs"]] == [900]
    assert "status" not in _job_query(transport)


def test_user_filter_is_applied_client_side(transport: _FakeTransport) -> None:
    """NetBox 4.5 types the `user` job filter as an integer, 4.6+ as usernames."""
    payload = cli_json(_run("list", "--user", "emersonfelipesp", "--json").output)
    assert [job["id"] for job in payload["jobs"]] == [24422]
    assert "user" not in _job_query(transport)

    transport.routes["/api/core/jobs/"] = [_envelope([_job_row(), _FOREIGN_ROW])]
    transport.calls.clear()
    payload = cli_json(_run("list", "--user", "nobody", "--json").output)
    assert payload["jobs"] == []


def test_since_conflicting_with_an_explicit_bound_is_refused(
    transport: _FakeTransport,
) -> None:
    """Two answers to one question must not silently resolve to one of them."""
    result = _run("list", "--since", "7d", "--created-after", "2026-08-01T00:00:00Z")

    assert result.exit_code != 0
    output = strip_terminal_control(result.output)
    assert "both bound" in output
    assert transport.job_list_calls() == []


def test_since_on_a_different_field_than_an_explicit_bound_is_allowed(
    transport: _FakeTransport,
) -> None:
    result = _run(
        "list",
        "--since",
        "7d",
        "--date-field",
        "completed",
        "--created-after",
        "2026-08-01T00:00:00Z",
        "--json",
    )

    assert result.exit_code == 0, result.output
    query = _job_query(transport)
    assert query["created__after"] == "2026-08-01T00:00:00Z"
    assert "completed__after" in query


def test_window_reports_all_bounds_in_effect(transport: _FakeTransport) -> None:
    result = _run(
        "list",
        "--created-after",
        "2026-08-01T00:00:00Z",
        "--completed-before",
        "2026-08-28T00:00:00Z",
        "--json",
    )

    assert result.exit_code == 0, result.output
    payload = cli_json(result.output)
    fields = [bound[0] for bound in payload["window"]["bounds"]]
    assert fields == ["created", "completed"]
    assert "created >=" in payload["window_display"]
    assert "completed <=" in payload["window_display"]


def test_a_legacy_targeted_vm_job_is_found_by_its_vm(transport: _FakeTransport) -> None:
    legacy = {
        "id": 950,
        "name": "Proxbox Sync: Virtual machine 199",
        "status": {"value": "completed", "label": "Completed"},
        "queue_name": "default",
        "data": {},
        "log_entries": [],
    }
    transport.routes["/api/core/jobs/"] = [_envelope([legacy])]

    payload = cli_json(_run("list", "--vm", "199", "--json").output)

    assert [job["id"] for job in payload["jobs"]] == [950]
    assert payload["jobs"][0]["params_inferred"] is True


def test_a_legacy_targeted_vm_job_does_not_match_an_unrelated_stage(
    transport: _FakeTransport,
) -> None:
    legacy = {
        "id": 951,
        "name": "Proxbox Sync: Virtual machine 199",
        "status": {"value": "completed", "label": "Completed"},
        "queue_name": "default",
        "data": {},
        "log_entries": [],
    }
    transport.routes["/api/core/jobs/"] = [_envelope([legacy])]

    payload = cli_json(_run("list", "--type", "storage", "--json").output)
    assert payload["jobs"] == []


@pytest.mark.parametrize(
    "hostile",
    [
        "\x1b[2Jcleared",
        "\x1b]0;spoofed title\x07",
        "line\rOVERWRITTEN",
    ],
    ids=["CSI-clear", "OSC-title", "carriage-return"],
)
def test_hostile_job_fields_cannot_inject_terminal_control_sequences(
    transport: _FakeTransport, hostile: str
) -> None:
    """Rich `Text` preserves CSI/OSC verbatim, so every job field is sanitized.

    Asserted on the raw captured output — stripping escapes first would remove
    the very thing under test.
    """
    row = _job_row(
        id=960,
        name=hostile,
        status={"value": hostile, "label": hostile},
        error=hostile,
        data={"proxbox_sync": {"params": {"sync_types": [hostile]}}},
        log_entries=[{"level": hostile, "message": hostile, "timestamp": hostile}],
    )
    transport.routes["/api/core/jobs/"] = [_envelope([row])]
    listing = _run("list", "--wide").output

    transport.routes["/api/core/jobs/"] = [row]
    detail = _run("get", "960").output

    for raw in (listing, detail):
        assert "\x1b[2J" not in raw
        assert "\x1b]0;" not in raw
        assert "\rOVERWRITTEN" not in raw


# --------------------------------------------------------------------------
# Round-2 review regressions
# --------------------------------------------------------------------------


def test_the_default_window_honours_date_field(transport: _FakeTransport) -> None:
    """`--date-field completed` alone must move the default look-back too.

    Hard-coding `created_after` made the flag silently do nothing without
    `--since`, contradicting the help and both documentation mirrors.
    """
    result = _run("list", "--date-field", "completed", "--json")

    assert result.exit_code == 0, result.output
    query = _job_query(transport)
    assert "completed__after" in query
    assert "created__after" not in query
    assert [bound[0] for bound in cli_json(result.output)["window"]["bounds"]] == ["completed"]


def test_the_default_window_still_targets_created_by_default(
    transport: _FakeTransport,
) -> None:
    assert _run("list", "--json").exit_code == 0
    assert "created__after" in _job_query(transport)


@pytest.mark.parametrize(
    "hostile",
    ["[link=https://evil.example]click[/link]", "[/unmatched]", "[bold]spoof[/bold]"],
    ids=["link-markup", "unmatched-close", "style-markup"],
)
def test_response_markup_is_rendered_literally_and_never_crashes(
    transport: _FakeTransport, hostile: str
) -> None:
    """Rich parses markup in a plain `str` cell but not in a `Text` instance.

    An attacker-controlled `[link=...]` became a real hyperlink, and an
    unmatched closing tag raised MarkupError and killed `jobs get`.
    """
    row = _job_row(
        id=970,
        data={
            "proxbox_sync": {
                "params": {"sync_types": ["all"]},
                "response": {hostile: hostile},
            }
        },
    )
    transport.routes["/api/core/jobs/"] = [row]

    result = _run("get", "970")

    assert result.exit_code == 0, result.output
    assert "\x1b]8;" not in result.output  # no OSC-8 hyperlink was emitted
    # The markup must survive as literal text rather than being interpreted.
    rendered = strip_terminal_control(result.output).replace("\n", "")
    assert hostile.split("]")[0].lstrip("[")[:12] in rendered


def test_json_output_is_strict_json_even_when_the_job_carries_infinities(
    transport: _FakeTransport,
) -> None:
    """`json.loads("1e400")` is inf, and `json.dumps` re-emits it as `Infinity`.

    Normalising only the fields this module parses is not enough: the response
    block, the log entries and the untouched `raw` row all pass through, so a
    strict JSON consumer would choke on output this command called machine
    readable.
    """
    row = _job_row(
        id=980,
        data={
            "proxbox_sync": {
                "params": {"sync_types": ["all"]},
                "runtime_seconds": float("inf"),
                "response": {"metric": float("inf"), "nested": {"deep": float("-inf")}},
            }
        },
        log_entries=[{"level": "info", "message": "m", "timestamp": "t", "value": float("nan")}],
    )
    transport.routes["/api/core/jobs/"] = [_envelope([row])]

    listing = _run("list", "--json")
    assert listing.exit_code == 0, listing.output
    payload = json.loads(
        strip_terminal_control(listing.output)[strip_terminal_control(listing.output).index("{") :]
    )
    assert payload["jobs"][0]["response"]["metric"] is None
    assert payload["jobs"][0]["response"]["nested"]["deep"] is None

    transport.routes["/api/core/jobs/"] = [row]
    detail = _run("get", "980", "--json")
    assert detail.exit_code == 0, detail.output
    text = strip_terminal_control(detail.output)
    # A strict parser must accept it, and the literal must not appear at all.
    parsed = json.loads(text[text.index("{") :])
    assert "Infinity" not in text
    assert "NaN" not in text
    assert parsed["raw"]["data"]["proxbox_sync"]["response"]["metric"] is None
    assert parsed["log_entries"][0]["value"] is None
