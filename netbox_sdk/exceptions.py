"""SDK-specific errors raised by the NetBox HTTP client and high-level ``api()`` facade.

Security note: All token handling strips CR/LF/null bytes to prevent HTTP header injection.
URL validation rejects non-HTTP schemes, embedded credentials, and control characters.
Cache keys use SHA-256 fingerprints rather than raw tokens.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from netbox_sdk.client import ApiResponse


@dataclass(frozen=True, slots=True)
class BulkOperationEntryError:
    """One object that failed inside a NetBox 4.7+ bulk create or update.

    ``index`` is the zero-based position in the submitted list (creates, and
    updates whose body could not be matched to an object). ``id`` is the
    matched object id. The two are mutually exclusive on the wire. ``errors``
    is keyed by field name; non-field failures appear under ``__all__``.
    """

    errors: dict[str, Any]
    index: int | None = None
    id: int | None = None


def _payload_from_response(response: ApiResponse) -> Any:
    json_fn = getattr(response, "json", None)
    if not callable(json_fn):
        return None
    try:
        return json_fn()
    except (ValueError, TypeError):
        return None


def _nonneg_int(value: Any) -> int | None:
    """Return ``value`` when it is a real non-negative int, not a bool."""
    if type(value) is int and value >= 0:
        return value
    return None


def _parse_bulk_entry(item: Any) -> BulkOperationEntryError | None:
    """Parse one bulk-failure row. Malformed locators are dropped, not trusted."""
    if not isinstance(item, dict):
        return None
    field_errors = item.get("errors")
    if not isinstance(field_errors, dict):
        return None
    index_present = "index" in item
    id_present = "id" in item
    if index_present == id_present:
        return None
    if index_present:
        index = _nonneg_int(item.get("index"))
        if index is None:
            return None
        return BulkOperationEntryError(errors=field_errors, index=index, id=None)
    object_id = _nonneg_int(item.get("id"))
    if object_id is None:
        return None
    return BulkOperationEntryError(errors=field_errors, index=None, id=object_id)


def _entry_errors_from_payload(payload: Any) -> tuple[BulkOperationEntryError, ...]:
    if not isinstance(payload, dict):
        return ()
    raw_errors = payload.get("errors")
    if not isinstance(raw_errors, list):
        return ()
    entries: list[BulkOperationEntryError] = []
    for item in raw_errors:
        parsed = _parse_bulk_entry(item)
        if parsed is not None:
            entries.append(parsed)
    return tuple(entries)


def _request_error_message(response: ApiResponse, detail: str | None, entry_count: int) -> str:
    status = getattr(response, "status", "?")
    message = f"Request failed with status {status}"
    if entry_count and detail:
        return f"{message}: {detail}"
    return message


class RequestError(RuntimeError):
    """Raised when a NetBox HTTP response indicates failure (typically status >= 400).

    NetBox 4.7 bulk create/update failures return
    ``{"detail": ..., "errors": [{"index": N, "errors": {...}}]}``. That shape
    is parsed onto :attr:`detail` and :attr:`entry_errors` so callers can
    correct the failing objects instead of treating the body as opaque text.
    Other error envelopes leave :attr:`entry_errors` empty and keep the
    historical message string.
    """

    def __init__(self, response: ApiResponse) -> None:
        self.response = response
        payload = _payload_from_response(response)
        self.payload = payload
        self.detail: str | None = payload.get("detail") if isinstance(payload, dict) else None
        if self.detail is not None and not isinstance(self.detail, str):
            self.detail = str(self.detail)
        self.entry_errors: tuple[BulkOperationEntryError, ...] = _entry_errors_from_payload(payload)
        super().__init__(_request_error_message(response, self.detail, len(self.entry_errors)))


class ContentError(RuntimeError):
    """Raised when the server response body is not valid JSON where JSON was expected."""

    def __init__(self, response: ApiResponse) -> None:
        self.response = response
        super().__init__("The server returned invalid (non-json) data.")


class ResponseSizeLimitError(RuntimeError):
    """Raised while streaming a response that exceeds a caller-declared bound."""

    def __init__(self, max_bytes: int) -> None:
        self.max_bytes = max_bytes
        super().__init__(f"Response body exceeds the {max_bytes}-byte size limit")


class AllocationError(RuntimeError):
    """Raised when an available-IPs/prefixes style allocation endpoint cannot fulfill the request."""

    def __init__(self, response: ApiResponse) -> None:
        self.response = response
        super().__init__("The requested allocation could not be fulfilled.")


class ParameterValidationError(ValueError):
    """Raised when filter or request parameters fail local validation before the HTTP call."""

    def __init__(self, errors: list[str] | str) -> None:
        self.error = errors
        super().__init__(f"The request parameter validation returned an error: {errors}")


class JsonPayloadError(ValueError):
    """Raised when ``--body-json`` or ``--body-file`` content is invalid JSON or not an object/array."""


class PaginationError(RuntimeError):
    """Raised when automatic pagination receives malformed or cyclic page data."""


class BranchingPluginUnavailableError(RuntimeError):
    """Raised when a branching operation is requested but the plugin is not installed on the server."""

    def __init__(
        self, message: str = "The netbox-branching plugin is not installed on this server."
    ) -> None:
        super().__init__(message)


class BranchConflictError(RuntimeError):
    """Raised when a branching sync or merge action reports conflicts (HTTP 409)."""

    def __init__(
        self, conflicts: list[Any] | dict[str, Any] | str, response: ApiResponse | None = None
    ) -> None:
        self.conflicts = conflicts
        self.response = response
        if isinstance(conflicts, (list, tuple)):
            count = len(conflicts)
            summary = f"{count} branching conflict{'s' if count != 1 else ''} detected."
        else:
            summary = f"Branching conflict detected: {conflicts!r}"
        super().__init__(summary)


class BranchJobTimeoutError(RuntimeError):
    """Raised when a branching action's background job does not finish within the allotted polling window."""

    def __init__(self, job_id: int, last_status: str | None = None) -> None:
        self.job_id = job_id
        self.last_status = last_status
        super().__init__(
            f"Branching job {job_id} did not complete in time (last status={last_status!r})."
        )
