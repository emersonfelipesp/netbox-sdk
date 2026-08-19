"""Request metrics activate on an OTLP endpoint alone and never break a request.

Tracing requires an explicit ``otel_enabled`` opt-in, because spans are
per-request records a consumer chooses to emit. Metrics deliberately do not: a
deployment that already exports telemetry should get request counts and
latencies without per-service wiring, which is what this issue asked for.

The hazard a metrics API has and a tracing API does not is cardinality. A span
may carry ``/api/dcim/devices/17/``; a metric attribute must never, or one time
series is created per object id.
"""

from __future__ import annotations

from typing import Any

import pytest

from netbox_sdk import metrics

pytestmark = pytest.mark.suite_sdk

_ENDPOINT_VARS = ("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT", "OTEL_EXPORTER_OTLP_ENDPOINT")


@pytest.fixture(autouse=True)
def _isolate(monkeypatch: pytest.MonkeyPatch):
    """No ambient OTLP configuration may leak into or out of these tests."""
    for name in (*_ENDPOINT_VARS, "OTEL_SDK_DISABLED", "OTEL_METRICS_EXPORTER"):
        monkeypatch.delenv(name, raising=False)
    metrics._reset_for_tests()
    yield
    metrics._reset_for_tests()


def test_disabled_without_an_endpoint() -> None:
    assert metrics.metrics_enabled() is False


@pytest.mark.parametrize("variable", _ENDPOINT_VARS)
def test_either_endpoint_variable_activates_metrics(
    variable: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(variable, "http://localhost:4318")

    assert metrics.metrics_enabled() is True


@pytest.mark.parametrize(
    ("name", "value"),
    [
        pytest.param("OTEL_SDK_DISABLED", "true", id="sdk-disabled"),
        pytest.param("OTEL_METRICS_EXPORTER", "none", id="exporter-none"),
    ],
)
def test_explicit_opt_out_wins_over_a_configured_endpoint(
    name: str, value: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An operator turning telemetry off must beat an inherited endpoint variable."""
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    monkeypatch.setenv(name, value)

    assert metrics.metrics_enabled() is False


def test_blank_endpoint_does_not_activate(monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty variable is a common way to *unset* an inherited value."""
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "   ")

    assert metrics.metrics_enabled() is False


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        pytest.param("/api/dcim/devices/", "/api/dcim/devices/", id="collection-unchanged"),
        pytest.param("/api/dcim/devices/17/", "/api/dcim/devices/{id}/", id="numeric-id"),
        pytest.param(
            "/api/plugins/x/y/3f2504e0-4f89-11d3-9a0c-0305e82c3301/",
            "/api/plugins/x/y/{id}/",
            id="uuid-id",
        ),
        pytest.param(
            "/api/ipam/prefixes/9/available-ips/",
            "/api/ipam/prefixes/{id}/available-ips/",
            id="nested-action",
        ),
        pytest.param("/api/dcim/devices/?limit=5", "/api/dcim/devices/", id="query-dropped"),
    ],
)
def test_operation_template_bounds_cardinality(path: str, expected: str) -> None:
    assert metrics.operation_template(path) == expected


def test_distinct_object_ids_collapse_to_one_series() -> None:
    """The property that matters, stated directly rather than via examples."""
    templates = {metrics.operation_template(f"/api/dcim/devices/{i}/") for i in range(500)}

    assert templates == {"/api/dcim/devices/{id}/"}


def test_recording_is_a_no_op_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Disabled must cost nothing and must not touch OpenTelemetry at all."""

    def _explode() -> None:
        raise AssertionError("disabled metrics must not build instruments")

    monkeypatch.setattr(metrics, "_get_instruments", _explode)

    metrics.record_client_request(
        method="GET", path="/api/dcim/devices/", status=200, duration_seconds=0.01
    )


def test_records_against_counter_and_histogram(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    added: list[tuple[int, dict[str, Any]]] = []
    recorded: list[tuple[float, dict[str, Any]]] = []

    class _Counter:
        def add(self, amount: int, attributes: dict[str, Any]) -> None:
            added.append((amount, attributes))

    class _Histogram:
        def record(self, value: float, attributes: dict[str, Any]) -> None:
            recorded.append((value, attributes))

    monkeypatch.setattr(
        metrics,
        "_get_instruments",
        lambda: metrics._MetricInstruments(counter=_Counter(), duration=_Histogram()),
    )

    metrics.record_client_request(
        method="get",
        path="/api/dcim/devices/17/",
        status=200,
        duration_seconds=0.25,
        server_address="netbox.example.com",
    )

    assert added == [
        (
            1,
            {
                "http.request.method": "GET",
                "url.template": "/api/dcim/devices/{id}/",
                "http.response.status_code": 200,
                "server.address": "netbox.example.com",
            },
        )
    ]
    assert recorded[0][0] == pytest.approx(0.25)
    assert recorded[0][1]["url.template"] == "/api/dcim/devices/{id}/"


def test_a_failed_request_is_still_counted(monkeypatch: pytest.MonkeyPatch) -> None:
    """A metric that only sees successes hides the incident it exists to surface."""
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    added: list[dict[str, Any]] = []

    class _Counter:
        def add(self, _amount: int, attributes: dict[str, Any]) -> None:
            added.append(attributes)

    class _Histogram:
        def record(self, _value: float, _attributes: dict[str, Any]) -> None:
            return None

    monkeypatch.setattr(
        metrics,
        "_get_instruments",
        lambda: metrics._MetricInstruments(counter=_Counter(), duration=_Histogram()),
    )

    metrics.record_client_request(
        method="GET", path="/api/dcim/devices/", status=None, duration_seconds=0.5
    )

    assert added and "http.response.status_code" not in added[0]


def test_a_broken_instrument_never_reaches_the_caller(monkeypatch: pytest.MonkeyPatch) -> None:
    """Telemetry that can break the call it observes is worse than no telemetry."""
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")

    class _Exploding:
        def add(self, *_args: Any, **_kwargs: Any) -> None:
            raise RuntimeError("exporter is on fire")

        def record(self, *_args: Any, **_kwargs: Any) -> None:
            raise RuntimeError("exporter is on fire")

    monkeypatch.setattr(
        metrics,
        "_get_instruments",
        lambda: metrics._MetricInstruments(counter=_Exploding(), duration=_Exploding()),
    )

    metrics.record_client_request(
        method="GET", path="/api/dcim/devices/", status=200, duration_seconds=0.1
    )


def test_missing_optional_dependency_degrades_to_a_no_op(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The base SDK must stay usable without the ``otel`` extra installed."""
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    monkeypatch.setattr(metrics, "_load_modules", lambda: None)

    assert metrics._get_instruments() is None
    metrics.record_client_request(
        method="GET", path="/api/dcim/devices/", status=200, duration_seconds=0.1
    )


def test_instruments_are_built_once_per_process(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    builds = {"count": 0}

    class _Meter:
        def create_counter(self, *_a: Any, **_k: Any) -> Any:
            builds["count"] += 1
            return object()

        def create_histogram(self, *_a: Any, **_k: Any) -> Any:
            return object()

    class _Provider:
        def get_meter(self, *_a: Any, **_k: Any) -> Any:
            return _Meter()

    monkeypatch.setattr(
        metrics,
        "_load_modules",
        lambda: {"metrics": type("M", (), {"get_meter_provider": staticmethod(_Provider)})},
    )

    first = metrics._get_instruments()
    second = metrics._get_instruments()

    assert first is second
    assert builds["count"] == 1


def test_an_existing_host_provider_is_reused_not_replaced(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Installing over a host's MeterProvider would redirect its own metrics."""
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")

    class _HostProvider:
        def get_meter(self, *_a: Any, **_k: Any) -> Any:
            return type(
                "M",
                (),
                {
                    "create_counter": lambda *_a, **_k: object(),
                    "create_histogram": lambda *_a, **_k: object(),
                },
            )()

    def _never(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("an existing provider must not be replaced")

    monkeypatch.setattr(
        metrics,
        "_load_modules",
        lambda: {"metrics": type("M", (), {"get_meter_provider": staticmethod(_HostProvider)})},
    )
    monkeypatch.setattr(metrics, "_install_sdk_provider", _never)

    assert metrics._get_instruments() is not None


@pytest.mark.parametrize(
    "name", ["NoOpMeterProvider", "_DefaultMeterProvider", "ProxyMeterProvider"]
)
def test_placeholder_providers_are_not_mistaken_for_real_ones(name: str) -> None:
    placeholder = type(name, (), {})()

    assert metrics._is_real_provider(placeholder) is False


async def test_the_client_request_path_records_one_measurement(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """End-to-end: instrumenting the module is worthless if the client never calls it.

    Drives ``NetBoxApiClient.request`` with the transport stubbed and asserts the
    recorded attributes, so a future refactor that bypasses the wrapper is caught
    here rather than by nobody.
    """
    from netbox_sdk.client import ApiResponse, NetBoxApiClient
    from netbox_sdk.config import Config

    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(
        "netbox_sdk.client.record_client_request", lambda **kwargs: calls.append(kwargs)
    )

    client = NetBoxApiClient(Config(base_url="https://netbox.example.com", token="t"))

    async def _fake_impl(**_kwargs: Any) -> ApiResponse:
        return ApiResponse(status=201, text="{}", headers={})

    monkeypatch.setattr(client, "_request_impl", _fake_impl)

    await client.request("POST", "/api/dcim/devices/42/")

    assert len(calls) == 1, f"expected exactly one measurement, saw {len(calls)}"
    assert calls[0]["method"] == "POST"
    assert calls[0]["status"] == 201
    assert calls[0]["server_address"] == "netbox.example.com"
    assert calls[0]["duration_seconds"] >= 0


async def test_a_raising_request_is_still_measured(monkeypatch: pytest.MonkeyPatch) -> None:
    """The failure path is the one an operator most needs counted."""
    from netbox_sdk.client import NetBoxApiClient
    from netbox_sdk.config import Config

    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(
        "netbox_sdk.client.record_client_request", lambda **kwargs: calls.append(kwargs)
    )

    client = NetBoxApiClient(Config(base_url="https://netbox.example.com", token="t"))

    async def _boom(**_kwargs: Any) -> Any:
        raise ConnectionError("network down")

    monkeypatch.setattr(client, "_request_impl", _boom)

    with pytest.raises(ConnectionError):
        await client.request("GET", "/api/dcim/devices/")

    assert len(calls) == 1
    assert calls[0]["status"] is None, "a request that never answered has no status code"
