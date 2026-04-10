"""Custom mock data loader for the NetBox mock API.

Loads user-provided initial state from JSON or YAML files, keyed by path template.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_MOCK_DATA_PATH = "/etc/netbox-sdk/mock-data.json"
ENV_VAR_NAME = "NETBOX_MOCK_DATA_PATH"


def get_mock_data_path() -> str | None:
    """Return the mock data file path from env or default."""
    return os.environ.get(ENV_VAR_NAME, DEFAULT_MOCK_DATA_PATH)


def load_mock_data(file_path: str | Path | None = None) -> dict[str, Any] | None:
    """Load custom mock data from a JSON or YAML file.

    The file should be a dict mapping path templates to initial data values.
    Returns None if the file does not exist or cannot be parsed.
    """
    path = file_path or get_mock_data_path()
    if not path:
        return None

    file_path_obj = Path(path)
    try:
        content = file_path_obj.read_text(encoding="utf-8")
    except OSError:
        return None

    suffix = file_path_obj.suffix.lower()
    if suffix in (".yaml", ".yml"):
        return _load_yaml(content)
    if suffix == ".json":
        return _load_json(content)
    return None


def _load_json(content: str) -> dict[str, Any] | None:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _load_yaml(content: str) -> dict[str, Any] | None:
    try:
        import yaml  # optional dependency

        data = yaml.safe_load(content)
    except ImportError:
        return None
    except Exception:  # noqa: BLE001
        return None
    return data if isinstance(data, dict) else None


__all__ = [
    "DEFAULT_MOCK_DATA_PATH",
    "ENV_VAR_NAME",
    "get_mock_data_path",
    "load_mock_data",
]
