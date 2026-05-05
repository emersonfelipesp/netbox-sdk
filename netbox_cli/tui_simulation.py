"""Generate fixture-backed SVG states for the main NetBox Textual TUI."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO
from unittest.mock import AsyncMock, patch

from netbox_sdk.client import ApiResponse, ConnectionProbe
from netbox_sdk.config import DEMO_BASE_URL, Config
from netbox_sdk.schema import build_schema_index

COMMAND = "nbx tui"
SCHEMA_VERSION = 1
TERMINAL_COLUMNS = 200
TERMINAL_ROWS = 60
THEMES: tuple[str, ...] = (
    "netbox-dark",
    "netbox-light",
    "dracula",
    "tokyo-night",
    "onedark-pro",
)
STATE_IDS: tuple[str, ...] = ("home", "devices", "details", "filter", "support")

_DOCGEN_SOURCE_ARTIFACTS: tuple[str, ...] = (
    "docs/generated/raw/035-tui-main-browser-nbx-tui-help.json",
    "docs/generated/raw/036-tui-main-browser-nbx-tui-theme.json",
    "docs/generated/raw/037-tui-main-browser-nbx-demo-tui-help.json",
)

_DEVICE_ROWS: tuple[dict[str, Any], ...] = (
    {
        "id": 1,
        "name": "dmi01-akron-rtr01",
        "display": "dmi01-akron-rtr01",
        "status": "active",
        "site": {"id": 1, "display": "DM-Akron"},
        "role": {"id": 3, "display": "Router"},
        "primary_ip4": {"id": 40, "display": "192.0.2.10/24"},
    },
    {
        "id": 2,
        "name": "dmi01-akron-sw01",
        "display": "dmi01-akron-sw01",
        "status": "planned",
        "site": {"id": 1, "display": "DM-Akron"},
        "role": {"id": 4, "display": "Switch"},
        "primary_ip4": {"id": 41, "display": "192.0.2.11/24"},
    },
    {
        "id": 3,
        "name": "dmi01-cincy-rtr01",
        "display": "dmi01-cincy-rtr01",
        "status": "offline",
        "site": {"id": 2, "display": "DM-Cincinnati"},
        "role": {"id": 3, "display": "Router"},
        "primary_ip4": {"id": 42, "display": "192.0.2.12/24"},
    },
)

_DEVICE_DETAILS: Mapping[int, dict[str, Any]] = {
    1: {
        **_DEVICE_ROWS[0],
        "device_type": {"id": 10, "display": "ISR 4451-X"},
        "serial": "FTX1234A1B2",
        "tenant": {"id": 7, "display": "Operations"},
        "last_updated": "2026-05-05T00:00:00Z",
    },
    2: {
        **_DEVICE_ROWS[1],
        "device_type": {"id": 11, "display": "Catalyst 9300"},
        "serial": "CAT9300A1B2",
        "tenant": {"id": 7, "display": "Operations"},
        "last_updated": "2026-05-05T00:00:00Z",
    },
    3: {
        **_DEVICE_ROWS[2],
        "device_type": {"id": 12, "display": "MX204"},
        "serial": "JNPR204A1B2",
        "tenant": {"id": 8, "display": "Transport"},
        "last_updated": "2026-05-05T00:00:00Z",
    },
}


class SimulationClient:
    """Small deterministic API client used only for docgen TUI simulation."""

    def __init__(self) -> None:
        self.config = Config(
            base_url=DEMO_BASE_URL,
            token_key="docgen",
            token_secret="docgen",
            ssl_verify=True,
        )

    async def probe_connection(self) -> ConnectionProbe:
        return ConnectionProbe(status=200, version="4.6", ok=True, error=None)

    async def close(self) -> None:
        return None

    async def request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        payload: dict[str, Any] | list[Any] | None = None,
    ) -> ApiResponse:
        del method, payload
        if path == "/api/dcim/devices/":
            rows = list(_DEVICE_ROWS)
            if query:
                rows = _filter_device_rows(rows, query)
            return ApiResponse(
                status=200,
                text=json.dumps(
                    {
                        "count": len(rows),
                        "next": None,
                        "previous": None,
                        "results": rows,
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        if path.startswith("/api/dcim/devices/"):
            device_id = _parse_detail_id(path)
            detail = _DEVICE_DETAILS.get(device_id, _DEVICE_DETAILS[1])
            return ApiResponse(
                status=200,
                text=json.dumps(detail),
                headers={"Content-Type": "application/json"},
            )

        return ApiResponse(
            status=200,
            text=json.dumps({"count": 0, "next": None, "previous": None, "results": []}),
            headers={"Content-Type": "application/json"},
        )


def simulation_filename(state_id: str, theme_name: str) -> str:
    """Return the stable SVG filename for a state/theme pair."""
    return f"main-browser-{state_id}-{theme_name}.svg"


def resolve_tui_simulation_paths(
    output: Path | None,
    assets_dir: Path | None,
) -> tuple[Path, Path]:
    """Resolve default paths under ``docs/generated/tui-simulation``."""
    default_dir = _repo_root() / "docs" / "generated" / "tui-simulation"
    docs_dir = _repo_root() / "docs"
    if not docs_dir.is_dir():
        if output is None or assets_dir is None:
            raise FileNotFoundError(
                "Cannot infer default TUI simulation paths: no docs/ directory next to "
                "netbox_cli. Run from the netbox-sdk checkout or pass --output and "
                "--assets-dir."
            )
        return output, assets_dir
    if output is None:
        output = default_dir / "main-browser.json"
    if assets_dir is None:
        assets_dir = output.parent
    return output, assets_dir


def generate_tui_simulation(
    *,
    output: Path,
    assets_dir: Path,
    log: TextIO | None = None,
) -> int:
    """Capture main-browser TUI states and write a structured manifest."""
    log = log or sys.stderr
    output.parent.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    for existing in assets_dir.glob("main-browser-*.svg"):
        existing.unlink()

    with tempfile.TemporaryDirectory(prefix="nbx-tui-simulation-") as config_home:
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": config_home}):
            captures = asyncio.run(_capture_all_states(assets_dir=assets_dir, log=log))

    manifest = build_manifest(
        captures=captures,
        generated_at=datetime.now(UTC).isoformat(),
        source_commit=_source_commit(),
        source_artifacts=_source_artifacts(),
    )
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output}", file=log)
    print(f"Wrote {len(STATE_IDS) * len(THEMES)} SVG captures under {assets_dir}", file=log)
    return 0


def build_manifest(
    *,
    captures: Mapping[str, Mapping[str, Mapping[str, Any]]],
    generated_at: str,
    source_commit: str,
    source_artifacts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the JSON-serializable simulation manifest."""
    states = []
    for state_id in STATE_IDS:
        theme_captures = captures.get(state_id, {})
        states.append(
            {
                "id": state_id,
                "captures": {
                    theme: theme_captures[theme] for theme in THEMES if theme in theme_captures
                },
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "command": COMMAND,
        "generated_at": generated_at,
        "source_commit": source_commit,
        "terminal_size": {"columns": TERMINAL_COLUMNS, "rows": TERMINAL_ROWS},
        "themes": list(THEMES),
        "state_ids": list(STATE_IDS),
        "states": states,
        "source_artifacts": source_artifacts or [],
    }


async def _capture_all_states(
    *,
    assets_dir: Path,
    log: TextIO,
) -> dict[str, dict[str, dict[str, Any]]]:
    captures: dict[str, dict[str, dict[str, Any]]] = {state_id: {} for state_id in STATE_IDS}
    for state_id in STATE_IDS:
        for theme_name in THEMES:
            print(f"Capturing {state_id}/{theme_name}...", file=log)
            captures[state_id][theme_name] = await _capture_state(
                state_id=state_id,
                theme_name=theme_name,
                assets_dir=assets_dir,
            )
    return captures


async def _capture_state(
    *,
    state_id: str,
    theme_name: str,
    assets_dir: Path,
) -> dict[str, Any]:
    from netbox_tui.app import NetBoxTuiApp  # noqa: PLC0415
    from netbox_tui.state import TuiState, ViewState  # noqa: PLC0415

    openapi_path = _repo_root() / "netbox_sdk" / "reference" / "openapi" / "netbox-openapi.json"
    index = build_schema_index(openapi_path)
    last_view = (
        ViewState(group="dcim", resource="devices")
        if state_id in {"devices", "details", "filter", "support"}
        else ViewState()
    )
    state = TuiState(last_view=last_view)
    filename = simulation_filename(state_id, theme_name)

    with (
        patch("netbox_tui.app.load_tui_state", return_value=state),
        patch("netbox_tui.app.save_tui_state", return_value=None),
        patch(
            "netbox_tui.app.enrich_schema_index_with_runtime_resources",
            AsyncMock(return_value=False),
        ),
    ):
        app = NetBoxTuiApp(client=SimulationClient(), index=index, theme_name=theme_name)
        async with app.run_test(size=(TERMINAL_COLUMNS, TERMINAL_ROWS)) as pilot:
            await _settle(pilot)
            if state_id in {"devices", "details", "filter", "support"}:
                await _wait_for_rows(app, pilot)
            if state_id == "details":
                app.action_show_details()
                await _settle(pilot)
            elif state_id == "filter":
                app.action_filter_modal()
                await _settle(pilot)
            elif state_id == "support":
                app.on_support_pressed()
                await _settle(pilot)

            app.save_screenshot(filename=filename, path=str(assets_dir))
            hotspots = _hotspots_for_state(app, state_id)
            app.exit()

    return {"svg": filename, "hotspots": hotspots}


async def _settle(pilot: Any, *, count: int = 3, delay: float = 0.05) -> None:
    for _ in range(count):
        await pilot.pause(delay)


async def _wait_for_rows(app: Any, pilot: Any) -> None:
    for _ in range(20):
        if getattr(app, "current_rows", None):
            await _settle(pilot)
            return
        await pilot.pause(0.05)


def _hotspots_for_state(app: Any, state_id: str) -> list[dict[str, Any]]:
    if state_id == "support":
        screen = app.screen_stack[-1]
        hotspot = _hotspot(
            screen,
            selector="#support_modal_close",
            hotspot_id="close-support",
            label="Close support dialog",
            action="state",
            target_state="devices",
        )
        return [hotspot] if hotspot is not None else []

    definitions: list[tuple[str, str, str, str, str | None]] = []
    if state_id == "home":
        definitions.append(("open-devices", "#nav_tree", "Open devices", "state", "devices"))
    if state_id == "devices":
        definitions.append(("show-details", "#results_table", "Show details", "state", "details"))
    if state_id in {"devices", "details"}:
        definitions.append(("choose-filter", "#filter_select", "Choose filter", "state", "filter"))
    if state_id == "filter":
        definitions.append(
            ("close-filter", "#filter_picker_cancel", "Close filter picker", "state", "devices")
        )
    if state_id in {"devices", "details"}:
        definitions.append(
            ("open-support", "#support_button", "Open support dialog", "state", "support")
        )
    if state_id in {"home", "devices", "details", "filter"}:
        definitions.append(("close-tui", "#close_tui_button", "Close TUI", "close", None))

    hotspots: list[dict[str, Any]] = []
    for hotspot_id, selector, label, action, target_state in definitions:
        hotspot = _hotspot(
            app,
            selector=selector,
            hotspot_id=hotspot_id,
            label=label,
            action=action,
            target_state=target_state,
        )
        if hotspot is not None:
            hotspots.append(hotspot)
    return hotspots


def _hotspot(
    scope: Any,
    *,
    selector: str,
    hotspot_id: str,
    label: str,
    action: str,
    target_state: str | None,
) -> dict[str, Any] | None:
    try:
        widget = scope.query_one(selector, object)
    except Exception:
        return None
    region = getattr(widget, "region", None)
    if region is None or region.width <= 0 or region.height <= 0:
        return None
    payload: dict[str, Any] = {
        "id": hotspot_id,
        "label": label,
        "action": action,
        "widget_id": selector.removeprefix("#"),
        "region": {
            "x": int(region.x),
            "y": int(region.y),
            "width": int(region.width),
            "height": int(region.height),
        },
    }
    if target_state is not None:
        payload["target_state"] = target_state
    return payload


def _filter_device_rows(
    rows: list[dict[str, Any]],
    query: Mapping[str, Any],
) -> list[dict[str, Any]]:
    filtered = rows
    for key, value in query.items():
        if key == "q":
            needle = str(value).lower()
            filtered = [
                row
                for row in filtered
                if needle in str(row.get("name", "")).lower()
                or needle in str(row.get("display", "")).lower()
            ]
            continue
        filtered = [row for row in filtered if str(row.get(key, "")) == str(value)]
    return filtered


def _parse_detail_id(path: str) -> int:
    parts = [part for part in path.split("/") if part]
    try:
        return int(parts[-1])
    except (IndexError, ValueError):
        return 1


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _source_commit() -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=_repo_root(),
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return completed.stdout.strip() or "unknown"


def _source_artifacts() -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    root = _repo_root()
    for relative in _DOCGEN_SOURCE_ARTIFACTS:
        path = root / relative
        entry: dict[str, Any] = {"path": relative, "exists": path.exists()}
        if path.exists():
            entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        artifacts.append(entry)
    return artifacts
