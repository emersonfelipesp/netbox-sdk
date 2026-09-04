import json
import re
from pathlib import Path
from typing import Any

import pytest

from netbox_sdk.client import _scoped_headers
from netbox_sdk.schema_resolution import clear_schema_caches

OPENAPI_PATH = (
    Path(__file__).resolve().parent.parent
    / "netbox_sdk"
    / "reference"
    / "openapi"
    / "netbox-openapi.json"
)


@pytest.fixture(autouse=True)
def _reset_scoped_headers():
    """Isolate the process-global ``X-NetBox-Branch`` ContextVar between tests.

    ``netbox_sdk.client._scoped_headers`` is mutated by the branch-scoping
    helpers (``header_scope``, ``BranchingClient.activate``, ``Api.activate_branch``)
    and by the CLI ``--branch`` option. Async tests run inside their own asyncio
    task context, so a value left set by one test can be inherited by a later
    test that asserts absolute ContextVar state (e.g. ``test_client_header_scope``)
    — which, under ``-n auto`` xdist, surfaces only for certain worker
    distributions. Snapshot and restore a clean baseline around every test so the
    suite is order-independent.
    """
    token = _scoped_headers.set({})
    try:
        yield
    finally:
        _scoped_headers.reset(token)


@pytest.fixture(autouse=True)
def _reset_schema_caches():
    """Prevent patched SDK or CLI schema loaders from leaking across tests."""
    clear_schema_caches()
    try:
        yield
    finally:
        clear_schema_caches()


# Rich renders the "Fetching..." status spinner whenever it believes stdout is a
# terminal, and it believes that whenever FORCE_COLOR is set — which Claude Code,
# many CI images, and plenty of developer shells do. CliRunner captures the
# spinner's cursor-hide, cursor-up and erase-line sequences into the same buffer
# as the payload, so a test that parses stdout as pure JSON passes or fails
# depending on the ambient environment rather than on the code under test.
#
# CI happens to run with it unset, which is why this stayed hidden there.
_CSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def strip_terminal_control(text: str) -> str:
    """Remove ANSI CSI sequences and carriage returns from captured output."""
    return _CSI_RE.sub("", text).replace("\r", "")


def cli_json(output: str) -> Any:
    """Parse the JSON document a CLI command printed, ignoring terminal noise.

    Stripping escapes alone is not enough: the spinner's *text* ("Fetching...")
    survives, because it is erased with cursor-movement sequences rather than by
    rewriting the buffer. So decode from the first JSON opening token instead of
    assuming the payload starts at byte zero.
    """
    cleaned = strip_terminal_control(output)
    for index, character in enumerate(cleaned):
        if character in "{[":
            return json.JSONDecoder().raw_decode(cleaned, index)[0]
    raise AssertionError(f"no JSON document in CLI output: {cleaned!r}")
