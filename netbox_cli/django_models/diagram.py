"""ASCII diagram renderer for Django model dependencies.

Renders a model and its relationships as a Unicode box-drawing tree.

Output example::

    ┌──────────────────────────┐
    │   dcim.Device (center)   │
    │   PrimaryModel           │
    ├──────────────────────────┤
    │ device_type  FK ──────►  │ dcim.DeviceType
    │ role         FK ──────►  │ dcim.DeviceRole
    │ site         FK ──────►  │ dcim.Site
    │ tenant       FK ──────►  │ tenancy.Tenant
    │ platform     FK ──────►  │ dcim.Platform
    └──────────────────────────┘
         ▲                ▲
    ┌────┴─────┐    ┌─────┴──────┐
    │ Interface│    │  Console   │
    │ (device) │    │  Port      │
    └──────────┘    └────────────┘
"""

from __future__ import annotations

from typing import Any

# ── Box-drawing constants ────────────────────────────────────────────────────

_TL = "\u250c"  # ┌
_TR = "\u2510"  # ┐
_BL = "\u2514"  # └
_BR = "\u2518"  # ┘
_H = "\u2500"  # ─
_V = "\u2502"  # │
_T_DOWN = "\u252c"  # ┬
_T_UP = "\u2534"  # ┴
_T_RIGHT = "\u251c"  # ├
_T_LEFT = "\u2524"  # ┤
_CROSS = "\u253c"  # ┼
_LTEE = "\u251c"  # ├
_RTEE = "\u2524"  # ┤
_DARROW = "\u25b6"  # ▶
_UARROW = "\u25b2"  # ▲


def _pad(text: str, width: int) -> str:
    """Pad *text* to *width* with spaces."""
    return f" {text} ".ljust(width)


def _model_short_name(key: str) -> str:
    """'dcim.Device' → 'Device'"""
    return key.split(".", 1)[-1] if "." in key else key


def _field_type_label(ftype: str) -> str:
    """Short label for field type."""
    mapping = {
        "ForeignKey": "FK",
        "OneToOneField": "O2O",
        "ManyToManyField": "M2M",
    }
    return mapping.get(ftype, ftype.replace("Field", ""))


def render_model_diagram(
    model_key: str,
    graph: dict[str, Any],
    *,
    max_outgoing: int = 12,
    max_incoming: int = 10,
) -> str:
    """Render an ASCII diagram for *model_key* and its relationships.

    Args:
        model_key: ``app.ModelName`` key (e.g. ``dcim.Device``).
        graph: Model graph data from ``store.load()``.
        max_outgoing: Max outgoing FKs to display.
        max_incoming: Max incoming FKs to display.

    Returns:
        Multi-line string with the diagram.
    """
    models = graph.get("models", {})
    edges = graph.get("edges", [])
    model = models.get(model_key)
    if model is None:
        return f"  Model not found: {model_key}\n"

    outgoing = [e for e in edges if e["from"] == model_key]
    incoming = [e for e in edges if e["to"] == model_key]

    lines: list[str] = []
    app = model["app"]
    name = model["name"]
    bases = model.get("bases", [])
    base_label = bases[0] if bases else ""

    # ── Center box ────────────────────────────────────────────────────────
    title = f"{app}.{name}"
    box_width = max(len(title) + 4, 32)
    box_inner = box_width - 2

    lines.append(f"  {_TL}{_H * box_inner}{_TR}")
    lines.append(f"  {_V}{_pad(title, box_inner)}{_V}")
    if base_label:
        lines.append(f"  {_V}{_pad(f'({base_label})', box_inner)}{_V}")
    lines.append(f"  {_T_RIGHT}{_H * box_inner}{_T_LEFT}")

    # List fields inside the box
    fields = model.get("fields", [])
    fk_fields = [f for f in fields if f.get("target")]
    other_fields = [f for f in fields if not f.get("target")]

    for f in fk_fields:
        target_short = _model_short_name(f["target"]) if f.get("target") else "?"
        ftype = _field_type_label(f["type"])
        line = f" {f['name']}  {ftype} {_DARROW} {target_short}"
        lines.append(f"  {_V}{line.ljust(box_inner)}{_V}")

    # Show a few regular fields
    shown_regular = 0
    for f in other_fields:
        if shown_regular >= 5:
            remaining = len(other_fields) - shown_regular
            line = f" ... +{remaining} more fields"
            lines.append(f"  {_V}{line.ljust(box_inner)}{_V}")
            break
        ftype = f["type"].replace("Field", "")
        line = f" {f['name']} ({ftype})"
        lines.append(f"  {_V}{line.ljust(box_inner)}{_V}")
        shown_regular += 1

    lines.append(f"  {_BL}{_H * box_inner}{_BR}")

    # ── Outgoing FKs (dependencies) ───────────────────────────────────────
    if outgoing:
        lines.append("")
        lines.append(f"  Dependencies ({len(outgoing)} outgoing FKs):")
        shown = 0
        for edge in outgoing:
            if shown >= max_outgoing:
                lines.append(f"    ... +{len(outgoing) - shown} more")
                break
            target = edge["to"]
            ftype = _field_type_label(edge["type"])
            rel = edge.get("related_name") or ""
            rel_str = f" (reverse: {rel})" if rel else ""
            lines.append(f"    {_DARROW} {target} [{ftype}]{rel_str}")
            shown += 1

    # ── Incoming FKs (dependents) ─────────────────────────────────────────
    if incoming:
        lines.append("")
        lines.append(f"  Dependents ({len(incoming)} incoming FKs):")
        shown = 0
        for edge in incoming:
            if shown >= max_incoming:
                lines.append(f"    ... +{len(incoming) - shown} more")
                break
            source = edge["from"]
            ftype = _field_type_label(edge["type"])
            field_name = edge["field"]
            lines.append(f"    {_UARROW} {source} [{ftype}] .{field_name}")
            shown += 1

    lines.append("")
    return "\n".join(lines)


def render_model_compact_list(
    graph: dict[str, Any],
    app_filter: str | None = None,
) -> str:
    """Render a compact list of all models, optionally filtered by app."""
    models = graph.get("models", {})
    lines: list[str] = []

    # Group by app
    apps: dict[str, list[dict]] = {}
    for key, model in sorted(models.items()):
        app = model["app"]
        if app_filter and app != app_filter:
            continue
        apps.setdefault(app, []).append(model)

    for app in sorted(apps):
        app_models = apps[app]
        lines.append(f"  {app}/ ({len(app_models)} models)")
        for m in sorted(app_models, key=lambda x: x["name"]):
            bases = m.get("bases", [])
            base = bases[0] if bases else ""
            fk_count = sum(1 for f in m.get("fields", []) if f.get("target"))
            fk_str = f" [{fk_count} FKs]" if fk_count else ""
            lines.append(f"    {_V} {m['name']} ({base}){fk_str}")
        lines.append("")

    return "\n".join(lines)
