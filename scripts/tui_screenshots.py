#!/usr/bin/env python3
"""Capture screenshots of all TUI applications across all themes.

Usage:
    python scripts/tui_screenshots.py

Output:
    docs/assets/screenshots/tui-{app}-{theme}.svg
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
SCREENSHOTS_DIR = REPO_ROOT / "docs" / "assets" / "screenshots"
TERMINAL_WIDTH = 200
TERMINAL_HEIGHT = 60

THEMES = [
    "netbox-dark",
    "netbox-light",
    "dracula",
    "tokyo-night",
    "onedark-pro",
]

# TUI apps to capture: (id, app_class_name, module_path)
TUIS = [
    ("main", "NetBoxTuiApp", "netbox_tui.app"),
    ("dev", "NetBoxDevTuiApp", "netbox_tui.dev_app"),
    ("graphql", "NetBoxGraphqlTuiApp", "netbox_tui.graphql_app"),
    ("logs", "NetBoxLogsTuiApp", "netbox_tui.logs_app"),
    ("cli", "NbxCliTuiApp", "netbox_tui.cli_tui"),
    ("django", "DjangoModelTuiApp", "netbox_tui.django_model_app"),
]

_GRAPHQL_INTROSPECTION_PAYLOAD = {
    "data": {
        "__schema": {
            "queryType": {"name": "Query"},
            "types": [
                {
                    "kind": "OBJECT",
                    "name": "Query",
                    "description": "Root query",
                    "fields": [
                        {
                            "name": "device_list",
                            "description": "List devices",
                            "args": [
                                {
                                    "name": "filters",
                                    "description": None,
                                    "defaultValue": None,
                                    "type": {
                                        "kind": "INPUT_OBJECT",
                                        "name": "DeviceFilter",
                                        "ofType": None,
                                    },
                                },
                                {
                                    "name": "pagination",
                                    "description": None,
                                    "defaultValue": None,
                                    "type": {
                                        "kind": "INPUT_OBJECT",
                                        "name": "OffsetPaginationInput",
                                        "ofType": None,
                                    },
                                },
                            ],
                            "type": {
                                "kind": "LIST",
                                "name": None,
                                "ofType": {"kind": "OBJECT", "name": "DeviceType", "ofType": None},
                            },
                        }
                    ],
                    "inputFields": [],
                    "enumValues": [],
                    "possibleTypes": [],
                },
                {
                    "kind": "OBJECT",
                    "name": "DeviceType",
                    "description": "Device",
                    "fields": [
                        {
                            "name": "id",
                            "description": None,
                            "args": [],
                            "type": {"kind": "SCALAR", "name": "ID", "ofType": None},
                        },
                        {
                            "name": "name",
                            "description": None,
                            "args": [],
                            "type": {"kind": "SCALAR", "name": "String", "ofType": None},
                        },
                    ],
                    "inputFields": [],
                    "enumValues": [],
                    "possibleTypes": [],
                },
                {
                    "kind": "INPUT_OBJECT",
                    "name": "DeviceFilter",
                    "description": "Filter",
                    "fields": [],
                    "inputFields": [
                        {
                            "name": "name",
                            "description": None,
                            "defaultValue": None,
                            "type": {"kind": "SCALAR", "name": "String", "ofType": None},
                        }
                    ],
                    "enumValues": [],
                    "possibleTypes": [],
                },
                {
                    "kind": "INPUT_OBJECT",
                    "name": "OffsetPaginationInput",
                    "description": "Pagination",
                    "fields": [],
                    "inputFields": [
                        {
                            "name": "limit",
                            "description": None,
                            "defaultValue": None,
                            "type": {"kind": "SCALAR", "name": "Int", "ofType": None},
                        },
                        {
                            "name": "offset",
                            "description": None,
                            "defaultValue": None,
                            "type": {"kind": "SCALAR", "name": "Int", "ofType": None},
                        },
                    ],
                    "enumValues": [],
                    "possibleTypes": [],
                },
            ],
        }
    }
}


def get_demo_client() -> Any:
    """Get an authenticated demo NetBox API client."""
    from netbox_sdk.client import NetBoxApiClient
    from netbox_sdk.config import DEMO_PROFILE, load_profile_config

    try:
        config = load_profile_config(DEMO_PROFILE)
        if config.token_secret or (config.token_key and config.token_secret):
            print("  Using existing demo token")
        else:
            raise RuntimeError("No demo token available")
    except Exception as e:
        username = os.environ.get("DEMO_USERNAME")
        password = os.environ.get("DEMO_PASSWORD")
        if not username or not password:
            raise RuntimeError(
                f"Demo profile not configured. Either run 'nbx demo init' first, "
                f"or set DEMO_USERNAME and DEMO_PASSWORD environment variables.\n"
                f"Error: {e}"
            )
        from netbox_sdk.demo_auth import bootstrap_demo_profile

        config = bootstrap_demo_profile(
            username=username,
            password=password,
            timeout=30.0,
            headless=True,
        )
    return NetBoxApiClient(config)


def get_mock_executor() -> Any:
    def executor(cmd: list[str]) -> tuple[int, str]:
        return (0, "Mock CLI output")

    return executor


def create_django_store() -> Any:
    from netbox_sdk.django_models.store import DjangoModelStore

    cache_data = {
        "models": {
            "dcim.Device": {"app": "dcim", "name": "Device", "fields": []},
            "dcim.Site": {"app": "dcim", "name": "Site", "fields": []},
            "ipam.IPAddress": {"app": "ipam", "name": "IPAddress", "fields": []},
        },
        "edges": [],
        "stats": {"total_models": 3, "total_edges": 0, "apps": ["dcim", "ipam"]},
        "meta": {
            "source_path": "/mock",
            "total_models": 3,
            "total_edges": 0,
            "apps": ["dcim", "ipam"],
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(cache_data, f)
        temp_path = f.name
    return DjangoModelStore(cache_path=Path(temp_path))


def create_graphql_screenshot_client(base_client: Any) -> Any:
    """Wrap the live demo client with deterministic GraphQL responses for screenshots."""
    from netbox_sdk.client import ConnectionProbe

    client = MagicMock()
    client.config = base_client.config
    client.probe_connection = AsyncMock(
        return_value=ConnectionProbe(status=200, version="4.2", ok=True, error=None)
    )
    client.request = AsyncMock(
        return_value=type(
            "Response",
            (),
            {
                "status": 200,
                "text": "{}",
                "headers": {"Content-Type": "application/json", "API-Version": "4.2"},
            },
        )()
    )

    async def graphql(query: str, variables: dict[str, Any] | None = None) -> Any:
        del variables
        if "__schema" in query:
            payload = _GRAPHQL_INTROSPECTION_PAYLOAD
        else:
            payload = {
                "data": {
                    "device_list": [
                        {"id": 1, "name": "edge-core-01"},
                        {"id": 2, "name": "leaf-nyc-02"},
                    ]
                }
            }
        return type(
            "Response",
            (),
            {
                "status": 200,
                "text": json.dumps(payload),
                "headers": {"Content-Type": "application/json"},
                "json": lambda self=None: payload,
            },
        )()

    client.graphql = AsyncMock(side_effect=graphql)
    return client


def screenshot_state_patches(app_id: str) -> list[Any]:
    """Return context-manager patches needed to isolate persisted TUI state."""
    if app_id == "dev":
        return [
            patch("netbox_tui.dev_app.load_dev_tui_state", return_value=MagicMock()),
            patch("netbox_tui.dev_app.save_dev_tui_state", return_value=None),
        ]
    if app_id == "graphql":
        from netbox_tui.graphql_state import GraphqlTuiState

        return [
            patch(
                "netbox_tui.graphql_app.load_graphql_tui_state",
                return_value=GraphqlTuiState(
                    last_query_text="query {\n  device_list {\n    id\n    name\n  }\n}",
                    last_variables_text='{"site": "nyc"}',
                    selected_root_field="device_list",
                ),
            ),
            patch("netbox_tui.graphql_app.save_graphql_tui_state", return_value=None),
        ]
    if app_id == "django":
        from netbox_tui.django_model_state import DjangoModelTuiState

        return [
            patch(
                "netbox_tui.django_model_app.load_django_model_tui_state",
                return_value=DjangoModelTuiState(theme_name="netbox-dark"),
            ),
            patch("netbox_tui.django_model_app.save_django_model_tui_state", return_value=None),
        ]
    return []


async def capture_screenshot_for_tui(
    app_class: type,
    app_kwargs: dict[str, Any],
    app_id: str,
) -> str:
    """Capture a screenshot of a TUI app."""
    patches = screenshot_state_patches(app_id)
    started: list[Any] = []
    try:
        for item in patches:
            started.append(item)
            item.start()
        app = app_class(**app_kwargs)
        async with app.run_test(size=(TERMINAL_WIDTH, TERMINAL_HEIGHT)) as pilot:
            await pilot.pause()
            await pilot.pause()
            filename = f"tui-{app_id}-{app_kwargs.get('theme_name', 'default')}.svg"
            output_path = SCREENSHOTS_DIR / filename
            app.save_screenshot(filename=filename, path=str(SCREENSHOTS_DIR))
            return str(output_path)
    except Exception as e:
        raise RuntimeError(f"Error capturing screenshot: {e}") from e
    finally:
        for item in reversed(started):
            item.stop()


def get_app_kwargs(app_id: str, theme: str, index: Any, client: Any) -> dict[str, Any]:
    """Get the appropriate kwargs for each TUI app."""
    if app_id == "main":
        return {"client": client, "index": index, "theme_name": theme}
    if app_id == "dev":
        return {"client": client, "index": index, "theme_name": theme}
    if app_id == "graphql":
        return {"client": create_graphql_screenshot_client(client), "theme_name": theme}
    if app_id == "logs":
        return {"theme_name": theme, "limit": 200}
    if app_id == "cli":
        return {
            "client": client,
            "index": index,
            "executor": get_mock_executor(),
            "theme_name": theme,
        }
    if app_id == "django":
        return {"store": create_django_store(), "theme_name": theme}
    return {}


async def main() -> None:
    """Main entry point - capture all TUI screenshots from demo.netbox.dev."""
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {SCREENSHOTS_DIR}")
    print("Connecting to demo.netbox.dev...")

    from netbox_sdk.schema import build_schema_index

    openapi_path = REPO_ROOT / "reference" / "openapi" / "netbox-openapi.json"
    index = build_schema_index(openapi_path)

    try:
        demo_client = get_demo_client()
        print("✓ Connected to demo.netbox.dev")
    except Exception as e:
        print(f"✗ Failed to connect to demo: {e}")
        raise SystemExit(1) from e

    total = len(TUIS) * len(THEMES)
    current = 0
    success_count = 0
    failed: list[str] = []

    for app_id, app_class_name, module_path in TUIS:
        module = __import__(module_path, fromlist=[app_class_name])
        app_class = getattr(module, app_class_name)

        print(f"\n{'=' * 60}")
        print(f"Capturing: {app_id} ({app_class_name})")
        print(f"{'=' * 60}")

        for theme in THEMES:
            current += 1
            print(f"[{current}/{total}] {app_id} with {theme}...", end=" ", flush=True)
            try:
                app_kwargs = get_app_kwargs(app_id, theme, index, demo_client)
                result = await capture_screenshot_for_tui(app_class, app_kwargs, app_id)
                print(f"✓ Saved: {Path(result).name}")
                success_count += 1
            except Exception as e:
                print(f"✗ Error: {type(e).__name__}: {e}")
                failed.append(f"{app_id}/{theme}")

    print(f"\n{'=' * 60}")
    print("Screenshot capture complete!")
    print(f"Output: {SCREENSHOTS_DIR}")
    print(f"{'=' * 60}")

    svg_files = list(SCREENSHOTS_DIR.glob("*.svg"))
    print(f"\nCaptured {len(svg_files)}/{total} screenshots:")
    for f in sorted(svg_files):
        print(f"  - {f.name}")
    if failed:
        print(f"\nFailed captures: {', '.join(failed)}")
    if success_count != total:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
