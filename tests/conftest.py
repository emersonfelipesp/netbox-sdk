from pathlib import Path

import pytest

from netbox_sdk.client import _scoped_headers

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
