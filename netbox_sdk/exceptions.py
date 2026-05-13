"""SDK-specific errors raised by the NetBox HTTP client and high-level ``api()`` facade.

Security note: All token handling strips CR/LF/null bytes to prevent HTTP header injection.
URL validation rejects non-HTTP schemes, embedded credentials, and control characters.
Cache keys use SHA-256 fingerprints rather than raw tokens.
"""

from __future__ import annotations

from typing import Any


class RequestError(RuntimeError):
    """Raised when a NetBox HTTP response indicates failure (typically status >= 400)."""

    def __init__(self, response: Any) -> None:
        self.response = response
        super().__init__(f"Request failed with status {response.status}")


class ContentError(RuntimeError):
    """Raised when the server response body is not valid JSON where JSON was expected."""

    def __init__(self, response: Any) -> None:
        self.response = response
        super().__init__("The server returned invalid (non-json) data.")


class AllocationError(RuntimeError):
    """Raised when an available-IPs/prefixes style allocation endpoint cannot fulfill the request."""

    def __init__(self, response: Any) -> None:
        self.response = response
        super().__init__("The requested allocation could not be fulfilled.")


class ParameterValidationError(ValueError):
    """Raised when filter or request parameters fail local validation before the HTTP call."""

    def __init__(self, errors: list[str] | str) -> None:
        self.error = errors
        super().__init__(f"The request parameter validation returned an error: {errors}")


class JsonPayloadError(ValueError):
    """Raised when ``--body-json`` or ``--body-file`` content is invalid JSON or not an object/array."""


class BranchingPluginUnavailableError(RuntimeError):
    """Raised when a branching operation is requested but the plugin is not installed on the server."""

    def __init__(
        self, message: str = "The netbox-branching plugin is not installed on this server."
    ) -> None:
        super().__init__(message)


class BranchConflictError(RuntimeError):
    """Raised when a branching sync or merge action reports conflicts (HTTP 409)."""

    def __init__(
        self, conflicts: list[Any] | dict[str, Any] | str, response: Any | None = None
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
