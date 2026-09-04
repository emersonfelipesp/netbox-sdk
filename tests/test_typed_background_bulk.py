"""NetBox 4.7 background bulk operations, reachable from the typed surface.

4.7 adds ``?background=true`` to bulk POST/PUT/PATCH/DELETE, answering ``202``
with a job reference rather than executing synchronously — it exists to avoid
proxy timeouts on large batches.

The pinned upstream artifact (``v4.7.0``) does not describe the capability,
so the generated bindings were faithful to a schema that omits it and the typed
client simply could not ask. A generator overlay declares the parameter, and the
runtime selects the response model from the request.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from netbox_sdk.typed_runtime import (
    BackgroundJobReference,
    response_model_for_request,
)

pytestmark = pytest.mark.suite_sdk

BUNDLED_4_7 = (
    Path(__file__).resolve().parent.parent
    / "netbox_sdk"
    / "reference"
    / "openapi"
    / "netbox-openapi-4.7.json"
)


def test_the_committed_bundle_stays_faithful_to_upstream() -> None:
    """The overlay must never leak into the committed artifact.

    Provenance verification compares the bundle against the pinned upstream
    document; writing the overlay through would break it and, worse, would make
    the guard below meaningless.
    """
    document = json.loads(BUNDLED_4_7.read_text(encoding="utf-8"))
    background_params = 0
    responses_202 = 0
    for item in document.get("paths", {}).values():
        if not isinstance(item, dict):
            continue
        for operation in item.values():
            if not isinstance(operation, dict):
                continue
            for parameter in operation.get("parameters", []) or []:
                if isinstance(parameter, dict) and parameter.get("name") == "background":
                    background_params += 1
            if "202" in (operation.get("responses") or {}):
                responses_202 += 1

    assert background_params == 0, (
        "The pinned 4.7 schema now describes `background`. The overlay in "
        "scripts/generate_typed_sdk.py has outlived its reason to exist — drop it "
        "and generate straight from upstream."
    )
    assert responses_202 == 0, (
        "The pinned 4.7 schema now describes a 202 response. Re-check whether the "
        "overlay and the runtime job-reference selection are still needed."
    )


def test_generated_4_7_bindings_expose_background() -> None:
    """The overlay is worthless if it does not reach the generated query models."""
    from netbox_sdk.typed_versions import v4_7

    source = Path(v4_7.__file__).read_text(encoding="utf-8")

    assert "background: bool | None = None" in source
    assert ") -> Site | list[Site] | BackgroundJobReference:" in source
    assert ") -> BackgroundJobReference | None:" in source


@pytest.mark.parametrize(
    "query",
    [
        pytest.param({"background": True}, id="dict-true"),
        pytest.param({"background": "true"}, id="string-true"),
        pytest.param({"background": "1"}, id="string-1"),
    ],
)
def test_background_request_expects_a_job_reference(query: dict[str, Any]) -> None:
    from netbox_sdk.models.v4_7 import Site

    assert response_model_for_request(Site, {"name": "a"}, query) is BackgroundJobReference


@pytest.mark.parametrize(
    "query",
    [
        pytest.param(None, id="no-query"),
        pytest.param({}, id="empty-query"),
        pytest.param({"background": False}, id="explicit-false"),
        pytest.param({"background": "false"}, id="string-false"),
        pytest.param({"limit": 10}, id="unrelated-query"),
    ],
)
def test_synchronous_path_is_unchanged(query: Any) -> None:
    """Anything short of an affirmative background flag keeps the declared model."""
    from netbox_sdk.models.v4_7 import Site

    assert response_model_for_request(Site, {"name": "a"}, query) is Site


def test_background_wins_over_body_shape() -> None:
    """A backgrounded batch returns a job, not a list of the committed objects."""
    from netbox_sdk.models.v4_7 import Site

    assert (
        response_model_for_request(Site, [{"name": "a"}, {"name": "b"}], {"background": True})
        is BackgroundJobReference
    )


def test_a_list_body_without_background_still_returns_a_list() -> None:
    """The correction shipped for bulk responses must survive this change."""
    from netbox_sdk.models.v4_7 import Site

    assert response_model_for_request(Site, [{"name": "a"}], None) == list[Site]


def test_background_response_does_not_require_a_synchronous_model() -> None:
    assert (
        response_model_for_request(None, {"name": "a"}, {"background": True})
        is BackgroundJobReference
    )


def test_job_reference_parses_a_realistic_202_body() -> None:
    body = {
        "job": {
            "id": 4211,
            "url": "https://nb.example/api/core/jobs/4211/",
            "status": "pending",
            "created": "2026-01-01T00:00:00Z",
        }
    }

    parsed = BackgroundJobReference.model_validate(body)

    assert parsed.job.id == 4211
    assert parsed.job.status == "pending"
    # Extra keys are preserved rather than rejected: the job serializer carries
    # more than this binding names, and dropping the response over an unmodelled
    # field would defeat the point.
    assert parsed.job.model_dump().get("created") == "2026-01-01T00:00:00Z"


def _harness(*, generated: bool = False) -> tuple[Any, list[dict[str, Any]]]:
    from netbox_sdk.typed_runtime import TypedApiBase, TypedAppBase

    calls: list[dict[str, Any]] = []

    class _Response:
        def __init__(self, status: int, body: Any) -> None:
            self.status = status
            self.text = json.dumps(body)
            self.headers = {"Content-Type": "application/json"}
            self._body = body

        def json(self) -> Any:
            return self._body

    class _Client:
        netbox_version = "4.7"

        async def request(self, method: str, path: str, **kwargs: Any) -> Any:
            query = kwargs.get("query") or {}
            calls.append({"method": method, "path": path, "query": dict(query)})
            if str(query.get("background", "")).lower() in {"true", "1"}:
                return _Response(
                    202,
                    {
                        "job": {
                            "id": 7,
                            "url": "https://nb.example/api/core/jobs/7/",
                            "status": "pending",
                        }
                    },
                )
            payload = kwargs.get("payload")
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
            return _Response(201, body if isinstance(payload, list) else body[0])

    class _Api(TypedApiBase):
        pass

    client = _Client()
    if generated:
        from netbox_sdk.typed_versions.v4_7 import TypedApiV4_7

        return TypedApiV4_7(client).dcim.sites, calls  # type: ignore[arg-type]
    return TypedAppBase(_Api(client=client, netbox_version="4.7")), calls  # type: ignore[arg-type]


async def test_generated_bulk_delete_background_returns_a_validated_job_reference() -> None:
    endpoint, calls = _harness(generated=True)

    result = await endpoint.bulk_delete(
        body=[{"name": "B1", "slug": "b1"}],
        query={"background": True},
    )

    assert isinstance(result, BackgroundJobReference)
    assert result.job.id == 7
    assert calls == [
        {
            "method": "DELETE",
            "path": "/api/dcim/sites/",
            "query": {"background": "True"},
        }
    ]


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
async def test_all_four_bulk_verbs_accept_background(method: str) -> None:
    from netbox_sdk.models.v4_7 import Site

    app, calls = _harness()

    result = await app._typed_json_request(
        method,
        "/api/dcim/sites/",
        body_model=None,
        body=[{"name": "B1", "slug": "b1"}, {"name": "B2", "slug": "b2"}],
        query={"background": True},
        response_model=Site,
    )

    assert isinstance(result, BackgroundJobReference), f"{method} did not return a job reference"
    assert result.job.id == 7
    assert len(calls) == 1, "a backgrounded batch must not be retried"


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH"])
async def test_the_same_verbs_are_unchanged_without_background(method: str) -> None:
    from netbox_sdk.models.v4_7 import Site

    app, calls = _harness()

    result = await app._typed_json_request(
        method,
        "/api/dcim/sites/",
        body_model=None,
        body=[{"name": "B1", "slug": "b1"}, {"name": "B2", "slug": "b2"}],
        response_model=Site,
    )

    assert isinstance(result, list)
    assert [site.name for site in result] == ["B1", "B2"]
    assert len(calls) == 1


def test_overlay_skips_singular_collection_mutations() -> None:
    """Dashboard, script upload, and token provision are not bulk writes."""
    from scripts.generate_typed_sdk import apply_background_bulk_overlay

    document = json.loads(BUNDLED_4_7.read_text(encoding="utf-8"))
    overlaid = apply_background_bulk_overlay("4.7", document)

    def _has_background(path: str, method: str) -> bool:
        operation = overlaid["paths"][path][method]
        return any(
            isinstance(parameter, dict)
            and parameter.get("name") == "background"
            and parameter.get("in") == "query"
            for parameter in operation.get("parameters", []) or []
        )

    assert _has_background("/api/dcim/devices/", "post")
    assert _has_background("/api/dcim/devices/", "put")
    assert _has_background("/api/dcim/devices/", "delete")
    assert not _has_background("/api/extras/dashboard/", "put")
    assert not _has_background("/api/extras/dashboard/", "patch")
    assert not _has_background("/api/extras/scripts/upload/", "post")
    assert not _has_background("/api/users/tokens/provision/", "post")
    dashboard_delete = overlaid["paths"]["/api/extras/dashboard/"]["delete"]
    assert "background" not in {
        parameter.get("name")
        for parameter in dashboard_delete.get("parameters", []) or []
        if isinstance(parameter, dict)
    }
