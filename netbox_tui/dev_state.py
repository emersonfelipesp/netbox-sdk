"""Persistent state models and storage helpers for the developer TUI."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, ValidationError, field_validator

from netbox_sdk.config import config_path


@dataclass(slots=True)
class RequestExecution:
    method: str
    path: str
    query: dict[str, str]
    payload: dict[str, Any] | list[Any] | None
    duration_ms: float


class DevViewState(BaseModel):
    group: str | None = None
    resource: str | None = None
    method: str = "GET"
    path: str = ""
    query_text: str = ""
    body_text: str = ""

    @field_validator("group", "resource", mode="before")
    @classmethod
    def _coerce_optional_str(cls, value: object) -> str | None:
        if not isinstance(value, str):
            return None
        return value or None

    @field_validator("method", "path", "query_text", "body_text", mode="before")
    @classmethod
    def _coerce_text(cls, value: object, info: object) -> str:
        default_map = {
            "method": "GET",
            "path": "",
            "query_text": "",
            "body_text": "",
        }
        if isinstance(value, str):
            return value
        field_name = getattr(info, "field_name", "")
        return default_map.get(field_name, "")


class DevTuiState(BaseModel):
    last_view: DevViewState = Field(default_factory=DevViewState)
    theme_name: str | None = None

    @field_validator("last_view", mode="before")
    @classmethod
    def _coerce_last_view(cls, value: object) -> object:
        if isinstance(value, DevViewState):
            return value.model_dump()
        if not isinstance(value, dict):
            return {}
        return value

    @field_validator("theme_name", mode="before")
    @classmethod
    def _coerce_theme_name(cls, value: object) -> str | None:
        return value if isinstance(value, str) else None


_STATE_FILE = "dev_tui_state.json"


def _state_scope_key(base_url: str | None = None) -> str:
    raw = str(base_url or "").strip()
    if not raw:
        return "default"
    parsed = urlsplit(raw)
    host = parsed.netloc or parsed.path
    normalized = re.sub(r"[^a-z0-9]+", "-", host.lower()).strip("-")
    return normalized or "default"


def dev_tui_state_path(base_url: str | None = None) -> Path:
    scope = _state_scope_key(base_url)
    if scope == "default":
        return config_path().parent / _STATE_FILE
    return config_path().parent / f"dev_tui_state.{scope}.json"


def load_dev_tui_state(base_url: str | None = None) -> DevTuiState:
    path = dev_tui_state_path(base_url)
    if not path.exists():
        return DevTuiState()
    try:
        return DevTuiState.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError):
        return DevTuiState()


def save_dev_tui_state(state: DevTuiState, base_url: str | None = None) -> None:
    path = dev_tui_state_path(base_url)
    path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
