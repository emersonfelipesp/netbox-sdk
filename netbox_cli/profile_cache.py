"""In-process NetBox profile cache shared by the API client, CLI runtime, and docgen."""

from __future__ import annotations

from .config import Config
from .logging_runtime import get_logger

logger = get_logger(__name__)

_RUNTIME_CONFIGS: dict[str, Config] = {}


def _cache_profile(profile: str, cfg: Config) -> Config:
    _RUNTIME_CONFIGS[profile] = cfg
    logger.debug("cached profile %s", profile)
    return cfg
