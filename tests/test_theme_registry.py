from __future__ import annotations

from pathlib import Path

import pytest

from netbox_cli.theme_registry import ThemeCatalogError, load_theme_catalog


def test_theme_catalog_loads_default_and_dracula() -> None:
    catalog = load_theme_catalog()
    assert catalog.available_theme_names() == ("default", "dracula")
    assert catalog.resolve("netbox-dark") == "default"
    assert catalog.resolve("dracula") == "dracula"
    assert catalog.default_theme_name == "default"


def test_theme_catalog_invalid_color_fails(tmp_path: Path) -> None:
    theme_file = tmp_path / "broken.json"
    theme_file.write_text(
        """
{
  "name": "broken",
  "label": "Broken",
  "dark": true,
  "colors": {
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
  },
  "variables": {},
  "aliases": []
}
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
  "variables": {{}},
  "aliases": ["shared"]
}}
""".strip(),
            encoding="utf-8",
        )

    with pytest.raises(ThemeCatalogError, match="Alias 'shared'"):
        load_theme_catalog(tmp_path)
