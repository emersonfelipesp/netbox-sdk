"""``nbx proxbox jobs`` — retrieve and filter netbox-proxbox sync job records.

The sibling ``nbx proxbox sync`` command *starts* one job and streams it. This
module answers the other half of the question: which syncs ran, against which
endpoints, with what result, and what did they report.

Proxbox sync jobs are core NetBox ``core.Job`` rows (see
:mod:`netbox_sdk.proxbox_jobs`). NetBox cannot filter on the ``data`` blob that
identifies them, so the listing scans a server-filtered slice of the job list
and finishes the job client-side. That scan is deliberately bounded, and every
listing states its window, how many rows it looked at, and whether it stopped
early — a truncated answer must never read like a complete one.
"""

from __future__ import annotations

import asyncio
import inspect
import json
from math import isfinite
from typing import Any

import typer
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from netbox_cli.runtime import _get_client
from netbox_cli.support import console
from netbox_sdk.exceptions import RequestError
from netbox_sdk.output_safety import sanitize_terminal_text
from netbox_sdk.proxbox_jobs import (
    DEFAULT_MAX_SCAN,
    DEFAULT_PAGE_SIZE,
    DEFAULT_WINDOW,
    JOB_DATE_FIELDS,
    JOB_STATUS_VALUES,
    ProxboxJobFilterError,
    ProxboxJobFilters,
    ProxboxJobListResult,
    ProxboxJobScanWindow,
    ProxboxJobsClient,
    ProxboxSyncJobRecord,
    is_proxbox_sync_job,
    parse_time_expression,
    validate_date_field,
    validate_job_statuses,
    validate_sync_type_filters,
)
from netbox_sdk.proxbox_sync import ProxboxSyncClient, ProxboxSyncError

jobs_app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="List and inspect netbox-proxbox synchronization jobs.",
)

#: Columns shown by default — enough to triage a run at a glance.
#:
#: Seven, not more: their width floors below sum to just under 100 columns, and
#: Rich resolves an over-subscribed table by collapsing whole columns to zero
#: width rather than by overflowing. An eighth column costs `id` and `status`,
#: which are the two an operator can least afford to lose. `completed` and the
#: rest live in :data:`WIDE_COLUMNS`.
DEFAULT_COLUMNS: tuple[str, ...] = (
    "id",
    "status",
    "created",
    "name",
    "sync_types",
    "proxmox_endpoint_ids",
    "error",
)

#: Columns added by ``--wide``.
WIDE_COLUMNS: tuple[str, ...] = (
    "id",
    "name",
    "status",
    "created",
    "started",
    "completed",
    "runtime_seconds",
    "interval",
    "user",
    "queue_name",
    "sync_types",
    "proxmox_endpoint_ids",
    "netbox_vm_ids",
    "batch_object_type",
    "run_id",
    "log_entry_count",
    "error",
)

#: Every column name ``--fields`` accepts, in canonical display order.
AVAILABLE_COLUMNS: tuple[str, ...] = (
    "id",
    "name",
    "status",
    "status_label",
    "created",
    "scheduled",
    "started",
    "completed",
    "interval",
    "user",
    "queue_name",
    "rq_job_id",
    "object_type",
    "object_id",
    "sync_types",
    "proxmox_endpoint_ids",
    "netbox_endpoint_ids",
    "netbox_vm_ids",
    "batch_object_type",
    "batch_object_ids",
    "fastapi_endpoint_id",
    "run_id",
    "runtime_seconds",
    "log_entry_count",
    "error",
)

#: Orderings NetBox accepts for the core job list. Restricted on purpose: an
#: unknown ``ordering`` value is silently ignored by NetBox, which would make
#: the ``--limit`` cut-off non-deterministic without any visible error.
ALLOWED_ORDERINGS: tuple[str, ...] = (
    "id",
    "name",
    "status",
    "created",
    "scheduled",
    "started",
    "completed",
    "interval",
)

# Only bounds the work of flattening a multi-line error; the column itself
# ellipsizes to the width it was granted.
_ERROR_PREVIEW_CHARS = 240
_LOG_MESSAGE_PREVIEW_CHARS = 160
_LOG_LEVELS: tuple[str, ...] = ("debug", "info", "success", "warning", "failure", "error")

#: Per-column width floors for the listing table. Without these Rich collapses
#: the narrow columns to zero width once enough columns are requested.
_COLUMN_MIN_WIDTH: dict[str, int] = {
    "id": 6,
    "status": 8,
    "status_label": 8,
    "created": 16,
    "scheduled": 16,
    "started": 16,
    "completed": 16,
    "interval": 8,
    "user": 8,
    "queue_name": 7,
    "sync_types": 11,
    "proxmox_endpoint_ids": 7,
    "netbox_endpoint_ids": 7,
    "netbox_vm_ids": 7,
    "runtime_seconds": 8,
    "log_entry_count": 4,
    "run_id": 10,
    "name": 16,
    "error": 12,
}
_DEFAULT_COLUMN_MIN_WIDTH = 7

#: Columns that absorb the leftover width once every floor is satisfied.
_COLUMN_RATIO: dict[str, int] = {"name": 2, "error": 3}

#: Timestamp columns rendered compactly in tables; ``--json`` keeps full ISO-8601.
_TIMESTAMP_COLUMNS: frozenset[str] = frozenset({"created", "scheduled", "started", "completed"})

_STATUS_STYLES: dict[str, str] = {
    "completed": "green",
    "running": "cyan",
    "scheduled": "blue",
    "pending": "yellow",
    "errored": "red",
    "failed": "red",
}


@jobs_app.command("statuses")
def statuses_command() -> None:
    """Print the job status values accepted by ``nbx proxbox jobs list``."""
    table = Table(title="Proxbox Sync Job Statuses", show_header=True, header_style="bold")
    table.add_column("Status", style="cyan", no_wrap=True)
    table.add_column("Meaning")
    meanings = {
        "pending": "Queued, not yet picked up by a worker",
        "scheduled": "Scheduled to start at a future time",
        "running": "Currently executing",
        "completed": "Finished successfully",
        "errored": "Finished with an error",
        "failed": "Failed to run (worker/dispatch failure)",
    }
    for value in JOB_STATUS_VALUES:
        table.add_row(value, meanings.get(value, ""))
    console.print(table)


@jobs_app.command("list")
def list_command(  # noqa: PLR0913 — one option per documented filter
    statuses: list[str] | None = typer.Option(
        None,
        "--status",
        "-s",
        help="Core job status. Repeat for multiple. Run 'nbx proxbox jobs statuses'.",
        show_default=False,
    ),
    sync_types: list[str] | None = typer.Option(
        None,
        "--type",
        "-t",
        help="Proxbox sync type slug. Repeat for multiple. Jobs recorded as 'all' match any type.",
        show_default=False,
    ),
    endpoints: list[str] | None = typer.Option(
        None,
        "--endpoint",
        "-e",
        help="Proxmox endpoint PK or exact name. Repeat for multiple.",
        show_default=False,
    ),
    clusters: list[str] | None = typer.Option(
        None,
        "--cluster",
        help="Proxmox cluster PK or name; matched through the cluster's endpoint.",
        show_default=False,
    ),
    nodes: list[str] | None = typer.Option(
        None,
        "--node",
        help="Proxmox node PK or name; matched through the node's endpoint.",
        show_default=False,
    ),
    vm_ids: list[str] | None = typer.Option(
        None,
        "--vm",
        help="NetBox virtual machine PK targeted by the run. Repeat for multiple.",
        show_default=False,
    ),
    run_ids: list[str] | None = typer.Option(
        None,
        "--run-id",
        help="Proxbox run identifier recorded in the job parameters.",
        show_default=False,
    ),
    batch_object_type: str | None = typer.Option(
        None,
        "--batch-object-type",
        help="Batch object type recorded in the job parameters (e.g. 'virtualization.cluster').",
    ),
    job_ids: list[int] | None = typer.Option(
        None,
        "--id",
        help="Core job PK. Repeat for multiple. Disables the default time window.",
        show_default=False,
    ),
    user: str | None = typer.Option(
        None,
        "--user",
        help="NetBox username that enqueued the job (username, not PK).",
    ),
    name: str | None = typer.Option(None, "--name", help="Exact job name."),
    name_contains: str | None = typer.Option(
        None, "--name-contains", help="Case-insensitive job-name substring."
    ),
    queue: str | None = typer.Option(None, "--queue", help="RQ queue name."),
    rq_job_id: str | None = typer.Option(
        None, "--rq-job-id", help="RQ job UUID recorded on the core job row."
    ),
    object_type: str | None = typer.Option(
        None,
        "--object-type",
        help="Core job object type the run was attached to (e.g. 'netbox_proxbox.proxmoxendpoint').",
    ),
    object_id: int | None = typer.Option(
        None, "--object-id", help="PK of the object the core job was attached to."
    ),
    since: str | None = typer.Option(
        None,
        "--since",
        help=(
            "Start of the window: a relative offset such as '24h', '7d', '2w', "
            f"or an ISO-8601 timestamp. Defaults to '{DEFAULT_WINDOW}'."
        ),
        show_default=False,
    ),
    until: str | None = typer.Option(
        None, "--until", help="End of the window; same syntax as --since.", show_default=False
    ),
    date_field: str = typer.Option(
        "created",
        "--date-field",
        help=f"Timestamp --since/--until apply to. One of: {', '.join(JOB_DATE_FIELDS)}.",
    ),
    all_time: bool = typer.Option(
        False, "--all-time", help="Drop the default time window and scan as far back as allowed."
    ),
    created_after: str | None = typer.Option(
        None,
        "--created-after",
        help="Only jobs whose creation time is on or after this instant "
        "(relative offset or ISO-8601).",
        show_default=False,
    ),
    created_before: str | None = typer.Option(
        None,
        "--created-before",
        help="Only jobs whose creation time is on or before this instant "
        "(relative offset or ISO-8601).",
        show_default=False,
    ),
    scheduled_after: str | None = typer.Option(
        None,
        "--scheduled-after",
        help="Only jobs whose scheduled-start time is on or after this instant "
        "(relative offset or ISO-8601).",
        show_default=False,
    ),
    scheduled_before: str | None = typer.Option(
        None,
        "--scheduled-before",
        help="Only jobs whose scheduled-start time is on or before this instant "
        "(relative offset or ISO-8601).",
        show_default=False,
    ),
    started_after: str | None = typer.Option(
        None,
        "--started-after",
        help="Only jobs whose start time is on or after this instant "
        "(relative offset or ISO-8601).",
        show_default=False,
    ),
    started_before: str | None = typer.Option(
        None,
        "--started-before",
        help="Only jobs whose start time is on or before this instant "
        "(relative offset or ISO-8601).",
        show_default=False,
    ),
    completed_after: str | None = typer.Option(
        None,
        "--completed-after",
        help="Only jobs whose completion time is on or after this instant "
        "(relative offset or ISO-8601).",
        show_default=False,
    ),
    completed_before: str | None = typer.Option(
        None,
        "--completed-before",
        help="Only jobs whose completion time is on or before this instant "
        "(relative offset or ISO-8601).",
        show_default=False,
    ),
    errored: bool = typer.Option(
        False, "--errored", help="Only jobs that failed or recorded an error."
    ),
    recurring: bool | None = typer.Option(
        None,
        "--recurring/--one-shot",
        help="Only recurring (scheduled interval) jobs, or only one-shot jobs.",
        show_default=False,
    ),
    limit: int = typer.Option(
        20, "--limit", min=0, help="Maximum jobs to return. 0 returns every match found."
    ),
    max_scan: int = typer.Option(
        DEFAULT_MAX_SCAN,
        "--max-scan",
        min=0,
        help="Ceiling on core job rows examined. 0 removes the ceiling.",
    ),
    page_size: int = typer.Option(
        DEFAULT_PAGE_SIZE, "--page-size", min=1, max=1000, help="Rows fetched per request."
    ),
    order: str = typer.Option(
        "-created",
        "--order",
        help=f"Sort field, '-' for descending: {', '.join(ALLOWED_ORDERINGS)}.",
    ),
    fields: str | None = typer.Option(
        None, "--fields", help="Comma-separated columns to display. Run with --help for the list."
    ),
    wide: bool = typer.Option(False, "--wide", help="Show the extended column set."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """List netbox-proxbox sync jobs, filtered and bounded."""
    try:
        columns = _resolve_columns(fields=fields, wide=wide)
        window, date_bounds = _resolve_window(
            since=since,
            until=until,
            date_field=date_field,
            all_time=all_time,
            explicit_bounds={
                "created_after": created_after,
                "created_before": created_before,
                "scheduled_after": scheduled_after,
                "scheduled_before": scheduled_before,
                "started_after": started_after,
                "started_before": started_before,
                "completed_after": completed_after,
                "completed_before": completed_before,
            },
            has_id_filter=bool(job_ids),
        )
        base_filters = ProxboxJobFilters(
            statuses=validate_job_statuses(statuses or []),
            ids=tuple(job_ids or []),
            name=name,
            name_contains=name_contains,
            queue_name=queue,
            user=user,
            rq_job_id=rq_job_id,
            object_type=object_type,
            object_id=object_id,
            ordering=_validate_ordering(order),
            sync_types=validate_sync_type_filters(sync_types or []),
            vm_ids=tuple(dict.fromkeys(str(value).strip() for value in (vm_ids or []) if value)),
            run_ids=tuple(dict.fromkeys(str(value).strip() for value in (run_ids or []) if value)),
            batch_object_type=batch_object_type,
            recurring=recurring,
            errored_only=errored,
            **date_bounds,
        )
    except (ProxboxJobFilterError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc

    try:
        result = asyncio.run(
            _run_list(
                filters=base_filters,
                endpoints=list(endpoints or []),
                clusters=list(clusters or []),
                nodes=list(nodes or []),
                limit=limit or None,
                max_scan=max_scan,
                page_size=page_size,
                window=window,
            )
        )
    except (ProxboxSyncError, ProxboxJobFilterError, RequestError, ValueError) as exc:
        _render_error(exc, json_output=json_output)
        raise typer.Exit(code=1) from exc

    if json_output:
        _emit_json(_result_payload(result, columns=columns))
        return
    _render_result_table(result, columns=columns)


@jobs_app.command("get")
def get_command(
    job_id: int = typer.Argument(..., metavar="JOB_ID", help="Core job PK."),
    logs: bool = typer.Option(True, "--logs/--no-logs", help="Include the job log entries."),
    log_level: str | None = typer.Option(
        None, "--log-level", help=f"Only show log entries at this level: {', '.join(_LOG_LEVELS)}."
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit the complete record as JSON."),
) -> None:
    """Show one Proxbox sync job in full, including its parameters and logs."""
    try:
        record = asyncio.run(_run_get(job_id))
    except (ProxboxSyncError, ProxboxJobFilterError, RequestError, ValueError) as exc:
        _render_error(exc, json_output=json_output)
        raise typer.Exit(code=1) from exc

    entries = _filter_log_entries(record.log_entries, log_level) if logs else []
    # `get` fetches by core job PK, which is not restricted to Proxbox rows.
    # Showing another plugin's job is useful — but it must not be presented as a
    # Proxbox sync, whose parameters would then read as "empty" rather than
    # "absent".
    is_proxbox = is_proxbox_sync_job(record.raw)
    if json_output:
        payload = record.detail(include_logs=logs)
        payload["log_entries"] = entries
        payload["is_proxbox_sync_job"] = is_proxbox
        _emit_json(payload)
        return

    if not is_proxbox:
        console.print(
            Text(
                f"Note: core job {record.id} is not a Proxbox sync job. "
                "Its Proxbox parameters are absent, not empty.",
                style="yellow",
            )
        )
    _render_detail(record)
    if logs:
        console.print(_log_table(entries, filtered=log_level is not None))


# --------------------------------------------------------------------------
# Async plumbing
# --------------------------------------------------------------------------


async def _run_list(
    *,
    filters: ProxboxJobFilters,
    endpoints: list[str],
    clusters: list[str],
    nodes: list[str],
    limit: int | None,
    max_scan: int,
    page_size: int,
    window: ProxboxJobScanWindow,
) -> ProxboxJobListResult:
    raw_client = _get_client()
    try:
        jobs_client = ProxboxJobsClient.from_client(raw_client, page_size=page_size)
        endpoint_ids = await _resolve_endpoint_ids(
            raw_client, jobs_client, endpoints=endpoints, clusters=clusters, nodes=nodes
        )
        active = (
            filters.model_copy(update={"endpoint_ids": endpoint_ids}) if endpoint_ids else filters
        )
        return await jobs_client.list_jobs(active, limit=limit, max_scan=max_scan, window=window)
    finally:
        await _close_client(raw_client)


async def _run_get(job_id: int) -> ProxboxSyncJobRecord:
    raw_client = _get_client()
    try:
        return await ProxboxJobsClient.from_client(raw_client).get_job(job_id)
    finally:
        await _close_client(raw_client)


async def _resolve_endpoint_ids(
    raw_client: Any,
    jobs_client: ProxboxJobsClient,
    *,
    endpoints: list[str],
    clusters: list[str],
    nodes: list[str],
) -> tuple[int, ...]:
    """Turn ``--endpoint`` / ``--cluster`` / ``--node`` into Proxmox endpoint PKs.

    The three flags are a union, not an intersection: a job that touched any of
    the named scopes matches.
    """
    resolved: list[int] = []
    if endpoints:
        sync_client = ProxboxSyncClient.from_client(raw_client)
        for value in endpoints:
            resolved.append(await sync_client.resolve_endpoint(value))
    for value in clusters:
        resolved.extend(await jobs_client.resolve_cluster_endpoint_ids(value))
    for value in nodes:
        resolved.extend(await jobs_client.resolve_node_endpoint_ids(value))
    return tuple(dict.fromkeys(resolved))


async def _close_client(raw_client: Any) -> None:
    close_fn = getattr(raw_client, "close", None)
    if not callable(close_fn):
        return
    result = close_fn()
    if inspect.isawaitable(result):
        await result


# --------------------------------------------------------------------------
# Option resolution
# --------------------------------------------------------------------------


def _resolve_columns(*, fields: str | None, wide: bool) -> tuple[str, ...]:
    if fields:
        requested = [part.strip() for part in fields.split(",") if part.strip()]
        unknown = [part for part in requested if part not in AVAILABLE_COLUMNS]
        if unknown:
            available = ", ".join(AVAILABLE_COLUMNS)
            raise ProxboxJobFilterError(
                f"Unknown column(s): {', '.join(unknown)}. Available: {available}"
            )
        if not requested:
            raise ProxboxJobFilterError("--fields must name at least one column")
        return tuple(dict.fromkeys(requested))
    return WIDE_COLUMNS if wide else DEFAULT_COLUMNS


def _validate_ordering(order: str) -> str:
    text = order.strip()
    field_name = text[1:] if text.startswith("-") else text
    if field_name not in ALLOWED_ORDERINGS:
        available = ", ".join(ALLOWED_ORDERINGS)
        raise ProxboxJobFilterError(f"Unknown sort field {order!r}. Available: {available}")
    return text


def _resolve_window(
    *,
    since: str | None,
    until: str | None,
    date_field: str,
    all_time: bool,
    explicit_bounds: dict[str, str | None],
    has_id_filter: bool,
) -> tuple[ProxboxJobScanWindow, dict[str, str | None]]:
    """Resolve the scan window into concrete ``__after`` / ``__before`` bounds.

    Precedence: explicit ``--<field>-after/-before`` values win; then
    ``--since``/``--until`` against ``--date-field``; then, only when nothing
    else bounds the scan, the default look-back. ``--all-time`` and an explicit
    ``--id`` lookup both suppress the default.
    """
    if all_time and (since or until):
        raise ProxboxJobFilterError("--all-time cannot be combined with --since/--until")

    field_name = validate_date_field(date_field)
    bounds: dict[str, str | None] = {
        key: (parse_time_expression(value) if value else None)
        for key, value in explicit_bounds.items()
    }

    # An explicit `--<field>-after` and a `--since` aimed at the same field are
    # two different answers to one question. Silently letting one overwrite the
    # other would run a scan the caller did not ask for and then report it as
    # theirs, so the conflict is refused instead.
    for suffix, relative, flag in (("after", since, "--since"), ("before", until, "--until")):
        if not relative:
            continue
        key = f"{field_name}_{suffix}"
        if bounds.get(key):
            raise ProxboxJobFilterError(
                f"{flag} and --{field_name}-{suffix} both bound the '{field_name}' "
                "timestamp. Use one or the other."
            )
        bounds[key] = parse_time_expression(relative)

    if not any(bounds.values()):
        if all_time or has_id_filter:
            # Nothing bounds the scan on purpose: --all-time was asked for, or
            # the caller named exact job PKs and a window would only hide them.
            return ProxboxJobScanWindow(), bounds
        # Honour --date-field: the help and both documentation mirrors say the
        # default look-back can target another timestamp, and hard-coding
        # `created` made `--date-field completed` silently filter creation time.
        bounds[f"{field_name}_after"] = parse_time_expression(DEFAULT_WINDOW)

    # Report every bound in effect, not one of them: a scan bounded on two
    # fields is narrower than either, and naming one describes a scan that did
    # not happen.
    return ProxboxJobScanWindow.from_bounds(bounds), bounds


def _filter_log_entries(
    entries: list[dict[str, Any]], log_level: str | None
) -> list[dict[str, Any]]:
    if not log_level:
        return list(entries)
    wanted = log_level.strip().lower()
    if wanted not in _LOG_LEVELS:
        available = ", ".join(_LOG_LEVELS)
        raise typer.BadParameter(f"Unknown log level {log_level!r}. Available: {available}")
    return [entry for entry in entries if str(entry.get("level", "")).lower() == wanted]


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


def _json_safe(value: Any) -> Any:
    """Strip values that are valid Python floats but not valid JSON.

    ``json.loads("1e400")`` yields ``inf``, and ``json.dumps`` re-emits it as the
    bare literal ``Infinity`` — which is not JSON, and which a strict consumer
    rejects. Normalising only the fields this module parses is not enough: the
    response block, the log entries and the untouched ``raw`` row all pass
    through unmodified, so the walk has to cover the whole document.
    """
    if isinstance(value, float):
        return value if isfinite(value) else None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _emit_json(payload: Any) -> None:
    """Emit strict JSON. ``allow_nan=False`` is the backstop, not the mechanism."""
    typer.echo(
        json.dumps(_json_safe(payload), indent=2, sort_keys=True, default=str, allow_nan=False)
    )


def _result_payload(result: ProxboxJobListResult, *, columns: tuple[str, ...]) -> dict[str, Any]:
    """JSON envelope. Carries the scan facts alongside the rows, never just rows."""
    return {
        "window": result.window.model_dump(),
        "window_display": result.window.describe(),
        "scanned": result.scanned,
        "matched": result.matched,
        "total_core_jobs_in_window": result.total_available,
        "truncated": result.truncated,
        "truncation_reason": result.truncation_reason,
        "columns": list(columns),
        # The stage-summary block rides along; `log_entries` deliberately does
        # not — it is the heavy part of a core job row, and `jobs get` has it.
        "jobs": [{**record.summary_row(), "response": record.response} for record in result.jobs],
    }


def _column_widths(columns: tuple[str, ...], available: int) -> dict[str, int]:
    """Assign each column a fixed width, so none of them can be collapsed away.

    Rich resolves an over-subscribed table by reducing every column by the same
    ratio and clamping at zero. With `no_wrap` set (which is what keeps a row on
    one line) its gentler collapse pass is skipped entirely, so the *narrowest*
    columns — `id` and `status`, the two an operator most needs — are the first
    to vanish, while a long error message keeps its width. `min_width` does not
    help: it constrains measurement, not that final reduction.

    So the widths are decided here instead. Every column gets its floor; any
    slack left over goes to the columns that benefit from it (`name`, `error`).
    When even the floors do not fit, they are kept anyway and the table is left
    to overflow: Rich crops the right-hand side, which loses the trailing
    columns rather than the leading ones.
    """
    floors = [_COLUMN_MIN_WIDTH.get(column, _DEFAULT_COLUMN_MIN_WIDTH) for column in columns]
    # Two padding cells and one border per column, plus the table's closing border.
    overhead = 3 * len(columns) + 1
    budget = available - overhead
    if budget <= sum(floors):
        return dict(zip(columns, floors, strict=True))

    slack = budget - sum(floors)
    weights = [_COLUMN_RATIO.get(column, 0) for column in columns]
    total_weight = sum(weights)
    if not total_weight:
        return dict(zip(columns, floors, strict=True))

    widths = list(floors)
    granted = 0
    for index, weight in enumerate(weights):
        if weight:
            share = slack * weight // total_weight
            widths[index] += share
            granted += share
    # Hand the rounding remainder to the heaviest column so the table fills the
    # terminal exactly instead of leaving a ragged gap.
    widths[weights.index(max(weights))] += slack - granted
    return dict(zip(columns, widths, strict=True))


def _render_result_table(result: ProxboxJobListResult, *, columns: tuple[str, ...]) -> None:
    table = Table(
        title="Proxbox Sync Jobs",
        show_header=True,
        header_style="bold",
        expand=False,
    )
    for column, width in _column_widths(columns, console.width).items():
        table.add_column(column, overflow="ellipsis", no_wrap=True, width=width)
    for record in result.jobs:
        row = record.summary_row()
        table.add_row(*[_cell(column, row.get(column), record) for column in columns])
    console.print(table)
    console.print(_scan_footer(result))


def _scan_footer(result: ProxboxJobListResult) -> Text:
    """One line stating exactly how complete the answer is."""
    footer = Text()
    footer.append("window ", style="dim")
    footer.append(result.window.describe(), style="bold")
    footer.append("  •  scanned ", style="dim")
    footer.append(str(result.scanned), style="bold")
    footer.append(" core job row(s)  •  matched ", style="dim")
    footer.append(str(result.matched), style="bold")
    if result.total_available is not None:
        footer.append(f"  •  {result.total_available} core job(s) matched server-side", style="dim")
    if result.truncated:
        footer.append("\nTRUNCATED: ", style="bold yellow")
        # The reason already says what was cut and why; appending a generic
        # "more may exist" made the `--limit` line contradict itself, since that
        # reason is only emitted once a further match has actually been seen.
        footer.append(str(result.truncation_reason), style="yellow")
    return footer


def _compact_timestamp(value: Any) -> str:
    """Render an ISO-8601 instant as ``YYYY-MM-DD HH:MM`` for table display.

    Anything that is not a recognisable timestamp is passed through unchanged
    rather than blanked — an unexpected value is still information.
    """
    text = str(value or "").strip()
    if len(text) < 16 or text[4] != "-" or text[10] not in {"T", " "}:
        return text
    return f"{text[:10]} {text[11:16]}"


def _safe(value: Any) -> str:
    """Every server-controlled string passes through here before rendering.

    Rich's ``Text`` preserves embedded CSI/OSC sequences verbatim, so any job
    field rendered raw — a status, a sync-type slug, a log timestamp — is an
    injection point that can clear or spoof the terminal. Sanitizing at the one
    place cells are built means a new column cannot forget to do it.
    """
    return sanitize_terminal_text(str(value))


def _cell(column: str, value: Any, record: ProxboxSyncJobRecord) -> Text:
    if column in _TIMESTAMP_COLUMNS:
        compact = _compact_timestamp(value)
        return Text(_safe(compact)) if compact else Text("—", style="dim")
    if column == "status":
        status = _safe(value or "")
        return Text(status, style=_STATUS_STYLES.get(status, ""))
    if column == "error":
        return Text(_preview(str(value or ""), _ERROR_PREVIEW_CHARS), style="red" if value else "")
    if column == "sync_types":
        return Text(_safe(record.sync_types_display))
    if column == "proxmox_endpoint_ids":
        return Text(_safe(record.endpoints_display))
    if isinstance(value, list):
        return Text(_safe(", ".join(str(item) for item in value)))
    if value is None:
        return Text("—", style="dim")
    return Text(_safe(value))


def _preview(text: str, limit: int) -> str:
    cleaned = sanitize_terminal_text(text.strip().replace("\n", " "))
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 1]}…"


def _render_detail(record: ProxboxSyncJobRecord) -> None:
    table = Table(title=f"Proxbox Sync Job {record.id}", show_header=True, header_style="bold")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", overflow="fold")
    for key, value in record.summary_row().items():
        if key == "id":
            continue
        table.add_row(Text(_safe(key)), _detail_value(key, value, record))
    console.print(table)

    if record.response:
        response_table = Table(title="Response", show_header=True, header_style="bold")
        response_table.add_column("Key", style="cyan", no_wrap=True)
        response_table.add_column("Value", overflow="fold")
        for key, value in record.response.items():
            # `Table.add_row` with a plain `str` lets Rich parse markup in it, so
            # a server-supplied `[link=...]` renders as a hyperlink and an
            # unmatched closing tag raises MarkupError and kills the command.
            # A `Text` instance is rendered literally.
            response_table.add_row(Text(_safe(key)), Text(_safe(json.dumps(value, default=str))))
        console.print(response_table)


def _detail_value(key: str, value: Any, record: ProxboxSyncJobRecord) -> Text:
    if key == "proxmox_endpoint_ids":
        return Text(_safe(record.endpoints_display))
    if key == "sync_types":
        return Text(_safe(record.sync_types_display))
    if key == "status":
        status = _safe(value or "")
        return Text(status, style=_STATUS_STYLES.get(status, ""))
    if isinstance(value, list):
        return Text(_safe(", ".join(str(item) for item in value)) or "—")
    if value is None or value == "":
        return Text("—", style="dim")
    return Text(_safe(value))


def _log_table(entries: list[dict[str, Any]], *, filtered: bool) -> Table:
    title = "Log Entries (filtered)" if filtered else "Log Entries"
    table = Table(title=title, show_header=True, header_style="bold")
    table.add_column("Timestamp", style="dim", no_wrap=True)
    table.add_column("Level", no_wrap=True)
    table.add_column("Message", overflow="fold")
    for entry in entries:
        level = _safe(entry.get("level", ""))
        style = "red" if level in {"failure", "error"} else "yellow" if level == "warning" else ""
        table.add_row(
            Text(_safe(entry.get("timestamp", ""))),
            Text(level, style=style),
            Text(_preview(str(entry.get("message", "")), _LOG_MESSAGE_PREVIEW_CHARS)),
        )
    if not entries:
        table.add_row("—", "—", "no log entries")
    return table


def _render_error(exc: Exception, *, json_output: bool) -> None:
    message = _error_message(exc)
    if json_output:
        _emit_json({"ok": False, "error": {"type": exc.__class__.__name__, "message": message}})
        return
    style = "yellow" if isinstance(exc, ProxboxSyncError) and exc.status == 403 else "red"
    title = "Permission Denied" if style == "yellow" else "Proxbox Job Error"
    console.print(
        Panel(Text(sanitize_terminal_text(message), style=style), title=title, border_style=style)
    )


def _error_message(exc: Exception) -> str:
    if isinstance(exc, RequestError):
        body = exc.response.text.strip()
        return body or str(exc)
    return str(exc)


__all__ = [
    "AVAILABLE_COLUMNS",
    "DEFAULT_COLUMNS",
    "WIDE_COLUMNS",
    "jobs_app",
]
