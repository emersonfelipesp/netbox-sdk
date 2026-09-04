"""Release-line registry for bundled NetBox OpenAPI and typed support."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, cast

from pydantic import BaseModel, ConfigDict

SupportedNetBoxVersion = Literal["4.7", "4.6", "4.5", "4.4", "4.3"]


class ReleaseLine(BaseModel):
    """Artifacts and lifecycle status owned by a supported NetBox release line."""

    model_config = ConfigDict(frozen=True)

    line: str
    status: Literal["stable", "preview"]
    openapi_asset: str
    models_module: str
    typed_module: str

    @property
    def module_suffix(self) -> str:
        """Return the ``<major>_<minor>`` suffix shared by this line's modules."""
        return self.line.replace(".", "_")


_RELEASE_LINE_REGISTRY: dict[SupportedNetBoxVersion, ReleaseLine] = {
    # NetBox v4.7.0 is the official GA record for the 4.7 release line.
    "4.7": ReleaseLine(
        line="4.7",
        status="stable",
        openapi_asset="netbox-openapi-4.7.json",
        models_module="netbox_sdk.models.v4_7",
        typed_module="netbox_sdk.typed_versions.v4_7",
    ),
    "4.6": ReleaseLine(
        line="4.6",
        status="stable",
        openapi_asset="netbox-openapi-4.6.json",
        models_module="netbox_sdk.models.v4_6",
        typed_module="netbox_sdk.typed_versions.v4_6",
    ),
    "4.5": ReleaseLine(
        line="4.5",
        status="stable",
        openapi_asset="netbox-openapi-4.5.json",
        models_module="netbox_sdk.models.v4_5",
        typed_module="netbox_sdk.typed_versions.v4_5",
    ),
    "4.4": ReleaseLine(
        line="4.4",
        status="stable",
        openapi_asset="netbox-openapi-4.4.json",
        models_module="netbox_sdk.models.v4_4",
        typed_module="netbox_sdk.typed_versions.v4_4",
    ),
    "4.3": ReleaseLine(
        line="4.3",
        status="stable",
        openapi_asset="netbox-openapi-4.3.json",
        models_module="netbox_sdk.models.v4_3",
        typed_module="netbox_sdk.typed_versions.v4_3",
    ),
}

SUPPORTED_NETBOX_VERSIONS: tuple[SupportedNetBoxVersion, ...] = tuple(_RELEASE_LINE_REGISTRY)


class UnsupportedNetBoxVersionError(ValueError):
    """Raised when a requested NetBox version is outside the supported release lines."""


def release_lines() -> tuple[ReleaseLine, ...]:
    """Return supported release records in newest-to-oldest registry order."""
    return tuple(_RELEASE_LINE_REGISTRY.values())


def release_line(line: str) -> ReleaseLine:
    """Return the registry record for ``line`` after normalizing it."""
    normalized = normalize_netbox_version(line)
    return _RELEASE_LINE_REGISTRY[normalized]


def describe_supported_versions() -> str:
    """Return the canonical user-facing description of supported release lines.

    Lines are enumerated oldest-first and preview lines are labelled. A range
    summary ("4.3 through 4.7") would silently advertise a pre-release line as
    fully supported, and would also be wrong if the registry ever skipped a line.
    """
    return ", ".join(
        line if _RELEASE_LINE_REGISTRY[line].status == "stable" else f"{line} (preview)"
        for line in reversed(SUPPORTED_NETBOX_VERSIONS)
    )


def latest_stable_line() -> SupportedNetBoxVersion:
    """Return the newest release line marked stable in registry order."""
    for line, record in _RELEASE_LINE_REGISTRY.items():
        if record.status == "stable":
            return line
    raise RuntimeError("No stable NetBox release line is registered")


DEFAULT_NETBOX_VERSION: SupportedNetBoxVersion = latest_stable_line()


def normalize_netbox_version(version: str | None) -> SupportedNetBoxVersion:
    if version is None:
        return DEFAULT_NETBOX_VERSION
    raw = version.strip().removeprefix("v")
    parts = raw.split(".")
    if len(parts) < 2:
        raise UnsupportedNetBoxVersionError(
            f"Unsupported NetBox version '{version}'. Expected one of: {', '.join(SUPPORTED_NETBOX_VERSIONS)}."
        )
    release_line = f"{parts[0]}.{parts[1]}"
    if release_line not in SUPPORTED_NETBOX_VERSIONS:
        raise UnsupportedNetBoxVersionError(
            f"Unsupported NetBox version '{version}'. Supported release lines: {', '.join(SUPPORTED_NETBOX_VERSIONS)}."
        )
    return cast(SupportedNetBoxVersion, release_line)


def bundled_openapi_path(version: SupportedNetBoxVersion) -> Path:
    """Return the bundled OpenAPI path for ``version``.

    Registered lines resolve through the registry. An unregistered runtime string
    still falls back to the historical name computation rather than raising, so
    this public helper keeps the permissive behaviour callers had before the
    registry existed.
    """
    record = _RELEASE_LINE_REGISTRY.get(version)
    asset = record.openapi_asset if record is not None else f"netbox-openapi-{version}.json"
    return Path(__file__).resolve().parent / "reference" / "openapi" / asset


def version_module_suffix(version: SupportedNetBoxVersion) -> str:
    """Return the ``<major>_<minor>`` module suffix for ``version``.

    Permissive for the same reason as :func:`bundled_openapi_path`: an
    unregistered runtime string computes the historical suffix instead of
    raising ``KeyError``.
    """
    record = _RELEASE_LINE_REGISTRY.get(version)
    return record.module_suffix if record is not None else version.replace(".", "_")
