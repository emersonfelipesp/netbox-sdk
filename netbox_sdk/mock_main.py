"""Standalone mock API server entrypoint for the netbox-sdk mock."""

from __future__ import annotations

import os

import uvicorn

from netbox_sdk.mock.app import create_mock_app

app = create_mock_app()


def run() -> None:
    """Console-script entrypoint: start the NetBox mock API with uvicorn."""
    uvicorn.run(
        "netbox_sdk.mock_main:app",
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8001")),
        reload=os.environ.get("RELOAD", "").lower() in ("1", "true"),
    )


__all__ = ["app", "run"]
