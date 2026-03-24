#!/usr/bin/env python3
"""Capture screenshots of all TUI applications across all themes using demo.netbox.dev.

Usage:
    python scripts/tui_screenshots.py

Requirements:
    - Demo profile must be configured (run 'nbx demo init' first)
    - Or set DEMO_USERNAME and DEMO_PASSWORD environment variables

Output: docs/assets/screenshots/tui-{app}-{theme}.svg
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

# Configuration
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
SCREENSHOTS_DIR = REPO_ROOT / "docs" / "assets" / "screenshots"

# Terminal size for Full HD screenshots
TERMINAL_WIDTH = 200
TERMINAL_HEIGHT = 60

# All available themes
THEMES = [
    "netbox-dark",
    "netbox-light",
    "dracula",
    "tokyo-night",
    "onedark-pro",
]

# TUI apps to capture: (id, app_class_name, module_path)
TUIS = [
    ("main", "NetBoxTuiApp", "netbox_cli.ui.app"),
    ("dev", "NetBoxDevTuiApp", "netbox_cli.ui.dev_app"),
    ("logs", "NetBoxLogsTuiApp", "netbox_cli.ui.logs_app"),
    ("cli", "NbxCliTuiApp", "netbox_cli.ui.cli_tui"),
    ("django", "DjangoModelTuiApp", "netbox_cli.ui.django_model_app"),
]


def get_demo_client() -> Any:
    """Get an authenticated demo NetBox API client."""
    from netbox_cli.api import NetBoxApiClient
    from netbox_cli.config import DEMO_PROFILE, load_profile_config

    # Try to load existing demo profile
    try:
        config = load_profile_config(DEMO_PROFILE)

        if config.token_secret:
            print("  Using existing demo token")
        else:
            raise RuntimeError("No demo token available")

    except Exception as e:
        # No existing demo profile - try environment variables
        username = os.environ.get("DEMO_USERNAME")
        password = os.environ.get("DEMO_PASSWORD")

        if not username or not password:
            raise RuntimeError(
                f"Demo profile not configured. Either run 'nbx demo init' first, "
                f"or set DEMO_USERNAME and DEMO_PASSWORD environment variables.\n"
                f"Error: {e}"
            )

        from netbox_cli.demo_auth import bootstrap_demo_profile

        config = bootstrap_demo_profile(
            username=username,
            password=password,
            timeout=30.0,
            headless=True,
        )

    return NetBoxApiClient(config)


def get_mock_executor():
    """Create a mock CLI executor for CLI TUI."""

    def executor(cmd: list[str]) -> tuple[int, str]:
        return (0, "Mock CLI output")

    return executor


def create_django_store():
    """Create a mock DjangoModelStore for Django TUI."""
    from netbox_cli.django_models.store import DjangoModelStore

    # Create a minimal cache file for testing
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

    # Create temp file
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(cache_data, f)
        temp_path = f.name

    # Create store with temp path
    store = DjangoModelStore(cache_path=Path(temp_path))
    return store


async def capture_screenshot_for_tui(
    app_class: type,
    app_kwargs: dict,
    app_id: str,
) -> str:
    """Capture a screenshot of a TUI app."""

    # Create app
    try:
        app = app_class(**app_kwargs)
    except Exception as e:
        print(f"Failed to create app: {e}")
        raise

    # Run app in test mode and capture screenshot
    try:
        async with app.run_test(
            size=(TERMINAL_WIDTH, TERMINAL_HEIGHT),
        ) as pilot:
            await pilot.pause()

            # Give more time for UI to render
            await pilot.pause()

            # Capture screenshot
            filename = f"tui-{app_id}-{app_kwargs.get('theme_name', 'default')}.svg"
            output_path = SCREENSHOTS_DIR / filename

            app.save_screenshot(
                filename=filename,
                path=str(SCREENSHOTS_DIR),
            )

            return str(output_path)

    except Exception as e:
        raise Exception(f"Error capturing screenshot: {e}")


def get_app_kwargs(app_id: str, theme: str, index: Any, client: Any) -> dict:
    """Get the appropriate kwargs for each TUI app."""

    if app_id == "main":
        return {
            "client": client,
            "index": index,
            "theme_name": theme,
        }

    elif app_id == "dev":
        with patch("netbox_cli.ui.dev_app.load_dev_tui_state", return_value=MagicMock()):
            with patch("netbox_cli.ui.dev_app.save_dev_tui_state", return_value=None):
                return {
                    "client": client,
                    "index": index,
                    "theme_name": theme,
                }

    elif app_id == "logs":
        # Create a temporary log file for the logs TUI
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            log_entries = [
                {
                    "v": 1,
                    "ts": "2024-01-15T10:30:00Z",
                    "level": "INFO",
                    "logger": "cli",
                    "message": "Application started",
                    "module": "cli",
                },
                {
                    "v": 1,
                    "ts": "2024-01-10T10:30:01Z",
                    "level": "WARNING",
                    "logger": "config",
                    "message": "Config file not found, using defaults",
                    "module": "config",
                },
                {
                    "v": 1,
                    "ts": "2024-01-10T10:30:02Z",
                    "level": "ERROR",
                    "logger": "api",
                    "message": "Connection failed to NetBox server",
                    "module": "api",
                },
                {
                    "v": 1,
                    "ts": "2024-01-10T10:30:03Z",
                    "level": "DEBUG",
                    "logger": "api",
                    "message": "Retrying connection attempt 1/3",
                    "module": "api",
                },
                {
                    "v": 1,
                    "ts": "2024-01-10T10:30:05Z",
                    "level": "INFO",
                    "logger": "api",
                    "message": "Successfully connected to NetBox",
                    "module": "api",
                },
            ]
            for entry in log_entries:
                f.write(json.dumps(entry) + "\n")

        return {
            "theme_name": theme,
            "limit": 200,
        }

    elif app_id == "cli":
        return {
            "client": client,
            "index": index,
            "executor": get_mock_executor(),
            "theme_name": theme,
        }

    elif app_id == "django":
        return {
            "store": create_django_store(),
            "theme_name": theme,
        }

    return {}


async def main():
    """Main entry point - capture all TUI screenshots from demo.netbox.dev."""

    # Create output directory
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {SCREENSHOTS_DIR}")
    print("Connecting to demo.netbox.dev...")

    # Load schema index
    sys.path.insert(0, str(REPO_ROOT))
    from netbox_cli.schema import build_schema_index

    openapi_path = REPO_ROOT / "reference" / "openapi" / "netbox-openapi.json"
    index = build_schema_index(openapi_path)

    # Get demo client
    try:
        demo_client = get_demo_client()
        print("✓ Connected to demo.netbox.dev")
    except Exception as e:
        print(f"✗ Failed to connect to demo: {e}")
        sys.exit(1)

    total = len(TUIS) * len(THEMES)
    current = 0
    success_count = 0
    failed = []

    for app_id, app_class_name, module_path in TUIS:
        # Import the app class dynamically
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
                result = await capture_screenshot_for_tui(
                    app_class,
                    app_kwargs,
                    app_id,
                )
                if result:
                    print(f"✓ Saved: {Path(result).name}")
                    success_count += 1
                else:
                    print("✗ Failed")
                    failed.append(f"{app_id}/{theme}")
            except Exception as e:
                print(f"✗ Error: {type(e).__name__}: {e}")
                failed.append(f"{app_id}/{theme}")

    print(f"\n{'=' * 60}")
    print("Screenshot capture complete!")
    print(f"Output: {SCREENSHOTS_DIR}")
    print(f"{'=' * 60}")

    # List all captured files
    svg_files = list(SCREENSHOTS_DIR.glob("*.svg"))
    print(f"\nCaptured {len(svg_files)}/{total} screenshots:")
    for f in sorted(svg_files):
        print(f"  - {f.name}")

    if failed:
        print(f"\nFailed captures: {', '.join(failed)}")


if __name__ == "__main__":
    from unittest.mock import MagicMock, patch

    asyncio = __import__("asyncio")
    asyncio.run(main())
