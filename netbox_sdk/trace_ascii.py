"""ASCII renderers for cable and trace path output in terminal views."""

from __future__ import annotations

from typing import Any


def _box(lines: list[str], width: int = 38) -> list[str]:
    inner_width = width - 2
    rendered = ["┌" + "─" * inner_width + "┐"]
    for line in lines:
        centered = line.center(inner_width)[:inner_width].ljust(inner_width)
        rendered.append("│" + centered + "│")
    rendered.append("└" + "─" * inner_width + "┘")
    return rendered


def _cable_segment_lines(
    label: str, status: str = "Connected", *, dashed: bool = False
) -> list[str]:
    stem = "┆" if dashed else "│"
    center = " " * 16
    lines = [center + stem]
    if label:
        lines.append(center + f"{stem}  {label}")
    if status:
        lines.append(center + f"{stem}  {status}")
    lines.append(center + stem)
    return lines


def _simple_segment_lines(*, dashed: bool = False) -> list[str]:
    stem = "┆" if dashed else "│"
    center = " " * 16
    return [center + stem, center + stem, center + stem]


def _endpoint_lines(endpoint: dict[str, Any], *, device_first: bool) -> list[str]:
    device = endpoint.get("device")
    device_label = (
        str(device.get("display") or device.get("name")) if isinstance(device, dict) else ""
    )
    port_label = str(endpoint.get("display") or endpoint.get("name") or "Endpoint")
    if device_first:
        return [line for line in [device_label, port_label] if line]
    return [line for line in [port_label, device_label] if line]


def _trace_segments(
    trace_payload: Any,
) -> list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]:
    if not isinstance(trace_payload, list) or not trace_payload:
        return []

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
    return segments


def render_cable_trace_ascii(trace_payload: Any) -> str | None:
    segments = _trace_segments(trace_payload)
    if not segments:
        return None

    result: list[str] = []
    first_near, _, _ = segments[0]
    result.extend(_box(_endpoint_lines(first_near, device_first=True)))

    for index, (near, cable, far) in enumerate(segments):
        if index > 0:
            result.extend(_box(_endpoint_lines(near, device_first=False)))
        cable_label = str(cable.get("display") or cable.get("label") or "Cable")
        cable_status = str(cable.get("status") or "connected").title()
        result.extend(_cable_segment_lines(cable_label, cable_status))
        result.extend(_box(_endpoint_lines(far, device_first=False)))

    result.append("")
    result.append(f"Trace Completed - {len(segments)} segment(s)")
    return "\n".join(result)


def _path_node_lines(node: dict[str, Any]) -> list[str]:
    url = str(node.get("url") or "")
    display = str(node.get("display") or node.get("name") or "Endpoint")

    if "/api/dcim/interfaces/" in url:
        return _endpoint_lines(node, device_first=True)

    if "/api/circuits/circuit-terminations/" in url:
        circuit = node.get("circuit")
        if isinstance(circuit, dict):
            cid = str(circuit.get("display") or circuit.get("cid") or "Circuit")
            provider = circuit.get("provider")
            provider_label = (
                str(provider.get("display") or provider.get("name"))
                if isinstance(provider, dict)
                else ""
            )
            return [display, f"Circuit {cid}", provider_label or "Circuit"]
        return [display]

    if "/api/circuits/provider-networks/" in url:
        return [display]

    if "/api/dcim/sites/" in url:
        return [display]

    return [display]


def render_cable_paths_ascii(paths_payload: Any) -> str | None:
    if not isinstance(paths_payload, list) or not paths_payload:
        return None

    selected_path: list[Any] | None = None
    for entry in paths_payload:
        if isinstance(entry, dict) and isinstance(entry.get("path"), list) and entry["path"]:
            selected_path = entry["path"]
            break
    if not selected_path:
        return None

    result: list[str] = []
    segment_count = 0

    for index, step in enumerate(selected_path):
        if not isinstance(step, list) or not step or not isinstance(step[0], dict):
            continue
        node = step[0]
        url = str(node.get("url") or "")

        if "/api/dcim/cables/" in url:
            label = str(node.get("label") or node.get("display") or "Cable")
            if label and not label.lower().startswith("cable "):
                label = f"Cable {label}"
            result.extend(_cable_segment_lines(label, "Connected"))
            segment_count += 1
            continue

        if result:
            next_url = ""
            next_step = selected_path[index + 1] if index + 1 < len(selected_path) else None
            if isinstance(next_step, list) and next_step and isinstance(next_step[0], dict):
                next_url = str(next_step[0].get("url") or "")
            dashed = "/api/circuits/provider-networks/" in next_url
            result.extend(_simple_segment_lines(dashed=dashed))

        result.extend(_box(_path_node_lines(node)))

    if not result:
        return None

    result.append("")
    result.append(f"Trace Completed - {segment_count} segment(s)")
    return "\n".join(result)


def render_any_trace_ascii(payload: Any) -> str | None:
    rendered = render_cable_trace_ascii(payload)
    if rendered:
        return rendered
    return render_cable_paths_ascii(payload)
