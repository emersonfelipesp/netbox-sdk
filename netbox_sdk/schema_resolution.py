"""Shared NetBox release-line override and OpenAPI index resolution policy."""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import Awaitable, Callable, Mapping
from typing import Any, cast

import netbox_sdk.schema as schema_module
from netbox_sdk.schema import SchemaIndex
from netbox_sdk.versioning import (
    DEFAULT_NETBOX_VERSION,
    SupportedNetBoxVersion,
    UnsupportedNetBoxVersionError,
    normalize_netbox_version,
)

logger = logging.getLogger(__name__)

_NETBOX_VERSION_FLAGS = ("--netbox-version", "--api-version")
_NETBOX_VERSION_ENV_VARS = (
    "NETBOX_SDK_NETBOX_VERSION",
    "NETBOX_API_VERSION",
    "NETBOX_VERSION",
)
_BUNDLED_INDEXES: dict[SupportedNetBoxVersion, SchemaIndex] = {}
_SCHEMA_CACHE_RESETTERS: list[Callable[[], None]] = []


def _raw_requested_netbox_version(
    argv: list[str] | None = None,
    env: Mapping[str, str] | None = None,
) -> str | None:
    """Return the first CLI or environment release-line override."""
    args = list(sys.argv[1:] if argv is None else argv)
    for index, token in enumerate(args):
        for flag in _NETBOX_VERSION_FLAGS:
            if token == flag and index + 1 < len(args):
                return args[index + 1]
            if token.startswith(f"{flag}="):
                return token.split("=", 1)[1]
    environment = os.environ if env is None else env
    for name in _NETBOX_VERSION_ENV_VARS:
        value = environment.get(name)
        if value:
            return value
    return None


def requested_netbox_version(
    argv: list[str] | None = None,
    env: Mapping[str, str] | None = None,
    *,
    strict: bool = False,
) -> SupportedNetBoxVersion | None:
    """Resolve a CLI/environment override, warning on invalid lenient input."""
    raw = _raw_requested_netbox_version(argv, env)
    if not raw:
        return None
    try:
        return normalize_netbox_version(raw)
    except UnsupportedNetBoxVersionError:
        if strict:
            raise
        logger.warning(
            "ignoring unsupported requested NetBox version %r",
            raw,
            extra={"nbx_event": "schema_version_override_invalid", "version": raw},
        )
        return None


def bundled_index(
    line: SupportedNetBoxVersion | str | None = None,
) -> SchemaIndex:
    """Return an isolated clone of a process-cached bundled schema index.

    "Isolated" describes the *derived* maps: :meth:`SchemaIndex.clone` copies
    ``operations`` and the resource-path map, but every clone shares the one
    parsed OpenAPI document for that release line. The document is therefore
    frozen before it is cached, so a caller that mutates a nested part of
    ``index.schema`` gets an immediate :class:`SchemaDocumentFrozenError` at the
    offending line instead of silently corrupting every later SDK, CLI, TUI and
    MCP consumer in the process.

    Freezing costs one pass per release line, at first use. Deep-copying instead
    was rejected: the bundled documents are 7.7-9.6 MB and a copy costs more
    than twice the parse, on every call rather than once.
    """
    selected = normalize_netbox_version(line)
    cached = _BUNDLED_INDEXES.get(selected)
    if cached is None:
        document = schema_module.freeze_document(
            schema_module.load_openapi_schema(version=selected)
        )
        cached = SchemaIndex(document)
        _BUNDLED_INDEXES[selected] = cached
    return cached.clone()


def register_schema_cache_resetter(resetter: Callable[[], None]) -> None:
    """Register a package adapter cleared by :func:`clear_schema_caches`."""
    if resetter not in _SCHEMA_CACHE_RESETTERS:
        _SCHEMA_CACHE_RESETTERS.append(resetter)


def clear_schema_caches() -> None:
    """Clear every process-local schema cache through one shared invalidation API."""
    _BUNDLED_INDEXES.clear()
    for resetter in tuple(_SCHEMA_CACHE_RESETTERS):
        resetter()


def _clear_bundled_index_cache() -> None:
    """Compatibility alias for the shared schema-cache invalidation API."""
    clear_schema_caches()


class InvalidLiveSchemaError(RuntimeError):
    """Raised when a connected instance returns a document that is not OpenAPI.

    A 403 body, an HTML interstitial, or an error envelope from ``/api/schema/``
    is a *successful* HTTP response carrying an unusable document. Silently
    substituting the default bundled contract would let a surface answer for a
    server it cannot actually describe, so this is raised and only converted to
    the default bundle when the caller passed ``fall_back_on_error=True``.
    """


async def _version_from_status(client: Any) -> str | None:
    """Return the version reported by ``/api/status/``, or ``None``.

    Reading the status document is strictly best-effort: it is an enrichment over
    the root ``API-Version`` probe, not a replacement for it. A blocked,
    malformed, or non-JSON status endpoint must fall through to
    ``client.get_version()`` exactly as before this detection existed — otherwise
    an instance whose status endpoint is restricted would fail resolution
    outright, or be silently served the default bundled contract.
    """
    status_fn = getattr(client, "status", None)
    if not callable(status_fn):
        return None
    try:
        status = await cast(Awaitable[Any], status_fn())
    except Exception as exc:  # noqa: BLE001 - best-effort enrichment only
        logger.debug(
            "status probe failed (%s); falling back to the API-Version header",
            exc,
            extra={"nbx_event": "schema_version_status_probe_failed"},
        )
        return None
    if not isinstance(status, dict):
        return None
    reported = status.get("netbox-version")
    return reported if isinstance(reported, str) and reported else None


async def _detected_release_line(
    client: Any,
) -> tuple[str, SupportedNetBoxVersion | None]:
    version = await _version_from_status(client)
    detected_version = version if version is not None else cast(str, await client.get_version())
    try:
        return detected_version, normalize_netbox_version(detected_version)
    except UnsupportedNetBoxVersionError:
        return detected_version, None


async def detect_release_line(client: Any) -> SupportedNetBoxVersion | None:
    """Detect and map a connected NetBox version to a bundled release line."""
    _, detected = await _detected_release_line(client)
    return detected


async def _resolve_connected_index(client: Any) -> SchemaIndex:
    """Resolve a connected instance's index.

    Raises:
        InvalidLiveSchemaError: If the live document is not an OpenAPI document.
    """
    version, detected = await _detected_release_line(client)
    if detected is not None:
        logger.info(
            "loading bundled schema for NetBox %s",
            detected,
            extra={"nbx_event": "schema_version_bundled", "version": detected},
        )
        return bundled_index(detected)

    logger.info(
        "NetBox %s is not a bundled release line; fetching schema dynamically",
        version,
        extra={"nbx_event": "schema_version_dynamic_fetch", "version": version},
    )
    schema = await client.openapi()
    if not isinstance(schema.get("paths"), dict):
        logger.debug(
            "connected schema response did not contain OpenAPI paths; using default bundled schema",
            extra={"nbx_event": "schema_runtime_invalid_document"},
        )
        raise InvalidLiveSchemaError(
            "The connected instance returned a document without an OpenAPI 'paths' object."
        )
    return SchemaIndex(schema)


async def resolve_index(
    client: Any | None = None,
    *,
    prefer_live: bool = True,
    line: SupportedNetBoxVersion | str | None = None,
    argv: list[str] | None = None,
    env: Mapping[str, str] | None = None,
    use_ambient_pin: bool = False,
    fall_back_on_error: bool = False,
) -> SchemaIndex:
    """Resolve one isolated index using the shared release-line precedence ladder.

    Precedence: an explicit ``line`` wins; then, when pin lookup is enabled, a
    CLI/environment pin; then a connected supported instance's bundled line;
    then an unsupported instance's live OpenAPI document; then the default
    bundled line.

    Args:
        client: Connected client used for release detection and live fetches.
        prefer_live: Whether to consult ``client`` at all.
        line: Explicit release line, bypassing detection entirely.
        argv: Argument list for pin lookup. Supplying it is its own opt-in.
        env: Environment mapping for pin lookup. Supplying it is its own opt-in.
        use_ambient_pin: Consult process-global ``sys.argv`` / ``os.environ`` for
            a pin. **Off by default.** Reading ambient argv is right for the
            ``nbx`` entrypoint, but for a library call or a long-lived MCP server
            it is a hidden global dependency: an unrelated host-application
            ``--api-version`` flag must never silently repoint the schema.
        fall_back_on_error: Swallow detection/fetch failures - including a live
            document that is not OpenAPI - and return the default bundled index.
            **Off by default.** A caller that cannot reach or cannot parse its
            instance must see the error rather than silently receive a bundled
            contract that does not describe the server it is talking to.

    Raises:
        InvalidLiveSchemaError: If the live document is not an OpenAPI document.
        Exception: Whatever ``client`` raises during detection or the live
            OpenAPI fetch. Both are suppressed only when ``fall_back_on_error``
            is set.
    """
    if line is not None:
        return bundled_index(normalize_netbox_version(line))
    if use_ambient_pin or argv is not None or env is not None:
        # Only the sources the caller actually opted into are consulted. Without
        # use_ambient_pin, an omitted source defaults to EMPTY rather than to the
        # process globals, so resolve_index(client, argv=[]) cannot still absorb
        # os.environ (nor the symmetric env-only call absorb sys.argv).
        pin_argv = argv if argv is not None else (None if use_ambient_pin else [])
        pin_env: Mapping[str, str] | None = (
            env if env is not None else (None if use_ambient_pin else {})
        )
        requested = requested_netbox_version(pin_argv, pin_env)
        if requested is not None:
            return bundled_index(requested)
    if client is None or not prefer_live:
        return bundled_index(DEFAULT_NETBOX_VERSION)

    if not fall_back_on_error:
        return await _resolve_connected_index(client)

    try:
        return await _resolve_connected_index(client)
    except Exception as exc:  # noqa: BLE001
        logger.debug(
            "schema version detection failed (%s); using default bundled schema",
            exc,
            extra={"nbx_event": "schema_version_detection_failed"},
        )
        return bundled_index(DEFAULT_NETBOX_VERSION)
