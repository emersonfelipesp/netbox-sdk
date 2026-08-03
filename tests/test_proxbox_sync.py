"""Tests for netbox-proxbox SDK scheduling, SSE parsing, and stream transport."""

from __future__ import annotations

import json
from typing import Any

import pytest

from netbox_sdk.client import ApiResponse, NetBoxApiClient
from netbox_sdk.config import Config
from netbox_sdk.exceptions import RequestError
from netbox_sdk.proxbox_sync import ProxboxSyncClient, ProxboxSyncError, SseFrame

pytestmark = pytest.mark.suite_sdk


class _FakeApiClient:
    def __init__(self, responses: list[ApiResponse]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    async def request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        payload: Any = None,
        headers: dict[str, str] | None = None,
        expect_json: bool = True,
    ) -> ApiResponse:
        self.calls.append(
            {
                "method": method,
                "path": path,
                "query": query,
                "payload": payload,
                "headers": headers,
                "expect_json": expect_json,
            }
        )
        return self.responses.pop(0)


def _response(status: int, payload: Any) -> ApiResponse:
    return ApiResponse(status=status, text=json.dumps(payload), headers={})


def test_sse_frame_parse_block_event_and_json_data() -> None:
    frame = SseFrame.parse_block('event: step\ndata: {"step":"sync","status":"started"}\n')

    assert frame.event == "step"
    assert frame.data == {"step": "sync", "status": "started"}


def test_sse_frame_parse_block_multiline_data_and_raw_fallback() -> None:
    raw = SseFrame.parse_block("data: first\ndata: second\n")
    assert raw.event == "message"
    assert raw.data == {"raw": "first\nsecond"}

    non_object = SseFrame.parse_block('event: progress\ndata: ["not", "object"]\n')
    assert non_object.event == "progress"
    assert non_object.data == {"raw": '["not", "object"]'}


async def test_proxbox_schedule_posts_expected_body() -> None:
    fake = _FakeApiClient([_response(201, {"ok": True, "job_id": 42, "message": "queued"})])
    client = ProxboxSyncClient.from_client(fake)  # type: ignore[arg-type]

    result = await client.schedule(
        ["virtual-machines"],
        proxmox_endpoint_ids=[7],
        job_name="nightly",
    )

    assert result.job_id == 42
    assert fake.calls == [
        {
            "method": "POST",
            "path": "/api/plugins/proxbox/sync/schedule/",
            "query": None,
            "payload": {
                "sync_types": ["virtual-machines"],
                "proxmox_endpoint_ids": [7],
                "job_name": "nightly",
            },
            "headers": None,
            "expect_json": True,
        }
    ]


@pytest.mark.parametrize(
    ("status", "payload", "match"),
    [
        (400, {"errors": {"sync_types": ["bad type"]}}, "bad type"),
        (403, {"detail": "Missing enqueue permission"}, "Permission denied"),
    ],
)
async def test_proxbox_schedule_surfaces_error_bodies(
    status: int,
    payload: dict[str, Any],
    match: str,
) -> None:
    fake = _FakeApiClient([_response(status, payload)])
    client = ProxboxSyncClient.from_client(fake)  # type: ignore[arg-type]

    with pytest.raises(ProxboxSyncError, match=match):
        await client.schedule(["storage"])


async def test_resolve_endpoint_numeric_passthrough() -> None:
    fake = _FakeApiClient([])
    client = ProxboxSyncClient.from_client(fake)  # type: ignore[arg-type]

    assert await client.resolve_endpoint("123") == 123
    assert fake.calls == []


async def test_resolve_endpoint_exact_name_lookup() -> None:
    fake = _FakeApiClient(
        [
            _response(
                200,
                {"count": 1, "next": None, "results": [{"id": 9, "name": "pve-prod"}]},
            )
        ]
    )
    client = ProxboxSyncClient.from_client(fake)  # type: ignore[arg-type]

    assert await client.resolve_endpoint("pve-prod") == 9
    assert fake.calls[0]["query"] == {"name": "pve-prod"}


async def test_resolve_endpoint_falls_back_to_case_insensitive_list_lookup() -> None:
    fake = _FakeApiClient(
        [
            _response(200, {"count": 0, "next": None, "results": []}),
            _response(
                200,
                {"count": 1, "next": None, "results": [{"id": 10, "name": "PVE-Prod"}]},
            ),
        ]
    )
    client = ProxboxSyncClient.from_client(fake)  # type: ignore[arg-type]

    assert await client.resolve_endpoint("pve-prod") == 10
    assert fake.calls[1]["query"] is None


async def test_resolve_endpoint_not_found_raises_clear_error() -> None:
    fake = _FakeApiClient(
        [
            _response(200, {"count": 0, "next": None, "results": []}),
            _response(200, {"count": 0, "next": None, "results": []}),
        ]
    )
    client = ProxboxSyncClient.from_client(fake)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="No Proxmox endpoint found"):
        await client.resolve_endpoint("missing")


async def test_fetch_job_uses_core_jobs_path() -> None:
    fake = _FakeApiClient([_response(200, {"id": 42, "status": "completed"})])
    client = ProxboxSyncClient.from_client(fake)  # type: ignore[arg-type]

    assert await client.fetch_job(42) == {"id": 42, "status": "completed"}
    assert fake.calls[0]["path"] == "/api/core/jobs/42/"


class _FakeContent:
    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = list(chunks)

    def __aiter__(self) -> _FakeContent:
        return self

    async def __anext__(self) -> bytes:
        if not self._chunks:
            raise StopAsyncIteration
        return self._chunks.pop(0)


class _FakeStreamResponse:
    def __init__(
        self,
        status: int,
        chunks: list[bytes],
        text: str = "",
        content_type: str = "text/event-stream",
    ) -> None:
        self.status = status
        self.content = _FakeContent(chunks)
        self.headers = {"Content-Type": content_type}
        self._text = text

    async def __aenter__(self) -> _FakeStreamResponse:
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> bool:
        return False

    async def text(self) -> str:
        return self._text


class _FakeSession:
    def __init__(self, response: _FakeStreamResponse) -> None:
        self.response = response
        self.request_kwargs: dict[str, Any] = {}

    def request(self, **kwargs: Any) -> _FakeStreamResponse:
        self.request_kwargs = kwargs
        return self.response


async def test_stream_sse_yields_blocks_split_across_chunks(monkeypatch) -> None:
    cfg = Config(
        base_url="https://netbox.example.com",
        token_version="v1",
        token_secret="plain-token",
    )
    client = NetBoxApiClient(cfg)
    session = _FakeSession(
        _FakeStreamResponse(
            200,
            [
                b'event: step\ndata: {"step": "schedule"}',
                b'\n\nevent: complete\r\ndata: {"ok": true}\r\n\r\n',
            ],
        )
    )

    async def _fake_get_session() -> _FakeSession:
        return session

    monkeypatch.setattr(client, "_get_session", _fake_get_session)

    blocks = [block async for block in client.stream_sse("GET", "/plugins/proxbox/jobs/42/stream/")]

    assert blocks == [
        'event: step\ndata: {"step": "schedule"}',
        'event: complete\r\ndata: {"ok": true}',
    ]
    assert session.request_kwargs["headers"]["Accept"] == "text/event-stream"
    assert session.request_kwargs["headers"]["Authorization"] == "Token plain-token"
    assert session.request_kwargs["timeout"].total == 7200.0


async def test_stream_sse_prefers_case_insensitive_caller_authorization(monkeypatch) -> None:
    """A caller-supplied lower-case "authorization" header must override the
    client's own configured credential, and must not be sent alongside a
    separately-cased "Authorization" header."""
    cfg = Config(
        base_url="https://netbox.example.com",
        token_version="v1",
        token_secret="plain-token",
    )
    client = NetBoxApiClient(cfg)
    session = _FakeSession(_FakeStreamResponse(200, [b"data: {}\n\n"]))

    async def _fake_get_session() -> _FakeSession:
        return session

    monkeypatch.setattr(client, "_get_session", _fake_get_session)

    _ = [
        block
        async for block in client.stream_sse(
            "GET",
            "/plugins/proxbox/jobs/42/stream/",
            headers={"authorization": "Bearer caller-token"},
        )
    ]

    sent_headers = session.request_kwargs["headers"]
    assert sent_headers["Authorization"] == "Bearer caller-token"
    assert "authorization" not in sent_headers


async def test_stream_sse_authorization_precedence_preserves_explicit_empty_override(
    monkeypatch,
) -> None:
    cfg = Config(
        base_url="https://netbox.example.com",
        token_version="v1",
        token_secret="plain-token",
    )
    client = NetBoxApiClient(cfg)
    captured: list[dict[str, str]] = []

    async def _capture(
        *,
        headers: dict[str, str] | None = None,
        scoped_authorization: str | None = None,
    ) -> None:
        session = _FakeSession(_FakeStreamResponse(200, [b"data: {}\n\n"]))

        async def _fake_get_session() -> _FakeSession:
            return session

        monkeypatch.setattr(client, "_get_session", _fake_get_session)
        if scoped_authorization is None:
            _ = [
                block
                async for block in client.stream_sse(
                    "GET",
                    "/plugins/proxbox/jobs/42/stream/",
                    headers=headers,
                )
            ]
        else:
            with client.header_scope(**{"Authorization": scoped_authorization}):
                _ = [
                    block
                    async for block in client.stream_sse(
                        "GET",
                        "/plugins/proxbox/jobs/42/stream/",
                        headers=headers,
                    )
                ]
        captured.append(dict(session.request_kwargs["headers"]))

    await _capture(headers={"authorization": ""})
    await _capture(scoped_authorization="")
    await _capture(headers={"authorization": "Bearer delegated-token"})
    await _capture()

    assert "Authorization" not in captured[0]
    assert "Authorization" not in captured[1]
    assert captured[2]["Authorization"] == "Bearer delegated-token"
    assert captured[3]["Authorization"] == "Token plain-token"


async def test_stream_sse_raises_request_error_with_body(monkeypatch) -> None:
    client = NetBoxApiClient(Config(base_url="https://netbox.example.com"))
    session = _FakeSession(_FakeStreamResponse(403, [], text="permission denied"))

    async def _fake_get_session() -> _FakeSession:
        return session

    monkeypatch.setattr(client, "_get_session", _fake_get_session)

    with pytest.raises(RequestError) as excinfo:
        _ = [block async for block in client.stream_sse("GET", "/plugins/proxbox/jobs/42/stream/")]

    assert excinfo.value.response.status == 403
    assert "permission denied" in excinfo.value.response.text


async def test_stream_sse_rejects_non_event_stream_success(monkeypatch) -> None:
    client = NetBoxApiClient(Config(base_url="https://netbox.example.com"))
    session = _FakeSession(
        _FakeStreamResponse(
            200,
            [b"<html>login</html>"],
            text="<html>login</html>",
            content_type="text/html; charset=utf-8",
        )
    )

    async def _fake_get_session() -> _FakeSession:
        return session

    monkeypatch.setattr(client, "_get_session", _fake_get_session)

    with pytest.raises(RequestError) as excinfo:
        _ = [block async for block in client.stream_sse("GET", "/plugins/proxbox/jobs/42/stream/")]

    assert excinfo.value.response.status == 200
    assert "did not return an event stream" in excinfo.value.response.text
    # Redirects must not be followed for a stream request.
    assert session.request_kwargs["allow_redirects"] is False


async def test_stream_sse_rejects_redirect(monkeypatch) -> None:
    client = NetBoxApiClient(Config(base_url="https://netbox.example.com"))
    session = _FakeSession(_FakeStreamResponse(302, [], text="", content_type="text/html"))

    async def _fake_get_session() -> _FakeSession:
        return session

    monkeypatch.setattr(client, "_get_session", _fake_get_session)

    with pytest.raises(RequestError) as excinfo:
        _ = [block async for block in client.stream_sse("GET", "/plugins/proxbox/jobs/42/stream/")]

    assert excinfo.value.response.status == 302
