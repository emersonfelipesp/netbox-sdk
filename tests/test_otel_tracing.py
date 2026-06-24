"""Tests for optional OpenTelemetry request tracing."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from netbox_sdk.client import ApiResponse, NetBoxApiClient
from netbox_sdk.config import Config, load_config

pytestmark = pytest.mark.suite_sdk


def _reset_global_tracer_provider(trace: Any) -> None:
    set_once = getattr(trace, "_TRACER_PROVIDER_SET_ONCE", None)
    if set_once is not None and hasattr(set_once, "_done"):
        set_once._done = False  # noqa: SLF001
    if hasattr(trace, "_TRACER_PROVIDER"):
        trace._TRACER_PROVIDER = None  # noqa: SLF001


def _in_memory_span_exporter_class() -> Any:
    try:
        from opentelemetry.sdk.trace.export import InMemorySpanExporter
    except ImportError:
        from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
            InMemorySpanExporter,
        )
    return InMemorySpanExporter


@pytest.fixture
def span_exporter():
    pytest.importorskip("opentelemetry.sdk.trace")

    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor

    _reset_global_tracer_provider(trace)
    exporter = _in_memory_span_exporter_class()()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    try:
        yield exporter
    finally:
        provider.shutdown()
        _reset_global_tracer_provider(trace)


async def _fake_get_session(self: NetBoxApiClient) -> object:
    return object()


@pytest.mark.asyncio
async def test_enabled_request_emits_one_client_span(monkeypatch, tmp_path, span_exporter) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("NETBOX_OTEL_ENABLED", raising=False)
    monkeypatch.delenv("OTEL_SDK_DISABLED", raising=False)
    monkeypatch.setattr(NetBoxApiClient, "_get_session", _fake_get_session, raising=True)

    async def _fake_request_once(self: NetBoxApiClient, session: object, **kwargs: Any):
        return ApiResponse(status=201, text='{"ok": true}', headers={})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    client = NetBoxApiClient(
        Config(
            base_url="https://netbox.example.com:9443/netbox",
            token_version="v1",
            token_secret="plain-token",
            otel_enabled=True,
        )
    )

    response = await client.request("POST", "/api/dcim/devices/", payload={"name": "sw01"})

    from opentelemetry.trace import SpanKind

    spans = span_exporter.get_finished_spans()
    assert response.status == 201
    assert len(spans) == 1
    span = spans[0]
    assert span.name == "HTTP POST"
    assert span.kind == SpanKind.CLIENT
    assert span.attributes["http.request.method"] == "POST"
    assert span.attributes["server.address"] == "netbox.example.com"
    assert span.attributes["url.path"] == "/api/dcim/devices/"
    assert span.attributes["http.response.status_code"] == 201


@pytest.mark.asyncio
async def test_disabled_request_emits_zero_spans(monkeypatch, tmp_path, span_exporter) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("NETBOX_OTEL_ENABLED", raising=False)
    monkeypatch.delenv("OTEL_SDK_DISABLED", raising=False)
    monkeypatch.setattr(NetBoxApiClient, "_get_session", _fake_get_session, raising=True)

    async def _fake_request_once(self: NetBoxApiClient, session: object, **kwargs: Any):
        return ApiResponse(status=200, text='{"ok": true}', headers={})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    client = NetBoxApiClient(
        Config(
            base_url="https://netbox.example.com",
            token_version="v1",
            token_secret="plain-token",
            otel_enabled=False,
        )
    )

    response = await client.request("POST", "/api/dcim/devices/", payload={"name": "sw01"})

    assert response.status == 200
    assert not span_exporter.get_finished_spans()


def test_base_import_does_not_import_opentelemetry_when_disabled() -> None:
    env = os.environ.copy()
    env.pop("NETBOX_OTEL_ENABLED", None)
    env.pop("OTEL_SDK_DISABLED", None)
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import netbox_sdk; "
                "print(any(name.startswith('opentelemetry') for name in sys.modules))"
            ),
        ],
        cwd=repo_root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "False"


@pytest.mark.asyncio
async def test_authenticated_request_does_not_leak_token_to_span(
    monkeypatch, tmp_path, span_exporter
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("NETBOX_OTEL_ENABLED", raising=False)
    monkeypatch.delenv("OTEL_SDK_DISABLED", raising=False)
    monkeypatch.setattr(NetBoxApiClient, "_get_session", _fake_get_session, raising=True)

    secret = "super-secret-token-value"

    async def _fake_request_once(self: NetBoxApiClient, session: object, **kwargs: Any):
        assert kwargs["authorization"] == f"Token {secret}"
        return ApiResponse(status=200, text='{"ok": true}', headers={})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    client = NetBoxApiClient(
        Config(
            base_url="https://netbox.example.com",
            token_version="v1",
            token_secret=secret,
            otel_enabled=True,
        )
    )

    await client.request("POST", "/api/dcim/devices/", payload={"name": "sw01"})

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    serialized_span = _serialize_span_attributes_and_events(spans[0])
    assert secret not in serialized_span
    assert f"Token {secret}" not in serialized_span
    assert "Authorization" not in serialized_span


def test_otel_enabled_env_merges_into_default_config(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("NETBOX_OTEL_ENABLED", "true")

    assert load_config().otel_enabled is True


def _serialize_span_attributes_and_events(span: Any) -> str:
    parts: list[str] = []
    for key, value in span.attributes.items():
        parts.append(str(key))
        parts.append(str(value))
    for event in span.events:
        parts.append(str(event.name))
        for key, value in event.attributes.items():
            parts.append(str(key))
            parts.append(str(value))
    return "\n".join(parts)
