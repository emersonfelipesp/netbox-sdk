#!/usr/bin/env python3
"""Block unconfirmed mutating ``nbx`` commands in PreToolUse hooks."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import PurePosixPath
from typing import Any

CONFIRMATION = "NETBOX_SDK_CONFIRM_WRITE=1"
WRITE_ACTIONS = frozenset(
    {
        "create",
        "update",
        "patch",
        "delete",
        "bulk-update",
        "bulk-patch",
        "bulk-delete",
    }
)
_SEPARATORS = frozenset({";", "&&", "||", "|", "&", "(", ")"})
_SHELLS = frozenset({"bash", "dash", "fish", "ksh", "sh", "zsh"})
_GLOBAL_OPTIONS_WITH_VALUES = frozenset({"--api-version", "--branch", "--netbox-version"})
_OPTIONS_WITH_VALUES = frozenset(
    {
        "--body-file",
        "--body-json",
        "--columns",
        "--header",
        "--id",
        "--max-columns",
        "--max-records",
        "--query",
        "--select",
        "-H",
        "-q",
    }
)


def _segments(command: str) -> list[list[str]]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
    lexer.commenters = ""
    lexer.whitespace_split = True
    tokens = list(lexer)
    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in _SEPARATORS or all(character in ";&|()" for character in token):
            if current:
                segments.append(current)
                current = []
            continue
        current.append(token)
    if current:
        segments.append(current)
    return segments


def _command_name(token: str) -> str:
    return PurePosixPath(token.replace("\\", "/")).name


def _positionals_after_nbx(tokens: list[str], nbx_index: int) -> list[str]:
    positionals: list[str] = []
    index = nbx_index + 1
    while index < len(tokens):
        token = tokens[index]
        if token in _GLOBAL_OPTIONS_WITH_VALUES or token in _OPTIONS_WITH_VALUES:
            index += 2
            continue
        if token.startswith("--") and "=" in token:
            index += 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        positionals.append(token)
        index += 1
    return positionals


def _segment_has_unconfirmed_write(tokens: list[str], *, inherited_confirmation: bool) -> bool:
    for index, token in enumerate(tokens):
        name = _command_name(token)
        if name == "nbx":
            positionals = _positionals_after_nbx(tokens, index)
            if any(action in WRITE_ACTIONS for action in positionals[2:4]):
                if not (inherited_confirmation or CONFIRMATION in tokens[:index]):
                    return True
        if name in _SHELLS and "-c" in tokens[index + 1 :]:
            option_index = tokens.index("-c", index + 1)
            if option_index + 1 < len(tokens) and command_has_unconfirmed_write(
                tokens[option_index + 1],
                inherited_confirmation=(inherited_confirmation or CONFIRMATION in tokens[:index]),
            ):
                return True
    return False


def command_has_unconfirmed_write(command: str, *, inherited_confirmation: bool = False) -> bool:
    """Return whether ``command`` contains an unconfirmed mutating nbx invocation."""
    try:
        return any(
            _segment_has_unconfirmed_write(segment, inherited_confirmation=inherited_confirmation)
            for segment in _segments(command)
        )
    except ValueError:
        # If shell quoting is malformed, fail closed only when the command
        # still plainly names both nbx and a write action. Unrelated malformed
        # Bash remains outside this hook's narrow scope.
        words = re.findall(r"[A-Za-z0-9_.\-/]+", command)
        return any(_command_name(word) == "nbx" for word in words) and any(
            word in WRITE_ACTIONS for word in words
        )


def _hook_command(payload: dict[str, Any]) -> str | None:
    if payload.get("tool_name") != "Bash":
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    command = tool_input.get("command")
    return command if isinstance(command, str) else None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0
    if not isinstance(payload, dict):
        return 0
    command = _hook_command(payload)
    environment_confirmed = os.environ.get("NETBOX_SDK_CONFIRM_WRITE") == "1"
    if command is None or not command_has_unconfirmed_write(
        command, inherited_confirmation=environment_confirmed
    ):
        return 0
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    "Mutating nbx commands require an explicit confirmation marker. "
                    f"Prefix the invocation with {CONFIRMATION} after reviewing a dry-run."
                ),
            }
        },
        sys.stdout,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
