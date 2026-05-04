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
