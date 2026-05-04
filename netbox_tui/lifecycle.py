"""Lifecycle helpers shared by Textual apps."""

from __future__ import annotations

import inspect
from typing import Any

from netbox_sdk.logging_runtime import get_logger

logger = get_logger(__name__)


async def close_client_for_tui(client: Any, *, event: str) -> None:
    close_fn = getattr(client, "close", None)
    if not callable(close_fn):
        return
    try:
        result = close_fn()
        if inspect.isawaitable(result):
            await result
    except Exception:
        logger.debug(
            "tui client close failed",
            extra={"nbx_event": event},
            exc_info=True,
        )
