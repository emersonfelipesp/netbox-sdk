"""Docgen package — CLI capture engine, format conversion, and artifact storage.

Architecture (SOLID):
    models.py      — Value objects and constants  (SRP)
    engine.py      — Parallel CLI capture engine  (SRP + DIP)
    format.py      — Output format conversion      (SRP + OCP)
    specs.py       — Re-export of CaptureSpec defs  (SRP)

Public facade lives in ``netbox_cli.docgen_capture`` (backward compat).
"""

from .engine import CaptureEngine as CaptureEngine
from .format import convert_json_to_variants as convert_json_to_variants
from .models import CaptureArtifact as CaptureArtifact
from .models import CaptureResult as CaptureResult
from .models import CaptureSpec as CaptureSpec
