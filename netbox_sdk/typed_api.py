"""Public factory for versioned typed NetBox clients."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Literal, TypeAlias, overload

from netbox_sdk.versioning import SupportedNetBoxVersion, normalize_netbox_version, version_module_suffix

if TYPE_CHECKING:
    from netbox_sdk.typed_versions.v4_3 import TypedApiV4_3
    from netbox_sdk.typed_versions.v4_4 import TypedApiV4_4
    from netbox_sdk.typed_versions.v4_5 import TypedApiV4_5

    TypedApiClient: TypeAlias = TypedApiV4_3 | TypedApiV4_4 | TypedApiV4_5
else:
    TypedApiClient = object


@overload
def typed_api(url: str, token: str | None = None, *, netbox_version: Literal["4.5"]) -> "TypedApiV4_5": ...


@overload
def typed_api(url: str, token: str | None = None, *, netbox_version: Literal["4.4"]) -> "TypedApiV4_4": ...


@overload
def typed_api(url: str, token: str | None = None, *, netbox_version: Literal["4.3"]) -> "TypedApiV4_3": ...


def typed_api(
    url: str,
    token: str | None = None,
    *,
    netbox_version: SupportedNetBoxVersion | str,
) -> "TypedApiClient":
    version = normalize_netbox_version(netbox_version)
    module_name = f"netbox_sdk.typed_versions.v{version_module_suffix(version)}"
    module = import_module(module_name)
    return module.build_api(url, token)
