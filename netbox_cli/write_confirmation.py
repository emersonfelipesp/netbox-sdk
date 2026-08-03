"""Process-local confirmation gate for live NetBox CLI writes."""

from __future__ import annotations

import os

import typer

WRITE_CONFIRMATION_ENV_VAR = "NETBOX_SDK_CONFIRM_WRITE"
WRITE_HTTP_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def require_write_confirmation(*, confirmed: bool = False) -> None:
    """Refuse a live write unless this ``nbx`` process was explicitly authorized."""
    if confirmed or os.environ.get(WRITE_CONFIRMATION_ENV_VAR) == "1":
        return
    raise typer.BadParameter(
        "Live NetBox writes require explicit confirmation. Review a --dry-run when "
        f"available, then pass --confirm or set {WRITE_CONFIRMATION_ENV_VAR}=1."
    )


__all__ = [
    "WRITE_CONFIRMATION_ENV_VAR",
    "WRITE_HTTP_METHODS",
    "require_write_confirmation",
]
