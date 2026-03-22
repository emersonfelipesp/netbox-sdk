"""Tests for theme-aware NetBox logo rendering colors."""

from __future__ import annotations

from netbox_cli.theme_registry import load_theme_catalog
from netbox_cli.ui.logo_render import build_netbox_logo


def _hex(span_index: int, logo) -> str:
    return logo.spans[span_index].style.color.get_truecolor().hex.upper()


def test_netbox_dark_logo_uses_bright_teal_and_white() -> None:
    theme = load_theme_catalog().theme_for("netbox-dark")
    logo = build_netbox_logo(theme)

    assert str(logo) == "● NetBox"
    assert logo.spans[0].style.bold is True
    assert _hex(0, logo) == "#00F2D4"
    assert _hex(1, logo) == "#FFFFFF"
    assert _hex(2, logo) == "#00F2D4"


def test_netbox_light_logo_uses_dark_teal_and_dark_wordmark() -> None:
    theme = load_theme_catalog().theme_for("netbox-light")
    logo = build_netbox_logo(theme)

    assert str(logo) == "● NetBox"
    assert logo.spans[0].style.bold is True
    assert _hex(0, logo) == "#00857D"
    assert _hex(1, logo) == "#001423"
    assert _hex(2, logo) == "#00857D"
