"""Runtime state and shared factory helpers for the nbx CLI.

Holds the global schema index cache and per-profile config cache so that
all command modules can share the same in-process state without circular
imports.  All mutations are in-place (dict operations) so any module that
imports ``_RUNTIME_CONFIGS`` by name stays in sync automatically.
"""

from __future__ import annotations

from collections.abc import Callable
from contextvars import ContextVar
from copy import deepcopy

import typer

from netbox_cli.support import run_with_spinner
from netbox_sdk.client import ConnectionProbe, NetBoxApiClient
from netbox_sdk.config import (
    DEFAULT_PROFILE,
    DEMO_BASE_URL,
    DEMO_PROFILE,
    Config,
    authorization_header_value,
    is_runtime_config_complete,
    load_profile_config,
    normalize_base_url,
    save_config,
    save_profile_config,
)
from netbox_sdk.http_ssl import (
    is_certificate_verify_failure,
    is_certificate_verify_failure_text,
)
from netbox_sdk.logging_runtime import get_logger
from netbox_sdk.schema import SchemaIndex, load_openapi_schema

try:
    import aiohttp
except ModuleNotFoundError:  # pragma: no cover
    aiohttp = None  # type: ignore[assignment, misc]

_VERIFY_REQUEST_ERRORS: tuple[type[BaseException], ...] = (RuntimeError, OSError)
if aiohttp is not None:
    _VERIFY_REQUEST_ERRORS = (*_VERIFY_REQUEST_ERRORS, aiohttp.ClientError)

_SCHEMA_DOCUMENT: dict | None = None
_RUNTIME_CONFIGS: dict[str, Config] = {}
logger = get_logger(__name__)


async def _detect_and_fetch_schema(cfg: Config) -> dict:
    from netbox_sdk.schema import fetch_schema_for_client  # noqa: PLC0415

    client = _get_client_for_config(cfg)
    return await fetch_schema_for_client(client)


def _load_schema_for_connected_instance(
    profile: str = DEFAULT_PROFILE,
    cfg: Config | None = None,
) -> dict:
    """Resolve the OpenAPI schema for a profile's NetBox instance.

    Uses a bundled schema when the connected version is a supported release line,
    fetches it dynamically via /api/schema/ for unsupported versions, and falls
    back to the default bundled schema when config is absent or any error occurs.
    """
    try:
        cfg = cfg or load_profile_config(profile)
        if not cfg.base_url:
            logger.debug("no base_url configured; using default bundled schema")
            return load_openapi_schema()
        return run_with_spinner(_detect_and_fetch_schema(cfg))
    except Exception as exc:  # noqa: BLE001
        logger.debug(
            "schema version detection failed (%s); using default bundled schema",
            exc,
            extra={"nbx_event": "schema_version_detection_failed"},
        )
        return load_openapi_schema()


def _get_index() -> SchemaIndex:
    global _SCHEMA_DOCUMENT
    if _SCHEMA_DOCUMENT is None:
        logger.info("loading bundled openapi schema")
        _SCHEMA_DOCUMENT = load_openapi_schema()
    # Return a fresh mutable index for each caller so runtime discoveries from one
    # NetBox instance can't leak into another app session.
    return SchemaIndex(deepcopy(_SCHEMA_DOCUMENT))


def _get_connected_index(
    profile: str = DEFAULT_PROFILE,
    cfg: Config | None = None,
) -> SchemaIndex:
    """Return a schema index selected from the connected NetBox instance."""
    return SchemaIndex(deepcopy(_load_schema_for_connected_instance(profile, cfg)))


def _get_enriched_index(client: NetBoxApiClient | None = None) -> SchemaIndex:
    """Return a fresh schema index enriched with live plugin/custom-object resources."""
    from netbox_sdk.plugin_discovery import (  # noqa: PLC0415
        enrich_schema_index_with_runtime_resources,
    )

    active_client = client or _get_client()
    index = _get_connected_index(DEFAULT_PROFILE, active_client.config)
    run_with_spinner(enrich_schema_index_with_runtime_resources(index, active_client))
    return index


def _get_client() -> NetBoxApiClient:
    logger.debug("creating default profile api client")
    import netbox_cli as cli_mod  # noqa: PLC0415 — late import so tests can patch cli_mod._ensure_runtime_config

    return NetBoxApiClient(cli_mod._ensure_runtime_config())


def _get_client_for_tui() -> NetBoxApiClient:
    """Create a client for TUI launch without prompting for credentials.

    Loads the stored profile config when available. If credentials are absent
    the TUI will prompt interactively via LoginModal instead of the terminal.
    """
    try:
        cfg = load_profile_config(DEFAULT_PROFILE) or Config()
    except Exception:  # noqa: BLE001
        cfg = Config()
    _cache_profile(DEFAULT_PROFILE, cfg)
    return _get_client_for_config(cfg)


def _demo_token_refresh_callback(
    config: Config,
) -> tuple[str | None, Config]:
    """Injected into NetBoxApiClient for automatic demo token refresh."""
    from netbox_sdk.demo_auth import refresh_demo_profile  # noqa: PLC0415

    refreshed = refresh_demo_profile(config, headless=True)
    save_profile_config(DEMO_PROFILE, refreshed)
    _cache_profile(DEMO_PROFILE, refreshed)
    return authorization_header_value(refreshed), refreshed


def _get_client_for_config(cfg: Config) -> NetBoxApiClient:
    on_refresh = _demo_token_refresh_callback if cfg.base_url == DEMO_BASE_URL else None
    return NetBoxApiClient(cfg, on_token_refresh=on_refresh)


def _get_demo_client() -> NetBoxApiClient:
    logger.debug("creating demo profile api client")
    return _get_client_for_config(_ensure_demo_runtime_config())


def _default_dev_http_client_factory() -> NetBoxApiClient:
    return _get_client()


_dev_http_client_factory_ctx: ContextVar[Callable[[], NetBoxApiClient]] = ContextVar(
    "_dev_http_client_factory_ctx",
    default=_default_dev_http_client_factory,
)


def dev_http_api_client() -> NetBoxApiClient:
    """Return the NetBox client for ``nbx dev http`` / ``nbx demo dev http``."""
    return _dev_http_client_factory_ctx.get()()


def _prompt_ssl_verify_if_unset(cfg: Config, profile: str) -> None:
    """Prompt to persist ssl_verify when unset and TLS verification failed."""
    if cfg.ssl_verify is not None:
        return
    typer.echo(
        "TLS certificate verification failed. The server may use a self-signed or untrusted certificate.",
        err=True,
    )
    if typer.confirm(
        "Disable TLS certificate verification for this profile? (insecure; saved to config)",
        default=False,
    ):
        cfg.ssl_verify = False
        save_profile_config(profile, cfg)
        _cache_profile(profile, cfg)
        return
    cfg.ssl_verify = True
    save_profile_config(profile, cfg)
    _cache_profile(profile, cfg)
    typer.echo(
        "SSL verification remains enabled. Fix the server certificate or install the correct CA bundle.",
        err=True,
    )
    raise typer.Exit(code=1)


def _retry_probe_after_ssl_prompt(
    cfg: Config, profile: str, probe: ConnectionProbe
) -> ConnectionProbe:
    """If probe failed with TLS verification, optionally prompt and re-probe once."""
    if probe.ok or cfg.ssl_verify is not None:
        return probe
    if not is_certificate_verify_failure_text(probe.error):
        return probe
    _prompt_ssl_verify_if_unset(cfg, profile)
    return run_with_spinner(_get_client_for_config(cfg).probe_connection())


def _verify_runtime_config(cfg: Config, *, context: str, profile: str = DEFAULT_PROFILE) -> None:
    logger.info("verifying runtime config for %s", context)
    client = _get_client_for_config(cfg)
    try:
        response = run_with_spinner(client.request("GET", "/api/status/"))
    except _VERIFY_REQUEST_ERRORS as exc:
        if cfg.ssl_verify is None and is_certificate_verify_failure(exc):
            _prompt_ssl_verify_if_unset(cfg, profile)
            client = _get_client_for_config(cfg)
            response = run_with_spinner(client.request("GET", "/api/status/"))
        else:
            logger.error(
                "runtime config verification request failed: %s",
                exc,
                extra={"nbx_event": "cli_verify_status_failed", "profile": profile},
            )
            raise
    if response.status >= 400:
        detail = response.text.strip() or f"HTTP {response.status}"
        raise typer.BadParameter(f"{context} verification failed: {detail}")


def _load_cached_profile(profile: str) -> Config | None:
    cfg = _RUNTIME_CONFIGS.get(profile)
    if cfg is not None and is_runtime_config_complete(cfg):
        return cfg
    return None


def _cache_profile(profile: str, cfg: Config) -> Config:
    _RUNTIME_CONFIGS[profile] = cfg
    logger.debug("cached profile %s", profile)
    return cfg


def _ensure_profile_config(profile: str) -> Config:
    cached = _load_cached_profile(profile)
    if cached is not None:
        logger.debug("using cached profile %s", profile)
        return cached

    cfg = load_profile_config(profile)
    if is_runtime_config_complete(cfg):
        if profile == DEMO_PROFILE:
            cfg = _repair_demo_profile_if_needed(cfg)
        logger.info("loaded complete profile config for %s", profile)
        return _cache_profile(profile, cfg)

    if profile == DEMO_PROFILE:
        from netbox_cli.demo import _initialize_demo_profile  # noqa: PLC0415

        return _initialize_demo_profile(force=True)

    typer.echo("NetBox endpoint configuration is required.")
    if not cfg.base_url:
        cfg.base_url = normalize_base_url(
            typer.prompt("NetBox host (example: https://netbox.example.com)")
        )
    if not cfg.token_key:
        cfg.token_key = typer.prompt("NetBox token key")
    if not cfg.token_secret:
        cfg.token_secret = typer.prompt("NetBox token secret", hide_input=True)

    save_config(cfg)
    typer.echo("Configuration saved.")
    logger.info("interactively completed profile config for %s", profile)
    cfg = _cache_profile(profile, cfg)
    client = _get_client_for_config(cfg)
    try:
        run_with_spinner(client.request("GET", "/api/status/"))
    except _VERIFY_REQUEST_ERRORS as exc:
        if cfg.ssl_verify is None and is_certificate_verify_failure(exc):
            _prompt_ssl_verify_if_unset(cfg, profile)
            run_with_spinner(_get_client_for_config(cfg).request("GET", "/api/status/"))
        else:
            logger.error(
                "post-save status check failed: %s",
                exc,
                extra={"nbx_event": "cli_post_save_verify_failed", "profile": profile},
            )
            raise
    return cfg


def _ensure_runtime_config() -> Config:
    return _ensure_profile_config(DEFAULT_PROFILE)


def _ensure_demo_runtime_config() -> Config:
    return _ensure_profile_config(DEMO_PROFILE)


def _repair_demo_profile_if_needed(cfg: Config) -> Config:
    if profile_requires_demo_repair(cfg) is False:
        return cfg
    logger.info("checking demo profile token health")
    client = _get_client_for_config(cfg)
    try:
        response = run_with_spinner(client.request("GET", "/api/status/"))
    except _VERIFY_REQUEST_ERRORS as exc:
        if cfg.ssl_verify is None and is_certificate_verify_failure(exc):
            _prompt_ssl_verify_if_unset(cfg, DEMO_PROFILE)
            response = run_with_spinner(_get_client_for_config(cfg).request("GET", "/api/status/"))
        else:
            logger.error(
                "demo repair status check failed: %s",
                exc,
                extra={"nbx_event": "cli_demo_repair_status_failed"},
            )
            raise
    if response.status < 400 or "invalid v1 token" not in response.text.lower():
        return cfg

    logger.warning("demo profile token expired; reinitializing with saved credentials")
    try:
        from netbox_sdk.demo_auth import refresh_demo_profile  # noqa: PLC0415

        refreshed = refresh_demo_profile(cfg, headless=True)
    except (RuntimeError, OSError, ValueError) as exc:
        logger.exception(
            "demo profile token refresh failed: %s",
            exc,
            extra={"nbx_event": "cli_demo_token_refresh_failed"},
        )
        return cfg

    try:
        save_profile_config(DEMO_PROFILE, refreshed)
    except OSError as exc:
        logger.exception(
            "failed to persist repaired demo profile: %s",
            exc,
            extra={"nbx_event": "cli_demo_profile_save_failed"},
        )
        return cfg

    typer.echo("Demo token was refreshed automatically.")
    return refreshed


def profile_requires_demo_repair(cfg: Config) -> bool:
    return bool(
        cfg.base_url == DEMO_BASE_URL
        and cfg.token_version == "v1"
        and cfg.token_secret
        and cfg.demo_username
        and cfg.demo_password
    )
