#!/usr/bin/env python3
"""Example 6: Running the mock as a standalone HTTP server.

Starts the mock API server on localhost so you can interact with it
via curl, Postman, or any HTTP client — as if it were a real NetBox.

Usage (foreground):
    uv run python examples/mock-api/06_standalone_server.py

Or via the installed script:
    uv run nbx-mock

Environment variables:
    NETBOX_MOCK_VERSION  NetBox release line to simulate (default: 4.5)
    HOST                 Bind address (default: 0.0.0.0)
    PORT                 Listen port (default: 8001)

Then try:
    curl http://localhost:8001/health
    curl http://localhost:8001/api/status/
    curl http://localhost:8001/api/dcim/sites/
    curl -X POST http://localhost:8001/api/dcim/sites/ \\
         -H 'Content-Type: application/json' \\
         -d '{"name": "My Site", "slug": "my-site"}'
    curl http://localhost:8001/docs    # Swagger UI
"""

import os

import uvicorn

from netbox_sdk.mock import create_mock_app

app = create_mock_app()

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8001"))
    version = os.environ.get("NETBOX_MOCK_VERSION", "4.5")

    print("=" * 60)
    print("NetBox Mock API Server")
    print("=" * 60)
    print(f"  NetBox version : {version}")
    print(f"  Listening on   : http://{host}:{port}")
    print(f"  Swagger UI     : http://localhost:{port}/docs")
    print(f"  Health check   : http://localhost:{port}/health")
    print(f"  API status     : http://localhost:{port}/api/status/")
    print()
    print("Press Ctrl+C to stop.")
    print("=" * 60)

    uvicorn.run(app, host=host, port=port)
