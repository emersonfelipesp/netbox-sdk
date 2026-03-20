from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from netbox_cli.config import config_path


@dataclass(slots=True)
class ViewState:
    group: str | None = None
    resource: str | None = None
    query_text: str = ""
    details_expanded: bool = False


@dataclass(slots=True)
class TuiState:
    last_view: ViewState
    theme_name: str | None = None


_STATE_FILE = "tui_state.json"



def tui_state_path() -> Path:
    return config_path().parent / _STATE_FILE



def load_tui_state() -> TuiState:
    path = tui_state_path()
    if not path.exists():
        return TuiState(last_view=ViewState(), theme_name=None)

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return TuiState(last_view=ViewState(), theme_name=None)

    view = raw.get("last_view") if isinstance(raw, dict) else None
    if not isinstance(view, dict):
        return TuiState(last_view=ViewState(), theme_name=None)

    return TuiState(
        last_view=ViewState(
            group=view.get("group") if isinstance(view.get("group"), str) else None,
            resource=view.get("resource") if isinstance(view.get("resource"), str) else None,
            query_text=view.get("query_text") if isinstance(view.get("query_text"), str) else "",
            details_expanded=bool(view.get("details_expanded", False)),
        ),
        theme_name=raw.get("theme_name") if isinstance(raw.get("theme_name"), str) else None,
    )



def save_tui_state(state: TuiState) -> None:
    path = tui_state_path()
    path.write_text(json.dumps(asdict(state), indent=2), encoding="utf-8")
