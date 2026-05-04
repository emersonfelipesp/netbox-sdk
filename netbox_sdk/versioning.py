"""Version helpers for bundled NetBox OpenAPI support."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, cast, get_args

SupportedNetBoxVersion = Literal["4.6", "4.5", "4.4", "4.3"]
SUPPORTED_NETBOX_VERSIONS: tuple[SupportedNetBoxVersion, ...] = get_args(SupportedNetBoxVersion)

_DEFAULT_VERSION: SupportedNetBoxVersion = "4.5"


class UnsupportedNetBoxVersionError(ValueError):
    """Raised when a requested NetBox version is outside the supported release lines."""


def normalize_netbox_version(version: str | None) -> SupportedNetBoxVersion:
    if version is None:
        return _DEFAULT_VERSION
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
    return (
        Path(__file__).resolve().parent / "reference" / "openapi" / f"netbox-openapi-{version}.json"
    )


def version_module_suffix(version: SupportedNetBoxVersion) -> str:
    return version.replace(".", "_")
