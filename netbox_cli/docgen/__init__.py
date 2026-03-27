"""Docgen package — CLI capture engine, format conversion, and artifact storage.

Architecture (SOLID):
    models.py      — Value objects and constants  (SRP)
    engine.py      — Parallel CLI capture engine  (SRP + DIP)
    format.py      — Output format conversion      (SRP + OCP)
    specs.py       — Re-export of CaptureSpec defs  (SRP)

Public facade lives in ``netbox_cli.docgen_capture`` (backward compat).
"""

from netbox_cli.docgen.engine import CaptureEngine as CaptureEngine
from netbox_cli.docgen.format import convert_json_to_variants as convert_json_to_variants
from netbox_cli.docgen.models import CaptureArtifact as CaptureArtifact
from netbox_cli.docgen.models import CaptureResult as CaptureResult
from netbox_cli.docgen.models import CaptureSpec as CaptureSpec
