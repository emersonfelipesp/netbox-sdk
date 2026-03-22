"""Runtime state and shared factory helpers for the nbx CLI.

Holds the global schema index cache and per-profile config cache so that
all command modules can share the same in-process state without circular
imports.  All mutations are in-place (dict operations) so any module that
imports ``_RUNTIME_CONFIGS`` by name stays in sync automatically.
"""

from __future__ import annotations

import typer

from ..api import NetBoxApiClient
from ..config import (
    DEFAULT_PROFILE,
    DEMO_PROFILE,
    Config,
    is_runtime_config_complete,
    load_profile_config,
    normalize_base_url,
    save_config,
)
from ..schema import SchemaIndex, build_schema_index
from .support import run_with_spinner

_SCHEMA_INDEX: SchemaIndex | None = None
_RUNTIME_CONFIGS: dict[str, Config] = {}


def _get_index() -> SchemaIndex:
    global _SCHEMA_INDEX
    if _SCHEMA_INDEX is None:
        _SCHEMA_INDEX = build_schema_index()
    return _SCHEMA_INDEX


def _get_client() -> NetBoxApiClient:
    return NetBoxApiClient(_ensure_runtime_config())


def _get_client_for_config(cfg: Config) -> NetBoxApiClient:
    return NetBoxApiClient(cfg)


def _get_demo_client() -> NetBoxApiClient:
    return _get_client_for_config(_ensure_demo_runtime_config())


def _verify_runtime_config(cfg: Config, *, context: str) -> None:
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
    return cfg


def _ensure_profile_config(profile: str) -> Config:
    cached = _load_cached_profile(profile)
    if cached is not None:
        return cached

    cfg = load_profile_config(profile)
    if is_runtime_config_complete(cfg):
        return _cache_profile(profile, cfg)

    if profile == DEMO_PROFILE:
        from .demo import _initialize_demo_profile  # noqa: PLC0415

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
    return _cache_profile(profile, cfg)


def _ensure_runtime_config() -> Config:
    return _ensure_profile_config(DEFAULT_PROFILE)


def _ensure_demo_runtime_config() -> Config:
    return _ensure_profile_config(DEMO_PROFILE)
