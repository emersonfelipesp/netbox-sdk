"""Opt-in OpenTelemetry tracing for NetBox API requests.

This module intentionally performs no OpenTelemetry imports at module import
time. The base SDK must remain importable without the optional ``otel`` extra,
and disabled tracing must stay a cheap no-op.
"""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from types import TracebackType
from typing import Any, Literal
from urllib.parse import urlsplit

from netbox_sdk.config import OTEL_ENABLED_ENV_VAR

logger = logging.getLogger(__name__)

_DEFAULT_SERVICE_NAME = "netbox-sdk"
_SERVICE_INSTANCE_ID = str(uuid.uuid4())
_TRACER_NAME = "netbox_sdk.client"
_PROXY_PROVIDER_CLASS_NAMES = {"ProxyTracerProvider", "NoOpTracerProvider"}


@dataclass(frozen=True)
class _OtelModules:
    trace: Any
    span_kind: Any
    status: Any
    status_code: Any
    resource: Any
    tracer_provider: Any
    batch_span_processor: Any
    otlp_span_exporter: Any


_OTEL_MODULES: _OtelModules | None = None
_OTEL_IMPORT_FAILED = False
_SDK_PROVIDER: Any | None = None


def is_enabled(config: object) -> bool:
    """Return whether request tracing is explicitly enabled for this process."""
    if _coerce_optional_bool(os.environ.get("OTEL_SDK_DISABLED")) is True:
        return False

    config_enabled = _coerce_optional_bool(getattr(config, "otel_enabled", None))
    env_enabled = _coerce_optional_bool(os.environ.get(OTEL_ENABLED_ENV_VAR))
    return config_enabled is True or env_enabled is True


def server_address_from_url(base_url: str | None) -> str:
    """Return the host component used for the ``server.address`` span attribute."""
    if not base_url:
        return ""
    return urlsplit(base_url).hostname or ""


class _NoOpClientRequestSpan:
    def __enter__(self) -> _NoOpClientRequestSpan:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> Literal[False]:
        return False

    def set_response_status(self, status_code: int) -> None:
        return

    def set_cache_status(self, cache_status: str | None) -> None:
        return


_NOOP_CLIENT_REQUEST_SPAN = _NoOpClientRequestSpan()


def client_request_span(
    config: object,
    method: str,
    path: str,
    server_address: str,
) -> ClientRequestSpan | _NoOpClientRequestSpan:
    """Return a context manager for one NetBox HTTP CLIENT span."""
    if not is_enabled(config) or _OTEL_IMPORT_FAILED:
        return _NOOP_CLIENT_REQUEST_SPAN
    return ClientRequestSpan(
        config=config,
        method=method,
        path=path,
        server_address=server_address,
    )


class ClientRequestSpan:
    """Small no-op-safe wrapper around an OpenTelemetry span context manager."""

    def __init__(
        self,
        *,
        config: object,
        method: str,
        path: str,
        server_address: str,
    ) -> None:
        self._config = config
        self._method = method.upper()
        self._path = _span_url_path(path)
        self._server_address = server_address
        self._span_cm: Any | None = None
        self._span: Any | None = None
        self._modules: _OtelModules | None = None

    def __enter__(self) -> ClientRequestSpan:
        if not is_enabled(self._config):
            return self

        modules = _load_otel_modules()
        if modules is None:
            return self

        tracer = _get_tracer(modules)
        if tracer is None:
            return self

        attributes: dict[str, str] = {
            "http.request.method": self._method,
            "url.path": self._path,
        }
        if self._server_address:
            attributes["server.address"] = self._server_address

        try:
            self._modules = modules
            span_cm = tracer.start_as_current_span(
                f"HTTP {self._method}",
                kind=modules.span_kind.CLIENT,
                attributes=attributes,
            )
            self._span_cm = span_cm
            self._span = span_cm.__enter__()
        except Exception:
            logger.debug("failed to start OpenTelemetry request span", exc_info=True)
            self._span_cm = None
            self._span = None
            self._modules = None
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> Literal[False]:
        if self._span is not None and exc is not None:
            self._record_exception(exc)

        if self._span_cm is not None:
            try:
                self._span_cm.__exit__(exc_type, exc, tb)
            except Exception:
                logger.debug("failed to end OpenTelemetry request span", exc_info=True)
        return False

    def set_response_status(self, status_code: int) -> None:
        """Attach the final response status code to the span."""
        if self._span is None:
            return
        try:
            self._span.set_attribute("http.response.status_code", int(status_code))
            if status_code >= 400:
                self._set_error_status()
        except Exception:
            logger.debug("failed to set OpenTelemetry response status", exc_info=True)

    def set_cache_status(self, cache_status: str | None) -> None:
        """Attach SDK cache disposition when a synthetic cache header is present."""
        if self._span is None or not cache_status:
            return
        try:
            self._span.set_attribute("netbox.cache_status", cache_status)
        except Exception:
            logger.debug("failed to set OpenTelemetry cache status", exc_info=True)

    def _record_exception(self, exc: BaseException) -> None:
        if self._span is None:
            return
        try:
            self._span.record_exception(exc)
            self._set_error_status()
        except Exception:
            logger.debug("failed to record OpenTelemetry exception", exc_info=True)

    def _set_error_status(self) -> None:
        if self._span is None or self._modules is None:
            return
        try:
            self._span.set_status(self._modules.status(self._modules.status_code.ERROR))
        except Exception:
            logger.debug("failed to set OpenTelemetry error status", exc_info=True)


def _coerce_optional_bool(value: object) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if value == 1:
            return True
        if value == 0:
            return False
    raw = str(value).strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    return None


def _span_url_path(path: str) -> str:
    parsed = urlsplit(str(path))
    raw_path = parsed.path or "/"
    return raw_path if raw_path.startswith("/") else f"/{raw_path}"


def _load_otel_modules() -> _OtelModules | None:
    global _OTEL_IMPORT_FAILED, _OTEL_MODULES

    if _OTEL_IMPORT_FAILED:
        return None
    if _OTEL_MODULES is not None:
        return _OTEL_MODULES

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.trace import SpanKind, Status, StatusCode
    except ImportError:
        _OTEL_IMPORT_FAILED = True
        return None

    _OTEL_MODULES = _OtelModules(
        trace=trace,
        span_kind=SpanKind,
        status=Status,
        status_code=StatusCode,
        resource=Resource,
        tracer_provider=TracerProvider,
        batch_span_processor=BatchSpanProcessor,
        otlp_span_exporter=OTLPSpanExporter,
    )
    return _OTEL_MODULES


def _get_tracer(modules: _OtelModules) -> Any | None:
    provider = modules.trace.get_tracer_provider()
    if _is_real_provider(provider):
        return provider.get_tracer(_TRACER_NAME, _sdk_version())

    provider = _install_sdk_provider(modules)
    if provider is None:
        return None
    return provider.get_tracer(_TRACER_NAME, _sdk_version())


def _is_real_provider(provider: object) -> bool:
    return provider.__class__.__name__ not in _PROXY_PROVIDER_CLASS_NAMES


def _install_sdk_provider(modules: _OtelModules) -> Any | None:
    global _SDK_PROVIDER

    if _SDK_PROVIDER is not None:
        return _SDK_PROVIDER
    if not _should_install_otlp_exporter():
        return None

    try:
        provider = modules.tracer_provider(resource=_resource(modules))
        exporter = modules.otlp_span_exporter()
        provider.add_span_processor(modules.batch_span_processor(exporter))
        modules.trace.set_tracer_provider(provider)
    except Exception:
        logger.debug("failed to initialize OpenTelemetry provider", exc_info=True)
        return None

    _SDK_PROVIDER = provider
    return provider


def _should_install_otlp_exporter() -> bool:
    exporter_setting = os.environ.get("OTEL_TRACES_EXPORTER")
    if exporter_setting is not None and exporter_setting.strip():
        exporters = {item.strip().lower() for item in exporter_setting.split(",") if item.strip()}
        if "none" in exporters or "otlp" not in exporters:
            return False

    protocol = (
        os.environ.get("OTEL_EXPORTER_OTLP_TRACES_PROTOCOL")
        or os.environ.get("OTEL_EXPORTER_OTLP_PROTOCOL")
        or "http/protobuf"
    )
    return protocol.strip().lower() == "http/protobuf"


def _resource(modules: _OtelModules) -> Any:
    attributes = {
        "service.name": _service_name(),
        "service.version": _sdk_version(),
        "service.instance.id": _SERVICE_INSTANCE_ID,
    }
    return modules.resource.create(attributes)


def _service_name() -> str:
    explicit = os.environ.get("OTEL_SERVICE_NAME")
    if explicit:
        return explicit
    resource_service_name = _resource_attribute("service.name")
    return resource_service_name or _DEFAULT_SERVICE_NAME


def _resource_attribute(name: str) -> str | None:
    raw = os.environ.get("OTEL_RESOURCE_ATTRIBUTES")
    if not raw:
        return None
    for item in raw.split(","):
        key, sep, value = item.partition("=")
        if sep and key.strip() == name:
            stripped = value.strip()
            return stripped or None
    return None


def _sdk_version() -> str:
    try:
        return version("netbox-sdk")
    except PackageNotFoundError:
        try:
            from netbox_sdk import __version__
        except Exception:
            return "unknown"
        return __version__
