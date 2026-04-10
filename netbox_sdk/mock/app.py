"""Standalone FastAPI app factory for the schema-driven NetBox mock API."""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI

from netbox_sdk import __version__ as _sdk_version
from netbox_sdk.mock.loader import load_mock_data
from netbox_sdk.mock.routes import netbox_mock_route_state, register_netbox_mock_routes
from netbox_sdk.mock.state import ThreadSafeMockStore, mock_store, reset_mock_state
from netbox_sdk.schema import load_openapi_schema
from netbox_sdk.versioning import SupportedNetBoxVersion, normalize_netbox_version


def create_mock_app(
    *,
    version: SupportedNetBoxVersion | None = None,
) -> FastAPI:
    """Build the standalone NetBox mock API FastAPI application.

    Reads ``NETBOX_MOCK_VERSION`` env var (default ``"4.5"``), loads the
    bundled OpenAPI schema, and registers all NetBox endpoints as dynamic
    in-memory CRUD routes.

    Args:
        version: NetBox release line override. Defaults to ``NETBOX_MOCK_VERSION``
            env var or ``"4.5"``.

    Returns:
        Configured :class:`fastapi.FastAPI` instance ready for ``uvicorn``.
    """
    resolved_version: SupportedNetBoxVersion = version or normalize_netbox_version(
        os.environ.get("NETBOX_MOCK_VERSION", "4.5")
    )

    openapi_doc = load_openapi_schema(version=resolved_version)
    netbox_api_version = openapi_doc.get("info", {}).get("version", resolved_version)

    app = FastAPI(
        title="NetBox Mock API",
        description=(
            "Schema-driven in-memory FastAPI mock for the NetBox REST API. "
            "All endpoints support full CRUD with in-memory state."
        ),
        version=_sdk_version,
    )

    # -------------------------------------------------------------------
    # Utility routes
    # -------------------------------------------------------------------

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, Any]:
        state = netbox_mock_route_state()
        return {
            "message": "NetBox mock API — schema-driven in-memory server",
            "netbox_version": netbox_api_version,
            "sdk_version": _sdk_version,
            "schema_version": resolved_version,
            "route_count": state.get("route_count", 0),
        }

    @app.get("/health", include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ready"}

    @app.get("/api/status/", tags=["status"])
    async def netbox_status() -> dict[str, Any]:
        """NetBox-compatible status endpoint."""
        return {
            "django-version": "5.2",
            "installed-apps": {},
            "netbox-version": netbox_api_version,
            "plugins": {},
            "python-version": "3.11",
            "rq-workers-running": 1,
        }

    @app.post("/mock/reset", tags=["mock control"])
    async def mock_reset() -> dict[str, str]:
        """Reset all in-memory mock state to empty."""
        reset_mock_state()
        return {"status": "reset", "message": "All mock state has been cleared."}

    @app.get("/mock/state", tags=["mock control"])
    async def mock_state_info() -> dict[str, Any]:
        """Return metadata about the current mock state and registered routes."""
        from netbox_sdk.mock.schema_helpers import schema_fingerprint

        fingerprint = schema_fingerprint(openapi_doc)
        store: ThreadSafeMockStore = mock_store(fingerprint)
        route_state = netbox_mock_route_state()
        return {
            "route_count": route_state.get("route_count"),
            "schema_version": route_state.get("schema_version"),
            "store_stats": store.stats(),
        }

    # -------------------------------------------------------------------
    # Register all NetBox API routes
    # -------------------------------------------------------------------
    custom_data = load_mock_data()
    register_netbox_mock_routes(
        app,
        version=resolved_version,
        openapi_document=openapi_doc,
        custom_mock_data=custom_data,
    )

    return app


__all__ = ["create_mock_app"]
