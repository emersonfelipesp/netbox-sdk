from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from textual.theme import Theme

_REQUIRED_COLOR_KEYS = (
    "primary",
    "secondary",
    "warning",
    "error",
    "success",
    "accent",
    "background",
    "surface",
    "panel",
    "boost",
)
_REQUIRED_VARIABLE_KEYS = (
    "nb-success-text",
    "nb-info-text",
    "nb-warning-text",
    "nb-danger-text",
    "nb-secondary-text",
    "nb-success-bg",
    "nb-info-bg",
    "nb-warning-bg",
    "nb-danger-bg",
    "nb-secondary-bg",
    "nb-border",
    "nb-border-subtle",
    "nb-muted-text",
    "nb-link-text",
    "nb-id-text",
    "nb-key-text",
)
_HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
_NAME_RE = re.compile(r"^[a-z][a-z0-9-]{1,31}$")


class ThemeCatalogError(ValueError):
    """Raised when theme JSON files are invalid or inconsistent."""


@dataclass(slots=True, frozen=True)
class ThemeDefinition:
    name: str
    label: str
    dark: bool
    colors: dict[str, str]
    variables: dict[str, str]
    aliases: tuple[str, ...]
    source_path: Path

    def to_textual_theme(self) -> Theme:
        return Theme(
            name=self.name,
            dark=self.dark,
            primary=self.colors["primary"],
            secondary=self.colors["secondary"],
            warning=self.colors["warning"],
            error=self.colors["error"],
            success=self.colors["success"],
            accent=self.colors["accent"],
            background=self.colors["background"],
            surface=self.colors["surface"],
            panel=self.colors["panel"],
            boost=self.colors["boost"],
            variables=self.variables,
        )


@dataclass(slots=True, frozen=True)
class ThemeCatalog:
    themes: tuple[ThemeDefinition, ...]
    aliases: dict[str, str]
    default_theme_name: str

    def available_theme_names(self) -> tuple[str, ...]:
        return tuple(theme.name for theme in self.themes)

    def select_options(self) -> tuple[tuple[str, str], ...]:
        return tuple((f"- {theme.label}", theme.name) for theme in self.themes)

    def resolve(self, name: str | None) -> str | None:
        if name is None:
            return None
        key = name.strip().lower()
        if not key:
            return None
        return self.aliases.get(key)

    def theme_for(self, name: str) -> ThemeDefinition:
        for theme in self.themes:
            if theme.name == name:
                return theme
        raise ThemeCatalogError(f"Theme '{name}' was not found in loaded catalog")


def themes_path() -> Path:
    return Path(__file__).resolve().parent / "themes"


def load_theme_catalog(path: Path | None = None) -> ThemeCatalog:
    target = path or themes_path()
    if not target.exists() or not target.is_dir():
        raise ThemeCatalogError(f"Themes directory is missing: {target}")

    json_files = sorted(
        p for p in target.iterdir() if p.is_file() and p.suffix == ".json"
    )
    if not json_files:
        raise ThemeCatalogError(f"No theme JSON files were found in {target}")

    themes: list[ThemeDefinition] = []
    for json_file in json_files:
        themes.append(_load_theme_file(json_file))

    name_map: dict[str, ThemeDefinition] = {}
    aliases: dict[str, str] = {}
    for theme in themes:
        if theme.name in name_map:
            raise ThemeCatalogError(
                f"Duplicate theme name '{theme.name}' found in {theme.source_path} "
                f"and {name_map[theme.name].source_path}"
            )
        name_map[theme.name] = theme
        aliases[theme.name] = theme.name
        for alias in theme.aliases:
            if alias in aliases and aliases[alias] != theme.name:
                raise ThemeCatalogError(
                    f"Alias '{alias}' in {theme.source_path} conflicts with theme '{aliases[alias]}'"
                )
            aliases[alias] = theme.name

    default_theme_name = "default" if "default" in name_map else themes[0].name
    return ThemeCatalog(
        themes=tuple(themes), aliases=aliases, default_theme_name=default_theme_name
    )


def _load_theme_file(path: Path) -> ThemeDefinition:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ThemeCatalogError(f"{path}: invalid JSON ({exc})") from exc
    except OSError as exc:
        raise ThemeCatalogError(f"{path}: unable to read theme file ({exc})") from exc

    if not isinstance(payload, dict):
        raise ThemeCatalogError(f"{path}: top-level JSON must be an object")

    allowed_top_keys = {"name", "label", "dark", "colors", "variables", "aliases"}
    unknown_top = set(payload.keys()) - allowed_top_keys
    if unknown_top:
        raise ThemeCatalogError(
            f"{path}: unknown keys: {', '.join(sorted(unknown_top))}"
        )

    name = _require_string(path, payload, "name")
    if not _NAME_RE.match(name):
        raise ThemeCatalogError(
            f"{path}: name '{name}' is invalid. Use lowercase letters/numbers/hyphens (2-32 chars)."
        )

    label = _require_string(path, payload, "label")
    if not label.strip():
        raise ThemeCatalogError(f"{path}: label must not be empty")

    dark = payload.get("dark")
    if not isinstance(dark, bool):
        raise ThemeCatalogError(f"{path}: dark must be true or false")

    colors = payload.get("colors")
    if not isinstance(colors, dict):
        raise ThemeCatalogError(f"{path}: colors must be an object")
    validated_colors = _validate_colors(path, colors)

    variables_raw = payload.get("variables", {})
    if not isinstance(variables_raw, dict):
        raise ThemeCatalogError(f"{path}: variables must be an object")
    variables = _validate_variables(path, variables_raw)

    aliases_raw = payload.get("aliases", [])
    if not isinstance(aliases_raw, list):
        raise ThemeCatalogError(f"{path}: aliases must be a list of strings")
    aliases = _validate_aliases(path, aliases_raw, theme_name=name)

    return ThemeDefinition(
        name=name,
        label=label,
        dark=dark,
        colors=validated_colors,
        variables=variables,
        aliases=aliases,
        source_path=path,
    )


def _require_string(path: Path, payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ThemeCatalogError(f"{path}: '{key}' must be a string")
    return value


def _validate_colors(path: Path, colors: dict[object, object]) -> dict[str, str]:
    unknown = {
        str(key) for key in colors.keys() if str(key) not in _REQUIRED_COLOR_KEYS
    }
    if unknown:
        raise ThemeCatalogError(
            f"{path}: colors has unknown keys: {', '.join(sorted(unknown))}"
        )

    missing = [key for key in _REQUIRED_COLOR_KEYS if key not in colors]
    if missing:
        raise ThemeCatalogError(f"{path}: colors is missing keys: {', '.join(missing)}")

    validated: dict[str, str] = {}
    for key in _REQUIRED_COLOR_KEYS:
        raw_value = colors[key]
        if not isinstance(raw_value, str):
            raise ThemeCatalogError(f"{path}: colors.{key} must be a string")
        if not _HEX_COLOR_RE.match(raw_value):
            raise ThemeCatalogError(f"{path}: colors.{key} must be in #RRGGBB format")
        validated[key] = raw_value
    return validated


def _validate_variables(path: Path, variables: dict[object, object]) -> dict[str, str]:
    missing = [key for key in _REQUIRED_VARIABLE_KEYS if key not in variables]
    if missing:
        raise ThemeCatalogError(
            f"{path}: variables is missing keys: {', '.join(missing)}"
        )

    validated: dict[str, str] = {}
    for key, value in variables.items():
        if not isinstance(key, str):
            raise ThemeCatalogError(f"{path}: variables keys must be strings")
        if not isinstance(value, str):
            raise ThemeCatalogError(f"{path}: variables.{key} must be a string")
        if not _HEX_COLOR_RE.match(value):
            raise ThemeCatalogError(
                f"{path}: variables.{key} must be in #RRGGBB format"
            )
        validated[key] = value
    return validated


def _validate_aliases(
    path: Path, aliases: list[object], theme_name: str
) -> tuple[str, ...]:
    normalized: list[str] = []
    seen: set[str] = set()
    for item in aliases:
        if not isinstance(item, str):
            raise ThemeCatalogError(f"{path}: aliases must contain only strings")
        alias = item.strip().lower()
        if not alias:
            raise ThemeCatalogError(f"{path}: aliases must not contain empty values")
        if alias == theme_name:
            continue
        if alias in seen:
            raise ThemeCatalogError(f"{path}: duplicate alias '{alias}'")
        seen.add(alias)
        normalized.append(alias)
    return tuple(normalized)
