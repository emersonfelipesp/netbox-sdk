"""SDK helpers for retrieving netbox-proxbox synchronization job records.

netbox-proxbox does not own a job model. A Proxbox sync is a **core NetBox
``core.Job`` row** whose ``data`` carries a ``proxbox_sync`` block::

    {"proxbox_sync": {"params": {"sync_types": ["all"],
                                 "proxmox_endpoint_ids": ["5", "11"], ...},
                      "runtime_seconds": 12.3,
                      "response": {...}}}

``GET /api/core/jobs/`` serialises every field an operator needs, and filters
server-side on ``status``, ``name``, ``queue_name``, ``user``, ``object_type``,
``object_id``, ``id``, ``interval`` and the four timestamp fields — but it
cannot filter on ``data``. So every Proxbox-specific predicate is evaluated
here, client-side, over a **bounded** scan of the server-filtered list.

Two properties of that split drive the design:

* **Unknown query parameters are silently ignored by NetBox.** A misspelled
  filter name does not error — it simply disappears, and the request returns
  *every* job. Every parameter this module sends is therefore drawn from
  :data:`SERVER_PARAM_WHITELIST`, and :meth:`ProxboxJobFilters.server_query`
  refuses to emit anything outside it.
* **The scan has to be bounded and say so.** ``log_entries`` ride along on every
  list row, so a page of 100 jobs is hundreds of kilobytes. Listing always
  reports how many rows were scanned and whether the scan was cut short; a
  truncated result must never be mistaken for an exhaustive one.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from math import isfinite
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from pydantic import BaseModel, ConfigDict, Field

from netbox_sdk.client import NetBoxApiClient
from netbox_sdk.exceptions import ContentError
from netbox_sdk.proxbox_sync import (
    SYNC_TYPE_VALUES,
    ProxboxSyncError,
    SyncType,
)

# --------------------------------------------------------------------------
# Parity constants — mirrored from netbox_proxbox
# --------------------------------------------------------------------------
# These reproduce ``netbox_proxbox.jobs.is_proxbox_sync_job`` so the CLI lists
# exactly the rows the plugin's own "Sync Jobs" page lists. They are duplicated
# rather than imported because the SDK never depends on the plugin being
# installed locally; ``tests/test_proxbox_jobs.py`` pins the behaviour with a
# row matrix rather than trusting the four branches were transcribed correctly.

#: ``job.data`` key written by ``ProxboxSyncJob.enqueue``.
PROXBOX_SYNC_DATA_KEY = "proxbox_sync"

#: ``ProxboxSyncJob.Meta.name`` — the default job label.
PROXBOX_DEFAULT_JOB_NAME = "Proxbox Sync"

#: Legacy dedicated RQ queue; any row on it is a Proxbox sync.
PROXBOX_LEGACY_QUEUE_NAME = "netbox_proxbox.sync"

#: NetBox's shared default queue, which Proxbox syncs use today. On its own it
#: is not a discriminator — it only counts alongside the default name.
PROXBOX_DEFAULT_QUEUE_NAME = "default"

#: Queue names accepted alongside an exact default-name match. The empty string
#: is the plugin's ``queue_name or ""`` normalisation of a null queue.
PROXBOX_DEFAULT_NAME_QUEUES: frozenset[str] = frozenset(
    {"", PROXBOX_DEFAULT_QUEUE_NAME, PROXBOX_LEGACY_QUEUE_NAME}
)

#: Targeted single-VM sync job names.
TARGETED_VM_JOB_NAME_RE = re.compile(r"^Proxbox Sync: Virtual machine (\d+)$")

#: Dependency order the plugin runs stages in, mirrored from
#: ``sync_types._SYNC_STAGE_ORDER``. :func:`normalize_sync_types` returns
#: survivors in this order so its output matches the plugin's for the same input.
SYNC_STAGE_ORDER: tuple[str, ...] = (
    SyncType.DEVICES.value,
    SyncType.STORAGE.value,
    SyncType.VIRTUAL_MACHINES.value,
    SyncType.TASK_HISTORY.value,
    SyncType.VM_DISKS.value,
    SyncType.VM_BACKUPS.value,
    SyncType.VM_SNAPSHOTS.value,
    SyncType.NETWORK_INTERFACES.value,
    SyncType.VM_INTERFACES.value,
    SyncType.IP_ADDRESSES.value,
    SyncType.SDN.value,
    SyncType.REPLICATIONS.value,
    SyncType.BACKUP_ROUTINES.value,
)

SYNC_STAGE_ORDER_INDEX: dict[str, int] = {
    slug: index for index, slug in enumerate(SYNC_STAGE_ORDER)
}

#: Stages a targeted single-VM sync runs, mirrored from the plugin's
#: ``sync_types._TARGETED_VM_SYNC_TYPES``. Used to rebuild the params a legacy
#: targeted job row never wrote.
TARGETED_VM_SYNC_TYPES: tuple[str, ...] = (
    SyncType.VIRTUAL_MACHINES.value,
    SyncType.VM_BACKUPS.value,
    SyncType.VM_SNAPSHOTS.value,
)

#: Core ``JobStatusChoices`` values (NetBox 4.3 – 4.7).
JOB_STATUS_VALUES: tuple[str, ...] = (
    "pending",
    "scheduled",
    "running",
    "completed",
    "errored",
    "failed",
)

#: Statuses that mean the run is over.
JOB_TERMINAL_STATUSES: frozenset[str] = frozenset({"completed", "errored", "failed"})

#: Statuses that mean the run is over and did not succeed.
JOB_FAILURE_STATUSES: tuple[str, ...] = ("errored", "failed")

#: Timestamp fields a relative window (``--since``/``--until``) can target.
JOB_DATE_FIELDS: tuple[str, ...] = ("created", "scheduled", "started", "completed")

#: Core job list endpoint.
JOBS_LIST_PATH = "/api/core/jobs/"

#: Plugin inventory endpoints used to resolve ``--cluster`` / ``--node``.
PROXMOX_CLUSTERS_PATH = "/api/plugins/proxbox/proxmox-clusters/"
PROXMOX_NODES_PATH = "/api/plugins/proxbox/proxmox-nodes/"

#: Every query parameter this module is allowed to send to ``/api/core/jobs/``.
#:
#: NetBox ignores unknown parameters instead of rejecting them, so an
#: unwhitelisted (or misspelled) name would silently widen the query to the
#: whole job table. Emission is checked against this set at build time.
SERVER_PARAM_WHITELIST: frozenset[str] = frozenset(
    {
        "id",
        "limit",
        "offset",
        "ordering",
        "status",
        "name",
        "name__ic",
        "queue_name",
        "job_id",
        "object_type",
        "object_id",
        "interval__empty",
        "created__after",
        "created__before",
        "scheduled__after",
        "scheduled__before",
        "started__after",
        "started__before",
        "completed__after",
        "completed__before",
    }
)

#: Only an ASCII, optionally signed integer, bounded in length so a
#: pathological digit string cannot hit CPython's int-conversion limit.
_ASCII_INTEGER_RE = re.compile(r"[+-]?[0-9]{1,18}")

_RELATIVE_WINDOW_RE = re.compile(r"^(?P<value>\d+)\s*(?P<unit>[smhdw])$", re.IGNORECASE)
_RELATIVE_UNITS: dict[str, str] = {
    "s": "seconds",
    "m": "minutes",
    "h": "hours",
    "d": "days",
    "w": "weeks",
}

#: Default look-back applied when the caller names no window at all.
DEFAULT_WINDOW = "30d"

#: Default ceiling on rows pulled out of ``/api/core/jobs/`` for one listing.
DEFAULT_MAX_SCAN = 5000

#: Default rows per request. Core job rows carry their full ``log_entries``,
#: so a page of 100 is already several hundred kilobytes.
DEFAULT_PAGE_SIZE = 100

_MAX_PAGES = 1000


def _reconcile_exhausted_scan(result: ProxboxJobListResult) -> ProxboxJobListResult:
    """Check a scan that believes it finished against the count it started with.

    Repeated pages and repeated job ids catch drift that *duplicates* a row, but
    not drift that *removes* one: delete a row that an earlier page already
    returned and every later offset shifts back by one, so a different row is
    stepped over entirely. Nothing repeats, so nothing looked wrong — and the
    listing claimed to be complete while missing a job.

    The server's own ``count`` from the first page is the cheap check. Fewer
    rows seen than advertised means the list moved underneath the scan.
    """
    expected = result.total_available
    if expected is None or result.scanned >= expected:
        return result
    result.truncated = True
    result.truncation_reason = (
        f"the job list shifted during the scan (NetBox advertised {expected} matching "
        f"core job rows but only {result.scanned} were returned, so at least one was "
        "stepped over); results may be incomplete — re-run with a narrower window"
    )
    return result


def _mark_scan_truncated(result: ProxboxJobListResult, max_scan: int) -> ProxboxJobListResult:
    result.truncated = True
    result.truncation_reason = (
        f"scan limit of {max_scan} core job rows reached; "
        "narrow the window or filters, or raise --max-scan"
    )
    return result


def _canonical_query_key(query: Mapping[str, Any] | None) -> str:
    """Stable identity for a page request, used to detect a repeated page."""
    if not query:
        return ""
    parts: list[str] = []
    for key in sorted(query):
        value = query[key]
        if isinstance(value, list):
            parts.append(f"{key}={','.join(str(item) for item in value)}")
        else:
            parts.append(f"{key}={value}")
    return "&".join(parts)


def _query_from_next_url(query_string: str) -> dict[str, Any] | None:
    """Parse a pagination ``next`` query string, preserving repeated keys.

    ``dict(parse_qsl(...))`` keeps only the last value per key, so a pushed-down
    ``status=errored&status=failed`` would silently narrow to ``status=failed``
    from page two onward — page one filtered on one thing and every later page
    on another, with no error anywhere. This repository has already been bitten
    by exactly that shape in plugin discovery (``?tag=a&tag=b`` collapsing to
    ``tag=b``), so repeated keys are folded into list values instead.
    """
    parsed: dict[str, Any] = {}
    for key, value in parse_qsl(query_string, keep_blank_values=True):
        if key not in parsed:
            parsed[key] = value
        elif isinstance(parsed[key], list):
            parsed[key].append(value)
        else:
            parsed[key] = [parsed[key], value]
    return parsed or None


class ProxboxJobFilterError(ValueError):
    """Raised when a caller supplies an unusable Proxbox job filter."""


# --------------------------------------------------------------------------
# Record models
# --------------------------------------------------------------------------


def _as_mapping(value: Any) -> dict[str, Any]:
    """Return ``value`` as a plain dict, or an empty dict for anything else."""
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


class ScopeState(StrEnum):
    """How much a job's recorded scope list can be trusted.

    A scope filter (``--endpoint``, ``--type``, ``--vm``) has to distinguish
    four cases that a plain list cannot:

    * ``ABSENT`` — the key was never written. For endpoints and sync types the
      plugin's own default applies, which is "everything".
    * ``EMPTY`` — the key is present and explicitly empty, which the schedule
      API writes to mean "every endpoint".
    * ``VALID`` — usable values were recorded.
    * ``INVALID`` — the key is present but its content cannot be read.

    ``INVALID`` must not collapse into ``EMPTY``. It did in the first cut, and
    the consequence was concrete: ``proxmox_endpoint_ids: [{"id": 5}]`` parsed
    to ``[]``, which reads as "all endpoints", so a job scoped to one endpoint
    matched a query for a completely different one. A scope that cannot be read
    is not a scope that covers everything — scoped filters fail closed on it.
    """

    ABSENT = "absent"
    EMPTY = "empty"
    VALID = "valid"
    INVALID = "invalid"


def _parse_scope(container: Mapping[str, Any], key: str) -> tuple[list[str], ScopeState]:
    """Read one scope list out of a params block, classifying what was found."""
    if key not in container:
        return [], ScopeState.ABSENT
    raw = container[key]
    if raw is None:
        # A present `null` is not a missing key. The plugin only ever writes
        # lists, so a null is a malformed value, and reading it as "the default"
        # would let `proxmox_endpoint_ids: null` match every endpoint query.
        return [], ScopeState.INVALID
    if isinstance(raw, bool) or isinstance(raw, Mapping):
        # A mapping is not a list of ids. An earlier version took its keys,
        # which turned `{"all": false}` into `["all"]` — reading a negation as
        # an assertion.
        return [], ScopeState.INVALID
    if isinstance(raw, str | int | float):
        text = str(raw).strip()
        return ([text], ScopeState.VALID) if text else ([], ScopeState.INVALID)
    if isinstance(raw, Iterable):
        elements = list(raw)
        if not elements:
            return [], ScopeState.EMPTY
        items: list[str] = []
        for item in elements:
            if isinstance(item, str | int | float) and not isinstance(item, bool):
                text = str(item).strip()
                if text:
                    items.append(text)
        if len(items) != len(elements):
            # Partially unreadable is still unreadable: acting on the half that
            # parsed would answer a scope question with incomplete evidence.
            return items, ScopeState.INVALID
        return items, ScopeState.VALID
    return [], ScopeState.INVALID


def _as_str_list(value: Any) -> list[str]:
    """Coerce a JSON value into a list of non-empty strings, tolerantly.

    Used where only the values matter and their trustworthiness does not (batch
    object ids). Scope lists go through :func:`_parse_scope` instead.
    """
    if value is None or isinstance(value, bool) or isinstance(value, Mapping):
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, int | float):
        return [str(value)]
    if isinstance(value, Iterable):
        items: list[str] = []
        for item in value:
            if isinstance(item, str | int | float) and not isinstance(item, bool):
                text = str(item).strip()
                if text:
                    items.append(text)
        return items
    return []


def _as_optional_str(value: Any) -> str | None:
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, int | float) and not isinstance(value, bool):
        return str(value)
    return None


def _as_optional_int(value: Any) -> int | None:
    """Read an integer out of untrusted JSON without ever raising.

    ``json.loads("1e400")`` is valid JSON and yields ``inf``; ``int(inf)``
    raises ``OverflowError``, which would abort an entire listing over one bad
    row. Non-finite and non-integral floats are therefore rejected rather than
    converted.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not isfinite(value) or value != int(value):
            return None
        return int(value)
    if isinstance(value, str):
        # `str.isdigit()` is true for characters like "²", which `int()` then
        # refuses, and CPython caps int(str) conversion length — both raise out
        # of what is contracted to be a total parser. Match an ASCII grammar and
        # still guard the conversion.
        text = value.strip()
        if _ASCII_INTEGER_RE.fullmatch(text):
            try:
                return int(text)
            except ValueError:
                return None
    return None


def _as_optional_float(value: Any) -> float | None:
    """Read a float out of untrusted JSON without raising or yielding infinity.

    A JSON integer can be large enough that ``float()`` raises ``OverflowError``,
    and ``1e400`` parses to ``inf`` — which would then be serialised by ``--json``
    as the non-standard literal ``Infinity``. Both are refused.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        try:
            result = float(value)
        except (OverflowError, ValueError):
            return None
        return result if isfinite(result) else None
    if isinstance(value, str):
        try:
            result = float(value.strip())
        except (OverflowError, ValueError):
            return None
        return result if isfinite(result) else None
    return None


def _choice_value(value: Any) -> str:
    """Read a NetBox ``{"value": ..., "label": ...}`` choice, or a bare string."""
    if isinstance(value, Mapping):
        return _as_optional_str(value.get("value")) or ""
    return _as_optional_str(value) or ""


def _choice_label(value: Any) -> str:
    if isinstance(value, Mapping):
        return _as_optional_str(value.get("label")) or _choice_value(value)
    return _as_optional_str(value) or ""


class ProxboxSyncJobParams(BaseModel):
    """The ``data['proxbox_sync']['params']`` block, parsed defensively."""

    sync_types: list[str] = Field(default_factory=list)
    proxmox_endpoint_ids: list[str] = Field(default_factory=list)
    netbox_endpoint_ids: list[str] = Field(default_factory=list)
    netbox_vm_ids: list[str] = Field(default_factory=list)
    batch_object_type: str | None = None
    batch_object_ids: list[str] = Field(default_factory=list)
    fastapi_endpoint_id: int | None = None
    run_id: str | None = None
    sync_type_scope: ScopeState = ScopeState.ABSENT
    endpoint_scope: ScopeState = ScopeState.ABSENT
    vm_scope: ScopeState = ScopeState.ABSENT
    inferred: bool = False

    @classmethod
    def from_block(cls, block: Any) -> ProxboxSyncJobParams:
        """Parse a ``params`` block of any shape into a params model.

        Every branch degrades rather than raising: this data comes from a
        NetBox instance the SDK does not control, and a malformed row must
        still be listed — its core fields are still meaningful — instead of
        killing the whole listing. What it must *not* do is let unreadable
        content pass as a meaningful value, which is what the scope states
        record.
        """
        params = _as_mapping(block)
        sync_types, sync_scope = _parse_scope(params, "sync_types")
        if sync_scope in {ScopeState.ABSENT, ScopeState.EMPTY}:
            # Rows written by older plugin versions carry the singular key.
            legacy, legacy_scope = _parse_scope(params, "sync_type")
            if legacy_scope is ScopeState.VALID:
                sync_types, sync_scope = legacy, legacy_scope
        endpoint_ids, endpoint_scope = _parse_scope(params, "proxmox_endpoint_ids")
        vm_ids, vm_scope = _parse_scope(params, "netbox_vm_ids")
        netbox_endpoint_ids, _ = _parse_scope(params, "netbox_endpoint_ids")
        return cls(
            sync_types=sync_types,
            proxmox_endpoint_ids=endpoint_ids,
            netbox_endpoint_ids=netbox_endpoint_ids,
            netbox_vm_ids=vm_ids,
            batch_object_type=_as_optional_str(params.get("batch_object_type")),
            batch_object_ids=_as_str_list(params.get("batch_object_ids")),
            fastapi_endpoint_id=_as_optional_int(params.get("fastapi_endpoint_id")),
            run_id=_as_optional_str(params.get("run_id")),
            sync_type_scope=sync_scope,
            endpoint_scope=endpoint_scope,
            vm_scope=vm_scope,
        )

    @classmethod
    def for_targeted_vm(
        cls,
        vm_id: str,
        *,
        fastapi_endpoint_id: int | None = None,
        endpoint_scope: ScopeState = ScopeState.EMPTY,
        proxmox_endpoint_ids: list[str] | None = None,
    ) -> ProxboxSyncJobParams:
        """Rebuild the params a legacy targeted single-VM job never recorded.

        Rows named ``Proxbox Sync: Virtual machine <id>`` predate the params
        block, so their `data` is empty. The plugin reconstructs them the same
        way in ``sync_params._infer_targeted_vm_job_params`` — the VM id from
        the name and the three targeted stages — and without mirroring that,
        ``--vm <id>`` would miss the very job that targeted that VM while
        ``--type storage`` would wrongly match it through the "no recorded
        types means all" rule.
        """
        return cls(
            sync_types=list(TARGETED_VM_SYNC_TYPES),
            netbox_vm_ids=[vm_id],
            proxmox_endpoint_ids=list(proxmox_endpoint_ids or []),
            fastapi_endpoint_id=fastapi_endpoint_id,
            sync_type_scope=ScopeState.VALID,
            endpoint_scope=endpoint_scope,
            vm_scope=ScopeState.VALID,
            inferred=True,
        )

    @property
    def targets_all_endpoints(self) -> bool:
        """True when the run covered every endpoint (none named, none broken)."""
        return self.endpoint_scope in {ScopeState.ABSENT, ScopeState.EMPTY}

    @property
    def endpoint_ids(self) -> tuple[int, ...]:
        """Numeric Proxmox endpoint PKs, ignoring anything non-numeric."""
        ids: list[int] = []
        for value in self.proxmox_endpoint_ids:
            parsed = _as_optional_int(value)
            if parsed is not None:
                ids.append(parsed)
        return tuple(ids)

    def covers_sync_type(self, sync_type: str) -> bool:
        """True when this run included ``sync_type``.

        A job recorded as ``["all"]`` ran every stage, so it covers any
        requested type. A job with no recorded types is treated the same way —
        the plugin's own default is ``all``, and hiding such rows would
        silently drop them from a type-scoped query. A job whose recorded types
        cannot be read answers **no**: an unreadable scope is not a universal
        one.
        """
        wanted = sync_type.strip()
        if not wanted:
            return False
        if self.sync_type_scope is ScopeState.INVALID:
            return False
        if not self.sync_types:
            return True
        if SyncType.ALL.value in self.sync_types:
            return True
        return wanted in self.sync_types

    def covers_endpoint(self, endpoint_id: int) -> bool:
        """True when this run covered the Proxmox endpoint ``endpoint_id``.

        An absent or explicitly empty ``proxmox_endpoint_ids`` means "every
        endpoint" — that is what the schedule API stores when the caller names
        none. An unreadable one means nothing can be concluded, so it matches
        no endpoint-scoped query rather than all of them.
        """
        if self.endpoint_scope is ScopeState.INVALID:
            return False
        if self.targets_all_endpoints:
            return True
        return endpoint_id in self.endpoint_ids

    def covers_vm(self, vm_id: str) -> bool:
        """True when this run targeted the NetBox virtual machine ``vm_id``."""
        if self.vm_scope is ScopeState.INVALID:
            return False
        return vm_id in self.netbox_vm_ids


class ProxboxSyncJobRecord(BaseModel):
    """One Proxbox sync job: the core ``Job`` row plus its parsed sync block."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str = ""
    status: str = ""
    status_label: str = ""
    created: str | None = None
    scheduled: str | None = None
    started: str | None = None
    completed: str | None = None
    interval: int | None = None
    user: str | None = None
    queue_name: str = ""
    rq_job_id: str | None = None
    error: str = ""
    object_type: str | None = None
    object_id: int | None = None
    params: ProxboxSyncJobParams = Field(default_factory=ProxboxSyncJobParams)
    runtime_seconds: float | None = None
    response: dict[str, Any] | None = None
    log_entries: list[dict[str, Any]] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> ProxboxSyncJobRecord:
        """Build a record from a ``/api/core/jobs/`` row, tolerating any shape."""
        data = _as_mapping(row.get("data"))
        block = _as_mapping(data.get(PROXBOX_SYNC_DATA_KEY))
        user = row.get("user")
        user_name = (
            _as_optional_str(user.get("username")) or _as_optional_str(user.get("display"))
            if isinstance(user, Mapping)
            else _as_optional_str(user)
        )
        object_type = row.get("object_type")
        # `log_entries: 5` is truthy and not iterable; iterating it raised
        # TypeError and took the whole listing down over one bad row.
        raw_log_entries = row.get("log_entries")
        log_entries = (
            [_as_mapping(entry) for entry in raw_log_entries if isinstance(entry, Mapping)]
            if isinstance(raw_log_entries, list)
            else []
        )
        job_id = _as_optional_int(row.get("id"))
        if job_id is None:
            raise ProxboxJobFilterError("Core job row is missing a numeric 'id'")
        name = _as_optional_str(row.get("name")) or ""
        return cls(
            id=job_id,
            name=name,
            status=_choice_value(row.get("status")),
            status_label=_choice_label(row.get("status")),
            created=_as_optional_str(row.get("created")),
            scheduled=_as_optional_str(row.get("scheduled")),
            started=_as_optional_str(row.get("started")),
            completed=_as_optional_str(row.get("completed")),
            interval=_as_optional_int(row.get("interval")),
            user=user_name,
            queue_name=_as_optional_str(row.get("queue_name")) or "",
            rq_job_id=_as_optional_str(row.get("job_id")),
            error=_as_optional_str(row.get("error")) or "",
            object_type=_as_optional_str(object_type)
            if not isinstance(object_type, Mapping)
            else _as_optional_str(object_type.get("value")),
            object_id=_as_optional_int(row.get("object_id")),
            params=_params_for_row(name, block),
            runtime_seconds=_as_optional_float(block.get("runtime_seconds")),
            response=_as_mapping(block.get("response")) or None,
            log_entries=log_entries,
            raw=dict(row),
        )

    @property
    def is_failure(self) -> bool:
        return self.status in JOB_FAILURE_STATUSES

    @property
    def is_terminal(self) -> bool:
        return self.status in JOB_TERMINAL_STATUSES

    @property
    def is_recurring(self) -> bool:
        return self.interval is not None

    @property
    def sync_types_display(self) -> str:
        return ", ".join(self.params.sync_types) if self.params.sync_types else "all"

    @property
    def endpoints_display(self) -> str:
        """Human label for the run's Proxmox endpoint scope (``all`` when open)."""
        if self.params.targets_all_endpoints:
            return "all"
        return ", ".join(self.params.proxmox_endpoint_ids)

    @property
    def log_entry_count(self) -> int:
        return len(self.log_entries)

    def summary_row(self) -> dict[str, Any]:
        """Flat, JSON-safe projection used by table rendering and ``--json``."""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "status_label": self.status_label,
            "created": self.created,
            "scheduled": self.scheduled,
            "started": self.started,
            "completed": self.completed,
            "interval": self.interval,
            "user": self.user,
            "queue_name": self.queue_name,
            "rq_job_id": self.rq_job_id,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "sync_types": list(self.params.sync_types),
            "proxmox_endpoint_ids": list(self.params.proxmox_endpoint_ids),
            "netbox_endpoint_ids": list(self.params.netbox_endpoint_ids),
            "netbox_vm_ids": list(self.params.netbox_vm_ids),
            "batch_object_type": self.params.batch_object_type,
            "batch_object_ids": list(self.params.batch_object_ids),
            "fastapi_endpoint_id": self.params.fastapi_endpoint_id,
            "run_id": self.params.run_id,
            # Scope trust travels with the row: a consumer must be able to tell
            # "this run covered every endpoint" from "this run's endpoint list
            # could not be read", and a reconstructed legacy row from a
            # recorded one.
            "endpoint_scope": self.params.endpoint_scope.value,
            "sync_type_scope": self.params.sync_type_scope.value,
            "vm_scope": self.params.vm_scope.value,
            "params_inferred": self.params.inferred,
            "runtime_seconds": self.runtime_seconds,
            "error": self.error,
            "log_entry_count": self.log_entry_count,
        }

    def detail(self, *, include_logs: bool = True) -> dict[str, Any]:
        """Complete record, including the untouched core row."""
        payload = self.summary_row()
        payload["response"] = self.response
        payload["log_entries"] = list(self.log_entries) if include_logs else []
        payload["raw"] = self.raw
        return payload


def normalize_sync_types(values: Iterable[str]) -> list[str]:
    """Mirror the plugin's ``sync_types.normalize_sync_types``.

    Unknown slugs are dropped, duplicates collapse, ``all`` anywhere collapses
    the whole list to ``["all"]``, and nothing recognisable also means
    ``["all"]`` — the documented default. Survivors come back in the plugin's
    dependency order, not the order they happened to be recorded in.

    Used for the inference decision, so that ``["all", "storage"]`` reaches the
    same verdict here as it does in the plugin; an exact comparison against
    ``["all"]`` would not.
    """
    unique: list[str] = []
    seen: set[str] = set()
    for raw in values:
        slug = str(raw).strip()
        if slug not in SYNC_TYPE_VALUES or slug in seen:
            continue
        seen.add(slug)
        unique.append(slug)
    if not unique or SyncType.ALL.value in seen:
        return [SyncType.ALL.value]
    return sorted(unique, key=lambda slug: SYNC_STAGE_ORDER_INDEX.get(slug, 99))


def _params_for_row(name: str, block: Mapping[str, Any]) -> ProxboxSyncJobParams:
    """Parse a row's params, reconstructing them for a legacy targeted-VM job.

    A row named ``Proxbox Sync: Virtual machine <id>`` is a real, identifiable
    job whose scope is knowable from its name. Reading it as "no scope" would
    make ``--vm <id>`` miss it and ``--type <anything>`` match it.

    The trigger is the plugin's, transcribed from
    ``jobs.proxbox_sync_params_from_job``: the name matches, no VM ids were
    recorded, and the **normalized** sync types are the default ``["all"]``. It
    is deliberately *not* "the params block is missing" — a row can carry a
    params block recording only the default, and the plugin infers for it too.

    One place this refuses where the plugin cannot: a scope whose JSON shape is
    unreadable. The plugin only ever sees an already-parsed list, so it has no
    way to distinguish "recorded nothing" from "recorded something unreadable".
    Here that distinction exists, and reconstructing over corruption would
    present a guess as a record.
    """
    params = ProxboxSyncJobParams.from_block(block.get("params"))
    match = TARGETED_VM_JOB_NAME_RE.match(name.strip())
    if match is None or params.netbox_vm_ids:
        return params
    if ScopeState.INVALID in {params.vm_scope, params.sync_type_scope}:
        return params
    if normalize_sync_types(params.sync_types) != [SyncType.ALL.value]:
        return params
    # The backend pin outlives a replay, so it must survive reconstruction —
    # the plugin threads it through both return paths for the same reason.
    # The name tells us the VM and the stages; it says nothing about endpoints.
    # So an unreadable endpoint list has to survive reconstruction — replacing
    # it with "empty" would turn a scope we could not read into "all endpoints"
    # and hand every endpoint-scoped query a row it should never match.
    return ProxboxSyncJobParams.for_targeted_vm(
        match.group(1),
        fastapi_endpoint_id=params.fastapi_endpoint_id,
        endpoint_scope=params.endpoint_scope,
        proxmox_endpoint_ids=params.proxmox_endpoint_ids,
    )


def is_proxbox_sync_job(row: Mapping[str, Any]) -> bool:
    """True when a core job row is a Proxbox sync job.

    Parity with ``netbox_proxbox.jobs.is_proxbox_sync_job``: the ``data`` key,
    the legacy queue, the exact default name on an accepted queue, or a
    targeted single-VM job name. ``queue_name`` is normalised as
    ``queue_name or ""`` so a null queue still matches the default-name branch.
    """
    data = row.get("data")
    if isinstance(data, Mapping) and PROXBOX_SYNC_DATA_KEY in data:
        return True

    queue_name = _as_optional_str(row.get("queue_name")) or ""
    if queue_name == PROXBOX_LEGACY_QUEUE_NAME:
        return True

    name = (_as_optional_str(row.get("name")) or "").strip()
    if name == PROXBOX_DEFAULT_JOB_NAME and queue_name in PROXBOX_DEFAULT_NAME_QUEUES:
        return True
    return bool(TARGETED_VM_JOB_NAME_RE.match(name))


# --------------------------------------------------------------------------
# Time windows
# --------------------------------------------------------------------------


def parse_time_expression(value: str, *, now: datetime | None = None) -> str:
    """Normalise ``7d`` / ``24h`` / an ISO timestamp into an ISO-8601 UTC string.

    Args:
        value: Relative offset (``<int><s|m|h|d|w>``) or an ISO-8601 date or
            datetime. A relative offset is interpreted as "this long ago".
        now: Reference instant for relative offsets; defaults to UTC now.

    Returns:
        An ISO-8601 string with a ``Z`` suffix, suitable for NetBox's
        ``__after`` / ``__before`` filters.

    Raises:
        ProxboxJobFilterError: If the expression is neither form.
    """
    text = value.strip()
    if not text:
        raise ProxboxJobFilterError("Time expression cannot be empty")

    relative = _RELATIVE_WINDOW_RE.match(text)
    if relative is not None:
        amount = int(relative.group("value"))
        unit = _RELATIVE_UNITS[relative.group("unit").lower()]
        reference = now or datetime.now(UTC)
        moment = reference - timedelta(**{unit: amount})
        return _iso_utc(moment)

    candidate = text.replace(" ", "T", 1) if " " in text and "T" not in text else text
    if candidate.endswith("Z"):
        candidate = f"{candidate[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ProxboxJobFilterError(
            f"Unrecognized time expression {value!r}. Use a relative offset such as "
            "'24h', '7d', '2w' or an ISO-8601 timestamp such as '2026-08-21T00:00:00Z'."
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return _iso_utc(parsed)


def _iso_utc(moment: datetime) -> str:
    return moment.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_job_statuses(values: Iterable[str]) -> tuple[str, ...]:
    """Validate and de-duplicate core job status slugs."""
    normalized: list[str] = []
    unknown: list[str] = []
    for raw in values:
        text = str(raw).strip().lower()
        if not text:
            continue
        if text not in JOB_STATUS_VALUES:
            unknown.append(text)
        elif text not in normalized:
            normalized.append(text)
    if unknown:
        available = ", ".join(JOB_STATUS_VALUES)
        raise ProxboxJobFilterError(
            f"Unknown job status(es): {', '.join(unknown)}. Available: {available}"
        )
    return tuple(normalized)


def validate_sync_type_filters(values: Iterable[str]) -> tuple[str, ...]:
    """Validate sync-type slugs used as *filters*.

    Unlike :func:`netbox_sdk.proxbox_sync.validate_sync_types`, combining
    ``all`` with other values is allowed here: filters are a disjunction, not a
    scheduling request.
    """
    normalized: list[str] = []
    unknown: list[str] = []
    for raw in values:
        text = str(raw).strip()
        if not text:
            continue
        if text not in SYNC_TYPE_VALUES:
            unknown.append(text)
        elif text not in normalized:
            normalized.append(text)
    if unknown:
        available = ", ".join(SYNC_TYPE_VALUES)
        raise ProxboxJobFilterError(
            f"Unknown Proxbox sync type(s): {', '.join(unknown)}. Available: {available}"
        )
    return tuple(normalized)


def validate_date_field(value: str) -> str:
    """Validate the timestamp field a relative window applies to."""
    text = value.strip().lower()
    if text not in JOB_DATE_FIELDS:
        available = ", ".join(JOB_DATE_FIELDS)
        raise ProxboxJobFilterError(f"Unknown date field {value!r}. Available: {available}")
    return text


# --------------------------------------------------------------------------
# Filters
# --------------------------------------------------------------------------


class ProxboxJobFilters(BaseModel):
    """Every filter one ``nbx proxbox jobs list`` invocation can carry.

    Fields split cleanly in two: those NetBox can evaluate (emitted by
    :meth:`server_query`) and those that need ``data`` (evaluated by
    :meth:`matches`). Nothing is evaluated twice.
    """

    model_config = ConfigDict(frozen=True)

    # Server-side
    statuses: tuple[str, ...] = ()
    ids: tuple[int, ...] = ()
    name: str | None = None
    name_contains: str | None = None
    queue_name: str | None = None
    user: str | None = None
    rq_job_id: str | None = None
    object_type: str | None = None
    object_id: int | None = None
    created_after: str | None = None
    created_before: str | None = None
    scheduled_after: str | None = None
    scheduled_before: str | None = None
    started_after: str | None = None
    started_before: str | None = None
    completed_after: str | None = None
    completed_before: str | None = None
    ordering: str = "-created"

    # Client-side (need ``job.data``)
    sync_types: tuple[str, ...] = ()
    endpoint_ids: tuple[int, ...] = ()
    vm_ids: tuple[str, ...] = ()
    run_ids: tuple[str, ...] = ()
    batch_object_type: str | None = None
    recurring: bool | None = None
    errored_only: bool = False

    def server_query(self, *, page_size: int) -> dict[str, Any]:
        """Build the ``/api/core/jobs/`` query for the first page.

        Only names in :data:`SERVER_PARAM_WHITELIST` may be emitted. NetBox
        drops unknown parameters silently, so an unwhitelisted name would not
        fail loudly — it would quietly return the entire job table.
        """
        query: dict[str, Any] = {"limit": page_size, "ordering": self.ordering}
        if self.statuses:
            query["status"] = list(self.statuses)
        # `errored_only` deliberately pushes nothing. Narrowing to the failure
        # statuses would discard the rows it most needs: a run can finish
        # `completed` while recording a stage error, and that is exactly what an
        # operator is looking for. The check happens client-side in `matches`.
        if self.ids:
            query["id"] = [str(value) for value in self.ids]
        if self.name:
            query["name"] = self.name
        if self.name_contains:
            query["name__ic"] = self.name_contains
        if self.queue_name is not None:
            query["queue_name"] = self.queue_name
        # `user` is deliberately NOT pushed down. NetBox changed the filter's
        # type across the release lines this SDK supports — 4.5 declares
        # `/api/core/jobs/` `user` as an integer, 4.6 and 4.7 as an array of
        # usernames — so a username sent to a 4.5 instance is a validation
        # error, not a filter. Comparing client-side is the one behaviour that
        # is correct on every supported line.
        if self.rq_job_id:
            query["job_id"] = self.rq_job_id
        if self.object_type:
            query["object_type"] = self.object_type
        if self.object_id is not None:
            query["object_id"] = str(self.object_id)
        if self.recurring is not None:
            # ``interval__empty=true`` selects one-shot jobs; false selects
            # recurring ones. Recurrence lives on the core row, so it is pushed
            # down rather than filtered client-side.
            query["interval__empty"] = "false" if self.recurring else "true"
        for field_name in JOB_DATE_FIELDS:
            for bound in ("after", "before"):
                value = getattr(self, f"{field_name}_{bound}")
                if value:
                    query[f"{field_name}__{bound}"] = value

        unknown = sorted(set(query) - SERVER_PARAM_WHITELIST)
        if unknown:
            raise ProxboxJobFilterError(
                "Refusing to send non-whitelisted NetBox job filter(s): "
                f"{', '.join(unknown)}. NetBox ignores unknown query parameters, so "
                "sending one would silently return every job."
            )
        return query

    def matches(self, record: ProxboxSyncJobRecord) -> bool:
        """Apply the filters NetBox cannot evaluate to one parsed record."""
        if self.sync_types and not any(
            record.params.covers_sync_type(value) for value in self.sync_types
        ):
            return False
        if self.endpoint_ids and not any(
            record.params.covers_endpoint(value) for value in self.endpoint_ids
        ):
            return False
        if self.vm_ids and not any(record.params.covers_vm(value) for value in self.vm_ids):
            return False
        if self.user and (record.user or "").casefold() != self.user.casefold():
            return False
        if self.run_ids and record.params.run_id not in self.run_ids:
            return False
        if self.batch_object_type and record.params.batch_object_type != self.batch_object_type:
            return False
        if self.errored_only and not (record.is_failure or record.error):
            return False
        return True


class ProxboxJobScanWindow(BaseModel):
    """Every time bound a listing was actually run under.

    All of them, not one: a listing bounded on both ``created`` and
    ``completed`` is narrower than either bound alone, and a completeness
    envelope that names only one of them describes a scan that did not happen.
    """

    bounds: list[tuple[str, str, str]] = Field(default_factory=list)

    @classmethod
    def from_bounds(cls, bounds: Mapping[str, str | None]) -> ProxboxJobScanWindow:
        """Build a window from ``{"<field>_after": value, ...}`` filter bounds."""
        collected: list[tuple[str, str, str]] = []
        for field_name in JOB_DATE_FIELDS:
            for suffix, operator in (("after", ">="), ("before", "<=")):
                value = bounds.get(f"{field_name}_{suffix}")
                if value:
                    collected.append((field_name, operator, value))
        return cls(bounds=collected)

    @property
    def is_open(self) -> bool:
        return not self.bounds

    @property
    def fields(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(field_name for field_name, _, _ in self.bounds))

    def describe(self) -> str:
        if self.is_open:
            return "all time"
        return ", ".join(
            f"{field_name} {operator} {value}" for field_name, operator, value in self.bounds
        )


class ProxboxJobListResult(BaseModel):
    """A bounded listing plus the facts needed to judge its completeness."""

    jobs: list[ProxboxSyncJobRecord] = Field(default_factory=list)
    scanned: int = 0
    total_available: int | None = None
    truncated: bool = False
    truncation_reason: str | None = None
    window: ProxboxJobScanWindow = Field(default_factory=ProxboxJobScanWindow)

    @property
    def matched(self) -> int:
        return len(self.jobs)


class ProxboxJobsClient:
    """Read-only client for netbox-proxbox sync job records."""

    def __init__(
        self,
        client: NetBoxApiClient,
        *,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> None:
        if page_size < 1:
            raise ProxboxJobFilterError("page_size must be at least 1")
        self._client = client
        self._page_size = page_size

    @classmethod
    def from_client(
        cls, client: NetBoxApiClient, *, page_size: int = DEFAULT_PAGE_SIZE
    ) -> ProxboxJobsClient:
        return cls(client, page_size=page_size)

    async def list_jobs(
        self,
        filters: ProxboxJobFilters | None = None,
        *,
        limit: int | None = None,
        max_scan: int = DEFAULT_MAX_SCAN,
        window: ProxboxJobScanWindow | None = None,
    ) -> ProxboxJobListResult:
        """Scan the core job list and return the Proxbox sync jobs in it.

        Args:
            filters: Server-side and client-side filters to apply.
            limit: Stop once this many Proxbox jobs have matched. ``None``
                collects every match within the scan bound.
            max_scan: Hard ceiling on core job rows fetched. ``0`` disables it.
            window: Window description echoed back in the result. Purely for
                reporting; the actual bounds live in ``filters``.

        Returns:
            A :class:`ProxboxJobListResult` carrying the matches together with
            the number of rows scanned and whether the scan was cut short.
        """
        active = filters or ProxboxJobFilters()
        result = ProxboxJobListResult(window=window or ProxboxJobScanWindow())
        seen_core_job_ids: set[int] = set()
        visited_pages: set[tuple[str, str]] = set()

        path = JOBS_LIST_PATH
        query: dict[str, Any] | None = active.server_query(page_size=self._page_size)
        for _ in range(_MAX_PAGES):
            if max_scan:
                # Ask only for what the remaining budget can examine. Checking
                # the ceiling *after* decoding a full page made the bound
                # advisory: `--max-scan 1 --page-size 1000` still pulled a
                # thousand rows, each carrying its whole log history.
                remaining = max_scan - result.scanned
                if remaining <= 0:
                    return _mark_scan_truncated(result, max_scan)
                query = dict(query or {})
                query["limit"] = min(self._page_size, remaining)

            page_key = (path, _canonical_query_key(query))
            if page_key in visited_pages:
                # Offset pagination over a table that is still being written can
                # hand back a page already seen. Stopping and saying so beats
                # looping, and beats reporting a complete listing built from
                # duplicated rows.
                result.truncated = True
                result.truncation_reason = (
                    "the job list shifted during the scan (a page repeated); "
                    "results may be incomplete — re-run with a narrower window"
                )
                return result
            visited_pages.add(page_key)

            payload = await self._request_object("GET", path, query=query, action="job listing")
            if result.total_available is None:
                result.total_available = _as_optional_int(payload.get("count"))
            rows = _paginated_results(payload)
            next_url = payload.get("next")
            has_next = isinstance(next_url, str) and bool(next_url)

            for index, row in enumerate(rows):
                result.scanned += 1
                row_id = _as_optional_int(row.get("id"))
                if row_id is not None and row_id in seen_core_job_ids:
                    # A row inserted or deleted mid-scan shifts every later
                    # offset, so a row can be delivered twice. Deduplicating it
                    # silently would be worse than useless: the same drift can
                    # push a row *past* an offset we already read, so a repeat is
                    # evidence that something may have been skipped entirely.
                    result.truncated = True
                    result.truncation_reason = (
                        f"the job list shifted during the scan (core job {row_id} was "
                        "delivered twice, so another row may have been skipped); "
                        "results may be incomplete — re-run with a narrower window"
                    )
                    return result
                if row_id is not None:
                    seen_core_job_ids.add(row_id)

                if is_proxbox_sync_job(row):
                    record = ProxboxSyncJobRecord.from_row(row)
                    if active.matches(record):
                        result.jobs.append(record)
                        if limit is not None and len(result.jobs) > limit:
                            # One past the limit is the proof that more exist;
                            # stopping *at* the limit could not tell "exactly
                            # this many" from "more to come".
                            result.jobs = result.jobs[:limit]
                            result.truncated = True
                            result.truncation_reason = (
                                f"result limit of {limit} reached; more matches exist"
                            )
                            return result

                if max_scan and result.scanned >= max_scan:
                    # Only a ceiling that actually cut something short is a
                    # truncation. Reaching it on the last row of the last page
                    # means the scan finished; saying otherwise would report an
                    # exhaustive answer as a partial one.
                    rows_left_here = len(rows) - (index + 1)
                    if rows_left_here or has_next:
                        return _mark_scan_truncated(result, max_scan)
                    return result

            if not has_next:
                return _reconcile_exhausted_scan(result)
            parsed = urlsplit(str(next_url))
            path = parsed.path
            query = _query_from_next_url(parsed.query)

        result.truncated = True
        result.truncation_reason = f"pagination exceeded {_MAX_PAGES} pages"
        return result

    async def get_job(self, job_id: int) -> ProxboxSyncJobRecord:
        """Fetch one core job by PK and parse it as a Proxbox sync record."""
        payload = await self._request_object(
            "GET", f"{JOBS_LIST_PATH}{job_id}/", action="job fetch"
        )
        return ProxboxSyncJobRecord.from_row(payload)

    async def resolve_cluster_endpoint_ids(self, identifier: str | int) -> tuple[int, ...]:
        """Resolve a Proxmox cluster PK or name to its endpoint PK(s)."""
        return await self._resolve_via_inventory(PROXMOX_CLUSTERS_PATH, identifier, label="cluster")

    async def resolve_node_endpoint_ids(self, identifier: str | int) -> tuple[int, ...]:
        """Resolve a Proxmox node PK or name to its endpoint PK(s)."""
        return await self._resolve_via_inventory(PROXMOX_NODES_PATH, identifier, label="node")

    async def _resolve_via_inventory(
        self,
        path: str,
        identifier: str | int,
        *,
        label: str,
    ) -> tuple[int, ...]:
        text = str(identifier).strip()
        if not text:
            raise ProxboxJobFilterError(f"Proxmox {label} identifier cannot be empty")
        rows = await self._list_all(path, action=f"{label} lookup")
        wanted_id = _as_optional_int(text)
        lowered = text.casefold()
        matches = [
            row
            for row in rows
            if (wanted_id is not None and _as_optional_int(row.get("id")) == wanted_id)
            or (_as_optional_str(row.get("name")) or "").casefold() == lowered
        ]
        if not matches:
            raise ProxboxJobFilterError(f"No Proxmox {label} found matching {text!r}")
        endpoint_ids: list[int] = []
        for row in matches:
            endpoint = row.get("endpoint")
            endpoint_id = (
                _as_optional_int(endpoint.get("id"))
                if isinstance(endpoint, Mapping)
                else _as_optional_int(endpoint)
            )
            if endpoint_id is not None and endpoint_id not in endpoint_ids:
                endpoint_ids.append(endpoint_id)
        if not endpoint_ids:
            raise ProxboxJobFilterError(
                f"Proxmox {label} {text!r} is not linked to a Proxmox endpoint, "
                "so no sync job can be attributed to it"
            )
        return tuple(endpoint_ids)

    async def _list_all(self, path: str, *, action: str) -> list[dict[str, Any]]:
        query: dict[str, Any] | None = {"limit": self._page_size}
        rows: list[dict[str, Any]] = []
        request_path = path
        for _ in range(_MAX_PAGES):
            payload = await self._request_object("GET", request_path, query=query, action=action)
            rows.extend(_paginated_results(payload))
            next_url = payload.get("next")
            if not isinstance(next_url, str) or not next_url:
                return rows
            parsed = urlsplit(next_url)
            request_path = parsed.path
            query = _query_from_next_url(parsed.query)
        raise ProxboxSyncError(f"Pagination did not terminate during Proxbox {action}")

    async def _request_object(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        action: str,
    ) -> dict[str, Any]:
        response = await self._client.request(method, path, query=query)
        if response.status >= 400:
            raise ProxboxSyncError.from_response(response, action=action)
        payload = response.json()
        if not isinstance(payload, dict):
            raise ContentError(response)
        return payload


def _paginated_results(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    results = payload.get("results")
    if not isinstance(results, list):
        raise ProxboxSyncError(
            "NetBox returned a body without a paginated 'results' array; "
            "the endpoint may not be a list endpoint on this instance"
        )
    return [dict(item) for item in results if isinstance(item, Mapping)]


__all__ = [
    "DEFAULT_MAX_SCAN",
    "DEFAULT_PAGE_SIZE",
    "DEFAULT_WINDOW",
    "JOB_DATE_FIELDS",
    "JOB_FAILURE_STATUSES",
    "JOB_STATUS_VALUES",
    "JOB_TERMINAL_STATUSES",
    "JOBS_LIST_PATH",
    "PROXBOX_DEFAULT_JOB_NAME",
    "PROXBOX_DEFAULT_NAME_QUEUES",
    "PROXBOX_LEGACY_QUEUE_NAME",
    "PROXBOX_SYNC_DATA_KEY",
    "SERVER_PARAM_WHITELIST",
    "SYNC_STAGE_ORDER",
    "TARGETED_VM_JOB_NAME_RE",
    "TARGETED_VM_SYNC_TYPES",
    "ProxboxJobFilterError",
    "ProxboxJobFilters",
    "ProxboxJobListResult",
    "ProxboxJobScanWindow",
    "ProxboxJobsClient",
    "ProxboxSyncJobParams",
    "ProxboxSyncJobRecord",
    "ScopeState",
    "is_proxbox_sync_job",
    "normalize_sync_types",
    "parse_time_expression",
    "validate_date_field",
    "validate_job_statuses",
    "validate_sync_type_filters",
]
