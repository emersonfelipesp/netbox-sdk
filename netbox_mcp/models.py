"""Strict Pydantic input models for the NetBox MCP tool surface."""

from __future__ import annotations

import posixpath
from typing import Annotated, Any, Literal
from urllib.parse import unquote

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

Name = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=200,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.\-/]*$",
    ),
]
PositiveId = Annotated[int, Field(gt=0)]
MaxRecords = Annotated[int, Field(ge=1, le=100_000)]
Token = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=8192)]
HttpMethod = Literal["GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"]


class ToolInput(BaseModel):
    """Base model that rejects unrecognized tool arguments."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("token", check_fields=False)
    @classmethod
    def _validate_token(cls, value: str | None) -> str | None:
        if value is not None and any(character in value for character in ("\r", "\n", "\x00")):
            raise ValueError("token must not contain control characters")
        return value


class LiveInput(ToolInput):
    live: bool = False
    token: Token | None = None


class GroupInput(ToolInput):
    group: Name
    live: bool = False
    token: Token | None = None


class ResourceInput(ToolInput):
    group: Name
    resource: Name


class LiveResourceInput(ResourceInput):
    live: bool = False
    token: Token | None = None


class ListInput(ResourceInput):
    query: list[str] = Field(default_factory=list, max_length=500)
    all: bool = False
    max_records: MaxRecords = 10_000
    header: list[str] = Field(default_factory=list, max_length=100)
    live: bool = False
    token: Token | None = None


class GetInput(ResourceInput):
    id: PositiveId
    header: list[str] = Field(default_factory=list, max_length=100)
    live: bool = False
    token: Token | None = None


class MutationInput(ResourceInput):
    payload: dict[str, Any]
    dry_run: bool = False
    header: list[str] = Field(default_factory=list, max_length=100)
    token: Token | None = None


class DetailMutationInput(MutationInput):
    id: PositiveId


class DeleteInput(ResourceInput):
    id: PositiveId
    dry_run: bool = False
    header: list[str] = Field(default_factory=list, max_length=100)
    token: Token | None = None


class BulkMutationInput(ResourceInput):
    payload: list[dict[str, Any]] = Field(min_length=1, max_length=10_000)
    dry_run: bool = False
    header: list[str] = Field(default_factory=list, max_length=100)
    token: Token | None = None


class PluginDiscoverInput(ToolInput):
    plugin: Name
    token: Token | None = None


class CallInput(ToolInput):
    method: HttpMethod
    path: str = Field(min_length=6, max_length=2048)
    query: list[str] = Field(default_factory=list, max_length=500)
    payload: dict[str, Any] | list[Any] | None = None
    header: list[str] = Field(default_factory=list, max_length=100)
    token: Token | None = None

    @field_validator("method", mode="before")
    @classmethod
    def _normalize_method(cls, value: object) -> str:
        return str(value).strip().upper()

    @field_validator("path")
    @classmethod
    def _validate_path(cls, value: str) -> str:
        path = value.strip()
        if any(character in path for character in ("\r", "\n", "\x00", "?", "#")):
            raise ValueError("path must not contain controls, a query string, or a fragment")
        if "://" in path or "\\" in path:
            raise ValueError("path must be a relative /api/ path with no backslashes")
        if not path.startswith("/api/"):
            raise ValueError("path must begin with /api/")
        # A reverse proxy, NetBox itself, or NetBoxApiClient's own dot-segment
        # resolution (used to keep cache keys aligned with the outbound
        # request) may resolve dot segments server- or client-side even
        # though this raw path never states its true target explicitly. A
        # path like "/api/dcim/../ipam/prefixes/" would still land under
        # /api/ and pass a naive prefix check, but silently resolve to a
        # different resource than its literal text names — reject "." and
        # ".." segments outright instead of trying to reason about where
        # they would resolve, so a raw call always targets exactly the
        # resource its path spells out.
        decoded = unquote(path)
        if any(character in decoded for character in ("\r", "\n", "\x00")) or "\\" in decoded:
            raise ValueError("path must not contain controls or backslashes once decoded")
        if "://" in decoded:
            raise ValueError("path must be a relative /api/ path once decoded")
        if any(segment in (".", "..") for segment in decoded.split("/")):
            raise ValueError("path must not contain '.' or '..' segments")
        normalized = posixpath.normpath(decoded)
        if normalized != "/api" and not normalized.startswith("/api/"):
            raise ValueError("path must stay within /api/ once decoded and normalized")
        return path
