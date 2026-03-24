"""Django model AST parser — scans NetBox source for model definitions.

Parses Python files using regex (not full AST) for speed and simplicity.
Extracts:
- Model class names, base classes, docstrings
- Field definitions (ForeignKey, OneToOneField, ManyToManyField, CharField, etc.)
- Foreign key target references (string-based like 'dcim.Device')

Usage::

    models = parse_netbox_models(Path("/path/to/netbox/netbox/"))
    data = build_model_graph(models)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# ── Regex patterns ───────────────────────────────────────────────────────────

# Matches: class Device(PrimaryModel):
_MODEL_CLASS_RE = re.compile(
    r"^class\s+(\w+)\s*\(([^)]*)\)\s*:",
    re.MULTILINE,
)

# Matches: device_type = models.ForeignKey(
#          to='dcim.DeviceType',
# Captures: field_name, field_type, target_ref
_FK_FIELD_RE = re.compile(
    r"^\s+(\w+)\s*=\s*models\.(ForeignKey|OneToOneField|ManyToManyField)\s*\(\s*"
    r"(?:to\s*=\s*)?['\"]([^'\"]+)['\"]",
    re.MULTILINE,
)

# Matches: name = models.CharField(max_length=64, ...)
_GENERIC_FIELD_RE = re.compile(
    r"^\s+(\w+)\s*=\s*models\.(\w+Field)\s*\(",
    re.MULTILINE,
)

# Matches the docstring (triple-quoted) right after class definition
_DOCSTRING_RE = re.compile(
    r'^\s+(?:\'\'\'|""")(.+?)(?:\'\'\'|""")',
    re.DOTALL,
)

# Apps to scan
_DEFAULT_APPS = (
    "circuits",
    "core",
    "dcim",
    "extras",
    "ipam",
    "tenancy",
    "users",
    "utilities",
    "virtualization",
    "vpn",
    "wireless",
)


@dataclass(slots=True)
class ParsedField:
    """A single model field."""

    name: str
    field_type: str  # e.g. "ForeignKey", "CharField"
    target: str | None = None  # e.g. "dcim.Device" for FK fields
    nullable: bool = False
    on_delete: str | None = None
    related_name: str | None = None


@dataclass(slots=True)
class ParsedModel:
    """A single Django model class."""

    app: str
    name: str
    bases: list[str]
    fields: list[ParsedField]
    file_path: str
    line_number: int
    docstring: str = ""


def _resolve_target_ref(ref: str, current_app: str) -> str:
    """Resolve a ForeignKey target reference.

    'dcim.Device' → 'dcim.Device'
    'Device' (same-app) → 'dcim.Device' (qualified)
    'self' → '<current_app>.<ClassName>' (resolved later)
    """
    if "." in ref:
        return ref
    if ref == "self":
        return ref  # resolved during graph building
    return f"{current_app}.{ref}"


def _parse_fields_from_body(body: str, app: str) -> list[ParsedField]:
    """Extract fields from the class body text."""
    fields: list[ParsedField] = []
    seen: set[str] = set()

    # First pass: FK / OneToOne / ManyToMany (these have explicit target refs)
    for match in _FK_FIELD_RE.finditer(body):
        name = match.group(1)
        ftype = match.group(2)
        target = _resolve_target_ref(match.group(3), app)
        if name not in seen:
            seen.add(name)
            fields.append(ParsedField(name=name, field_type=ftype, target=target))

    # Second pass: generic fields (skip already-seen FK fields)
    for match in _GENERIC_FIELD_RE.finditer(body):
        name = match.group(1)
        ftype = match.group(2)
        if name not in seen:
            seen.add(name)
            fields.append(ParsedField(name=name, field_type=ftype))

    return fields


def _extract_docstring(body: str) -> str:
    """Extract the first docstring from the class body."""
    match = _DOCSTRING_RE.search(body)
    if match:
        return " ".join(match.group(1).split())[:200]
    return ""


def parse_python_file(file_path: Path, app: str) -> list[ParsedModel]:
    """Parse a single Python file for Django model classes."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    models: list[ParsedModel] = []

    for match in _MODEL_CLASS_RE.finditer(content):
        name = match.group(1)
        bases_str = match.group(2)
        line_number = content[: match.start()].count("\n") + 1

        # Skip non-model classes (utility classes, exceptions, etc.)
        if name.startswith("_") or name.endswith("Form") or name.endswith("ViewSet"):
            continue

        bases = [b.strip() for b in bases_str.split(",") if b.strip()]

        # Extract the class body (from class def to next top-level class or EOF)
        body_start = match.end()
        next_class = _MODEL_CLASS_RE.search(content, body_start + 1)
        body_end = next_class.start() if next_class else len(content)
        body = content[body_start:body_end]

        fields = _parse_fields_from_body(body, app)
        docstring = _extract_docstring(body)

        models.append(
            ParsedModel(
                app=app,
                name=name,
                bases=bases,
                fields=fields,
                file_path=str(file_path),
                line_number=line_number,
                docstring=docstring,
            )
        )

    return models


def parse_netbox_models(
    netbox_root: Path,
    apps: tuple[str, ...] = _DEFAULT_APPS,
) -> list[ParsedModel]:
    """Scan all model files under *netbox_root* and return parsed models.

    Args:
        netbox_root: Path to the ``netbox/`` Django project directory
            (e.g. ``/path/to/netbox/netbox/``).
        apps: Tuple of app names to scan.
    """
    all_models: list[ParsedModel] = []

    for app in apps:
        app_dir = netbox_root / app
        models_dir = app_dir / "models"
        if models_dir.is_dir():
            # App has a models/ package
            for py_file in sorted(models_dir.glob("*.py")):
                if py_file.name == "__init__.py":
                    continue
                all_models.extend(parse_python_file(py_file, app))
            # Also check __init__.py for re-exports that define models
            init_file = models_dir / "__init__.py"
            if init_file.exists():
                all_models.extend(parse_python_file(init_file, app))
        else:
            # App has a single models.py file
            models_file = app_dir / "models.py"
            if models_file.exists():
                all_models.extend(parse_python_file(models_file, app))

    return all_models


def build_model_graph(
    models: list[ParsedModel],
) -> dict[str, Any]:
    """Convert parsed models into a graph structure suitable for visualization.

    Returns a dict with:
    - ``models``: dict of ``app.ModelName → model data``
    - ``edges``: list of ``{from, to, field, type, related_name}``
    - ``stats``: summary counts
    """
    model_index: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    for m in models:
        key = f"{m.app}.{m.name}"
        model_index[key] = {
            "app": m.app,
            "name": m.name,
            "key": key,
            "bases": m.bases,
            "fields": [
                {
                    "name": f.name,
                    "type": f.field_type,
                    "target": f.target,
                    "nullable": f.nullable,
                }
                for f in m.fields
            ],
            "file_path": m.file_path,
            "line_number": m.line_number,
            "docstring": m.docstring,
        }

    # Resolve 'self' references and build edges
    for m in models:
        source = f"{m.app}.{m.name}"
        for f in m.fields:
            if f.target is None:
                continue
            target = f.target
            if target == "self":
                target = source
            edges.append(
                {
                    "from": source,
                    "to": target,
                    "field": f.name,
                    "type": f.field_type,
                    "related_name": f.related_name,
                }
            )

    # Count cross-app vs intra-app edges
    cross_app = sum(1 for e in edges if e["from"].split(".")[0] != e["to"].split(".")[0])

    return {
        "models": model_index,
        "edges": edges,
        "stats": {
            "total_models": len(model_index),
            "total_edges": len(edges),
            "cross_app_edges": cross_app,
            "intra_app_edges": len(edges) - cross_app,
            "apps": sorted({m.app for m in models}),
        },
    }
