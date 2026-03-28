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
    assert "nbx graphql --help" in titles
    assert "nbx demo graphql --help" in titles
    assert "nbx graphql tui --help" in titles
    assert "nbx graphql tui --theme" in titles
    assert "nbx demo graphql tui --help" in titles
    assert "nbx demo graphql tui --theme" in titles


def test_docgen_demo_backed_specs_use_demo_prefix() -> None:
    specs = load_specs()

    demo_specs = [spec for spec in specs if spec.argv and spec.argv[0] == "demo"]
    non_demo_safe_false = [
        spec for spec in specs if not spec.safe and (not spec.argv or spec.argv[0] != "demo")
    ]

    assert demo_specs
    assert not non_demo_safe_false


def test_docgen_drops_timeout_prone_live_api_sections() -> None:
    specs = load_specs()

    sections = {spec.section for spec in specs}

    assert "Live API" not in sections
    assert "Cable Trace" not in sections
