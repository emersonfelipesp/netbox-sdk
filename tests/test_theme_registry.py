from __future__ import annotations

from pathlib import Path

import pytest

from netbox_cli.theme_registry import ThemeCatalogError, load_theme_catalog


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
        "default",
        "dracula",
        "netbox-dark",
        "netbox-light",
    )
    assert catalog.resolve("netbox") == "netbox-dark"
    assert catalog.resolve("netbox-dark") == "netbox-dark"
    assert catalog.resolve("netbox-light") == "netbox-light"
    assert catalog.resolve("dracula") == "dracula"
    assert catalog.default_theme_name == "default"


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
