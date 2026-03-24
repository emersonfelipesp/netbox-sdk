"""Rich markup rendering helpers for Django Model Inspector TUI.

Provides vibrant syntax highlighting and themed formatting for:
- Python source code with IDE-style colors
- Model diagrams with colored borders and semantic content
- Field tables using Rich Table widgets
- Statistics with hierarchical coloring
- Interactive expandable dependencies sections
"""

from __future__ import annotations

import re
from typing import Any

from rich.table import Table
from rich.text import Text

# Box-drawing constants
_TL = "\u250c"  # ┌
_TR = "\u2510"  # ┐
_BL = "\u2514"  # └
_BR = "\u2518"  # ┘
_H = "\u2500"  # ─
_V = "\u2502"  # │
_T_RIGHT = "\u251c"  # ├
_T_LEFT = "\u2524"  # ┤
_DARROW = "\u25b6"  # ▶
_UARROW = "\u25b2"  # ▲
_DDARROW = "\u25bc"  # ▼  (for collapse/expand)
_RARROW = "\u25b8"  # ▸  (for collapsed state)

# Python syntax regex patterns for highlighting
_PYTHON_PATTERNS = {
    # Keywords - class, def, import, from, return, if, else, etc.
    "keywords": re.compile(
        r"\b(class|def|import|from|return|if|else|elif|try|except|finally|"
        r"with|as|for|while|break|continue|pass|raise|assert|yield|lambda|"
        r"and|or|not|in|is|None|True|False|self|super)\b"
    ),
    # String literals (single, double, triple quoted)
    "strings": re.compile(r'(""".*?"""|\'\'\'.*?\'\'\'|"[^"]*"|\'[^\']*\')'),
    # Comments (# to end of line)
    "comments": re.compile(r"#.*$", re.MULTILINE),
    # Numbers (integers, floats, hex)
    "numbers": re.compile(r"\b(\d+\.?\d*|\.\d+|0x[0-9a-fA-F]+)\b"),
    # Django field types
    "field_types": re.compile(
        r"\b(CharField|TextField|IntegerField|FloatField|BooleanField|"
        r"DateField|DateTimeField|TimeField|ForeignKey|OneToOneField|"
        r"ManyToManyField|AutoField|BigAutoField|SlugField|URLField|"
        r"EmailField|UUIDField|JSONField|DecimalField|PositiveIntegerField|"
        r"SmallIntegerField|BigIntegerField|FileField|ImageField)\b"
    ),
    # Model class names (CamelCase starting with capital)
    "model_names": re.compile(r"\b[A-Z][a-zA-Z0-9]*(?=\(|\s|:)"),
    # Function/method names
    "functions": re.compile(r"\b([a-z_][a-zA-Z0-9_]*)\s*(?=\()"),
}

# Global style cache - populated by configure_django_styles()
_DJANGO_STYLES: dict[str, str] = {}

# Global state for expandable dependencies - tracks which sections are expanded
_EXPANDED_DEPENDENCIES: set[str] = set()


def configure_django_styles(*, colors: dict[str, str], variables: dict[str, str]) -> None:
    """Configure Django-specific Rich styles from the active theme."""
    global _DJANGO_STYLES

    _DJANGO_STYLES = {
        # Python syntax highlighting colors (IDE-style vibrant)
        "python_keyword": colors["primary"],  # class, def, import
        "python_string": variables["nb-warning-text"],  # String literals
        "python_comment": variables["nb-muted-text"],  # Comments
        "python_number": colors["accent"],  # Numbers
        "python_field_type": variables["nb-info-text"],  # Django field types
        "python_model_name": variables["nb-link-text"],  # Model class names
        "python_function": variables["nb-key-text"],  # Function names
        # Diagram colors
        "diagram_border": colors["primary"],  # Box borders for main model
        "diagram_model_name": f"bold {variables['nb-link-text']}",  # Model names
        "diagram_field_name": variables["nb-key-text"],  # Field names
        "diagram_field_type": variables["nb-info-text"],  # Field types
        "diagram_related_model": variables["nb-link-text"],  # Related models
        "diagram_base_class": variables["nb-secondary-text"],  # Base classes
        "diagram_arrow": colors["primary"],  # FK arrows
        "diagram_section": f"bold {colors['primary']}",  # Section headers
        "diagram_expand_icon": colors["accent"],  # Expand/collapse icons
        "diagram_truncated": variables["nb-muted-text"],  # Truncated text indicators
        # Table colors
        "table_header": f"bold {colors['primary']}",  # Table headers
        "table_field_name": variables["nb-key-text"],  # Field names
        "table_field_type": variables["nb-info-text"],  # Field types
        "table_target": variables["nb-link-text"],  # FK targets
        "table_number": colors["accent"],  # Numeric values
        "table_app_name": variables["nb-info-text"],  # App names
        "table_border": variables["nb-border"],  # Table borders
    }


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


def _truncate_text(text: str, max_length: int, suffix: str = "…") -> str:
    """Truncate text to fit within max_length, adding suffix if needed."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def _get_responsive_box_width(title: str, fields: list[dict], max_width: int = 80) -> int:
    """Calculate optimal box width based on content and terminal constraints."""
    # Start with title requirements
    min_width = len(title) + 4  # Title + padding

    # Check field content requirements
    for field in fields:
        if field.get("target"):
            # FK field: " name  FK ▶ Target"
            target_short = _model_short_name(field["target"])
            ftype = _field_type_label(field["type"])
            field_line = f" {field['name']}  {ftype} {_DARROW} {target_short}"
        else:
            # Regular field: " name (Type)"
            ftype = field["type"].replace("Field", "")
            field_line = f" {field['name']} ({ftype})"

        min_width = max(min_width, len(field_line) + 2)  # field content + borders

    # Respect terminal width constraints
    min_width = max(min_width, 32)  # Absolute minimum
    return min(min_width, max_width)  # Don't exceed max


def render_model_diagram_rich(
    model_key: str,
    graph: dict[str, Any],
    *,
    max_outgoing: int = 12,
    max_incoming: int = 10,
    max_width: int = 80,
) -> Text:
    """Render an enhanced ASCII diagram with responsive width and expandable dependencies."""
    models = graph.get("models", {})
    edges = graph.get("edges", [])
    model = models.get(model_key)

    if model is None:
        text = Text()
        text.append(
            f"  Model not found: {model_key}\n", style=_DJANGO_STYLES.get("python_comment", "")
        )
        return text

    # Ensure sections are expanded by default for better UX with scrolling
    ensure_expanded_by_default(model_key)

    outgoing = [e for e in edges if e["from"] == model_key]
    incoming = [e for e in edges if e["to"] == model_key]

    result = Text()
    app = model["app"]
    name = model["name"]
    bases = model.get("bases", [])
    base_label = bases[0] if bases else ""

    # ── Responsive center box with colored borders ──
    title = f"{app}.{name}"
    fields = model.get("fields", [])
    box_width = _get_responsive_box_width(title, fields, max_width)
    box_inner = box_width - 2

    # Top border in primary color
    result.append(f"  {_TL}{_H * box_inner}{_TR}\n", style=_DJANGO_STYLES.get("diagram_border", ""))

    # Model title - truncate if needed
    title_display = _truncate_text(title, box_inner - 2)
    result.append(f"  {_V}", style=_DJANGO_STYLES.get("diagram_border", ""))
    result.append(
        f" {title_display} ".ljust(box_inner), style=_DJANGO_STYLES.get("diagram_model_name", "")
    )
    result.append(f"{_V}\n", style=_DJANGO_STYLES.get("diagram_border", ""))

    # Base class - truncate if needed
    if base_label:
        base_display = _truncate_text(f"({base_label})", box_inner - 2)
        result.append(f"  {_V}", style=_DJANGO_STYLES.get("diagram_border", ""))
        result.append(
            f" {base_display} ".ljust(box_inner), style=_DJANGO_STYLES.get("diagram_base_class", "")
        )
        result.append(f"{_V}\n", style=_DJANGO_STYLES.get("diagram_border", ""))

    # Middle border
    result.append(
        f"  {_T_RIGHT}{_H * box_inner}{_T_LEFT}\n", style=_DJANGO_STYLES.get("diagram_border", "")
    )

    # List fields inside the box with proper overflow handling
    fk_fields = [f for f in fields if f.get("target")]
    other_fields = [f for f in fields if not f.get("target")]

    # FK fields with arrows - show all with proper truncation
    for f in fk_fields:
        target_short = _model_short_name(f["target"]) if f.get("target") else "?"
        ftype = _field_type_label(f["type"])

        # Construct the line content
        field_name = _truncate_text(f["name"], 20)  # Limit field name length
        target_display = _truncate_text(target_short, 20)  # Limit target length

        result.append(f"  {_V}", style=_DJANGO_STYLES.get("diagram_border", ""))
        result.append(f" {field_name}", style=_DJANGO_STYLES.get("diagram_field_name", ""))
        result.append(f"  {ftype} ", style=_DJANGO_STYLES.get("diagram_field_type", ""))
        result.append(f"{_DARROW}", style=_DJANGO_STYLES.get("diagram_arrow", ""))
        result.append(f" {target_display}", style=_DJANGO_STYLES.get("diagram_related_model", ""))

        # Calculate padding to align right border
        line_content = f" {field_name}  {ftype} {_DARROW} {target_display}"
        padding = " " * max(0, box_inner - len(line_content))
        result.append(padding)
        result.append(f"{_V}\n", style=_DJANGO_STYLES.get("diagram_border", ""))

    # Regular fields - show first 20 by default, expandable for the rest
    shown_regular = 0
    max_regular_fields = 20  # Increased from 8 since we now have scrolling
    for f in other_fields:
        if shown_regular >= max_regular_fields:
            remaining = len(other_fields) - shown_regular
            result.append(f"  {_V}", style=_DJANGO_STYLES.get("diagram_border", ""))
            expand_key = f"{model_key}_fields"
            if expand_key in _EXPANDED_DEPENDENCIES:
                # Show remaining fields when expanded
                result.append(
                    f" {_DDARROW} Show less fields",
                    style=_DJANGO_STYLES.get("diagram_expand_icon", ""),
                )
                padding = " " * max(0, box_inner - len(f" {_DDARROW} Show less fields"))
                result.append(padding)
                result.append(f"{_V}\n", style=_DJANGO_STYLES.get("diagram_border", ""))
                # Show remaining fields
                for remaining_field in other_fields[shown_regular:]:
                    ftype = remaining_field["type"].replace("Field", "")
                    field_name = _truncate_text(remaining_field["name"], 25)
                    ftype_display = _truncate_text(ftype, 15)

                    result.append(f"  {_V}", style=_DJANGO_STYLES.get("diagram_border", ""))
                    result.append(
                        f" {field_name}", style=_DJANGO_STYLES.get("diagram_field_name", "")
                    )
                    result.append(
                        f" ({ftype_display})", style=_DJANGO_STYLES.get("diagram_field_type", "")
                    )

                    line_content = f" {field_name} ({ftype_display})"
                    padding = " " * max(0, box_inner - len(line_content))
                    result.append(padding)
                    result.append(f"{_V}\n", style=_DJANGO_STYLES.get("diagram_border", ""))
            else:
                # Show expand option
                expand_text = f" {_RARROW} +{remaining} more fields (click to expand)"
                expand_display = _truncate_text(expand_text, box_inner - 2)
                result.append(expand_display, style=_DJANGO_STYLES.get("diagram_truncated", ""))
                padding = " " * max(0, box_inner - len(expand_display))
                result.append(padding)
                result.append(f"{_V}\n", style=_DJANGO_STYLES.get("diagram_border", ""))
            break

        ftype = f["type"].replace("Field", "")
        field_name = _truncate_text(f["name"], 25)
        ftype_display = _truncate_text(ftype, 15)

        result.append(f"  {_V}", style=_DJANGO_STYLES.get("diagram_border", ""))
        result.append(f" {field_name}", style=_DJANGO_STYLES.get("diagram_field_name", ""))
        result.append(f" ({ftype_display})", style=_DJANGO_STYLES.get("diagram_field_type", ""))

        line_content = f" {field_name} ({ftype_display})"
        padding = " " * max(0, box_inner - len(line_content))
        result.append(padding)
        result.append(f"{_V}\n", style=_DJANGO_STYLES.get("diagram_border", ""))
        shown_regular += 1

    # Bottom border
    result.append(f"  {_BL}{_H * box_inner}{_BR}\n", style=_DJANGO_STYLES.get("diagram_border", ""))

    # ── Enhanced Outgoing FKs (dependencies) with expand/collapse ──
    if outgoing:
        result.append("\n")
        deps_key = f"{model_key}_dependencies"
        is_expanded = deps_key in _EXPANDED_DEPENDENCIES

        # Section header with expand/collapse icon
        icon = _DDARROW if is_expanded else _RARROW
        result.append("  ", style="")
        result.append(f"{icon}", style=_DJANGO_STYLES.get("diagram_expand_icon", ""))
        result.append(" Dependencies ", style=_DJANGO_STYLES.get("diagram_section", ""))
        result.append(
            f"({len(outgoing)} outgoing FKs)", style=_DJANGO_STYLES.get("diagram_base_class", "")
        )

        if is_expanded:
            result.append(
                " - click to collapse\n", style=_DJANGO_STYLES.get("diagram_truncated", "")
            )
            # Show all dependencies when expanded
            for edge in outgoing:
                target = edge["to"]
                ftype = _field_type_label(edge["type"])
                field_name = edge["field"]
                rel = edge.get("related_name") or ""
                rel_str = f" (reverse: {rel})" if rel else ""

                result.append("    ", style="")
                result.append(f"{_DARROW}", style=_DJANGO_STYLES.get("diagram_arrow", ""))
                result.append(f" {target}", style=_DJANGO_STYLES.get("diagram_related_model", ""))
                result.append(f" [{ftype}]", style=_DJANGO_STYLES.get("diagram_field_type", ""))
                result.append(f" .{field_name}", style=_DJANGO_STYLES.get("diagram_field_name", ""))
                result.append(f"{rel_str}\n", style=_DJANGO_STYLES.get("diagram_base_class", ""))
        else:
            result.append(" - click to expand\n", style=_DJANGO_STYLES.get("diagram_truncated", ""))
            # Show more items when collapsed since we have scrolling now
            shown = min(10, len(outgoing))  # Increased from 3 to 10
            for i, edge in enumerate(outgoing[:shown]):
                target = _truncate_text(edge["to"], 30)
                ftype = _field_type_label(edge["type"])

                result.append("    ", style="")
                result.append(f"{_DARROW}", style=_DJANGO_STYLES.get("diagram_arrow", ""))
                result.append(f" {target}", style=_DJANGO_STYLES.get("diagram_related_model", ""))
                result.append(f" [{ftype}]", style=_DJANGO_STYLES.get("diagram_field_type", ""))

                # Only show truncation message if we still have significantly more items
                if i == shown - 1 and len(outgoing) > shown and len(outgoing) > 15:
                    result.append(
                        f" ... and {len(outgoing) - shown} more",
                        style=_DJANGO_STYLES.get("diagram_truncated", ""),
                    )
                result.append("\n", style="")

    # ── Enhanced Incoming FKs (dependents) with expand/collapse ──
    if incoming:
        result.append("\n")
        deps_key = f"{model_key}_dependents"
        is_expanded = deps_key in _EXPANDED_DEPENDENCIES

        # Section header with expand/collapse icon
        icon = _DDARROW if is_expanded else _RARROW
        result.append("  ", style="")
        result.append(f"{icon}", style=_DJANGO_STYLES.get("diagram_expand_icon", ""))
        result.append(" Dependents ", style=_DJANGO_STYLES.get("diagram_section", ""))
        result.append(
            f"({len(incoming)} incoming FKs)", style=_DJANGO_STYLES.get("diagram_base_class", "")
        )

        if is_expanded:
            result.append(
                " - click to collapse\n", style=_DJANGO_STYLES.get("diagram_truncated", "")
            )
            # Show all dependents when expanded
            for edge in incoming:
                source = edge["from"]
                ftype = _field_type_label(edge["type"])
                field_name = edge["field"]

                result.append("    ", style="")
                result.append(f"{_UARROW}", style=_DJANGO_STYLES.get("diagram_arrow", ""))
                result.append(f" {source}", style=_DJANGO_STYLES.get("diagram_related_model", ""))
                result.append(f" [{ftype}]", style=_DJANGO_STYLES.get("diagram_field_type", ""))
                result.append(
                    f" .{field_name}\n", style=_DJANGO_STYLES.get("diagram_field_name", "")
                )
        else:
            result.append(" - click to expand\n", style=_DJANGO_STYLES.get("diagram_truncated", ""))
            # Show more items when collapsed since we have scrolling now
            shown = min(10, len(incoming))  # Increased from 3 to 10
            for i, edge in enumerate(incoming[:shown]):
                source = _truncate_text(edge["from"], 30)
                ftype = _field_type_label(edge["type"])

                result.append("    ", style="")
                result.append(f"{_UARROW}", style=_DJANGO_STYLES.get("diagram_arrow", ""))
                result.append(f" {source}", style=_DJANGO_STYLES.get("diagram_related_model", ""))
                result.append(f" [{ftype}]", style=_DJANGO_STYLES.get("diagram_field_type", ""))

                # Only show truncation message if we still have significantly more items
                if i == shown - 1 and len(incoming) > shown and len(incoming) > 15:
                    result.append(
                        f" ... and {len(incoming) - shown} more",
                        style=_DJANGO_STYLES.get("diagram_truncated", ""),
                    )
                result.append("\n", style="")

    result.append("\n")
    return result


def toggle_dependency_expansion(model_key: str, section: str) -> None:
    """Toggle the expansion state of a dependency section.

    Args:
        model_key: The model identifier (e.g., 'dcim.Device')
        section: The section type ('dependencies', 'dependents', 'fields')
    """
    global _EXPANDED_DEPENDENCIES
    expand_key = f"{model_key}_{section}"

    if expand_key in _EXPANDED_DEPENDENCIES:
        _EXPANDED_DEPENDENCIES.remove(expand_key)
    else:
        _EXPANDED_DEPENDENCIES.add(expand_key)


def is_section_expanded(model_key: str, section: str) -> bool:
    """Check if a dependency section is currently expanded.

    Args:
        model_key: The model identifier (e.g., 'dcim.Device')
        section: The section type ('dependencies', 'dependents', 'fields')

    Returns:
        True if the section is expanded, False if collapsed
    """
    expand_key = f"{model_key}_{section}"
    return expand_key in _EXPANDED_DEPENDENCIES


def clear_all_expansions() -> None:
    """Clear all expansion state (useful when switching models)."""
    global _EXPANDED_DEPENDENCIES
    _EXPANDED_DEPENDENCIES.clear()


def ensure_expanded_by_default(model_key: str) -> None:
    """Ensure that dependency sections are expanded by default for a model.

    This sets the default state to expanded so users can see all content
    and use scrolling to navigate, rather than having content truncated.

    Args:
        model_key: The model identifier (e.g., 'dcim.Device')
    """
    global _EXPANDED_DEPENDENCIES

    # Default to expanded state for all sections
    sections = ["dependencies", "dependents", "fields"]
    for section in sections:
        expand_key = f"{model_key}_{section}"
        if expand_key not in _EXPANDED_DEPENDENCIES:
            _EXPANDED_DEPENDENCIES.add(expand_key)


def render_python_source_rich(source_code: str) -> Text:
    """Render Python source code with vibrant IDE-style syntax highlighting."""
    if not source_code.strip():
        text = Text()
        text.append("# No source code available", style=_DJANGO_STYLES.get("python_comment", ""))
        return text

    result = Text()
    result.append(source_code)

    # Apply syntax highlighting in order (later patterns can override earlier ones)
    # Comments first (so keywords in comments stay as comments)
    result.highlight_regex(_PYTHON_PATTERNS["comments"], _DJANGO_STYLES.get("python_comment", ""))

    # Strings (so keywords in strings stay as strings)
    result.highlight_regex(_PYTHON_PATTERNS["strings"], _DJANGO_STYLES.get("python_string", ""))

    # Numbers
    result.highlight_regex(_PYTHON_PATTERNS["numbers"], _DJANGO_STYLES.get("python_number", ""))

    # Django field types (before general keywords to be more specific)
    result.highlight_regex(
        _PYTHON_PATTERNS["field_types"], _DJANGO_STYLES.get("python_field_type", "")
    )

    # Model class names
    result.highlight_regex(
        _PYTHON_PATTERNS["model_names"], _DJANGO_STYLES.get("python_model_name", "")
    )

    # Function names
    result.highlight_regex(_PYTHON_PATTERNS["functions"], _DJANGO_STYLES.get("python_function", ""))

    # Python keywords (last so they don't override field types)
    result.highlight_regex(_PYTHON_PATTERNS["keywords"], _DJANGO_STYLES.get("python_keyword", ""))

    return result


def render_fields_table_rich(model: dict[str, Any]) -> Table:
    """Render model fields as a Rich Table widget."""
    table = Table(
        show_header=True,
        header_style=_DJANGO_STYLES.get("table_header", ""),
        border_style=_DJANGO_STYLES.get("table_border", ""),
        show_lines=True,
    )

    table.add_column("Field", style=_DJANGO_STYLES.get("table_field_name", ""))
    table.add_column("Type", style=_DJANGO_STYLES.get("table_field_type", ""))
    table.add_column("Target", style=_DJANGO_STYLES.get("table_target", ""))

    fields = model.get("fields", [])
    if not fields:
        table.add_row("No fields found", "—", "—")
        return table

    for f in fields:
        name = f["name"]
        ftype = f["type"]
        target = f.get("target") or "—"

        table.add_row(name, ftype, target)

    return table


def render_stats_table_rich(graph: dict[str, Any]) -> Table:
    """Render statistics as a Rich Table widget with hierarchical sections."""
    table = Table(
        show_header=True,
        header_style=_DJANGO_STYLES.get("table_header", ""),
        border_style=_DJANGO_STYLES.get("table_border", ""),
        show_lines=False,
        title="NetBox Django Model Statistics",
        title_style=_DJANGO_STYLES.get("table_header", ""),
    )

    table.add_column("Metric", style="")
    table.add_column("Value", justify="right", style=_DJANGO_STYLES.get("table_number", ""))

    stats = graph.get("stats", {})
    meta = graph.get("meta", {})

    # Overall statistics
    table.add_row("Source Path", str(meta.get("source_path", "N/A")))
    table.add_row("Total Models", str(stats.get("total_models", 0)))
    table.add_row("Total Edges", str(stats.get("total_edges", 0)))
    table.add_row("Cross-app Edges", str(stats.get("cross_app_edges", 0)))
    table.add_row("Intra-app Edges", str(stats.get("intra_app_edges", 0)))

    # Add separator
    table.add_row("", "")

    # Apps breakdown
    models = graph.get("models", {})
    for app in stats.get("apps", []):
        app_models = [m for m in models.values() if m["app"] == app]
        app_fks = sum(1 for m in app_models for f in m.get("fields", []) if f.get("target"))

        app_text = Text()
        app_text.append(app, style=_DJANGO_STYLES.get("table_app_name", ""))
        app_text.append(f" ({app_fks} FKs)", style=_DJANGO_STYLES.get("python_comment", ""))

        table.add_row(app_text, str(len(app_models)))

    return table
