"""Static data store for Django model graph data.

Persists parsed model graph to JSON so the TUI can start instantly
without re-scanning the filesystem.

Usage::

    store = DjangoModelStore()
    if not store.exists():
        store.build(Path("/path/to/netbox/netbox/"))
    data = store.load()
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from netbox_sdk.config import config_path, legacy_config_path
from netbox_sdk.django_models.parser import build_model_graph, parse_netbox_models


def _default_cache_path() -> Path:
    """Default cache location under the NetBox SDK config dir."""
    return config_path().parent / "django_models.json"


def _legacy_cache_path() -> Path:
    return legacy_config_path().parent / "django_models.json"


class DjangoModelStore:
    """Manages the on-disk cache of parsed Django model graph data.

    The cache is a single JSON file containing:
    - ``models``: dict of ``app.ModelName → model metadata``
    - ``edges``: list of foreign-key / one-to-one / m2m relationships
    - ``stats``: summary counts
    - ``meta``: generation metadata (source path, timestamp, netbox version)
    """

    def __init__(self, cache_path: Path | None = None) -> None:
        self._path = cache_path or _default_cache_path()
        self._fallback_path = _legacy_cache_path() if cache_path is None else self._path

    @property
    def path(self) -> Path:
        return self._path

    def exists(self) -> bool:
        return self._path.exists() or self._fallback_path.exists()

    def load(self) -> dict[str, Any]:
        """Load cached graph data.  Raises FileNotFoundError if missing."""
        path = self._path if self._path.exists() else self._fallback_path
        return json.loads(path.read_text(encoding="utf-8"))

    def build(
        self,
        netbox_root: Path,
        apps: tuple[str, ...] | None = None,
    ) -> dict[str, Any]:
        """Parse NetBox source and write the cache file.

        Args:
            netbox_root: Path to the ``netbox/`` Django project root.
            apps: Apps to scan (defaults to all core apps).

        Returns:
            The built graph data dict.
        """
        from netbox_sdk.django_models.parser import _DEFAULT_APPS  # noqa: PLC0415

        if apps is None:
            apps = _DEFAULT_APPS

        models = parse_netbox_models(netbox_root, apps=apps)
        graph = build_model_graph(models)

        # Add metadata
        graph["meta"] = {
            "source_path": str(netbox_root),
            "total_models": graph["stats"]["total_models"],
            "total_edges": graph["stats"]["total_edges"],
            "apps": graph["stats"]["apps"],
        }

        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(graph, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        return graph

    def get_model(self, key: str) -> dict[str, Any] | None:
        """Get a single model by its ``app.ModelName`` key."""
        data = self.load()
        return data.get("models", {}).get(key)

    def get_model_edges(self, key: str) -> dict[str, list[dict[str, Any]]]:
        """Get all edges for a model: outgoing (FKs I have) and incoming (FKs pointing to me)."""
        data = self.load()
        edges = data.get("edges", [])
        outgoing = [e for e in edges if e["from"] == key]
        incoming = [e for e in edges if e["to"] == key]
        return {"outgoing": outgoing, "incoming": incoming}

    def get_model_source(self, key: str) -> str:
        """Read the raw Python source for a model from its file."""
        model = self.get_model(key)
        if model is None:
            return f"# Model not found: {key}"
        file_path = Path(model["file_path"])
        if not file_path.exists():
            return f"# File not found: {file_path}"
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
            start = max(0, model["line_number"] - 1)
            # Find the end of the class (next class or EOF)
            end = len(lines)
            for i in range(start + 1, len(lines)):
                if lines[i].startswith("class ") and not lines[i].startswith("    "):
                    end = i
                    break
            # Include ~20 lines of context after the detected end
            end = min(end + 20, len(lines))
            return "\n".join(lines[start:end])
        except OSError:
            return f"# Could not read: {file_path}"
