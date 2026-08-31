"""Helpers for NetBox custom-field values across release lines.

NetBox 4.7 returns selection and multiple-selection custom field values as
objects of the form ``{"value": "datacenter", "label": "Data Center"}`` (or a
list of those objects). Writes still accept the raw value. Earlier release
lines return the raw value on read as well.

Callers that copy a 4.7 read payload into a write body would submit the object
form and fail validation. ``custom_fields_for_write`` unwraps only the fields
the caller names as selections, so JSON custom fields that happen to use the
same shape are left intact. ``custom_field_write_value`` is the per-value
converter for a value already known to be a selection.
"""

from __future__ import annotations

from collections.abc import Collection
from typing import Any


def custom_field_write_value(value: Any) -> Any:
    """Return the raw write value for a known selection or multi-select field.

    A 4.7 selection object becomes its ``value`` key. A list is mapped
    element-wise so a multiple-selection field round-trips. Any other shape
    is returned unchanged.

    Call this only for a value that is already known to be a selection field.
    For a mixed ``custom_fields`` map, use :func:`custom_fields_for_write` with
    an explicit ``selection`` names list so JSON objects are not inferred.
    """
    if _is_selection_choice(value):
        return value["value"]
    if isinstance(value, list):
        return [custom_field_write_value(item) for item in value]
    return value


def custom_fields_for_write(
    custom_fields: dict[str, Any] | None,
    *,
    selection: Collection[str] | None = None,
) -> dict[str, Any]:
    """Return ``custom_fields`` ready for a write body.

    Only fields named in ``selection`` are converted from 4.7 read wrappers.
    Other values — including JSON custom fields whose payload happens to be
    exactly ``{"value": ..., "label": ...}`` — are copied unchanged.
    """
    if not custom_fields:
        return {}
    named = frozenset(selection or ())
    return {
        name: custom_field_write_value(value) if name in named else value
        for name, value in custom_fields.items()
    }


_SELECTION_KEYS = frozenset({"value", "label"})


def _is_selection_choice(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != _SELECTION_KEYS:
        return False
    if not isinstance(value["label"], str):
        return False
    raw = value["value"]
    return not isinstance(raw, (dict, list))
