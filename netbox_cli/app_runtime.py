"""Typer-free runtime factories shared by CLI, TUI, and docgen.

Default NetBox client resolution still delegates to :mod:`netbox_cli.cli` for
interactive profile setup (see :func:`get_default_client`).
"""

from __future__ import annotations

from copy import deepcopy

from .api import NetBoxApiClient
from .config import Config
from .logging_runtime import get_logger
from .schema import SchemaIndex, load_openapi_schema

logger = get_logger(__name__)

_openapi_document: dict | None = None


def get_schema_index() -> SchemaIndex:
    """Return a fresh mutable :class:`SchemaIndex` from the cached OpenAPI document."""
    global _openapi_document
    if _openapi_document is None:
        logger.info("loading base openapi schema")
        _openapi_document = load_openapi_schema()
    return SchemaIndex(deepcopy(_openapi_document))


def client_for_config(cfg: Config) -> NetBoxApiClient:
    """Build an API client for an explicit :class:`Config` (no profile prompts)."""
    return NetBoxApiClient(cfg)


def get_default_client() -> NetBoxApiClient:
    """API client for the active default profile (may prompt or load demo profile)."""
    import netbox_cli.cli as cli_mod  # noqa: PLC0415 — tests patch ``cli_mod._ensure_runtime_config``

    return NetBoxApiClient(cli_mod._ensure_runtime_config())
