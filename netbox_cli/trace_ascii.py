from __future__ import annotations

from typing import Any


def render_cable_trace_ascii(trace_payload: Any) -> str | None:
    if not isinstance(trace_payload, list) or not trace_payload:
        return None

    segments: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]] = []
    for raw_segment in trace_payload:
        if not (
            isinstance(raw_segment, list)
            and len(raw_segment) == 3
            and isinstance(raw_segment[0], list)
            and isinstance(raw_segment[2], list)
            and raw_segment[0]
            and raw_segment[2]
            and isinstance(raw_segment[0][0], dict)
            and isinstance(raw_segment[1], dict)
            and isinstance(raw_segment[2][0], dict)
        ):
            continue
        segments.append((raw_segment[0][0], raw_segment[1], raw_segment[2][0]))

    if not segments:
        return None

    def _endpoint_lines(endpoint: dict[str, Any], *, device_first: bool) -> list[str]:
        device = endpoint.get("device")
        device_label = (
            str(device.get("display") or device.get("name"))
            if isinstance(device, dict)
            else ""
        )
        port_label = str(endpoint.get("display") or endpoint.get("name") or "Endpoint")
        if device_first:
            return [line for line in [device_label, port_label] if line]
        return [line for line in [port_label, device_label] if line]

    def _box(lines: list[str], width: int = 38) -> list[str]:
        inner_width = width - 2
        rendered = ["┌" + "─" * inner_width + "┐"]
        for line in lines:
            centered = line.center(inner_width)[:inner_width].ljust(inner_width)
            rendered.append("│" + centered + "│")
        rendered.append("└" + "─" * inner_width + "┘")
        return rendered

    result: list[str] = []
    first_near, _, _ = segments[0]
    result.extend(_box(_endpoint_lines(first_near, device_first=True)))

    for index, (near, cable, far) in enumerate(segments):
        if index > 0:
            result.extend(_box(_endpoint_lines(near, device_first=False)))
        cable_label = str(cable.get("display") or cable.get("label") or "Cable")
        cable_status = str(cable.get("status") or "connected").title()
        center = " " * 16
        result.extend(
            [
                center + "│",
                center + f"│  {cable_label}",
                center + f"│  {cable_status}",
                center + "│",
            ]
        )
        result.extend(_box(_endpoint_lines(far, device_first=False)))

    result.append("")
    result.append(f"Trace Completed - {len(segments)} segment(s)")
    return "\n".join(result)
