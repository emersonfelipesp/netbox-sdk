"""Persistent state models and storage helpers for the Django Model Inspector TUI."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ValidationError, field_validator

from netbox_sdk.config import config_path


class DjangoModelTuiState(BaseModel):
    theme_name: str | None = None

    @field_validator("theme_name", mode="before")
    @classmethod
    def _coerce_theme_name(cls, value: object) -> str | None:
        return value if isinstance(value, str) else None


_STATE_FILE = "django_model_tui_state.json"


def django_model_tui_state_path() -> Path:
    return config_path().parent / _STATE_FILE


def load_django_model_tui_state() -> DjangoModelTuiState:
    path = django_model_tui_state_path()
    if not path.exists():
        return DjangoModelTuiState()
    try:
        return DjangoModelTuiState.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError):
        return DjangoModelTuiState()


def save_django_model_tui_state(state: DjangoModelTuiState) -> None:
    path = django_model_tui_state_path()
    path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
