"""``nbx proxbox`` commands for netbox-proxbox resources and sync jobs."""

from __future__ import annotations

import asyncio
import inspect
import json
import time
from dataclasses import dataclass, field
from typing import Any

import typer
from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TaskProgressColumn, TextColumn
from rich.table import Table
from rich.text import Text

from netbox_cli.dynamic import _build_action_command
from netbox_cli.proxbox_jobs import jobs_app
from netbox_cli.runtime import _get_client
from netbox_cli.support import (
    console,
    load_tui_callables,
    resolve_requested_theme,
    rethrow_theme_catalog_error,
)
from netbox_cli.write_confirmation import require_write_confirmation
from netbox_sdk.exceptions import RequestError
from netbox_sdk.logging_runtime import get_logger
from netbox_sdk.output_safety import sanitize_terminal_text
from netbox_sdk.proxbox import (
    ProxboxResourceSpec,
    build_proxbox_schema_index,
    find_proxbox_resource,
    proxbox_resources,
)
from netbox_sdk.proxbox_sync import (
    SYNC_TYPE_VALUES,
    ProxboxSyncClient,
    ProxboxSyncError,
    ScheduleResult,
    SseFrame,
    SyncType,
    validate_sync_types,
)
from netbox_sdk.schema import SchemaIndex

proxbox_app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Manage netbox-proxbox resources and synchronization jobs.",
)

_RECENT_EVENT_LIMIT = 14
_ERROR_EVENTS = {"error", "error_detail"}
_TERMINAL_JOB_STATUSES = frozenset(
    {"completed", "errored", "failed", "terminated", "canceled", "cancelled"}
)
_JOB_POLL_INTERVAL = 1.0
logger = get_logger(__name__)


def _proxbox_index_factory() -> SchemaIndex:
    return build_proxbox_schema_index()


@dataclass(slots=True)
class ProgressSnapshot:
    phase: str
    current: int
    total: int
    percent: float | None = None
    status: str = ""
    message: str = ""


@dataclass(slots=True)
class SyncErrorEntry:
    source: str
    phase: str = ""
    item: str = ""
    category: str = ""
    message: str = ""
    detail: str = ""
    suggestion: str = ""
    traceback: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "source": self.source,
            "phase": self.phase,
            "item": self.item,
            "category": self.category,
            "message": self.message,
            "detail": self.detail,
            "suggestion": self.suggestion,
            "traceback": self.traceback,
        }


@dataclass(slots=True)
class RenderState:
    job_id: int
    endpoint_label: str
    sync_types: list[str]
    schedule_message: str = ""
    progress: dict[str, ProgressSnapshot] = field(default_factory=dict)
    summaries: dict[str, dict[str, Any]] = field(default_factory=dict)
    recent_events: list[Text] = field(default_factory=list)
    errors: list[SyncErrorEntry] = field(default_factory=list)
    warnings: list[SyncErrorEntry] = field(default_factory=list)
    complete: dict[str, Any] | None = None


def frame_to_line(frame: SseFrame) -> Text:
    """Map an SSE frame to a styled Rich line without side effects."""
    data = frame.data
    event = frame.event
    style = _event_style(frame)
    line = Text(style=style)
    line.append(f"{event}", style=style)

    phase = _frame_phase(frame)
    if phase and phase != event:
        line.append(" | ", style="dim")
        line.append(phase, style="bold")

    item = _item_label(data.get("item"))
    if item:
        line.append(" | ", style="dim")
        line.append(item)

    message = _frame_message(frame)
    if message:
        line.append(" - ", style="dim")
        line.append(message)

    progress = data.get("progress")
    if isinstance(progress, dict):
        current = _int_value(progress.get("current"))
        total = _int_value(progress.get("total"))
        percent = _float_value(progress.get("percent"))
        if current is not None and total is not None:
            line.append(f" ({current}/{total})", style="bold")
        if percent is not None:
            line.append(f" {percent:.0f}%", style="bold")

    if event == "phase_summary" and isinstance(data.get("result"), dict):
        line.append(" | ", style="dim")
        line.append(_compact_counts(data["result"]), style="bold green")

    if event == "complete":
        ok = bool(data.get("ok"))
        line.stylize("bold green" if ok else "bold red")

    return line


def render_frame(frame: SseFrame, state: RenderState) -> None:
    """Update render state from one parsed SSE frame."""
    state.recent_events.append(frame_to_line(frame))
    if len(state.recent_events) > _RECENT_EVENT_LIMIT:
        del state.recent_events[: len(state.recent_events) - _RECENT_EVENT_LIMIT]

    data = frame.data
    progress = data.get("progress")
    if isinstance(progress, dict):
        phase = _frame_phase(frame)
        current = _int_value(progress.get("current")) or 0
        total = _int_value(progress.get("total")) or 100
        percent = _float_value(progress.get("percent"))
        if total <= 0 and percent is not None:
            total = 100
            current = int(percent)
        state.progress[phase] = ProgressSnapshot(
            phase=phase,
            current=current,
            total=total,
            percent=percent,
            status=_clean(data.get("status")),
            message=_frame_message(frame),
        )

    if frame.event == "phase_summary" and isinstance(data.get("result"), dict):
        state.summaries[_frame_phase(frame)] = dict(data["result"])

    if frame.event in _ERROR_EVENTS:
        state.errors.append(_error_from_frame(frame))
    elif frame.event == "item_progress" and data.get("error"):
        state.errors.append(_error_from_frame(frame, message_key="error"))
    elif frame.event == "item_progress" and data.get("warning"):
        state.warnings.append(_error_from_frame(frame, message_key="warning"))

    if frame.event == "complete":
        state.complete = dict(data)


@proxbox_app.command("resources")
def resources_command(
    json_output: bool = typer.Option(False, "--json", help="Emit the catalog as JSON."),
) -> None:
    """List Proxbox resources known to the dedicated CLI surface."""
    resources = proxbox_resources()
    if json_output:
        payload = [
            {
                "key": spec.key,
                "command": f"nbx proxbox {spec.command_path}",
                "category": spec.category,
                "label": spec.label,
                "list_path": spec.list_path,
                "detail_path": spec.detail_path,
                "actions": list(spec.supported_actions),
                "read_only": spec.read_only,
            }
            for spec in resources
        ]
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
        return

    table = Table(title="Proxbox Resource Catalog", show_header=True, header_style="bold cyan")
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Category", style="magenta")
    table.add_column("Actions", style="green")
    table.add_column("Description", overflow="fold", ratio=2)
    for spec in resources:
        table.add_row(
            f"proxbox {spec.command_path}",
            spec.category,
            ", ".join(spec.supported_actions),
            spec.description,
        )
    console.print(table)


@proxbox_app.command("ops")
def ops_command(
    resource: str = typer.Argument(
        ...,
        help="Catalog key or command path, for example endpoints/proxmox or firewall/rules.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit operations as JSON."),
) -> None:
    """Show HTTP operations for one Proxbox resource."""
    try:
        spec = find_proxbox_resource(resource)
    except KeyError as exc:
        raise typer.BadParameter(str(exc)) from exc

    operations = _operations_for_spec(spec)
    if json_output:
        typer.echo(json.dumps(operations, indent=2, sort_keys=True))
        return

    table = Table(title=f"Proxbox Operations: {spec.command_path}", show_header=True)
    table.add_column("Action", style="cyan", no_wrap=True)
    table.add_column("Method", style="bold")
    table.add_column("Path", overflow="fold", ratio=2)
    table.add_column("Notes", overflow="fold")
    for operation in operations:
        table.add_row(
            str(operation["action"]),
            str(operation["method"]),
            str(operation["path"]),
            str(operation["notes"]),
        )
    console.print(table)


@proxbox_app.command(
    "tui", context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def proxbox_tui_command(
    ctx: typer.Context,
    theme: bool = typer.Option(
        False,
        "--theme",
        help="Theme selector. Use '--theme' to list available themes or '--theme <name>' to launch with one.",
    ),
    confirm: bool = typer.Option(
        False,
        "--confirm",
        help="Confirm launching a workbench capable of live Proxbox writes.",
    ),
) -> None:
    """Launch the Proxbox-focused Textual request workbench."""
    available_theme_names, resolve_theme_name, run_proxbox_tui = load_tui_callables(
        "netbox_tui.proxbox_app",
        "available_theme_names",
        "resolve_theme_name",
        "run_proxbox_tui",
    )

    selected_theme = resolve_requested_theme(
        ctx,
        theme=theme,
        available_theme_names=available_theme_names,
        resolve_theme_name=resolve_theme_name,
        usage="nbx proxbox tui --theme <name>",
    )
    if theme and not ctx.args:
        return

    require_write_confirmation(confirmed=confirm)
    try:
        run_proxbox_tui(client=_get_client(), theme_name=selected_theme)
    except Exception as exc:
        rethrow_theme_catalog_error(exc)


@proxbox_app.command("sync")
def sync_command(
    endpoint: str | None = typer.Argument(
        None,
        metavar="ENDPOINT",
        help="Optional Proxmox endpoint PK or exact name. Omit to sync all endpoints.",
    ),
    sync_types: list[str] | None = typer.Option(
        None,
        "--type",
        "-t",
        help="Proxbox sync type slug. Repeat for multiple types. Defaults to all.",
        show_default=False,
    ),
    job_name: str | None = typer.Option(None, "--job-name", help="Optional NetBox job name."),
    timeout: float = typer.Option(
        7200.0,
        "--timeout",
        min=1.0,
        help="Maximum seconds to keep the SSE stream open.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit only a final machine-readable JSON result.",
    ),
    confirm: bool = typer.Option(
        False,
        "--confirm",
        help="Confirm scheduling this live Proxbox synchronization job.",
    ),
) -> None:
    """Schedule a Proxbox sync job and stream live progress until it finishes."""
    requested_types = _validate_cli_sync_types(sync_types)
    require_write_confirmation(confirmed=confirm)
    raw_client = _get_client()
    proxbox = ProxboxSyncClient.from_client(raw_client)
    try:
        result, queued = asyncio.run(
            _run_sync(
                raw_client=raw_client,
                proxbox=proxbox,
                endpoint=endpoint,
                sync_types=requested_types,
                job_name=job_name,
                timeout=timeout,
                json_output=json_output,
            )
        )
    except ProxboxSyncError as exc:
        _render_cli_exception(exc, json_output=json_output)
        raise typer.Exit(code=1) from exc
    except RequestError as exc:
        _render_cli_exception(exc, json_output=json_output)
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        _render_cli_exception(exc, json_output=json_output)
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps(result, indent=2, sort_keys=True, default=str))
    else:
        _render_final_result(result, queued=queued)

    if not result["ok"]:
        raise typer.Exit(code=1)


@proxbox_app.command("sync-types")
def sync_types_command() -> None:
    """Print the sync type slugs accepted by ``nbx proxbox sync``."""
    table = Table(title="Proxbox Sync Types", show_header=True, header_style="bold")
    table.add_column("Slug", style="cyan", no_wrap=True)
    table.add_column("Description")
    for value in SYNC_TYPE_VALUES:
        description = "Run every Proxbox sync stage" if value == SyncType.ALL else ""
        table.add_row(value, description)
    console.print(table)


def _operations_for_spec(spec: ProxboxResourceSpec) -> list[dict[str, str]]:
    operations: list[dict[str, str]] = []
    for action in spec.supported_actions:
        if action == "list":
            operations.append(
                {
                    "action": action,
                    "method": "GET",
                    "path": spec.list_path,
                    "notes": "List records; supports -q key=value and --all.",
                }
            )
        elif action == "get" and spec.detail_path:
            operations.append(
                {
                    "action": action,
                    "method": "GET",
                    "path": spec.detail_path,
                    "notes": "Read one record; requires --id.",
                }
            )
        elif action == "create":
            operations.append(
                {
                    "action": action,
                    "method": "POST",
                    "path": spec.list_path,
                    "notes": "Create a record from --body-json or --body-file.",
                }
            )
        elif action == "update" and spec.detail_path:
            operations.append(
                {
                    "action": action,
                    "method": "PUT",
                    "path": spec.detail_path,
                    "notes": "Replace one record; requires --id and a body.",
                }
            )
        elif action == "patch" and spec.detail_path:
            operations.append(
                {
                    "action": action,
                    "method": "PATCH",
                    "path": spec.detail_path,
                    "notes": "Partially update one record; requires --id and a body.",
                }
            )
        elif action == "delete" and spec.detail_path:
            operations.append(
                {
                    "action": action,
                    "method": "DELETE",
                    "path": spec.detail_path,
                    "notes": "Delete one record; requires --id.",
                }
            )
    return operations


def _proxbox_branch_help(command_path: tuple[str, ...]) -> str:
    label = " ".join(command_path)
    return f"Proxbox resource group: {label}"


def _register_proxbox_resource_commands(target_app: typer.Typer) -> None:
    """Attach catalog-backed ``nbx proxbox <resource> <action>`` commands."""
    apps: dict[tuple[str, ...], typer.Typer] = {(): target_app}
    for spec in proxbox_resources():
        parent_path: tuple[str, ...] = ()
        for index, part in enumerate(spec.command_parts, start=1):
            command_path = spec.command_parts[:index]
            if command_path not in apps:
                child_app = typer.Typer(
                    add_completion=False,
                    no_args_is_help=True,
                    help=_proxbox_branch_help(command_path),
                )
                apps[parent_path].add_typer(child_app, name=part)
                apps[command_path] = child_app
            parent_path = command_path

        leaf_app = apps[spec.command_parts]
        for action in spec.supported_actions:
            cmd = _build_action_command(
                group="plugins",
                resource=spec.resource,
                action=action,
                client_factory=_get_client,
                index_factory=_proxbox_index_factory,
            )
            leaf_app.command(
                name=action,
                help=f"{action} {spec.command_path}",
            )(cmd)


async def _run_sync(
    *,
    raw_client: Any,
    proxbox: ProxboxSyncClient,
    endpoint: str | None,
    sync_types: list[str],
    job_name: str | None,
    timeout: float,
    json_output: bool,
) -> tuple[dict[str, Any], bool]:
    try:
        endpoint_ids, endpoint_label = await _resolve_endpoint_arg(proxbox, endpoint)
        schedule = await proxbox.schedule(
            sync_types,
            proxmox_endpoint_ids=endpoint_ids,
            job_name=job_name,
        )
        job_id = _scheduled_job_id(schedule)
        state = RenderState(
            job_id=job_id,
            endpoint_label=endpoint_label,
            sync_types=sync_types,
            schedule_message=schedule.message,
        )
        stream_error: Exception | None = None
        stream_started_at = time.monotonic()
        try:
            if json_output:
                await _consume_stream(proxbox, state, timeout=timeout)
            else:
                with Live(
                    _live_renderable(state),
                    console=console,
                    refresh_per_second=4,
                    transient=False,
                ) as live:
                    await _consume_stream(proxbox, state, timeout=timeout, live=live)
        except Exception as exc:  # noqa: BLE001 - recover the authoritative job after any stream failure
            stream_error = exc
            state.warnings.append(
                SyncErrorEntry(
                    source="stream",
                    phase="stream",
                    message="SSE stream failed after the Proxbox job was scheduled.",
                    detail=f"{exc.__class__.__name__}: {exc}",
                )
            )

        if state.complete is None and stream_error is None:
            state.warnings.append(
                SyncErrorEntry(
                    source="stream",
                    phase="stream",
                    message="SSE stream ended before the terminal complete frame arrived.",
                )
            )
        stream_failed = stream_error is not None or state.complete is None

        try:
            job = await proxbox.fetch_job(job_id)
        except Exception as fetch_error:
            logger_message = (
                f"Authoritative fetch failed for scheduled Proxbox job {job_id}; "
                "inspect this existing job before considering another sync."
            )
            logger.warning(
                logger_message,
                extra={"nbx_event": "proxbox_authoritative_fetch_failed", "job_id": job_id},
                exc_info=True,
            )
            if not stream_failed:
                raise ProxboxSyncError(
                    f"{logger_message} "
                    f"Fetch error: {fetch_error.__class__.__name__}: {fetch_error}",
                    job_id=job_id,
                ) from fetch_error
            stream_detail = (
                f"{stream_error.__class__.__name__}: {stream_error}"
                if stream_error is not None
                else "the SSE stream ended before a terminal complete frame"
            )
            raise ProxboxSyncError(
                f"Proxbox job {job_id} stream failed ({stream_detail}); "
                "authoritative job fetch also failed "
                f"({fetch_error.__class__.__name__}: {fetch_error}). "
                "The sync was already scheduled; inspect this existing job before "
                "considering another sync.",
                job_id=job_id,
            ) from fetch_error
        if stream_failed and not _job_status_is_terminal(job):
            remaining_timeout = max(0.0, timeout - (time.monotonic() - stream_started_at))
            job, poll_error = await _poll_job_to_terminal(
                proxbox,
                job_id,
                initial_job=job,
                timeout=remaining_timeout,
            )
            if not _job_status_is_terminal(job):
                status = _status_value(job.get("status")) or "non-terminal"
                detail = (
                    f"Polling also failed ({poll_error.__class__.__name__}: {poll_error}). "
                    if poll_error is not None
                    else ""
                )
                state.errors.append(
                    SyncErrorEntry(
                        source="job",
                        phase=status,
                        message=(
                            f"Proxbox job {job_id} is still {status} server-side; "
                            "completion was not confirmed before the --timeout budget expired."
                        ),
                        detail=(
                            f"{detail}The sync was scheduled; inspect this existing job before "
                            "considering another sync."
                        ),
                    )
                )
        return _build_final_result(job_id, state, job)
    finally:
        await _close_raw_client(raw_client)


async def _consume_stream(
    proxbox: ProxboxSyncClient,
    state: RenderState,
    *,
    timeout: float,
    live: Live | None = None,
) -> None:
    async for frame in proxbox.stream_job(state.job_id, timeout=timeout):
        render_frame(frame, state)
        if live is not None:
            live.update(_live_renderable(state))
        if frame.event == "complete":
            break


async def _poll_job_to_terminal(
    proxbox: ProxboxSyncClient,
    job_id: int,
    *,
    initial_job: dict[str, Any],
    timeout: float,
) -> tuple[dict[str, Any], Exception | None]:
    """Poll an already scheduled job within the remaining stream timeout budget."""
    job = initial_job
    deadline = time.monotonic() + timeout
    while not _job_status_is_terminal(job):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return job, None
        await asyncio.sleep(min(_JOB_POLL_INTERVAL, remaining))
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return job, None
        try:
            job = await asyncio.wait_for(proxbox.fetch_job(job_id), timeout=remaining)
        except Exception as exc:  # noqa: BLE001 - report unresolved authoritative status
            return job, exc
    return job, None


def _job_status_is_terminal(job: dict[str, Any]) -> bool:
    return _status_value(job.get("status")) in _TERMINAL_JOB_STATUSES


async def _resolve_endpoint_arg(
    proxbox: ProxboxSyncClient,
    endpoint: str | None,
) -> tuple[list[int] | None, str]:
    if endpoint is None:
        return None, "all endpoints"
    endpoint_id = await proxbox.resolve_endpoint(endpoint)
    if str(endpoint).strip().isdigit():
        return [endpoint_id], f"PK {endpoint_id}"
    return [endpoint_id], f"{endpoint} (PK {endpoint_id})"


async def _close_raw_client(raw_client: Any) -> None:
    close_fn = getattr(raw_client, "close", None)
    if not callable(close_fn):
        return
    result = close_fn()
    if inspect.isawaitable(result):
        await result


def _validate_cli_sync_types(sync_types: list[str] | None) -> list[str]:
    try:
        return validate_sync_types(sync_types or [SyncType.ALL.value])
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc


def _scheduled_job_id(schedule: ScheduleResult) -> int:
    if schedule.job_id is None:
        raise ProxboxSyncError("Proxbox schedule response did not include a job_id")
    return schedule.job_id


def _build_final_result(
    job_id: int,
    state: RenderState,
    job: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    status = _status_value(job.get("status"))
    complete_status = _status_value((state.complete or {}).get("status"))
    stream_recovered = any(
        warning.source == "stream" and warning.phase == "stream" for warning in state.warnings
    )
    complete_ok = bool(state.complete.get("ok")) if state.complete is not None else stream_recovered
    errors = _dedupe_errors(
        [
            *state.errors,
            *_job_error_entries(job),
            *_complete_error_entries(state),
        ]
    )
    if status in _TERMINAL_JOB_STATUSES - {"completed"} and not errors:
        errors.append(
            SyncErrorEntry(
                source="job",
                phase=status,
                message=f"Proxbox job finished with status '{status}'.",
            )
        )
    warnings = _dedupe_errors(state.warnings)
    summary = _merged_summary(state, job)
    queued = (
        (state.complete is not None and state.complete.get("ok") is False)
        and (complete_status in {"waiting", "pending", "queued", "scheduled"})
    ) or (state.complete is None and status in {"waiting", "pending", "queued", "scheduled"})
    ok = complete_ok and status == "completed" and not errors
    return (
        {
            "job_id": job_id,
            "status": status,
            "ok": ok,
            "errors": [entry.as_dict() for entry in errors],
            "warnings": [entry.as_dict() for entry in warnings],
            "summary": summary,
        },
        queued,
    )


def _complete_error_entries(state: RenderState) -> list[SyncErrorEntry]:
    if state.complete is None or state.complete.get("ok") is not False:
        return []
    return [
        SyncErrorEntry(
            source="complete",
            phase=_clean(state.complete.get("status")),
            message=_clean(state.complete.get("message")) or "Proxbox sync did not complete.",
        )
    ]


def _job_error_entries(job: dict[str, Any]) -> list[SyncErrorEntry]:
    entries: list[SyncErrorEntry] = []
    job_error = job.get("error")
    if job_error:
        entries.append(
            SyncErrorEntry(
                source="job",
                phase=_status_value(job.get("status")),
                message="NetBox job error",
                detail=_clean(job_error),
            )
        )
    log_entries = job.get("log_entries")
    if isinstance(log_entries, list):
        for entry in log_entries:
            if isinstance(entry, dict) and _is_error_log(entry):
                entries.append(_error_from_log_entry(entry))
    return entries


def _error_from_log_entry(entry: dict[str, Any]) -> SyncErrorEntry:
    raw_data = entry.get("data")
    data: dict[str, Any] = raw_data if isinstance(raw_data, dict) else {}
    message = (
        entry.get("message")
        or entry.get("text")
        or entry.get("log")
        or data.get("message")
        or data.get("error")
    )
    return SyncErrorEntry(
        source="job-log",
        phase=_clean(entry.get("phase") or entry.get("grouping") or data.get("phase")),
        item=_clean(entry.get("object_repr") or data.get("item")),
        category=_clean(entry.get("category") or data.get("category") or entry.get("level")),
        message=_clean(message) or json.dumps(entry, sort_keys=True, default=str),
        detail=_clean(entry.get("detail") or data.get("detail")),
        suggestion=_clean(data.get("suggestion")),
        traceback=_clean(entry.get("traceback") or data.get("traceback")),
    )


def _is_error_log(entry: dict[str, Any]) -> bool:
    for key in ("level", "log_level", "status"):
        value = _clean(entry.get(key)).casefold()
        if value in {"error", "errored", "failed", "failure", "critical", "exception"}:
            return True
    return bool(entry.get("error"))


def _dedupe_errors(entries: list[SyncErrorEntry]) -> list[SyncErrorEntry]:
    seen: set[tuple[str, str, str, str, str]] = set()
    deduped: list[SyncErrorEntry] = []
    for entry in entries:
        key = (entry.phase, entry.item, entry.category, entry.message, entry.detail)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(entry)
    return deduped


def _merged_summary(state: RenderState, job: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = dict(state.summaries)
    data = job.get("data")
    if isinstance(data, dict):
        for key in ("summary", "result", "results"):
            value = data.get(key)
            if isinstance(value, dict):
                summary.setdefault("job", value)
                break
        else:
            numeric_counts = {
                key: value
                for key, value in data.items()
                if isinstance(value, int | float) and not isinstance(value, bool)
            }
            if numeric_counts:
                summary.setdefault("job", numeric_counts)
    return summary


def _live_renderable(state: RenderState) -> Group:
    return Group(
        _header_panel(state),
        _progress_panel(state),
        _recent_events_panel(state),
    )


def _header_panel(state: RenderState) -> Panel:
    grid = Table.grid(expand=True)
    grid.add_column(style="bold cyan", no_wrap=True)
    grid.add_column()
    grid.add_row("Job", str(state.job_id))
    grid.add_row("Endpoint", state.endpoint_label)
    grid.add_row("Types", ", ".join(state.sync_types))
    if state.schedule_message:
        grid.add_row("Message", state.schedule_message)
    return Panel(grid, title="Proxbox Sync", border_style="cyan")


def _progress_panel(state: RenderState) -> Panel:
    if not state.progress:
        return Panel(Text("Waiting for progress frames...", style="dim"), title="Progress")
    progress = Progress(
        TextColumn("[bold]{task.fields[phase]}"),
        BarColumn(bar_width=None),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        expand=True,
    )
    for phase, snapshot in state.progress.items():
        total = max(snapshot.total, 1)
        completed = min(max(snapshot.current, 0), total)
        if snapshot.percent is not None and snapshot.current == 0:
            total = 100
            completed = min(max(int(snapshot.percent), 0), 100)
        progress.add_task(
            snapshot.message or snapshot.status or phase,
            total=total,
            completed=completed,
            phase=phase,
        )
    return Panel(progress, title="Progress", border_style="blue")


def _recent_events_panel(state: RenderState) -> Panel:
    if not state.recent_events:
        return Panel(Text("No stream events yet.", style="dim"), title="Recent Events")
    return Panel(Group(*state.recent_events), title="Recent Events", border_style="magenta")


def _render_final_result(result: dict[str, Any], *, queued: bool) -> None:
    if result["ok"]:
        content_items: list[Any] = [
            Text("Proxbox sync completed successfully.", style="bold green"),
            _summary_table(result["summary"]),
        ]
        if result["warnings"]:
            content_items.append(_warning_table(result["warnings"]))
        console.print(Panel(Group(*content_items), title="Success", border_style="green"))
        return

    if queued:
        console.print(
            Panel(
                Text(
                    "The job is still queued and no worker picked it up before the stream ended.",
                    style="bold yellow",
                ),
                title="Job Still Queued",
                border_style="yellow",
            )
        )
    if result["warnings"]:
        console.print(_warning_table(result["warnings"]))
    errors = result["errors"] or [
        {
            "source": "job",
            "phase": result["status"],
            "item": "",
            "category": "",
            "message": "Proxbox sync failed without a structured error.",
            "detail": "",
            "suggestion": "",
            "traceback": "",
        }
    ]
    table = Table(title="Proxbox Sync Errors", show_header=True, header_style="bold red")
    table.add_column("Phase", style="red", overflow="fold")
    table.add_column("Item", overflow="fold")
    table.add_column("Category", overflow="fold")
    table.add_column("Message", overflow="fold", ratio=2)
    table.add_column("Detail", overflow="fold", ratio=2)
    for entry in errors:
        table.add_row(
            _clean(entry.get("phase")),
            _clean(entry.get("item")),
            _clean(entry.get("category")),
            _clean(entry.get("message")),
            _clean(entry.get("detail") or entry.get("suggestion") or entry.get("traceback")),
        )
    console.print(table)


def _warning_table(warnings: list[dict[str, Any]]) -> Table:
    table = Table(title="Proxbox Sync Warnings", show_header=True, header_style="bold yellow")
    table.add_column("Source", style="yellow", overflow="fold")
    table.add_column("Message", overflow="fold", ratio=2)
    table.add_column("Detail", overflow="fold", ratio=2)
    for entry in warnings:
        table.add_row(
            _clean(entry.get("source")),
            _clean(entry.get("message")),
            _clean(entry.get("detail") or entry.get("suggestion")),
        )
    return table


def _summary_table(summary: dict[str, Any]) -> Table:
    table = Table(show_header=True, header_style="bold green")
    table.add_column("Phase", style="cyan", no_wrap=True)
    table.add_column("Counts", overflow="fold")
    if not summary:
        table.add_row("job", "No result counts reported.")
        return table
    for phase, counts in summary.items():
        table.add_row(str(phase), _compact_counts(counts))
    return table


def _render_cli_exception(exc: Exception, *, json_output: bool) -> None:
    if json_output:
        payload = {
            "job_id": getattr(exc, "job_id", None),
            "status": "error",
            "ok": False,
            "errors": [
                {
                    "source": exc.__class__.__name__,
                    "phase": "",
                    "item": "",
                    "category": "",
                    "message": _exception_message(exc),
                    "detail": "",
                    "suggestion": "",
                    "traceback": "",
                }
            ],
            "warnings": [],
            "summary": {},
        }
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
        return

    style = "red"
    title = "Proxbox Sync Error"
    if isinstance(exc, ProxboxSyncError) and exc.status == 403:
        style = "yellow"
        title = "Permission Denied"
    console.print(
        Panel(Text(_exception_message(exc), style=style), title=title, border_style=style)
    )


def _exception_message(exc: Exception) -> str:
    if isinstance(exc, RequestError):
        body = exc.response.text.strip()
        return body or str(exc)
    return str(exc)


def _event_style(frame: SseFrame) -> str:
    if frame.event in {"error", "error_detail"}:
        return "bold red"
    if frame.event == "complete":
        return "bold green" if frame.data.get("ok") else "bold red"
    if frame.event == "discovery":
        return "cyan"
    if frame.event == "substep":
        return "blue"
    if frame.event == "phase_summary":
        return "green"
    if frame.event == "step":
        return "magenta dim"
    if frame.event == "item_progress":
        return "red" if frame.data.get("error") else "green" if frame.data.get("status") else ""
    return ""


def _frame_phase(frame: SseFrame) -> str:
    return _clean(frame.data.get("phase") or frame.data.get("step") or frame.event)


def _frame_message(frame: SseFrame) -> str:
    data = frame.data
    for key in ("message", "error", "warning", "detail", "status"):
        value = data.get(key)
        if value:
            return _clean(value)
    return ""


def _error_from_frame(frame: SseFrame, *, message_key: str = "message") -> SyncErrorEntry:
    data = frame.data
    item = data.get("item")
    return SyncErrorEntry(
        source=frame.event,
        phase=_frame_phase(frame),
        item=_item_label(item),
        category=_clean(data.get("category")),
        message=_clean(data.get(message_key) or data.get("message") or data.get("error")),
        detail=_clean(data.get("detail")),
        suggestion=_clean(data.get("suggestion")),
        traceback=_clean(data.get("traceback")),
    )


def _item_label(item: Any) -> str:
    if isinstance(item, dict):
        for key in ("name", "display", "item_type", "netbox_id", "id"):
            value = item.get(key)
            if value:
                return _clean(value)
        return _clean(item)
    return _clean(item)


def _compact_counts(value: Any) -> str:
    if isinstance(value, dict):
        parts = [f"{key}={_clean(val)}" for key, val in value.items()]
        return ", ".join(parts) if parts else "{}"
    return _clean(value)


def _status_value(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("value", "label", "name"):
            if value.get(key):
                return _clean(value[key]).casefold()
        return ""
    return _clean(value).casefold()


def _clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return sanitize_terminal_text(value)
    if isinstance(value, dict | list):
        return sanitize_terminal_text(json.dumps(value, sort_keys=True, default=str))
    return sanitize_terminal_text(str(value))


def _int_value(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float_value(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


_register_proxbox_resource_commands(proxbox_app)

# The catalog builds its own sub-Typers from `command_parts`, and Typer would
# silently accept a second sub-app under the same name — the job commands would
# just stop resolving. Fail at import instead if the catalog ever grows a "jobs"
# branch, rather than shipping a command tree with a shadowed group.
if any(spec.command_parts[:1] == ("jobs",) for spec in proxbox_resources()):
    raise RuntimeError(
        "The Proxbox resource catalog now defines a 'jobs' command group, which "
        "would shadow 'nbx proxbox jobs'. Rename one of them."
    )
proxbox_app.add_typer(jobs_app, name="jobs")


__all__ = [
    "RenderState",
    "frame_to_line",
    "jobs_app",
    "proxbox_app",
    "render_frame",
]
