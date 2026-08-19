"""Typed bulk mutations must validate the response shape the server returns.

NetBox reuses the collection path for bulk operations: posting a single object
returns that object, posting a **list** commits the batch and returns a **list**.
The upstream OpenAPI document declares only the singular response for that path,
so the generated bindings declare only the singular model.

Validating a list response against the singular model raises *after the server
has committed the batch*. The caller sees a failure for a mutation that
succeeded, and a retry creates duplicates — the worst available outcome. These
tests pin the request-shape-driven selection that prevents it.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from netbox_sdk.typed_runtime import response_model_for_payload

pytestmark = pytest.mark.suite_sdk


class _Model:
    """Stand-in for a generated response model; identity is all that matters."""


def test_single_object_payload_keeps_the_singular_model() -> None:
    assert response_model_for_payload(_Model, {"name": "one"}) is _Model


def test_list_payload_selects_a_list_model() -> None:
    selected = response_model_for_payload(_Model, [{"name": "one"}, {"name": "two"}])

    assert selected == list[_Model]
    assert selected is not _Model


def test_empty_list_payload_still_selects_a_list_model() -> None:
    """An empty batch is still a batch; the server answers with a list."""
    assert response_model_for_payload(_Model, []) == list[_Model]


def test_absent_response_model_stays_absent() -> None:
    """Endpoints with no declared response model must not gain one."""
    assert response_model_for_payload(None, [{"name": "one"}]) is None
    assert response_model_for_payload(None, {"name": "one"}) is None


async def test_bulk_create_returns_a_list_and_issues_exactly_one_request() -> None:
    """The end-to-end property: a committed batch is not reported as a failure.

    Counts requests explicitly, because the damage from the old behaviour was not
    the exception itself — it was a caller retrying a mutation the server had
    already applied.
    """
    from netbox_sdk.models.v4_6 import Site as SiteV46
    from netbox_sdk.typed_runtime import TypedApiBase, TypedAppBase

    calls: list[dict[str, Any]] = []

    class _Response:
        """Minimal stand-in for the client's ApiResponse."""

        def __init__(self, status: int, body: Any) -> None:
            self.status = status
            self.text = json.dumps(body)
            self.headers: dict[str, str] = {"Content-Type": "application/json"}
            self._body = body

        def json(self) -> Any:
            return self._body

    class _Client:
        netbox_version = "4.6"

        async def request(self, method: str, path: str, **kwargs: Any) -> Any:
            payload = kwargs.get("payload")
            calls.append({"method": method, "path": path, "payload": payload})
            rows = payload if isinstance(payload, list) else [payload]
            body = [
                {
                    "id": i + 1,
                    "url": f"https://nb.example/api/dcim/sites/{i + 1}/",
                    "display_url": f"https://nb.example/dcim/sites/{i + 1}/",
                    "display": row["name"],
                    "name": row["name"],
                    "slug": row["slug"],
                    "created": "2026-01-01T00:00:00Z",
                    "last_updated": "2026-01-01T00:00:00Z",
                    "circuit_count": 0,
                    "device_count": 0,
                    "prefix_count": 0,
                    "rack_count": 0,
                    "virtualmachine_count": 0,
                    "vlan_count": 0,
                }
                for i, row in enumerate(rows)
            ]
            # NetBox answers a list body with a list, a single body with an object.
            return _Response(201, body if isinstance(payload, list) else body[0])

    class _Api(TypedApiBase):
        pass

    api = _Api(client=_Client(), netbox_version="4.6")  # type: ignore[arg-type]
    app = TypedAppBase(api)

    result = await app._typed_json_request(
        "POST",
        "/api/dcim/sites/",
        body_model=None,
        body=[{"name": "B1", "slug": "b1"}, {"name": "B2", "slug": "b2"}],
        response_model=SiteV46,
    )

    assert isinstance(result, list), f"bulk create returned {type(result).__name__}, not a list"
    assert [site.name for site in result] == ["B1", "B2"]
    assert len(calls) == 1, f"a committed batch must not be retried; saw {len(calls)} requests"


def _bulk_harness() -> tuple[Any, list[dict[str, Any]]]:
    """Build a typed app over a fake client that mirrors NetBox's bulk semantics.

    The fake answers a list body with a list and a single body with an object,
    and answers ``DELETE`` with a bodyless ``204`` — the three shapes the
    collection path actually returns.
    """
    from netbox_sdk.typed_runtime import TypedApiBase, TypedAppBase

    calls: list[dict[str, Any]] = []

    class _Response:
        def __init__(self, status: int, body: Any) -> None:
            self.status = status
            self.text = "" if body is None else json.dumps(body)
            self.headers = {"Content-Type": "application/json"} if body is not None else {}
            self._body = body

        def json(self) -> Any:
            return self._body

    class _Client:
        netbox_version = "4.6"

        async def request(self, method: str, path: str, **kwargs: Any) -> Any:
            payload = kwargs.get("payload")
            calls.append({"method": method, "path": path, "payload": payload})
            if method == "DELETE":
                return _Response(204, None)
            rows = payload if isinstance(payload, list) else [payload]
            body = [
                {
                    "id": i + 1,
                    "url": f"https://nb.example/api/dcim/sites/{i + 1}/",
                    "display_url": f"https://nb.example/dcim/sites/{i + 1}/",
                    "display": row["name"],
                    "name": row["name"],
                    "slug": row["slug"],
                    "created": "2026-01-01T00:00:00Z",
                    "last_updated": "2026-01-01T00:00:00Z",
                    "circuit_count": 0,
                    "device_count": 0,
                    "prefix_count": 0,
                    "rack_count": 0,
                    "virtualmachine_count": 0,
                    "vlan_count": 0,
                }
                for i, row in enumerate(rows)
            ]
            status = 200 if method in {"PUT", "PATCH"} else 201
            return _Response(status, body if isinstance(payload, list) else body[0])

    class _Api(TypedApiBase):
        pass

    api = _Api(client=_Client(), netbox_version="4.6")  # type: ignore[arg-type]
    return TypedAppBase(api), calls


@pytest.mark.parametrize("method", ["PUT", "PATCH"])
async def test_bulk_update_and_patch_also_return_lists(method: str) -> None:
    """`bulk-update` and `bulk-patch` share the collection path, so they shared the defect.

    The correction lives in `_typed_json_request`, which every verb routes
    through — this pins that rather than assuming it.
    """
    from netbox_sdk.models.v4_6 import Site as SiteV46

    app, calls = _bulk_harness()

    result = await app._typed_json_request(
        method,
        "/api/dcim/sites/",
        body_model=None,
        body=[{"name": "B1", "slug": "b1"}, {"name": "B2", "slug": "b2"}],
        response_model=SiteV46,
    )

    assert isinstance(result, list), f"{method} returned {type(result).__name__}, not a list"
    assert [site.name for site in result] == ["B1", "B2"]
    assert len(calls) == 1, f"a committed batch must not be retried; saw {len(calls)} requests"


async def test_bulk_delete_returns_none_without_validating_a_body() -> None:
    """NetBox answers a bulk delete with a bodyless 204.

    There is no payload to validate, so the list-shaped request must not cause
    the runtime to demand a list-shaped response. Returning `None` here is what
    keeps a successful bulk delete from being reported as a failure.
    """
    from netbox_sdk.models.v4_6 import Site as SiteV46

    app, calls = _bulk_harness()

    result = await app._typed_json_request(
        "DELETE",
        "/api/dcim/sites/",
        body_model=None,
        body=[{"id": 1}, {"id": 2}],
        response_model=SiteV46,
    )

    assert result is None
    assert len(calls) == 1
    assert calls[0]["method"] == "DELETE"


async def test_single_object_body_still_returns_one_object() -> None:
    """The non-bulk path must be untouched by the shape selection."""
    from netbox_sdk.models.v4_6 import Site as SiteV46

    app, calls = _bulk_harness()

    result = await app._typed_json_request(
        "POST",
        "/api/dcim/sites/",
        body_model=None,
        body={"name": "solo", "slug": "solo"},
        response_model=SiteV46,
    )

    assert not isinstance(result, list)
    assert result.name == "solo"
    assert len(calls) == 1
