"""Persistent state models and storage helpers for the main TUI."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, ValidationError, field_validator

from netbox_sdk.config import config_path


class ViewState(BaseModel):
    group: str | None = None
    resource: str | None = None
    query_text: str = ""
    details_expanded: bool = False

    @field_validator("group", "resource", mode="before")
    @classmethod
    def _coerce_optional_str(cls, v: object) -> str | None:
        if not isinstance(v, str):
            return None
        return v or None

    @field_validator("query_text", mode="before")
    @classmethod
    def _coerce_query_text(cls, v: object) -> str:
        return v if isinstance(v, str) else ""

    @field_validator("details_expanded", mode="before")
    @classmethod
    def _coerce_bool(cls, v: object) -> bool:
        return bool(v)


class TuiState(BaseModel):
    last_view: ViewState = Field(default_factory=ViewState)
    theme_name: str | None = None

    @field_validator("last_view", mode="before")
    @classmethod
    def _coerce_last_view(cls, v: object) -> object:
        # Coerce null/non-dict to an empty dict so ViewState uses its defaults.
        if isinstance(v, ViewState):
            return v.model_dump()
        if not isinstance(v, dict):
            return {}
        return v

    @field_validator("theme_name", mode="before")
    @classmethod
    def _coerce_theme_name(cls, v: object) -> str | None:
        return v if isinstance(v, str) else None


_STATE_FILE = "tui_state.json"


def _state_scope_key(base_url: str | None = None) -> str:
    raw = str(base_url or "").strip()
    if not raw:
        return "default"
    parsed = urlsplit(raw)
    host = parsed.netloc or parsed.path
    normalized = re.sub(r"[^a-z0-9]+", "-", host.lower()).strip("-")
    return normalized or "default"


def tui_state_path(base_url: str | None = None) -> Path:
    scope = _state_scope_key(base_url)
    if scope == "default":
        return config_path().parent / _STATE_FILE
    return config_path().parent / f"tui_state.{scope}.json"


def load_tui_state(base_url: str | None = None) -> TuiState:
    path = tui_state_path(base_url)
    if not path.exists():
        return TuiState()
    try:
        return TuiState.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError):
        return TuiState()


def save_tui_state(state: TuiState, base_url: str | None = None) -> None:
    path = tui_state_path(base_url)
    path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
