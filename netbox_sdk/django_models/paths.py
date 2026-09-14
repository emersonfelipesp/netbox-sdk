"""Portable path handling for serialized Django model graphs."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any


class ModelBuildPathError(ValueError):
    """Raised when a model build contains a non-portable recorded path."""


def _inferred_checkout_root(payload: dict[str, Any]) -> Path | None:
    meta = payload.get("meta")
    if not isinstance(meta, dict):
        return None
    source_path = meta.get("source_path")
    if not isinstance(source_path, str) or not Path(source_path).is_absolute():
        return None
    source = Path(source_path).resolve(strict=False)
    if source.name != "netbox" or source.parent == Path(source.anchor):
        return None
    return source.parent


def _normalized_path(value: str, roots: tuple[Path, ...], location: str) -> str:
    path = Path(value)
    if not path.is_absolute():
        if ".." in path.parts:
            raise ModelBuildPathError(
                f"recorded path at {location} escapes the NetBox checkout root: {value!r}"
            )
        return path.as_posix()

    resolved_path = path.resolve(strict=False)
    for root in roots:
        try:
            relative = resolved_path.relative_to(root)
            if ".." not in relative.parts:
                return relative.as_posix()
        except ValueError:
            continue
    raise ModelBuildPathError(
        f"absolute recorded path at {location} is outside the known NetBox checkout roots: "
        f"{value!r}; regenerate this artifact with a current netbox-sdk builder"
    )


def _normalize_value(value: Any, roots: tuple[Path, ...], location: str) -> Any:
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            child_location = f"{location}.{key}"
            if key in {"file_path", "source_path"}:
                if not isinstance(item, str):
                    raise ModelBuildPathError(f"recorded path at {child_location} must be a string")
                normalized[key] = _normalized_path(item, roots, child_location)
            else:
                normalized[key] = _normalize_value(item, roots, child_location)
        return normalized
    if isinstance(value, list):
        return [
            _normalize_value(item, roots, f"{location}[{index}]")
            for index, item in enumerate(value)
        ]
    return value


def normalize_build_paths(
    payload: dict[str, Any], *, checkout_roots: Iterable[Path] = ()
) -> dict[str, Any]:
    """Make recorded paths relative to a known NetBox checkout root.

    Older artifacts identify their absolute ``netbox/`` source directory in
    ``meta.source_path``. Its parent is the checkout root and is inferred before
    any values are rewritten. Callers generating a graph should also pass their
    checkout root explicitly. Any absolute path outside those roots fails closed.
    """
    roots = tuple(Path(root).resolve(strict=False) for root in checkout_roots)
    inferred = _inferred_checkout_root(payload)
    if inferred is not None and inferred not in roots:
        roots += (inferred,)
    normalized = _normalize_value(payload, roots, "build")
    if not isinstance(normalized, dict):  # pragma: no cover - fixed by the input type
        raise TypeError("normalized model build must remain a JSON object")
    return normalized
