"""Tests for theme catalog loading and theme definition validation."""

from __future__ import annotations

from colorsys import rgb_to_hls
from pathlib import Path

import pytest

from netbox_tui.theme_registry import ThemeCatalogError, load_theme_catalog

pytestmark = pytest.mark.suite_tui


def test_themes_set_explicit_foreground_for_textual() -> None:
    """Textual derives similar auto-foregrounds for dark themes unless we set it."""
    catalog = load_theme_catalog()
    for name in catalog.available_theme_names():
        theme = catalog.theme_for(name)
        assert theme.foreground is not None, f"{name} should define foreground"
        tt = theme.to_textual_theme()
        assert tt.foreground == theme.foreground


def _required_variables_json() -> str:
    return """
    "nb-success-text": "#000001",
    "nb-info-text": "#000002",
    "nb-warning-text": "#000003",
    "nb-danger-text": "#000004",
    "nb-secondary-text": "#000005",
    "nb-success-bg": "#000006",
    "nb-info-bg": "#000007",
    "nb-warning-bg": "#000008",
    "nb-danger-bg": "#000009",
    "nb-secondary-bg": "#00000A",
    "nb-border": "#00000B",
    "nb-border-subtle": "#00000C",
    "nb-muted-text": "#00000D",
    "nb-link-text": "#00000E",
    "nb-id-text": "#00000F",
    "nb-key-text": "#000010"
""".strip()


def test_theme_catalog_loads_builtin_themes() -> None:
    catalog = load_theme_catalog()
    assert catalog.available_theme_names() == (
        "dracula",
        "netbox-dark",
        "netbox-light",
        "onedark-pro",
        "tokyo-night",
    )
    assert catalog.resolve("netbox") == "netbox-dark"
    assert catalog.resolve("netbox-dark") == "netbox-dark"
    assert catalog.resolve("default") == "netbox-dark"
    assert catalog.resolve("netbox-light") == "netbox-light"
    assert catalog.resolve("dracula") == "dracula"
    assert catalog.resolve("tokyo-night") == "tokyo-night"
    assert catalog.resolve("tokyo") == "tokyo-night"
    assert catalog.resolve("onedark-pro") == "onedark-pro"
    assert catalog.resolve("onedark") == "onedark-pro"
    assert catalog.resolve("one-dark") == "onedark-pro"
    assert catalog.default_theme_name == "netbox-dark"


def test_onedark_pro_surface_stack_matches_textual_atom_one_dark() -> None:
    """Textual's atom-one-dark uses surface/panel *above* background; inverted stacks break internals."""
    theme = load_theme_catalog().theme_for("onedark-pro")

    def _rgb_channels(hex_color: str) -> tuple[int, int, int]:
        value = hex_color.lstrip("#")
        return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))

    def _lightness(hex_color: str) -> float:
        red, green, blue = _rgb_channels(hex_color)
        _, lightness, _ = rgb_to_hls(red / 255, green / 255, blue / 255)
        return lightness

    background = theme.colors["background"]
    surface = theme.colors["surface"]
    panel = theme.colors["panel"]
    boost = theme.colors["boost"]

    assert background == "#282C34"
    assert surface == "#3B414D"
    assert panel == "#4F5666"
    assert boost == "#5C6370"
    assert _lightness(background) < _lightness(surface) < _lightness(panel) < _lightness(boost)


def test_dracula_surface_stack_stays_neutral_and_progressive() -> None:
    theme = load_theme_catalog().theme_for("dracula")

    def _rgb_channels(hex_color: str) -> tuple[int, int, int]:
        value = hex_color.lstrip("#")
        return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))

    def _lightness(hex_color: str) -> float:
        red, green, blue = _rgb_channels(hex_color)
        _, lightness, _ = rgb_to_hls(red / 255, green / 255, blue / 255)
        return lightness

    def _channel_spread(hex_color: str) -> int:
        channels = _rgb_channels(hex_color)
        return max(channels) - min(channels)

    background = theme.colors["background"]
    surface = theme.colors["surface"]
    panel = theme.colors["panel"]
    boost = theme.colors["boost"]

    assert _lightness(background) < _lightness(surface) < _lightness(panel) < _lightness(boost)
    assert _channel_spread(surface) <= 12
    assert _channel_spread(panel) <= 12
    assert _channel_spread(boost) <= 12


def test_theme_catalog_invalid_color_fails(tmp_path: Path) -> None:
    theme_file = tmp_path / "broken.json"
    theme_file.write_text(
        f"""
{{
  "name": "broken",
  "label": "Broken",
  "dark": true,
  "colors": {{
    "primary": "#12",
    "secondary": "#000000",
    "warning": "#000000",
    "error": "#000000",
    "success": "#000000",
    "accent": "#000000",
    "background": "#000000",
    "surface": "#000000",
    "panel": "#000000",
    "boost": "#000000"
  }},
  "variables": {{
    {_required_variables_json()}
  }},
  "aliases": []
}}
""".strip(),
        encoding="utf-8",
    )
    with pytest.raises(ThemeCatalogError, match="colors.primary"):
        load_theme_catalog(tmp_path)


def test_theme_catalog_alias_conflict_fails(tmp_path: Path) -> None:
    first = tmp_path / "one.json"
    second = tmp_path / "two.json"
    for path, name in ((first, "one"), (second, "two")):
        path.write_text(
            f"""
{{
  "name": "{name}",
  "label": "{name}",
  "dark": true,
  "colors": {{
    "primary": "#111111",
    "secondary": "#222222",
    "warning": "#333333",
    "error": "#444444",
    "success": "#555555",
    "accent": "#666666",
    "background": "#777777",
    "surface": "#888888",
    "panel": "#999999",
    "boost": "#AAAAAA"
  }},
  "variables": {{
    {_required_variables_json()}
  }},
  "aliases": ["shared"]
}}
""".strip(),
            encoding="utf-8",
        )

    with pytest.raises(ThemeCatalogError, match="Alias 'shared'"):
        load_theme_catalog(tmp_path)


def test_theme_catalog_missing_required_variable_fails(tmp_path: Path) -> None:
    theme_file = tmp_path / "broken-vars.json"
    theme_file.write_text(
        """
{
  "name": "broken-vars",
  "label": "Broken Vars",
  "dark": true,
  "colors": {
    "primary": "#111111",
    "secondary": "#222222",
    "warning": "#333333",
    "error": "#444444",
    "success": "#555555",
    "accent": "#666666",
    "background": "#777777",
    "surface": "#888888",
    "panel": "#999999",
    "boost": "#AAAAAA"
  },
  "variables": {
    "nb-success-text": "#000001"
  },
  "aliases": []
}
""".strip(),
        encoding="utf-8",
    )
    with pytest.raises(ThemeCatalogError, match="variables is missing keys"):
        load_theme_catalog(tmp_path)
