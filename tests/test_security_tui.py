"""Security tests for the netbox_tui package.

Covers: terminal escape injection through rendered API data, TUI state file
permissions, corrupt state handling, theme name injection, and GraphQL payload
structure.
"""

from __future__ import annotations

import os
import stat

import pytest

from netbox_sdk.formatting import humanize_value, semantic_cell
from netbox_sdk.output_safety import sanitize_terminal_text
from netbox_tui.state import TuiState, ViewState, load_tui_state, save_tui_state

pytestmark = pytest.mark.suite_tui


# ---------------------------------------------------------------------------
# Terminal escape injection through rendered API data
# ---------------------------------------------------------------------------

def test_ansi_color_code_stripped_from_humanized_api_response() -> None:
    """API response strings containing ANSI SGR sequences must be neutralized
    by humanize_value before data reaches TUI widgets."""
    result = humanize_value("normal\x1b[31mred\x1b[0mback")
    assert "\x1b" not in result
    assert "normalredback" in result


def test_osc_hyperlink_payload_stripped_from_humanized_value() -> None:
    """OSC 8 terminal hyperlink sequences from untrusted API payloads must be
    stripped by humanize_value before any TUI rendering."""
    evil_link = "\x1b]8;;https://evil.example.com\x1b\\click here\x1b]8;;\x1b\\"
    result = humanize_value(f"safe{evil_link}safe")
    assert "\x1b" not in result
    assert "evil.example.com" not in result
    assert "clickhere" in result or "safe" in result


def test_c1_csi_in_semantic_cell_is_replaced() -> None:
    """C1 CSI byte (U+009B) in API data rendered via semantic_cell must be
    replaced with the Unicode replacement character, not passed to the terminal."""
    cell = semantic_cell("status", "active\x9binjected")
    assert "\x9b" not in cell.plain


def test_c1_osc_in_semantic_cell_is_replaced() -> None:
    """C1 OSC byte (U+009D) in rendered data must be replaced."""
    cell = semantic_cell("name", "device\x9devil")
    assert "\x9d" not in cell.plain


def test_null_byte_in_rendered_value_replaced() -> None:
    """Null bytes from API responses must be replaced with the replacement
    character, not silently dropped or passed to terminal output."""
    result = sanitize_terminal_text("name\x00value")
    assert "\x00" not in result
    assert "\ufffd" in result


def test_bell_character_in_rendered_value_replaced() -> None:
    """BEL (0x07) from an API response must be neutralized so it cannot
    trigger terminal bell sounds."""
    result = sanitize_terminal_text("alert\x07boom")
    assert "\x07" not in result


def test_escape_sequence_in_nested_display_field() -> None:
    """A dict with a display field containing escape sequences must be
    sanitized when humanize_value renders it as a label."""
    nested = {"id": 1, "display": "\x1b[1mBoldDevice\x1b[0m", "name": "dev1"}
    result = humanize_value(nested)
    assert "\x1b" not in result


def test_c1_csi_sequence_through_sanitize_terminal_text() -> None:
    """C1 CSI (\\x9b) + parameters is the C1 equivalent of \\x1b[31m.
    After sanitisation no \\x9b must remain in output."""
    result = sanitize_terminal_text("\x9b31mcolored\x9b0m")
    assert "\x9b" not in result
    assert "colored" in result


def test_mixed_ansi_and_c1_payload_fully_sanitized() -> None:
    """A payload combining ESC-based and C1-based sequences must have all
    control characters neutralized."""
    payload = "\x1b[31mred\x9b32mgreen\x1b]8;;evil\x1b\\link\x1b]8;;\x1b\\"
    result = sanitize_terminal_text(payload)
    assert "\x1b" not in result
    assert "\x9b" not in result


# ---------------------------------------------------------------------------
# TUI state file permissions
# ---------------------------------------------------------------------------

def test_save_tui_state_creates_file_with_private_permissions(tmp_path, monkeypatch) -> None:
    """save_tui_state must create state files with 0o600 permissions so other
    local users cannot read the stored view state and theme preference."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    state = TuiState(last_view=ViewState(group="dcim", resource="devices"), theme_name="dark")

    save_tui_state(state)

    from netbox_tui.state import tui_state_path
    path = tui_state_path()
    if os.name != "nt":
        assert stat.S_IMODE(path.stat().st_mode) == 0o600, (
            f"Expected 0o600 permissions on {path}, got "
            f"{oct(stat.S_IMODE(path.stat().st_mode))}"
        )


def test_save_tui_state_with_base_url_creates_file_with_private_permissions(
    tmp_path, monkeypatch
) -> None:
    """Per-instance state files (scoped by base URL) must also use 0o600."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    state = TuiState(theme_name="light")

    save_tui_state(state, base_url="https://netbox.example.com")

    from netbox_tui.state import tui_state_path
    path = tui_state_path(base_url="https://netbox.example.com")
    if os.name != "nt":
        assert stat.S_IMODE(path.stat().st_mode) == 0o600, (
            f"Expected 0o600 permissions on {path}, got "
            f"{oct(stat.S_IMODE(path.stat().st_mode))}"
        )


# ---------------------------------------------------------------------------
# Corrupt/malicious state file handling
# ---------------------------------------------------------------------------

def test_load_tui_state_handles_corrupt_json_gracefully(tmp_path, monkeypatch) -> None:
    """Corrupt JSON in the TUI state file must not crash the TUI;
    a default TuiState() must be returned instead."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    from netbox_tui.state import tui_state_path
    path = tui_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{this is not valid json!!!", encoding="utf-8")

    state = load_tui_state()
    assert isinstance(state, TuiState)
    assert state.last_view.group is None
    assert state.theme_name is None


def test_load_tui_state_handles_wrong_type_in_json(tmp_path, monkeypatch) -> None:
    """A state file containing a JSON array (unexpected type) must not crash;
    a default TuiState() is returned."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    from netbox_tui.state import tui_state_path
    path = tui_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("[1, 2, 3]", encoding="utf-8")

    state = load_tui_state()
    assert isinstance(state, TuiState)


def test_load_tui_state_handles_malicious_extra_fields(tmp_path, monkeypatch) -> None:
    """Unknown fields in the state JSON must be silently ignored by Pydantic."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    from netbox_tui.state import tui_state_path
    path = tui_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '{"last_view": {}, "theme_name": "dark", "__proto__": {"admin": true}}',
        encoding="utf-8",
    )

    state = load_tui_state()
    assert isinstance(state, TuiState)
    assert state.theme_name == "dark"


# ---------------------------------------------------------------------------
# Theme name injection via state persistence
# ---------------------------------------------------------------------------

def test_tui_state_theme_name_with_path_traversal_round_trips_as_literal(
    tmp_path, monkeypatch
) -> None:
    """A theme_name like '../../etc/passwd' must be stored and loaded as a
    literal string; the TUI's theme loader (which separately validates theme
    names against registered themes) is what prevents it from being used."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    evil_theme = "../../etc/passwd"
    state = TuiState(theme_name=evil_theme)
    save_tui_state(state)

    loaded = load_tui_state()
    assert loaded.theme_name == evil_theme  # stored/loaded verbatim


def test_tui_state_theme_name_with_escape_sequences_round_trips(
    tmp_path, monkeypatch
) -> None:
    """A theme_name with ANSI escape sequences is stored as JSON-escaped text.
    The round-trip must preserve the exact string."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    evil_theme = "dark\x1b[31mred\x1b[0m"
    state = TuiState(theme_name=evil_theme)
    save_tui_state(state)

    loaded = load_tui_state()
    assert loaded.theme_name == evil_theme


# ---------------------------------------------------------------------------
# GraphQL query payload structure
# ---------------------------------------------------------------------------

def test_graphql_query_is_sent_as_json_dict_field() -> None:
    """NetBoxApiClient.graphql() must construct a dict payload with a 'query'
    key, not string-interpolate the query into a raw string. This ensures
    GraphQL queries with special characters are JSON-encoded, not injected."""
    import inspect
    from netbox_sdk.client import NetBoxApiClient

    source = inspect.getsource(NetBoxApiClient.graphql)
    # The method must build a payload dict and call self.request with payload=
    assert "payload" in source
    assert '"query"' in source or "'query'" in source
    assert "self.request" in source


def test_graphql_query_variables_are_in_separate_field() -> None:
    """GraphQL variables must travel in a separate 'variables' field of the
    payload dict, not be interpolated into the query string."""
    import inspect
    from netbox_sdk.client import NetBoxApiClient

    source = inspect.getsource(NetBoxApiClient.graphql)
    assert '"variables"' in source or "'variables'" in source
