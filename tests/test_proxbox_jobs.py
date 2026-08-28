"""Tests for the netbox-proxbox sync job SDK surface.

Three of these suites exist because reasoning about this code is not enough:

* the **predicate parity matrix** mirrors the plugin's own row-grid test rather
  than asserting four hand-picked cases, so a mis-transcribed branch fails here
  instead of silently hiding jobs from every listing;
* the **server-parameter whitelist** suite exists because NetBox *ignores*
  unknown query parameters, so a typo does not raise — it widens the query to
  every job in the instance;
* the **hostile-data** suite throws malformed ``job.data`` at the parser,
  because that blob is written by a remote plugin and a single ``AttributeError``
  there would take down the whole listing rather than one row.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import pytest

from netbox_sdk.client import ApiResponse
from netbox_sdk.proxbox_jobs import (
    DEFAULT_MAX_SCAN,
    JOB_DATE_FIELDS,
    SERVER_PARAM_WHITELIST,
    SYNC_STAGE_ORDER,
    TARGETED_VM_SYNC_TYPES,
    ProxboxJobFilterError,
    ProxboxJobFilters,
    ProxboxJobScanWindow,
    ProxboxJobsClient,
    ProxboxSyncJobParams,
    ProxboxSyncJobRecord,
    ScopeState,
    is_proxbox_sync_job,
    normalize_sync_types,
    parse_time_expression,
    validate_date_field,
    validate_job_statuses,
    validate_sync_type_filters,
)
from netbox_sdk.proxbox_sync import ProxboxSyncError

pytestmark = pytest.mark.suite_sdk


class _FakeApiClient:
    """Minimal stand-in for ``NetBoxApiClient`` that replays canned responses."""

    def __init__(self, responses: list[ApiResponse]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

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
        self.calls.append({"method": method, "path": path, "query": query})
        if not self.responses:
            raise AssertionError(f"unexpected extra request: {method} {path}")
        return self.responses.pop(0)


def _response(status: int, payload: Any) -> ApiResponse:
    return ApiResponse(status=status, text=json.dumps(payload), headers={})


def _page(results: list[dict[str, Any]], *, next_url: str | None = None, count: int | None = None):
    return _response(
        200,
        {
            "count": count if count is not None else len(results),
            "next": next_url,
            "previous": None,
            "results": results,
        },
    )


def _job_row(**overrides: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": 1,
        "name": "Proxbox Sync: Full update",
        "status": {"value": "completed", "label": "Completed"},
        "created": "2026-08-28T13:52:17.932733Z",
        "scheduled": None,
        "started": "2026-08-28T13:52:18.000000Z",
        "completed": "2026-08-28T14:27:56.121738Z",
        "interval": None,
        "user": {"id": 2, "username": "emersonfelipesp", "display": "emersonfelipesp"},
        "queue_name": "default",
        "job_id": "1cef3888-d5ef-4dcd-9821-1bda20db1015",
        "error": "",
        "object_type": None,
        "object_id": None,
        "data": {
            "proxbox_sync": {
                "params": {
                    "sync_types": ["all"],
                    "proxmox_endpoint_ids": ["5", "11"],
                    "netbox_endpoint_ids": [],
                    "netbox_vm_ids": [],
                    "batch_object_ids": [],
                    "batch_object_type": None,
                    "run_id": "91d88672-3098-4b31-96c6-c85fc5efe1cc",
                }
            }
        },
        "log_entries": [{"level": "info", "message": "started", "timestamp": "2026-08-28T13:52Z"}],
    }
    row.update(overrides)
    return row


# --------------------------------------------------------------------------
# Predicate parity matrix
# --------------------------------------------------------------------------

# One row per branch of ``netbox_proxbox.jobs.is_proxbox_sync_job`` plus the
# near-misses that must NOT match. Transcribed from the plugin predicate, not
# derived from this module's implementation — an assertion computed from the
# code under test would prove nothing.
_PREDICATE_MATRIX: tuple[tuple[str, dict[str, Any], bool], ...] = (
    (
        "data key present, unrelated name and queue",
        {"id": 1, "name": "Nightly refresh", "queue_name": "default", "data": {"proxbox_sync": {}}},
        True,
    ),
    (
        "data key present but empty block",
        {"id": 1, "name": "", "queue_name": "", "data": {"proxbox_sync": None}},
        True,
    ),
    (
        "legacy dedicated queue, unrelated name",
        {"id": 2, "name": "Something else", "queue_name": "netbox_proxbox.sync", "data": {}},
        True,
    ),
    (
        "default name on the shared default queue",
        {"id": 3, "name": "Proxbox Sync", "queue_name": "default", "data": {}},
        True,
    ),
    (
        "default name on a null queue (queue_name or '' normalisation)",
        {"id": 4, "name": "Proxbox Sync", "queue_name": None, "data": {}},
        True,
    ),
    (
        "default name with surrounding whitespace",
        {"id": 5, "name": "  Proxbox Sync  ", "queue_name": "", "data": {}},
        True,
    ),
    (
        "default name on a foreign queue",
        {"id": 6, "name": "Proxbox Sync", "queue_name": "high", "data": {}},
        False,
    ),
    (
        "targeted single-VM job name",
        {"id": 7, "name": "Proxbox Sync: Virtual machine 199", "queue_name": "high", "data": {}},
        True,
    ),
    (
        "targeted-VM shape with a non-numeric id",
        {"id": 8, "name": "Proxbox Sync: Virtual machine abc", "queue_name": "default", "data": {}},
        False,
    ),
    (
        "custom sync label without the data key",
        {"id": 9, "name": "Proxbox Sync: Full update", "queue_name": "default", "data": {}},
        False,
    ),
    (
        "another plugin's job",
        {"id": 10, "name": "RPC Execution: restart", "queue_name": "default", "data": {}},
        False,
    ),
    (
        "no data field at all",
        {"id": 11, "name": "Packer Build", "queue_name": "default"},
        False,
    ),
    (
        "data present but not a mapping",
        {"id": 12, "name": "Packer Build", "queue_name": "default", "data": ["proxbox_sync"]},
        False,
    ),
)


@pytest.mark.parametrize(
    ("label", "row", "expected"),
    _PREDICATE_MATRIX,
    ids=[case[0] for case in _PREDICATE_MATRIX],
)
def test_is_proxbox_sync_job_matrix(label: str, row: dict[str, Any], expected: bool) -> None:
    assert is_proxbox_sync_job(row) is expected, label


def test_custom_named_job_is_found_by_its_data_key_not_its_name() -> None:
    """A ``--job-name`` run keeps an arbitrary name; only ``data`` identifies it.

    This is exactly the row a name-prefix shortcut would miss, which is why the
    listing scans instead of pushing a name filter down.
    """
    row = _job_row(id=77, name="nightly-full", queue_name="default")
    assert is_proxbox_sync_job(row) is True


# --------------------------------------------------------------------------
# Hostile / malformed ``job.data``
# --------------------------------------------------------------------------

_HOSTILE_BLOCKS: tuple[Any, ...] = (
    None,
    "proxbox_sync",
    12345,
    [],
    ["params"],
    {"params": None},
    {"params": "all"},
    {"params": []},
    {"params": {"sync_types": "virtual-machines"}},
    {"params": {"sync_types": {"all": 1}}},
    {"params": {"sync_types": [None, True, {"nested": 1}]}},
    {"params": {"proxmox_endpoint_ids": "5"}},
    {"params": {"proxmox_endpoint_ids": [{"id": 5}]}},
    {"params": {"fastapi_endpoint_id": "not-a-number"}},
    {"params": {"run_id": {"uuid": "x"}}},
    {"params": {"__proto__": {"polluted": True}, "constructor": "x"}},
    {"params": {"netbox_vm_ids": [[1, 2], 3]}},
)


@pytest.mark.parametrize("block", _HOSTILE_BLOCKS, ids=[repr(b)[:40] for b in _HOSTILE_BLOCKS])
def test_params_parsing_never_raises_on_hostile_blocks(block: Any) -> None:
    params = ProxboxSyncJobParams.from_block(
        block.get("params") if isinstance(block, dict) else block
    )
    assert isinstance(params.sync_types, list)
    assert isinstance(params.proxmox_endpoint_ids, list)


@pytest.mark.parametrize("block", _HOSTILE_BLOCKS, ids=[repr(b)[:40] for b in _HOSTILE_BLOCKS])
def test_record_parsing_never_raises_on_hostile_data(block: Any) -> None:
    record = ProxboxSyncJobRecord.from_row(_job_row(data={"proxbox_sync": block}))
    assert record.id == 1
    assert record.status == "completed"


def test_record_parsing_survives_wholly_alien_row_shapes() -> None:
    record = ProxboxSyncJobRecord.from_row(
        {
            "id": "42",
            "name": None,
            "status": "running",
            "user": "someone",
            "queue_name": None,
            "interval": "15",
            "object_type": {"value": "dcim.device"},
            "data": "not-a-mapping",
            "log_entries": ["not-a-mapping", {"level": "info"}],
        }
    )
    assert record.id == 42
    assert record.name == ""
    assert record.status == "running"
    assert record.user == "someone"
    assert record.interval == 15
    assert record.object_type == "dcim.device"
    assert record.log_entries == [{"level": "info"}]


def test_record_parsing_rejects_a_row_without_a_usable_id() -> None:
    with pytest.raises(ProxboxJobFilterError):
        ProxboxSyncJobRecord.from_row({"name": "Proxbox Sync"})


def test_legacy_singular_sync_type_key_is_honoured() -> None:
    params = ProxboxSyncJobParams.from_block({"sync_type": "virtual-machines"})
    assert params.sync_types == ["virtual-machines"]
    assert params.covers_sync_type("virtual-machines") is True
    assert params.covers_sync_type("storage") is False


# --------------------------------------------------------------------------
# Documented filter semantics
# --------------------------------------------------------------------------


def test_empty_endpoint_params_mean_all_endpoints() -> None:
    params = ProxboxSyncJobParams.from_block({"proxmox_endpoint_ids": []})
    assert params.targets_all_endpoints is True
    assert params.covers_endpoint(5) is True
    assert params.covers_endpoint(999) is True


def test_named_endpoint_params_match_only_those_endpoints() -> None:
    params = ProxboxSyncJobParams.from_block({"proxmox_endpoint_ids": ["5", "11"]})
    assert params.targets_all_endpoints is False
    assert params.covers_endpoint(5) is True
    assert params.covers_endpoint(7) is False


def test_all_sync_type_covers_every_requested_type() -> None:
    params = ProxboxSyncJobParams.from_block({"sync_types": ["all"]})
    assert params.covers_sync_type("storage") is True
    assert params.covers_sync_type("virtual-machines") is True


def test_missing_sync_types_are_treated_as_all() -> None:
    params = ProxboxSyncJobParams.from_block({})
    assert params.covers_sync_type("sdn") is True


def test_specific_sync_types_do_not_match_other_types() -> None:
    params = ProxboxSyncJobParams.from_block({"sync_types": ["storage", "sdn"]})
    assert params.covers_sync_type("storage") is True
    assert params.covers_sync_type("virtual-machines") is False


# --------------------------------------------------------------------------
# Server parameter whitelist
# --------------------------------------------------------------------------


def test_server_query_emits_only_whitelisted_parameters() -> None:
    filters = ProxboxJobFilters(
        statuses=("errored", "failed"),
        ids=(1, 2),
        name="Proxbox Sync",
        name_contains="full",
        queue_name="default",
        user="emersonfelipesp",
        rq_job_id="uuid-1",
        object_type="netbox_proxbox.proxmoxendpoint",
        object_id=5,
        recurring=True,
        created_after="2026-08-01T00:00:00Z",
        completed_before="2026-08-28T00:00:00Z",
    )
    query = filters.server_query(page_size=50)

    assert set(query) <= SERVER_PARAM_WHITELIST
    assert query["status"] == ["errored", "failed"]
    assert query["id"] == ["1", "2"]
    assert query["name__ic"] == "full"
    assert query["interval__empty"] == "false"
    assert query["created__after"] == "2026-08-01T00:00:00Z"
    assert query["completed__before"] == "2026-08-28T00:00:00Z"
    assert query["limit"] == 50


def test_server_query_refuses_a_non_whitelisted_parameter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mutation check: shrink the whitelist and the builder must fail closed.

    Without this, a future filter could add a misspelled parameter name and the
    only symptom would be a listing that quietly covered the entire job table.
    """
    monkeypatch.setattr(
        "netbox_sdk.proxbox_jobs.SERVER_PARAM_WHITELIST", frozenset({"limit", "ordering"})
    )
    with pytest.raises(ProxboxJobFilterError, match="non-whitelisted"):
        ProxboxJobFilters(statuses=("errored",)).server_query(page_size=10)


def test_errored_only_pushes_no_status_filter() -> None:
    """`--errored` must not narrow the server query to the failure statuses.

    A run can finish `completed` while recording a stage error — the row an
    operator triaging a failure most wants. Pushing `status=errored,failed`
    discards it before the client-side error check ever runs.
    """
    query = ProxboxJobFilters(errored_only=True).server_query(page_size=10)
    assert "status" not in query


def test_explicit_statuses_are_still_pushed_alongside_errored() -> None:
    query = ProxboxJobFilters(errored_only=True, statuses=("running",)).server_query(page_size=10)
    assert query["status"] == ["running"]


async def test_errored_only_finds_a_completed_job_that_recorded_an_error() -> None:
    """End-to-end counterpart: the completed-with-error row must survive."""
    rows = [
        _job_row(id=1, error="RuntimeError('stage failed')"),
        _job_row(id=2, error=""),
    ]
    fake = _FakeApiClient([_page(rows)])
    client = ProxboxJobsClient.from_client(fake)  # type: ignore[arg-type]

    result = await client.list_jobs(ProxboxJobFilters(errored_only=True))

    assert [record.id for record in result.jobs] == [1]
    assert "status" not in (fake.calls[0]["query"] or {})


def test_user_is_filtered_client_side_not_pushed_down() -> None:
    """NetBox 4.5 types `user` as an integer; 4.6+ as usernames.

    Sending a username to a 4.5 instance is a validation error, not a filter,
    so the comparison happens on the parsed record instead.
    """
    query = ProxboxJobFilters(user="emersonfelipesp").server_query(page_size=10)
    assert "user" not in query
    assert "user" not in SERVER_PARAM_WHITELIST

    record = _record()
    assert ProxboxJobFilters(user="emersonfelipesp").matches(record) is True
    assert ProxboxJobFilters(user="EmersonFelipesp").matches(record) is True
    assert ProxboxJobFilters(user="someone-else").matches(record) is False


def test_one_shot_filter_pushes_interval_empty_true() -> None:
    query = ProxboxJobFilters(recurring=False).server_query(page_size=10)
    assert query["interval__empty"] == "true"


def test_every_date_field_bound_is_whitelisted() -> None:
    filters = ProxboxJobFilters(
        **{
            f"{field}_{bound}": "2026-08-01T00:00:00Z"
            for field in JOB_DATE_FIELDS
            for bound in ("after", "before")
        }
    )
    query = filters.server_query(page_size=10)
    for field in JOB_DATE_FIELDS:
        assert query[f"{field}__after"] == "2026-08-01T00:00:00Z"
        assert query[f"{field}__before"] == "2026-08-01T00:00:00Z"
    assert set(query) <= SERVER_PARAM_WHITELIST


# --------------------------------------------------------------------------
# Client-side matching
# --------------------------------------------------------------------------


def _record(**overrides: Any) -> ProxboxSyncJobRecord:
    return ProxboxSyncJobRecord.from_row(_job_row(**overrides))


def test_matches_applies_sync_type_endpoint_vm_and_run_filters() -> None:
    record = _record()
    assert ProxboxJobFilters(sync_types=("storage",)).matches(record) is True
    assert ProxboxJobFilters(endpoint_ids=(5,)).matches(record) is True
    assert ProxboxJobFilters(endpoint_ids=(42,)).matches(record) is False
    assert (
        ProxboxJobFilters(run_ids=("91d88672-3098-4b31-96c6-c85fc5efe1cc",)).matches(record) is True
    )
    assert ProxboxJobFilters(run_ids=("other",)).matches(record) is False
    assert ProxboxJobFilters(vm_ids=("199",)).matches(record) is False


def test_errored_only_also_matches_a_completed_job_carrying_an_error() -> None:
    """A run can finish ``completed`` while recording a stage error."""
    record = _record(error="RuntimeError('stage failed')")
    assert ProxboxJobFilters(errored_only=True).matches(record) is True
    assert ProxboxJobFilters(errored_only=True).matches(_record()) is False


def test_batch_object_type_filter_is_exact() -> None:
    record = ProxboxSyncJobRecord.from_row(
        _job_row(data={"proxbox_sync": {"params": {"batch_object_type": "virtualization.cluster"}}})
    )
    assert ProxboxJobFilters(batch_object_type="virtualization.cluster").matches(record) is True
    assert ProxboxJobFilters(batch_object_type="dcim.device").matches(record) is False


# --------------------------------------------------------------------------
# Validation helpers
# --------------------------------------------------------------------------


def test_validate_job_statuses_normalizes_and_rejects() -> None:
    assert validate_job_statuses(["Errored", "errored", " failed "]) == ("errored", "failed")
    with pytest.raises(ProxboxJobFilterError, match="Unknown job status"):
        validate_job_statuses(["nope"])


def test_validate_sync_type_filters_allows_all_combined_with_others() -> None:
    assert validate_sync_type_filters(["all", "storage"]) == ("all", "storage")
    with pytest.raises(ProxboxJobFilterError, match="Unknown Proxbox sync type"):
        validate_sync_type_filters(["storag"])


def test_validate_date_field_rejects_unknown_fields() -> None:
    assert validate_date_field("Completed") == "completed"
    with pytest.raises(ProxboxJobFilterError):
        validate_date_field("finished")


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("1h", "2026-08-28T11:00:00Z"),
        ("2d", "2026-08-26T12:00:00Z"),
        ("1w", "2026-08-21T12:00:00Z"),
        ("30m", "2026-08-28T11:30:00Z"),
        ("45s", "2026-08-28T11:59:15Z"),
        ("2026-08-01", "2026-08-01T00:00:00Z"),
        ("2026-08-01T05:30:00Z", "2026-08-01T05:30:00Z"),
        ("2026-08-01 05:30:00", "2026-08-01T05:30:00Z"),
    ],
)
def test_parse_time_expression(expression: str, expected: str) -> None:
    now = datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC)
    assert parse_time_expression(expression, now=now) == expected


@pytest.mark.parametrize("expression", ["", "   ", "7", "d7", "tomorrow", "7y", "-3d"])
def test_parse_time_expression_rejects_junk(expression: str) -> None:
    with pytest.raises(ProxboxJobFilterError):
        parse_time_expression(expression)


# --------------------------------------------------------------------------
# Bounded scanning
# --------------------------------------------------------------------------


async def test_list_jobs_filters_out_foreign_jobs_and_reports_the_scan() -> None:
    rows = [
        _job_row(id=10),
        {"id": 11, "name": "Packer Build", "queue_name": "default", "data": {}},
        _job_row(id=12, name="Proxbox Sync"),
    ]
    fake = _FakeApiClient([_page(rows, count=3)])
    client = ProxboxJobsClient.from_client(fake, page_size=100)  # type: ignore[arg-type]

    result = await client.list_jobs(ProxboxJobFilters())

    assert [record.id for record in result.jobs] == [10, 12]
    assert result.scanned == 3
    assert result.matched == 2
    assert result.total_available == 3
    assert result.truncated is False
    assert fake.calls[0]["path"] == "/api/core/jobs/"
    assert fake.calls[0]["query"]["ordering"] == "-created"


async def test_list_jobs_follows_pagination_until_exhausted() -> None:
    fake = _FakeApiClient(
        [
            _page([_job_row(id=1)], next_url="https://nb.example/api/core/jobs/?limit=1&offset=1"),
            _page([_job_row(id=2)]),
        ]
    )
    client = ProxboxJobsClient.from_client(fake, page_size=1)  # type: ignore[arg-type]

    result = await client.list_jobs(ProxboxJobFilters())

    assert [record.id for record in result.jobs] == [1, 2]
    assert fake.calls[1]["path"] == "/api/core/jobs/"
    assert fake.calls[1]["query"]["offset"] == "1"


async def test_list_jobs_stops_at_the_result_limit_and_says_so() -> None:
    fake = _FakeApiClient([_page([_job_row(id=1), _job_row(id=2), _job_row(id=3)])])
    client = ProxboxJobsClient.from_client(fake)  # type: ignore[arg-type]

    result = await client.list_jobs(ProxboxJobFilters(), limit=2)

    assert [record.id for record in result.jobs] == [1, 2]
    assert result.truncated is True
    assert result.truncation_reason is not None
    assert "limit of 2" in result.truncation_reason


async def test_list_jobs_stops_at_the_scan_ceiling_and_says_so() -> None:
    foreign = [
        {"id": 90 + n, "name": "Packer Build", "queue_name": "default", "data": {}}
        for n in range(3)
    ]
    fake = _FakeApiClient([_page(foreign, next_url="https://nb.example/api/core/jobs/?offset=3")])
    client = ProxboxJobsClient.from_client(fake)  # type: ignore[arg-type]

    result = await client.list_jobs(ProxboxJobFilters(), max_scan=2)

    assert result.jobs == []
    assert result.scanned == 2
    assert result.truncated is True
    assert result.truncation_reason is not None
    assert "scan limit of 2" in result.truncation_reason


async def test_list_jobs_with_max_scan_zero_scans_without_a_ceiling() -> None:
    fake = _FakeApiClient([_page([_job_row(id=1), _job_row(id=2)])])
    client = ProxboxJobsClient.from_client(fake)  # type: ignore[arg-type]

    result = await client.list_jobs(ProxboxJobFilters(), max_scan=0)

    assert result.scanned == 2
    assert result.truncated is False


async def test_list_jobs_surfaces_an_api_error() -> None:
    fake = _FakeApiClient([_response(403, {"detail": "You do not have permission."})])
    client = ProxboxJobsClient.from_client(fake)  # type: ignore[arg-type]

    with pytest.raises(ProxboxSyncError) as excinfo:
        await client.list_jobs(ProxboxJobFilters())
    assert excinfo.value.status == 403


async def test_list_jobs_rejects_a_body_without_a_results_array() -> None:
    fake = _FakeApiClient([_response(200, {"count": 1, "results": "nope"})])
    client = ProxboxJobsClient.from_client(fake)  # type: ignore[arg-type]

    with pytest.raises(ProxboxSyncError, match="results"):
        await client.list_jobs(ProxboxJobFilters())


async def test_list_jobs_echoes_the_reported_window() -> None:
    fake = _FakeApiClient([_page([])])
    client = ProxboxJobsClient.from_client(fake)  # type: ignore[arg-type]
    window = ProxboxJobScanWindow.from_bounds({"created_after": "2026-08-01T00:00:00Z"})

    result = await client.list_jobs(ProxboxJobFilters(), window=window)

    assert result.window.describe() == "created >= 2026-08-01T00:00:00Z"
    assert ProxboxJobScanWindow().describe() == "all time"


def test_window_reports_every_active_bound_not_just_one() -> None:
    """A scan bounded on two fields is narrower than either bound alone."""
    window = ProxboxJobScanWindow.from_bounds(
        {
            "created_after": "2026-08-01T00:00:00Z",
            "completed_before": "2026-08-28T00:00:00Z",
            "started_after": None,
        }
    )

    assert window.fields == ("created", "completed")
    assert window.describe() == (
        "created >= 2026-08-01T00:00:00Z, completed <= 2026-08-28T00:00:00Z"
    )
    assert window.is_open is False


def test_default_max_scan_is_a_real_ceiling() -> None:
    assert DEFAULT_MAX_SCAN > 0


async def test_get_job_returns_a_parsed_record() -> None:
    fake = _FakeApiClient([_response(200, _job_row(id=24422))])
    client = ProxboxJobsClient.from_client(fake)  # type: ignore[arg-type]

    record = await client.get_job(24422)

    assert record.id == 24422
    assert record.params.run_id == "91d88672-3098-4b31-96c6-c85fc5efe1cc"
    assert record.endpoints_display == "5, 11"
    assert record.sync_types_display == "all"
    assert record.log_entry_count == 1
    assert fake.calls[0]["path"] == "/api/core/jobs/24422/"


async def test_detail_includes_the_untouched_core_row() -> None:
    fake = _FakeApiClient([_response(200, _job_row(id=7))])
    client = ProxboxJobsClient.from_client(fake)  # type: ignore[arg-type]

    detail = (await client.get_job(7)).detail()

    assert detail["raw"]["job_id"] == "1cef3888-d5ef-4dcd-9821-1bda20db1015"
    assert detail["log_entries"]


# --------------------------------------------------------------------------
# Cluster / node resolution
# --------------------------------------------------------------------------


async def test_resolve_cluster_endpoint_ids_matches_name_or_pk() -> None:
    rows = [
        {"id": 3, "name": "PVE-CLUSTER-02", "endpoint": {"id": 2, "name": "Proxmox Endpoint"}},
        {"id": 6, "name": "TEST-CLUSTER", "endpoint": {"id": 5, "name": "Other"}},
    ]
    fake = _FakeApiClient([_page(rows), _page(rows)])
    client = ProxboxJobsClient.from_client(fake)  # type: ignore[arg-type]

    assert await client.resolve_cluster_endpoint_ids("TEST-CLUSTER") == (5,)
    assert await client.resolve_cluster_endpoint_ids(3) == (2,)


async def test_resolve_node_endpoint_ids_reports_an_unknown_node() -> None:
    fake = _FakeApiClient([_page([{"id": 7, "name": "pve01", "endpoint": {"id": 2}}])])
    client = ProxboxJobsClient.from_client(fake)  # type: ignore[arg-type]

    with pytest.raises(ProxboxJobFilterError, match="No Proxmox node found"):
        await client.resolve_node_endpoint_ids("pve99")


async def test_resolve_node_endpoint_ids_reports_an_unlinked_node() -> None:
    fake = _FakeApiClient([_page([{"id": 7, "name": "pve01", "endpoint": None}])])
    client = ProxboxJobsClient.from_client(fake)  # type: ignore[arg-type]

    with pytest.raises(ProxboxJobFilterError, match="not linked"):
        await client.resolve_node_endpoint_ids("pve01")


# --------------------------------------------------------------------------
# Pagination fidelity
# --------------------------------------------------------------------------


async def test_repeated_query_keys_survive_pagination() -> None:
    """Page two must carry the same multi-value filter page one did.

    ``dict(parse_qsl(...))`` keeps only the last value per key, so a pushed-down
    ``status=errored&status=failed`` would narrow to ``status=failed`` from page
    two onward — page one filtered on one thing and every later page on
    another, silently.
    """
    fake = _FakeApiClient(
        [
            _page(
                [_job_row(id=1)],
                next_url=(
                    "https://nb.example/api/core/jobs/"
                    "?limit=1&offset=1&status=errored&status=failed&id=1&id=2"
                ),
            ),
            _page([_job_row(id=2)]),
        ]
    )
    client = ProxboxJobsClient.from_client(fake, page_size=1)  # type: ignore[arg-type]

    await client.list_jobs(ProxboxJobFilters(statuses=("errored", "failed"), ids=(1, 2)))

    page_two = fake.calls[1]["query"]
    assert page_two["status"] == ["errored", "failed"]
    assert page_two["id"] == ["1", "2"]


async def test_single_valued_query_keys_stay_scalars_across_pages() -> None:
    fake = _FakeApiClient(
        [
            _page(
                [_job_row(id=1)],
                next_url="https://nb.example/api/core/jobs/?limit=1&offset=1&status=errored",
            ),
            _page([_job_row(id=2)]),
        ]
    )
    client = ProxboxJobsClient.from_client(fake, page_size=1)  # type: ignore[arg-type]

    await client.list_jobs(ProxboxJobFilters(statuses=("errored",)))

    assert fake.calls[1]["query"]["status"] == "errored"


async def test_inventory_pagination_also_preserves_repeated_keys() -> None:
    rows_one = [{"id": 3, "name": "A", "endpoint": {"id": 2}}]
    rows_two = [{"id": 4, "name": "B", "endpoint": {"id": 9}}]
    fake = _FakeApiClient(
        [
            _page(
                rows_one,
                next_url="https://nb.example/api/plugins/proxbox/proxmox-clusters/?tag=a&tag=b",
            ),
            _page(rows_two),
        ]
    )
    client = ProxboxJobsClient.from_client(fake)  # type: ignore[arg-type]

    assert await client.resolve_cluster_endpoint_ids("B") == (9,)
    assert fake.calls[1]["query"]["tag"] == ["a", "b"]


# --------------------------------------------------------------------------
# Scope trust: invalid is not "everything"
# --------------------------------------------------------------------------


def test_unreadable_endpoint_scope_matches_no_endpoint_query() -> None:
    """`[{"id": 5}]` is not "all endpoints" — it is an endpoint list we cannot read.

    Collapsing it to `[]` made a job scoped to one endpoint match a query for a
    different one, which is a wrong answer rather than a missing one.
    """
    params = ProxboxSyncJobParams.from_block({"proxmox_endpoint_ids": [{"id": 5}]})

    assert params.endpoint_scope is ScopeState.INVALID
    assert params.targets_all_endpoints is False
    assert params.covers_endpoint(5) is False
    assert params.covers_endpoint(9) is False


def test_absent_and_empty_endpoint_scopes_still_mean_all() -> None:
    absent = ProxboxSyncJobParams.from_block({})
    empty = ProxboxSyncJobParams.from_block({"proxmox_endpoint_ids": []})

    for params in (absent, empty):
        assert params.targets_all_endpoints is True
        assert params.covers_endpoint(9) is True


def test_a_present_null_scope_is_unreadable_not_absent() -> None:
    """The plugin only ever writes lists, so a null is malformed, not a default.

    Treating it as "key not written" made `proxmox_endpoint_ids: null` mean
    "every endpoint", so a corrupt row matched every endpoint-scoped query.
    """
    params = ProxboxSyncJobParams.from_block({"proxmox_endpoint_ids": None})

    assert params.endpoint_scope is ScopeState.INVALID
    assert params.targets_all_endpoints is False
    assert params.covers_endpoint(9) is False

    types = ProxboxSyncJobParams.from_block({"sync_types": None})
    assert types.sync_type_scope is ScopeState.INVALID
    assert types.covers_sync_type("storage") is False


def test_a_mapping_is_not_a_scope_list() -> None:
    """`{"all": false}` must not be read as `["all"]` — that inverts its meaning."""
    params = ProxboxSyncJobParams.from_block({"sync_types": {"all": False}})

    assert params.sync_types == []
    assert params.sync_type_scope is ScopeState.INVALID
    assert params.covers_sync_type("storage") is False


def test_partially_unreadable_scope_is_treated_as_unreadable() -> None:
    params = ProxboxSyncJobParams.from_block({"proxmox_endpoint_ids": ["5", {"id": 11}]})

    assert params.endpoint_scope is ScopeState.INVALID
    assert params.covers_endpoint(5) is False


def test_unreadable_vm_scope_matches_no_vm_query() -> None:
    params = ProxboxSyncJobParams.from_block({"netbox_vm_ids": [["199"]]})

    assert params.vm_scope is ScopeState.INVALID
    assert params.covers_vm("199") is False


@pytest.mark.parametrize(
    "value",
    [float("inf"), float("-inf"), float("nan"), 1.5, "1e400"],
    ids=["inf", "-inf", "nan", "non-integral", "string-overflow"],
)
def test_non_integral_ids_are_rejected_rather_than_raising(value: Any) -> None:
    """`json.loads("1e400")` is valid JSON and yields inf; `int(inf)` raises.

    One such row would abort an entire listing, so the coercion refuses instead.
    """
    params = ProxboxSyncJobParams.from_block({"fastapi_endpoint_id": value})
    assert params.fastapi_endpoint_id is None


def test_an_overflowing_endpoint_id_does_not_abort_the_record() -> None:
    record = ProxboxSyncJobRecord.from_row(
        _job_row(data={"proxbox_sync": {"params": {"proxmox_endpoint_ids": [float("inf")]}}})
    )
    assert record.params.endpoint_ids == ()


# --------------------------------------------------------------------------
# Legacy targeted-VM job reconstruction
# --------------------------------------------------------------------------


def test_legacy_targeted_vm_job_recovers_its_vm_and_stages() -> None:
    """Mirrors the plugin's ``_infer_targeted_vm_job_params``.

    Such a row predates the params block, so `data` is empty — but its scope is
    knowable from its name. Without this, `--vm 199` misses the job that
    targeted VM 199, and `--type storage` wrongly matches it through the
    "no recorded types means all" rule.
    """
    record = ProxboxSyncJobRecord.from_row(
        {
            "id": 500,
            "name": "Proxbox Sync: Virtual machine 199",
            "status": {"value": "completed"},
            "queue_name": "default",
            "data": {},
        }
    )

    assert record.params.inferred is True
    assert record.params.netbox_vm_ids == ["199"]
    assert record.params.covers_vm("199") is True
    assert set(record.params.sync_types) == set(TARGETED_VM_SYNC_TYPES)
    assert record.params.covers_sync_type("virtual-machines") is True
    assert record.params.covers_sync_type("storage") is False
    assert ProxboxJobFilters(vm_ids=("199",)).matches(record) is True
    assert ProxboxJobFilters(sync_types=("storage",)).matches(record) is False


def test_recorded_params_are_never_overwritten_by_inference() -> None:
    record = ProxboxSyncJobRecord.from_row(
        _job_row(
            id=501,
            name="Proxbox Sync: Virtual machine 199",
            data={"proxbox_sync": {"params": {"sync_types": ["storage"]}}},
        )
    )

    assert record.params.inferred is False
    assert record.params.sync_types == ["storage"]


def test_a_non_targeted_job_without_params_is_not_inferred() -> None:
    record = ProxboxSyncJobRecord.from_row(
        {"id": 502, "name": "Proxbox Sync", "queue_name": "default", "data": {}}
    )

    assert record.params.inferred is False
    assert record.params.netbox_vm_ids == []


# --------------------------------------------------------------------------
# Scan bounds and pagination integrity
# --------------------------------------------------------------------------


async def test_the_request_limit_never_exceeds_the_remaining_scan_budget() -> None:
    """`--max-scan 1 --page-size 1000` must not fetch a thousand rows first.

    Core job rows carry their whole log history, so checking the ceiling only
    after decoding a full page made the advertised bound advisory.
    """
    fake = _FakeApiClient([_page([_job_row(id=1)])])
    client = ProxboxJobsClient.from_client(fake, page_size=1000)  # type: ignore[arg-type]

    await client.list_jobs(ProxboxJobFilters(), max_scan=1)

    assert fake.calls[0]["query"]["limit"] == 1


async def test_limit_is_not_reported_as_truncated_when_the_matches_run_out() -> None:
    """Exactly `limit` matches and no more is a complete answer, not a cut one."""
    fake = _FakeApiClient([_page([_job_row(id=1), _job_row(id=2)])])
    client = ProxboxJobsClient.from_client(fake)  # type: ignore[arg-type]

    result = await client.list_jobs(ProxboxJobFilters(), limit=2)

    assert [record.id for record in result.jobs] == [1, 2]
    assert result.truncated is False
    assert result.truncation_reason is None


async def test_limit_is_reported_as_truncated_when_another_match_exists() -> None:
    fake = _FakeApiClient([_page([_job_row(id=1), _job_row(id=2), _job_row(id=3)])])
    client = ProxboxJobsClient.from_client(fake)  # type: ignore[arg-type]

    result = await client.list_jobs(ProxboxJobFilters(), limit=2)

    assert [record.id for record in result.jobs] == [1, 2]
    assert result.truncated is True
    assert result.truncation_reason is not None
    assert "more matches exist" in result.truncation_reason


async def test_a_row_redelivered_by_offset_drift_stops_the_scan() -> None:
    """A repeat is evidence of drift, and drift can skip as easily as repeat.

    An insert mid-scan shifts every later offset: one row comes back twice and
    another can be pushed past an offset already read. Silently de-duplicating
    would return a listing that is missing a job while reporting itself
    complete, which is the one outcome this envelope exists to prevent.
    """
    fake = _FakeApiClient(
        [
            _page(
                [_job_row(id=1), _job_row(id=2)],
                next_url="https://nb.example/api/core/jobs/?limit=2&offset=2",
            ),
            _page([_job_row(id=2), _job_row(id=3)]),
        ]
    )
    client = ProxboxJobsClient.from_client(fake, page_size=2)  # type: ignore[arg-type]

    result = await client.list_jobs(ProxboxJobFilters())

    assert result.truncated is True
    assert result.truncation_reason is not None
    assert "delivered twice" in result.truncation_reason
    assert [record.id for record in result.jobs] == [1, 2]


async def test_a_repeated_page_stops_the_scan_and_says_the_list_shifted() -> None:
    fake = _FakeApiClient(
        [
            _page(
                [_job_row(id=1)],
                next_url="https://nb.example/api/core/jobs/?limit=100&ordering=-created",
            ),
            _page([_job_row(id=2)]),
        ]
    )
    client = ProxboxJobsClient.from_client(fake, page_size=100)  # type: ignore[arg-type]

    result = await client.list_jobs(ProxboxJobFilters())

    assert result.truncated is True
    assert result.truncation_reason is not None
    assert "shifted" in result.truncation_reason


def test_targeted_vm_inference_matches_the_plugin_trigger_not_just_missing_params() -> None:
    """The plugin infers whenever the effective types are the default ``["all"]``.

    Transcribed from ``jobs.proxbox_sync_params_from_job``: it does not require
    the params block to be missing, only that no VM ids were recorded and the
    types are the default. Keying on "params block absent" instead would leave
    a row that recorded exactly the default without its scope.
    """
    recorded_default = ProxboxSyncJobRecord.from_row(
        {
            "id": 600,
            "name": "Proxbox Sync: Virtual machine 42",
            "status": {"value": "completed"},
            "queue_name": "default",
            "data": {"proxbox_sync": {"params": {"sync_types": ["all"], "netbox_vm_ids": []}}},
        }
    )
    assert recorded_default.params.inferred is True
    assert recorded_default.params.netbox_vm_ids == ["42"]

    already_scoped = ProxboxSyncJobRecord.from_row(
        {
            "id": 601,
            "name": "Proxbox Sync: Virtual machine 42",
            "status": {"value": "completed"},
            "queue_name": "default",
            "data": {"proxbox_sync": {"params": {"sync_types": ["all"], "netbox_vm_ids": ["7"]}}},
        }
    )
    assert already_scoped.params.inferred is False
    assert already_scoped.params.netbox_vm_ids == ["7"]


# --------------------------------------------------------------------------
# Round-2 review regressions
# --------------------------------------------------------------------------


async def test_reaching_the_scan_ceiling_on_the_last_row_is_not_truncation() -> None:
    """A ceiling that cut nothing short did not truncate anything.

    Marking it truncated reported an exhaustive answer as a partial one, which
    is the same class of lie as the reverse, just in the safe-looking direction.
    """
    fake = _FakeApiClient([_page([_job_row(id=1)])])
    client = ProxboxJobsClient.from_client(fake)  # type: ignore[arg-type]

    result = await client.list_jobs(ProxboxJobFilters(), max_scan=1)

    assert result.scanned == 1
    assert [record.id for record in result.jobs] == [1]
    assert result.truncated is False
    assert result.truncation_reason is None


async def test_the_ceiling_still_truncates_when_rows_remain_on_the_page() -> None:
    fake = _FakeApiClient([_page([_job_row(id=1), _job_row(id=2)])])
    client = ProxboxJobsClient.from_client(fake)  # type: ignore[arg-type]

    result = await client.list_jobs(ProxboxJobFilters(), max_scan=1)

    assert result.truncated is True
    assert result.truncation_reason is not None
    assert "scan limit of 1" in result.truncation_reason


async def test_the_ceiling_still_truncates_when_another_page_exists() -> None:
    fake = _FakeApiClient(
        [_page([_job_row(id=1)], next_url="https://nb.example/api/core/jobs/?offset=1")]
    )
    client = ProxboxJobsClient.from_client(fake)  # type: ignore[arg-type]

    result = await client.list_jobs(ProxboxJobFilters(), max_scan=1)

    assert result.truncated is True
    assert result.truncation_reason is not None
    assert "scan limit of 1" in result.truncation_reason


def test_normalize_sync_types_mirrors_the_plugin() -> None:
    """Transcribed from ``sync_types.normalize_sync_types``, not derived here."""
    assert normalize_sync_types(["all", "storage"]) == ["all"]
    assert normalize_sync_types([]) == ["all"]
    assert normalize_sync_types(["not-a-stage"]) == ["all"]
    assert normalize_sync_types(["storage", "storage"]) == ["storage"]
    assert normalize_sync_types(["storage", "sdn"]) == ["storage", "sdn"]


def test_inference_fires_when_recorded_types_normalize_to_all() -> None:
    """`["all", "storage"]` collapses to `["all"]` in the plugin, so it infers.

    An exact comparison against `["all"]` would not fire here, and the CLI would
    then disagree with the plugin about the same row.
    """
    record = ProxboxSyncJobRecord.from_row(
        {
            "id": 700,
            "name": "Proxbox Sync: Virtual machine 55",
            "status": {"value": "completed"},
            "queue_name": "default",
            "data": {"proxbox_sync": {"params": {"sync_types": ["all", "storage"]}}},
        }
    )

    assert record.params.inferred is True
    assert record.params.netbox_vm_ids == ["55"]


def test_inference_refuses_over_an_unreadable_scope() -> None:
    """Reconstructing over corruption would present a guess as a record."""
    record = ProxboxSyncJobRecord.from_row(
        {
            "id": 701,
            "name": "Proxbox Sync: Virtual machine 55",
            "status": {"value": "completed"},
            "queue_name": "default",
            "data": {"proxbox_sync": {"params": {"sync_types": {"all": True}}}},
        }
    )

    assert record.params.inferred is False
    assert record.params.sync_type_scope is ScopeState.INVALID
    assert record.params.netbox_vm_ids == []


def test_inference_preserves_the_recorded_backend_pin() -> None:
    """The plugin threads ``fastapi_endpoint_id`` through both return paths.

    It decides which proxbox-api a replay talks to, so dropping it on
    reconstruction would silently re-elect "first enabled backend".
    """
    record = ProxboxSyncJobRecord.from_row(
        {
            "id": 702,
            "name": "Proxbox Sync: Virtual machine 55",
            "status": {"value": "completed"},
            "queue_name": "default",
            "data": {"proxbox_sync": {"params": {"fastapi_endpoint_id": 3}}},
        }
    )

    assert record.params.inferred is True
    assert record.params.fastapi_endpoint_id == 3


@pytest.mark.parametrize(
    "value",
    [10**400, float("inf"), "1e400", "inf", "-inf", float("nan")],
    ids=["huge-int", "inf-float", "overflow-str", "inf-str", "-inf-str", "nan"],
)
def test_runtime_seconds_never_raises_and_never_becomes_infinity(value: Any) -> None:
    """`float(10**400)` raises OverflowError; `1e400` becomes a non-JSON Infinity."""
    record = ProxboxSyncJobRecord.from_row(
        _job_row(data={"proxbox_sync": {"runtime_seconds": value}})
    )
    assert record.runtime_seconds is None
    json.dumps(record.summary_row())


@pytest.mark.parametrize(
    "log_entries",
    [5, "entries", {"level": "info"}, None, True],
    ids=["int", "str", "mapping", "null", "bool"],
)
def test_a_non_list_log_entries_field_does_not_abort_the_row(log_entries: Any) -> None:
    """`log_entries: 5` is truthy and not iterable; iterating it raised TypeError."""
    record = ProxboxSyncJobRecord.from_row(_job_row(log_entries=log_entries))
    assert record.log_entries == []
    assert record.log_entry_count == 0


# --------------------------------------------------------------------------
# Round-3 review regressions
# --------------------------------------------------------------------------


async def test_a_deletion_mid_scan_is_caught_even_though_nothing_repeats() -> None:
    """Drift that removes a row leaves no duplicate to notice.

    Delete a row an earlier page already returned and every later offset shifts
    back by one, stepping over a different row entirely. Nothing repeats, so the
    duplicate and repeated-page checks both stay quiet — and the listing would
    claim to be complete while missing a job. The server's own `count` is the
    thing that disagrees.
    """
    fake = _FakeApiClient(
        [
            _page(
                [_job_row(id=4), _job_row(id=3)],
                next_url="https://nb.example/api/core/jobs/?limit=2&offset=2",
                count=4,
            ),
            _page([_job_row(id=1)], count=3),
        ]
    )
    client = ProxboxJobsClient.from_client(fake, page_size=2)  # type: ignore[arg-type]

    result = await client.list_jobs(ProxboxJobFilters())

    assert result.scanned == 3
    assert result.total_available == 4
    assert result.truncated is True
    assert result.truncation_reason is not None
    assert "stepped over" in result.truncation_reason


async def test_an_undisturbed_exhausted_scan_is_not_flagged_as_drift() -> None:
    fake = _FakeApiClient(
        [
            _page(
                [_job_row(id=4), _job_row(id=3)],
                next_url="https://nb.example/api/core/jobs/?limit=2&offset=2",
                count=3,
            ),
            _page([_job_row(id=1)], count=3),
        ]
    )
    client = ProxboxJobsClient.from_client(fake, page_size=2)  # type: ignore[arg-type]

    result = await client.list_jobs(ProxboxJobFilters())

    assert result.scanned == 3
    assert result.truncated is False


def test_reconstruction_preserves_an_unreadable_endpoint_scope() -> None:
    """The job name tells us the VM and the stages. It says nothing about endpoints.

    Replacing an unreadable endpoint list with "empty" during reconstruction
    would launder it into "all endpoints" and hand every endpoint-scoped query a
    row it must never match.
    """
    record = ProxboxSyncJobRecord.from_row(
        {
            "id": 800,
            "name": "Proxbox Sync: Virtual machine 77",
            "status": {"value": "completed"},
            "queue_name": "default",
            "data": {"proxbox_sync": {"params": {"proxmox_endpoint_ids": None}}},
        }
    )

    assert record.params.inferred is True
    assert record.params.netbox_vm_ids == ["77"]
    assert record.params.endpoint_scope is ScopeState.INVALID
    assert record.params.targets_all_endpoints is False
    assert record.params.covers_endpoint(5) is False
    assert ProxboxJobFilters(endpoint_ids=(5,)).matches(record) is False


def test_reconstruction_without_a_recorded_endpoint_scope_still_means_all() -> None:
    record = ProxboxSyncJobRecord.from_row(
        {
            "id": 801,
            "name": "Proxbox Sync: Virtual machine 77",
            "status": {"value": "completed"},
            "queue_name": "default",
            "data": {},
        }
    )

    assert record.params.inferred is True
    assert record.params.targets_all_endpoints is True
    assert record.params.covers_endpoint(5) is True


@pytest.mark.parametrize(
    "value",
    ["²", "١٢٣", "9" * 5000, "12.5", "", "  ", "0x10", "+-3"],
    ids=[
        "superscript",
        "arabic-digits",
        "oversized",
        "float-str",
        "empty",
        "spaces",
        "hex",
        "sign",
    ],
)
def test_integer_coercion_is_total_for_hostile_strings(value: str) -> None:
    """`"²".isdigit()` is True but `int("²")` raises, and CPython caps int(str).

    Either value in `job.data` aborted the whole listing from inside a helper
    contracted to be total.
    """
    params = ProxboxSyncJobParams.from_block({"fastapi_endpoint_id": value})
    assert params.fastapi_endpoint_id is None


def test_integer_coercion_still_accepts_ordinary_values() -> None:
    assert ProxboxSyncJobParams.from_block({"fastapi_endpoint_id": "3"}).fastapi_endpoint_id == 3
    assert ProxboxSyncJobParams.from_block({"fastapi_endpoint_id": "-3"}).fastapi_endpoint_id == -3
    assert ProxboxSyncJobParams.from_block({"fastapi_endpoint_id": 7}).fastapi_endpoint_id == 7


def test_normalize_sync_types_returns_the_plugins_stage_order() -> None:
    """The plugin sorts survivors by dependency order, not by input order."""
    assert normalize_sync_types(["sdn", "storage"]) == ["storage", "sdn"]
    assert normalize_sync_types(["ip-addresses", "devices", "storage"]) == [
        "devices",
        "storage",
        "ip-addresses",
    ]
    assert list(SYNC_STAGE_ORDER)[:3] == ["devices", "storage", "virtual-machines"]
