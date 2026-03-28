"""Persistent state models and storage helpers for the GraphQL TUI."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, ValidationError, field_validator

from netbox_sdk.config import config_path


class GraphqlHistoryEntry(BaseModel):
    title: str
    query_text: str
    variables_text: str = ""

    @field_validator("title", "query_text", "variables_text", mode="before")
    @classmethod
    def _coerce_text(cls, value: object) -> str:
        return value if isinstance(value, str) else ""


class GraphqlTuiState(BaseModel):
    theme_name: str | None = None
    last_query_text: str = ""
    last_variables_text: str = ""
    selected_root_field: str | None = None
    history: list[GraphqlHistoryEntry] = Field(default_factory=list)

    @field_validator("theme_name", "selected_root_field", mode="before")
    @classmethod
    def _coerce_optional_text(cls, value: object) -> str | None:
        return value if isinstance(value, str) and value else None

    @field_validator("last_query_text", "last_variables_text", mode="before")
    @classmethod
    def _coerce_text(cls, value: object) -> str:
        return value if isinstance(value, str) else ""


_STATE_FILE = "graphql_tui_state.json"


def _state_scope_key(base_url: str | None = None) -> str:
    raw = str(base_url or "").strip()
    if not raw:
        return "default"
    parsed = urlsplit(raw)
    host = parsed.netloc or parsed.path
    normalized = re.sub(r"[^a-z0-9]+", "-", host.lower()).strip("-")
    return normalized or "default"


def graphql_tui_state_path(base_url: str | None = None) -> Path:
    scope = _state_scope_key(base_url)
    if scope == "default":
        return config_path().parent / _STATE_FILE
    return config_path().parent / f"graphql_tui_state.{scope}.json"


def load_graphql_tui_state(base_url: str | None = None) -> GraphqlTuiState:
    path = graphql_tui_state_path(base_url)
    if not path.exists():
        return GraphqlTuiState()
    try:
        return GraphqlTuiState.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError):
        return GraphqlTuiState()


def save_graphql_tui_state(state: GraphqlTuiState, base_url: str | None = None) -> None:
    path = graphql_tui_state_path(base_url)
    path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
