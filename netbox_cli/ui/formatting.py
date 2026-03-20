from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Mapping

from rich.text import Text

_FIELD_PRIORITY = [
    "id",
    "name",
    "display",
    "label",
    "status",
    "type",
    "role",
    "site",
    "location",
    "device",
    "interface",
    "ip",
    "address",
    "prefix",
    "vlan",
    "tenant",
    "description",
    "created",
    "last_updated",
    "url",
]

_UPPER_TOKENS = {
    "api": "API",
    "asn": "ASN",
    "bgp": "BGP",
    "dcim": "DCIM",
    "dns": "DNS",
    "fhrp": "FHRP",
    "gnmi": "gNMI",
    "id": "ID",
    "ike": "IKE",
    "ip": "IP",
    "ip4": "IPv4",
    "ip6": "IPv6",
    "ipam": "IPAM",
    "ipsec": "IPSec",
    "l2vpn": "L2VPN",
    "mac": "MAC",
    "ont": "ONT",
    "pon": "PON",
    "rir": "RIR",
    "snmp": "SNMP",
    "url": "URL",
    "uuid": "UUID",
    "vm": "VM",
    "vlan": "VLAN",
    "vpn": "VPN",
    "vrf": "VRF",
}


def humanize_identifier(value: str) -> str:
    tokens = value.replace("_", "-").split("-")
    parts: list[str] = []
    for token in tokens:
        cleaned = token.strip()
        if not cleaned:
            continue
        lower = cleaned.lower()
        if lower in _UPPER_TOKENS:
            parts.append(_UPPER_TOKENS[lower])
        elif cleaned.isdigit():
            parts.append(cleaned)
        else:
            parts.append(cleaned.capitalize())
    return " ".join(parts) if parts else value


def humanize_group(group: str) -> str:
    return humanize_identifier(group)


def humanize_resource(resource: str) -> str:
    return humanize_identifier(resource)


def humanize_field(field: str) -> str:
    return humanize_identifier(field)


def _format_datetime(value: str) -> str:
    candidate = value.strip()
    if not candidate or "T" not in candidate:
        return value
    normalized = candidate.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return value
    if parsed.tzinfo is None:
        return parsed.strftime("%Y-%m-%d %H:%M:%S")
    return parsed.strftime("%Y-%m-%d %H:%M:%S %Z").strip()


def _dict_display(value: dict[str, Any], max_items: int = 3) -> str:
    for key in ("display", "name", "label", "title", "slug"):
        if key in value and value[key] not in (None, ""):
            display = str(value[key])
            if "id" in value and value["id"] not in (None, "") and key != "id":
                return f"{display} (ID {value['id']})"
            return display

    items: list[str] = []
    for index, (key, item_value) in enumerate(value.items()):
        if index >= max_items:
            remaining = len(value) - max_items
            if remaining > 0:
                items.append(f"+{remaining} more")
            break
        items.append(
            f"{humanize_field(str(key))}: {humanize_value(item_value, max_len=48)}"
        )
    return "; ".join(items) if items else "—"


def humanize_value(value: Any, max_len: int = 180) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        text = _format_datetime(value)
    elif isinstance(value, dict):
        text = _dict_display(value)
    elif isinstance(value, list):
        if not value:
            text = "—"
        elif all(not isinstance(item, (dict, list)) for item in value):
            text = ", ".join(humanize_value(item, max_len=48) for item in value)
        else:
            preview = [humanize_value(item, max_len=48) for item in value[:3]]
            if len(value) > 3:
                preview.append(f"+{len(value) - 3} more")
            text = " | ".join(preview)
    else:
        text = str(value)

    if len(text) <= max_len:
        return text
    return f"{text[: max_len - 3]}..."


def compact_cell(value: Any, max_len: int = 180) -> str:
    return humanize_value(value, max_len=max_len)


_STATUS_STATES: dict[frozenset[str], tuple[str, str]] = {
    frozenset({"active", "up", "enabled", "online", "true"}): ("●", "success"),
    frozenset({"planned", "staged", "provisioning", "standby"}): ("◐", "info"),
    frozenset({"offline", "disabled", "down", "decommissioning"}): ("◌", "warning"),
    frozenset({"failed", "error", "deprecated"}): ("✖", "danger"),
}

_STATUS_STYLES: dict[frozenset[str], tuple[str, str]] = {}
_CHIP_STYLES: dict[str, str] = {}
_VALUE_STYLES: dict[str, str] = {}


def _on_style(fg: str, bg: str) -> str:
    return f"{fg} on {bg}"


def configure_semantic_styles(
    *, colors: Mapping[str, str], variables: Mapping[str, str]
) -> None:
    """Build Rich style strings from the currently active theme."""
    del (
        colors
    )  # Styles below are intentionally derived from semantic theme variables only.

    global _STATUS_STYLES, _CHIP_STYLES, _VALUE_STYLES

    status_styles = {
        "success": _on_style(variables["nb-success-text"], variables["nb-success-bg"]),
        "info": _on_style(variables["nb-info-text"], variables["nb-info-bg"]),
        "warning": _on_style(variables["nb-warning-text"], variables["nb-warning-bg"]),
        "danger": _on_style(variables["nb-danger-text"], variables["nb-danger-bg"]),
        "neutral": _on_style(
            variables["nb-secondary-text"], variables["nb-secondary-bg"]
        ),
    }

    _STATUS_STYLES = {
        states: (icon, status_styles[tone])
        for states, (icon, tone) in _STATUS_STATES.items()
    }

    _CHIP_STYLES = {
        "role": status_styles["warning"],
        "type": status_styles["info"],
        "tenant": status_styles["success"],
        "neutral": status_styles["neutral"],
    }

    _VALUE_STYLES = {
        "bool_true": variables["nb-success-text"],
        "bool_false": variables["nb-danger-text"],
        "id": f"bold {variables['nb-id-text']}",
        "muted": variables["nb-muted-text"],
        "url": f"{variables['nb-link-text']} underline",
        "key": variables["nb-key-text"],
    }


def _status_meta(value: str) -> tuple[str, str]:
    text = value.strip().lower()
    for states, style in _STATUS_STYLES.items():
        if text in states:
            return style
    return ("•", _CHIP_STYLES.get("neutral", ""))


def status_badge(value: str) -> Text:
    raw_label = value.strip() or "Unknown"
    label = raw_label.replace("_", " ").replace("-", " ").title()
    icon, style = _status_meta(raw_label)
    return Text(f" {icon} {label} ", style=style)


def label_chip(value: str, *, tone: str = "neutral") -> Text:
    label = value.strip()
    if not label:
        label = "—"
    label = label.replace("_", " ").replace("-", " ").title()
    style = _CHIP_STYLES.get(tone, _CHIP_STYLES.get("neutral", ""))
    return Text(f" {label} ", style=style)


def semantic_cell(field_name: str, value: Any, max_len: int = 180) -> Text:
    lower = field_name.lower()
    human = compact_cell(value, max_len=max_len)

    if lower in {"status"} or lower.endswith("_status"):
        return status_badge(human)

    if "role" in lower:
        return label_chip(human, tone="role")
    if "type" in lower:
        return label_chip(human, tone="type")
    if "tenant" in lower:
        return label_chip(human, tone="tenant")

    if value is None:
        return Text("—", style=_VALUE_STYLES.get("muted", ""))

    if isinstance(value, bool):
        style_key = "bool_true" if value else "bool_false"
        return Text("Yes" if value else "No", style=_VALUE_STYLES.get(style_key, ""))

    if lower in {"id", "pk"} or lower.endswith("_id"):
        return Text(human, style=_VALUE_STYLES.get("id", ""))

    if (
        "date" in lower
        or "time" in lower
        or lower in {"created", "last_updated", "updated"}
    ):
        return Text(human, style=_VALUE_STYLES.get("muted", ""))

    if lower == "url" or lower.endswith("_url"):
        return Text(human, style=_VALUE_STYLES.get("url", ""))

    if any(
        token in lower for token in ("serial", "asset_tag", "mac", "address", "prefix")
    ):
        return Text(human, style=_VALUE_STYLES.get("key", ""))

    return Text(human)


def order_field_names(names: list[str]) -> list[str]:
    priority_index = {name: idx for idx, name in enumerate(_FIELD_PRIORITY)}

    def sort_key(field: str) -> tuple[int, int, str]:
        lower = field.lower()
        for token, idx in priority_index.items():
            if lower == token:
                return (0, idx, lower)
        for token, idx in priority_index.items():
            if lower.endswith(f"_{token}") or lower.endswith(f"-{token}"):
                return (1, idx, lower)
        return (2, 0, lower)

    return sorted(names, key=sort_key)


def parse_response_rows(text: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return [{"result": text[:1200]}]

    if isinstance(payload, dict):
        results = payload.get("results")
        if isinstance(results, list):
            return [row for row in results if isinstance(row, dict)]
        return [payload]
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    return [{"value": str(payload)}]


def key_value_rows(obj: dict[str, Any]) -> list[tuple[str, Text]]:
    rows: list[tuple[str, Text]] = []
    ordered = order_field_names([str(key) for key in obj.keys()])
    for key in ordered:
        value = obj.get(key)
        rows.append(
            (humanize_field(str(key)), semantic_cell(str(key), value, max_len=500))
        )
    return rows
