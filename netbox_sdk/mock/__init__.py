"""netbox_sdk.mock — Schema-driven in-memory FastAPI mock for the NetBox REST API."""

from __future__ import annotations

from netbox_sdk.mock.app import create_mock_app
from netbox_sdk.mock.routes import register_netbox_mock_routes
from netbox_sdk.mock.schema_helpers import RefResolver, schema_fingerprint
from netbox_sdk.mock.state import ThreadSafeMockStore, mock_store, reset_mock_state

__all__ = [
    "create_mock_app",
    "register_netbox_mock_routes",
    "ThreadSafeMockStore",
    "mock_store",
    "reset_mock_state",
    "RefResolver",
    "schema_fingerprint",
]
