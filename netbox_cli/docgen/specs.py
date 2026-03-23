"""Spec re-export — thin bridge between ``docgen_specs`` and the docgen package.

Single Responsibility: converts Pydantic ``CaptureSpec`` from ``docgen_specs``
into the stdlib ``CaptureSpec`` dataclass used by the capture engine.
"""

from __future__ import annotations

from ..docgen_specs import CaptureSpec as _PydanticSpec
from ..docgen_specs import all_specs as _pydantic_all_specs
from .models import CaptureSpec


def _from_pydantic(spec: _PydanticSpec) -> CaptureSpec:
    """Convert a Pydantic CaptureSpec to the docgen package's dataclass."""
    return CaptureSpec(
        section=spec.section,
        title=spec.title,
        argv=list(spec.argv),
        notes=spec.notes,
        safe=spec.safe,
    )


def load_specs(*, use_demo: bool = True) -> list[CaptureSpec]:
    """Return capture specs as docgen-internal dataclasses."""
    return [_from_pydantic(s) for s in _pydantic_all_specs(use_demo=use_demo)]
