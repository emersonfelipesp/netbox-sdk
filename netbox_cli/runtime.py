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
from netbox_sdk.client import NetBoxApiClient
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
from netbox_sdk.logging_runtime import get_logger
from netbox_sdk.schema import SchemaIndex, load_openapi_schema

_SCHEMA_DOCUMENT: dict | None = None
_RUNTIME_CONFIGS: dict[str, Config] = {}
logger = get_logger(__name__)


def _get_index() -> SchemaIndex:
    global _SCHEMA_DOCUMENT
    if _SCHEMA_DOCUMENT is None:
        logger.info("loading base openapi schema")
        _SCHEMA_DOCUMENT = load_openapi_schema()
    # Return a fresh mutable index for each caller so runtime discoveries from one
    # NetBox instance can't leak into another app session.
    return SchemaIndex(deepcopy(_SCHEMA_DOCUMENT))


def _get_client() -> NetBoxApiClient:
    logger.debug("creating default profile api client")
    import netbox_cli as cli_mod  # noqa: PLC0415 — late import so tests can patch cli_mod._ensure_runtime_config

    return NetBoxApiClient(cli_mod._ensure_runtime_config())


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


def _verify_runtime_config(cfg: Config, *, context: str) -> None:
    logger.info("verifying runtime config for %s", context)
    client = _get_client_for_config(cfg)
    response = run_with_spinner(client.request("GET", "/api/status/"))
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
    return _cache_profile(profile, cfg)


def _ensure_runtime_config() -> Config:
    return _ensure_profile_config(DEFAULT_PROFILE)


def _ensure_demo_runtime_config() -> Config:
    return _ensure_profile_config(DEMO_PROFILE)


def _repair_demo_profile_if_needed(cfg: Config) -> Config:
    if profile_requires_demo_repair(cfg) is False:
        return cfg
    logger.info("checking demo profile token health")
    client = _get_client_for_config(cfg)
    response = run_with_spinner(client.request("GET", "/api/status/"))
    if response.status < 400 or "invalid v1 token" not in response.text.lower():
        return cfg

    logger.warning("demo profile token expired; reinitializing with saved credentials")
    try:
        from netbox_sdk.demo_auth import refresh_demo_profile  # noqa: PLC0415

        refreshed = refresh_demo_profile(cfg, headless=True)
    except Exception:
        logger.exception("demo profile token refresh failed")
        return cfg

    try:
        save_profile_config(DEMO_PROFILE, refreshed)
    except Exception:
        logger.exception("failed to persist repaired demo profile")
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
