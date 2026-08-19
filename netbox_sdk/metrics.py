"""Opt-in OpenTelemetry metrics for NetBox API requests.

Like :mod:`netbox_sdk.telemetry`, this module performs **no** OpenTelemetry
imports at module import time: the base SDK stays importable without the optional
``otel`` extra, and disabled metrics stay a cheap no-op on the request path.

It differs from tracing in one deliberate way. Tracing requires an explicit
``otel_enabled`` opt-in, because spans are per-request records a consumer should
choose to emit. Metrics activate on the **presence of an OTLP endpoint** alone
(``OTEL_EXPORTER_OTLP_METRICS_ENDPOINT`` or ``OTEL_EXPORTER_OTLP_ENDPOINT``), so
a deployment that already exports telemetry gets request counts and latencies
without per-service wiring — which is the point of the issue this implements.

Cardinality is the hazard a metrics API has and a tracing API does not: a span
may carry ``/api/dcim/devices/17/``, but a metric attribute must never, or one
time series is created per object id. Attributes are therefore the HTTP method,
a **templated** operation path, and the status code.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)

_METER_NAME = "netbox_sdk.client"
_REQUEST_COUNTER_NAME = "netbox.client.request.count"
_REQUEST_DURATION_NAME = "netbox.client.request.duration"
_PROXY_PROVIDER_CLASS_NAMES = {"NoOpMeterProvider", "_DefaultMeterProvider", "ProxyMeterProvider"}

_METRICS_ENDPOINT_ENV_VARS = (
    "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT",
    "OTEL_EXPORTER_OTLP_ENDPOINT",
)

# A path segment that identifies one object rather than a collection. Numeric ids
# cover NetBox's primary keys; the UUID form covers plugin routes that use them.
_NUMERIC_SEGMENT_RE = re.compile(r"^\d+$")
_UUID_SEGMENT_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


@dataclass(frozen=True)
class _MetricInstruments:
    counter: Any
    duration: Any


_INSTRUMENTS: _MetricInstruments | None = None
_IMPORT_FAILED = False
_SDK_PROVIDER: Any | None = None


def _coerce_disabled() -> bool:
    value = os.environ.get("OTEL_SDK_DISABLED", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def metrics_enabled() -> bool:
    """Whether an OTLP endpoint is configured for this process.

    Deliberately cheap: two environment reads and no import, because this runs on
    every request whether metrics are on or off.
    """
    if _coerce_disabled():
        return False
    exporter = os.environ.get("OTEL_METRICS_EXPORTER", "").strip().lower()
    if exporter in {"none", "false"}:
        return False
    return any(os.environ.get(name, "").strip() for name in _METRICS_ENDPOINT_ENV_VARS)


def operation_template(path: str) -> str:
    """Return a bounded-cardinality template for ``path``.

    ``/api/dcim/devices/17/`` becomes ``/api/dcim/devices/{id}/``. Without this,
    every object id would create its own time series — the classic way a metrics
    integration takes down the backend it reports to.
    """
    raw = urlsplit(str(path)).path or "/"
    segments = raw.split("/")
    templated = [
        "{id}"
        if segment and (_NUMERIC_SEGMENT_RE.match(segment) or _UUID_SEGMENT_RE.match(segment))
        else segment
        for segment in segments
    ]
    return "/".join(templated)


def record_client_request(
    *,
    method: str,
    path: str,
    status: int | None,
    duration_seconds: float,
    server_address: str = "",
) -> None:
    """Record one request against the counter and the duration histogram.

    Never raises. Telemetry that can break the call it observes is worse than no
    telemetry, so every failure degrades to a debug log.
    """
    if not metrics_enabled():
        return
    try:
        instruments = _get_instruments()
        if instruments is None:
            return
        attributes: dict[str, Any] = {
            "http.request.method": str(method).upper(),
            "url.template": operation_template(path),
        }
        if status is not None:
            attributes["http.response.status_code"] = int(status)
        if server_address:
            attributes["server.address"] = server_address
        instruments.counter.add(1, attributes)
        instruments.duration.record(max(float(duration_seconds), 0.0), attributes)
    except Exception:  # noqa: BLE001 - telemetry must never reach the caller
        logger.debug("failed to record NetBox request metrics", exc_info=True)


def _get_instruments() -> _MetricInstruments | None:
    """Build the instruments once per process, reusing a host's provider if present."""
    global _INSTRUMENTS

    if _INSTRUMENTS is not None:
        return _INSTRUMENTS

    modules = _load_modules()
    if modules is None:
        return None

    metrics_api = modules["metrics"]
    provider = metrics_api.get_meter_provider()
    if not _is_real_provider(provider):
        provider = _install_sdk_provider(modules)
        if provider is None:
            return None

    meter = provider.get_meter(_METER_NAME, _sdk_version())
    _INSTRUMENTS = _MetricInstruments(
        counter=meter.create_counter(
            _REQUEST_COUNTER_NAME,
            unit="{request}",
            description="NetBox API requests issued by this client.",
        ),
        duration=meter.create_histogram(
            _REQUEST_DURATION_NAME,
            unit="s",
            description="Duration of NetBox API requests issued by this client.",
        ),
    )
    return _INSTRUMENTS


def _is_real_provider(provider: object) -> bool:
    """True when a host application already configured a usable MeterProvider.

    Installing over one would silently redirect the host's own metrics, so the
    existing provider wins whenever there is one.
    """
    return provider.__class__.__name__ not in _PROXY_PROVIDER_CLASS_NAMES


def _install_sdk_provider(modules: dict[str, Any]) -> Any | None:
    global _SDK_PROVIDER

    if _SDK_PROVIDER is not None:
        return _SDK_PROVIDER
    try:
        reader = modules["periodic_reader"](modules["otlp_metric_exporter"]())
        provider = modules["meter_provider"](metric_readers=[reader], resource=_resource(modules))
        modules["metrics"].set_meter_provider(provider)
    except Exception:  # noqa: BLE001
        logger.debug("failed to initialize OpenTelemetry MeterProvider", exc_info=True)
        return None
    _SDK_PROVIDER = provider
    return provider


def _resource(modules: dict[str, Any]) -> Any:
    """Build the same resource identity tracing uses, so both agree on the service.

    Imported lazily from :mod:`netbox_sdk.telemetry` rather than duplicated: two
    copies of this would drift, and a metric attributed to a different
    ``service.name`` than its own spans is worse than no metric.
    """
    from netbox_sdk import telemetry  # noqa: PLC0415

    return modules["resource"].create(
        {
            "service.name": telemetry._service_name(),
            "service.version": telemetry._sdk_version(),
            "service.instance.id": telemetry._SERVICE_INSTANCE_ID,
        }
    )


def _sdk_version() -> str:
    from netbox_sdk import telemetry  # noqa: PLC0415

    return telemetry._sdk_version()


def _load_modules() -> dict[str, Any] | None:
    global _IMPORT_FAILED

    if _IMPORT_FAILED:
        return None
    try:
        from opentelemetry import metrics
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource
    except ImportError:
        _IMPORT_FAILED = True
        return None
    return {
        "metrics": metrics,
        "otlp_metric_exporter": OTLPMetricExporter,
        "meter_provider": MeterProvider,
        "periodic_reader": PeriodicExportingMetricReader,
        "resource": Resource,
    }


def _reset_for_tests() -> None:
    """Clear process-cached provider/instrument state. Test adapter only."""
    global _INSTRUMENTS, _IMPORT_FAILED, _SDK_PROVIDER
    _INSTRUMENTS = None
    _IMPORT_FAILED = False
    _SDK_PROVIDER = None
