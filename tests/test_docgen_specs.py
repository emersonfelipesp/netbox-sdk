from __future__ import annotations

import pytest

from netbox_cli.docgen.specs import load_specs

pytestmark = pytest.mark.suite_cli


def test_docgen_specs_cover_cli_and_tui_surfaces() -> None:
    specs = load_specs()

    surfaces = {spec.surface for spec in specs}
    titles = {spec.title for spec in specs}

    assert surfaces == {"cli", "tui"}
    assert "nbx cli tui --help" in titles
    assert "nbx demo cli tui --help" in titles
    assert "nbx tui logs --theme" in titles


def test_docgen_live_api_examples_use_demo_prefix() -> None:
    specs = load_specs()

    live_specs = [spec for spec in specs if spec.section in {"Live API", "Cable Trace"}]

    assert live_specs
    assert all(spec.argv[0] == "demo" for spec in live_specs)
