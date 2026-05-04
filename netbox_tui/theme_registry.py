"""Theme catalog loading, validation, and lookup for built-in and custom themes."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import cast

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator, model_validator
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


class ThemeDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    label: str
    dark: bool
    colors: dict[str, str]
    variables: dict[str, str]
    # When set, drives Textual ``$foreground`` so themes diverge (auto-derived fg is often too similar).
    foreground: str | None = None
    aliases: tuple[str, ...] = ()
    source_path: Path

    @model_validator(mode="before")
    @classmethod
    def _remove_self_alias(cls, data: object) -> object:
        """Strip any alias that equals the theme's own name before field validation."""
        if isinstance(data, dict):
            data = cast(dict[str, object], data)
            name = str(data.get("name", ""))
            aliases = data.get("aliases", [])
            if isinstance(aliases, list):
                data["aliases"] = [
                    a for a in aliases if not (isinstance(a, str) and a.strip().lower() == name)
                ]
        return data

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        if not _NAME_RE.match(v):
            raise ValueError(
                f"name '{v}' is invalid. Use lowercase letters/numbers/hyphens (2-32 chars)."
            )
        return v

    @field_validator("label")
    @classmethod
    def _validate_label(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("label must not be empty")
        return v

    @field_validator("foreground")
    @classmethod
    def _validate_foreground(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("foreground must be a string or null")
        if not _HEX_COLOR_RE.match(v):
            raise ValueError("foreground must be in #RRGGBB format")
        return v

    @field_validator("colors")
    @classmethod
    def _validate_colors(cls, v: dict[str, str]) -> dict[str, str]:
        unknown = set(v.keys()) - set(_REQUIRED_COLOR_KEYS)
        if unknown:
            raise ValueError(f"colors has unknown keys: {', '.join(sorted(unknown))}")
        missing = [key for key in _REQUIRED_COLOR_KEYS if key not in v]
        if missing:
            raise ValueError(f"colors is missing keys: {', '.join(missing)}")
        for key, raw_value in v.items():
            if not isinstance(raw_value, str):
                raise ValueError(f"colors.{key} must be a string")
            if not _HEX_COLOR_RE.match(raw_value):
                raise ValueError(f"colors.{key} must be in #RRGGBB format")
        return v

    @field_validator("variables")
    @classmethod
    def _validate_variables(cls, v: dict[str, str]) -> dict[str, str]:
        missing = [key for key in _REQUIRED_VARIABLE_KEYS if key not in v]
        if missing:
            raise ValueError(f"variables is missing keys: {', '.join(missing)}")
        for key, value in v.items():
            if not isinstance(key, str):
                raise ValueError("variables keys must be strings")
            if not isinstance(value, str):
                raise ValueError(f"variables.{key} must be a string")
            if not _HEX_COLOR_RE.match(value):
                raise ValueError(f"variables.{key} must be in #RRGGBB format")
        return v

    @field_validator("aliases", mode="before")
    @classmethod
    def _validate_aliases(cls, v: object) -> tuple[str, ...]:
        if v is None:
            return ()
        if not isinstance(v, (list, tuple)):
            raise ValueError("aliases must be a list of strings")
        normalized: list[str] = []
        seen: set[str] = set()
        for item in v:
            if not isinstance(item, str):
                raise ValueError("aliases must contain only strings")
            alias = item.strip().lower()
            if not alias:
                raise ValueError("aliases must not contain empty values")
            if alias in seen:
                raise ValueError(f"duplicate alias '{alias}'")
            seen.add(alias)
            normalized.append(alias)
        return tuple(normalized)

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
            foreground=self.foreground,
            background=self.colors["background"],
            surface=self.colors["surface"],
            panel=self.colors["panel"],
            boost=self.colors["boost"],
            variables=self.variables,
        )


class ThemeCatalog(BaseModel):
    model_config = ConfigDict(frozen=True)

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

    json_files = sorted(p for p in target.iterdir() if p.is_file() and p.suffix == ".json")
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

    default_theme_name = "netbox-dark" if "netbox-dark" in name_map else themes[0].name
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

    try:
        return ThemeDefinition.model_validate({**payload, "source_path": path})
    except ValidationError as exc:
        messages = "; ".join(err["msg"] for err in exc.errors())
        raise ThemeCatalogError(f"{path}: {messages}") from exc
