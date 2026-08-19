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
CONFIRM_FLAG = "--confirm"
DRY_RUN_FLAG = "--dry-run"
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
# HTTP methods that mutate state when issued through the raw ``nbx call
# <METHOD> <path>`` escape hatch, which bypasses the named-action grammar
# WRITE_ACTIONS covers. `nbx call` uppercases the method before dispatch, but
# accepts any case, so this is matched case-insensitively too.
WRITE_HTTP_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
# `nbx branching ...` / `nbx branch ...` (alias) puts its verb immediately
# after the group name rather than at the end of the invocation.
_BRANCHING_ROOTS = frozenset({"branching", "branch"})
_BRANCHING_WRITE_VERBS = frozenset(
    {"create", "update", "delete", "sync", "merge", "revert", "archive"}
)
# `nbx dev http <verb> --path ...` issues a raw HTTP request against the
# configured NetBox instance; "post"/"put" are mutating but are not action
# names in WRITE_ACTIONS.
_DEV_HTTP_WRITE_VERBS = frozenset({"post", "put", "patch", "delete"})
# Combined word set for the fail-closed fallback path below, where malformed
# shell quoting means positional structure can't be trusted.
_ALL_WRITE_WORDS = WRITE_ACTIONS | _BRANCHING_WRITE_VERBS | _DEV_HTTP_WRITE_VERBS
# A positional built from a shell variable or command substitution (e.g.
# ``$method``, ``${action}``, `` `verb` ``), a pathname-expansion glob (e.g.
# ``del?te``, ``de*e``, ``de[l]ete``), or a brace expansion (e.g.
# ``del{e,e}te``) can resolve to any write verb at runtime even though the
# literal token itself never matches WRITE_ACTIONS/WRITE_HTTP_METHODS/etc. —
# shlex only tokenizes here, it never performs the shell's own variable/
# command substitution, filename-globbing, or brace-expansion passes, so the
# hook cannot know what the token will actually expand to. Any positional
# that could name a write verb is therefore treated as an unprovable, and
# thus mutating, invocation. The same reasoning applies when the *executable
# name itself* is a shell variable/command substitution or glob/brace
# expression (e.g. ``tool=nbx; $tool dcim devices delete --id 7`` or ``nb?
# dcim devices delete --id 7``, which the shell resolves to the installed
# ``nbx`` binary before exec): ``_command_name()`` can only compare the
# literal pre-expansion token against ``"nbx"``, so such a token would
# otherwise never be recognised as an nbx invocation at all and every check
# below would be silently skipped. See ``_command_token_index`` and its use
# in ``_segment_has_unconfirmed_write``.
#
# This pattern is only safe to apply where the inspected positional is a
# short bare verb/action word (a "could this glob-resolve into a write
# verb?" question). It must never be applied to a free-form payload
# positional (a GraphQL query document, a JSON blob, a path search term)
# that legitimately contains ``{``, ``}``, ``*``, ``?``, ``[``, or ``]`` as
# ordinary content rather than an unresolved shell token — see the
# ``root == "graphql"`` handling in ``_positionals_indicate_write``, which
# uses the narrower ``_SHELL_SUBSTITUTION_PATTERN`` instead.
_SHELL_EXPANSION_PATTERN = re.compile(r"[$`*?\[\]{}]")
# ``$``/backtick alone: command/variable substitution the shell performs
# even inside a double-quoted argument (unlike pathname/brace expansion,
# which only fires on unquoted words). Used for positionals expected to
# hold arbitrary payload text, where a full glob scan would false-positive
# on ordinary content.
_SHELL_SUBSTITUTION_PATTERN = re.compile(r"[$`]")
_SEPARATORS = frozenset({";", "&&", "||", "|", "&", "(", ")"})
_SHELLS = frozenset({"bash", "dash", "fish", "ksh", "sh", "zsh"})
# Matches a leading inline environment assignment (``VAR=value cmd ...``) so
# the real command-name token can be found past any such prefix.
_ENV_ASSIGNMENT_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
# `xargs` in default (non-replace-string) mode appends as many stdin-derived
# arguments as fit to the END of the command line it runs at execution time —
# so any positional visible after `nbx` in the static text can never be
# proven complete: more tokens, potentially including the write verb itself,
# can always be silently appended beyond what appears here. Replace-string
# mode (`-I repl` / `-i[repl]` / `--replace[=repl]`) does not fix this
# either: the placeholder itself can occupy the verb/action position (e.g.
# `printf delete | xargs -I {} nbx dcim devices {} --id 7`), and the value
# substituted into it at runtime is never visible in the static text. Both
# modes are therefore treated identically below: fail closed on any `xargs`
# invocation of `nbx` that is not explicitly confirmed.
# xargs options that consume the following token as a value, used to walk
# past xargs' own flags to find the command token it will actually invoke.
_XARGS_OPTIONS_WITH_VALUES = frozenset(
    {
        "-a",
        "-d",
        "-E",
        "-I",
        "-L",
        "-n",
        "-P",
        "-s",
        "--arg-file",
        "--delimiter",
        "--eof",
        "--max-args",
        "--max-chars",
        "--max-lines",
        "--max-procs",
    }
)
# `sudo`/`doas` re-invoke another command with elevated privileges; they do
# not themselves read stdin as commands, but when they wrap a stdin-reading
# shell (e.g. `printf '%s' 'nbx dcim devices delete --id 7' | sudo bash`),
# that shell is what actually executes the piped-in text. The pipe-consumer
# check below inspects only the segment's literal command-name token, so
# without unwrapping this prefix first, `sudo`/`doas` would hide the shell
# from detection the same way `-c` hides an inline string.
_PRIVILEGE_WRAPPERS = frozenset({"sudo", "doas"})
_SUDO_OPTIONS_WITH_VALUES = frozenset({"-U", "-u", "-g", "-p", "-h", "-C", "-D", "-R", "-T"})
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
        "--variables",
        "-H",
        "-q",
        "-v",
    }
)


def _segments(command: str) -> list[tuple[str | None, list[str]]]:
    """Split ``command`` into shell segments, paired with the separator before each.

    The separator (``None`` for the first segment) lets callers distinguish a
    pipe (``|``) from ``;``/``&&``/``||``/``&`` — only a pipe feeds one
    segment's stdout into the next segment's stdin, which matters for
    detecting a shell that consumes piped-in text as commands (see
    ``_shell_reads_stdin``).
    """
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
    lexer.commenters = ""
    lexer.whitespace_split = True
    tokens = list(lexer)
    segments: list[tuple[str | None, list[str]]] = []
    current: list[str] = []
    preceding_separator: str | None = None
    for token in tokens:
        if token in _SEPARATORS or all(character in ";&|()" for character in token):
            if current:
                segments.append((preceding_separator, current))
                current = []
            preceding_separator = token
            continue
        current.append(token)
    if current:
        segments.append((preceding_separator, current))
    return segments


def _command_name(token: str) -> str:
    return PurePosixPath(token.replace("\\", "/")).name


def _command_token_index(tokens: list[str]) -> int | None:
    """Return the index of the token occupying a segment's command-name position.

    A shell command may be preceded by inline environment assignments
    (``VAR=value cmd ...``); those tokens are not the invoked command.
    Returns ``None`` if every token in the segment looks like an assignment
    (or the segment is empty).
    """
    for index, token in enumerate(tokens):
        if not _ENV_ASSIGNMENT_PATTERN.match(token):
            return index
    return None


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


def _xargs_command_index(tokens: list[str], xargs_index: int) -> int | None:
    """Return the index of the command token ``xargs`` will invoke.

    Skips ``xargs``'s own option tokens (and the values of options that take
    one) to find the first positional, which is the command xargs runs for
    each input batch/line. Returns ``None`` when the end of the segment is
    reached without finding one.
    """
    index = xargs_index + 1
    while index < len(tokens):
        token = tokens[index]
        if token == "--":
            return index + 1 if index + 1 < len(tokens) else None
        if token in _XARGS_OPTIONS_WITH_VALUES:
            index += 2
            continue
        if token.startswith("--") and "=" in token:
            index += 1
            continue
        if token.startswith("-") and token != "-":
            index += 1
            continue
        return index
    return None


def _shell_reads_stdin(tokens: list[str], shell_index: int) -> bool:
    """Return whether the shell at ``shell_index`` will execute its stdin as commands.

    A shell reads commands from stdin whenever it is given no ``-c`` (an
    inline command string) and has no script-file positional following it —
    this covers a bare invocation, an explicit ``-s``, a heredoc (``<<EOF``),
    and a here-string (``<<<``) alike. It is the behavior that lets ``printf
    '%s' 'nbx dcim devices delete --id 7' | bash`` and ``bash -s <<< 'nbx
    dcim devices delete --id 7'`` execute an nbx write that never appears as
    a token positioned after a literal ``nbx`` on this shell's own command
    line, since shlex dequotes the payload into one multi-word token instead.
    """
    index = shell_index + 1
    while index < len(tokens):
        token = tokens[index]
        if token == "-c":
            return False
        if token == "<<<" or token.startswith("<<"):
            return True
        if token.startswith("-"):
            index += 1
            continue
        return False
    return True


def _unwrap_privilege_command_index(tokens: list[str], index: int | None) -> int | None:
    """Walk past any leading ``sudo``/``doas`` wrapper(s) to the wrapped command's index.

    Returns ``index`` unchanged when it does not point at a known privilege
    wrapper (including when it is ``None``).
    """
    while (
        index is not None
        and index < len(tokens)
        and _command_name(tokens[index]) in _PRIVILEGE_WRAPPERS
    ):
        index += 1
        while index < len(tokens) and tokens[index].startswith("-") and tokens[index] != "--":
            index += 2 if tokens[index] in _SUDO_OPTIONS_WITH_VALUES else 1
        if index < len(tokens) and tokens[index] == "--":
            index += 1
    return index if index is not None and index < len(tokens) else None


def _here_string_index(tokens: list[str], shell_index: int) -> int | None:
    """Return the index of a ``<<<`` here-string operator after ``shell_index``, if any."""
    for index in range(shell_index + 1, len(tokens)):
        if tokens[index] == "<<<":
            return index
    return None


def _positionals_indicate_write(positionals: list[str]) -> bool:
    """Return whether an ``nbx`` invocation's positionals name a mutating command.

    Each nbx command tree places its verb at a different fixed position, so
    each tree is modeled explicitly rather than relying on one slice shared
    across all of them:

    - ``nbx call <METHOD> <path>`` — the raw escape hatch; method is 2nd.
    - ``nbx branching|branch <verb> ...`` — verb is 2nd (before any
      ``<id_or_schema>`` positional), including verbs (sync/merge/revert/
      archive) that aren't in WRITE_ACTIONS at all.
    - ``nbx proxbox sync [ENDPOINT] ...`` and ``nbx proxbox tui`` — top-level
      write-capable commands, verb is 2nd.
    - ``nbx dev http <verb> --path ...`` and ``nbx demo dev http <verb>
      --path ...`` — both mount the same raw-HTTP ``dev_http_app`` Typer
      tree (``netbox_cli/demo.py`` nests it under ``demo dev``), so this
      looks for a ``"dev", "http", <verb>`` triple anywhere in the
      positionals rather than pinning it to a fixed offset — a future
      command tree that nests it one level deeper again must not silently
      fall through. "post"/"put" mutate but aren't in WRITE_ACTIONS.
    - Dynamic OpenAPI commands (``nbx <group> <resource...> <action>``) and
      the Proxbox catalog (``nbx proxbox <resource-path...> <action>``,
      variable nesting depth) place the action at a depth-dependent index
      with nothing but options after it, so any positional naming a write
      action is treated as one — an unrecognised option whose value happens
      to leak into the positional list (as with an untracked ``--flag``)
      must never hide a real trailing action, so this checks membership
      rather than a fixed or trailing position.
    - ``nbx graphql <query>`` is not a resource/action tree at all — its
      sole positional is a free-form GraphQL query document that routinely
      contains ``{``, ``}``, ``[``, and ``]`` as ordinary syntax (and
      ``*``/``?`` inside string literals or comments). Scanning it with the
      full glob pattern used for verb positions would deny virtually every
      real query, so this only fails closed on ``$``/backtick — the one
      construct the shell still expands inside a quoted argument.

    Every branch above that checks a verb/action position also fails closed
    the moment that positional contains a ``$``/backtick shell-expansion
    marker, or an unquoted filename-glob (``*``, ``?``, ``[...]``) or
    brace-expansion (``{...}``) metacharacter: a command like
    ``method=POST; nbx call $method /api/...`` or ``action=delete; nbx dcim
    devices $action --id 7`` tokenizes to a literal ``$method``/``$action``
    that never equals a known write verb, and ``nbx dcim devices del?te
    --id 7`` tokenizes to a literal ``del?te`` that never equals a known
    write verb either — but the shell resolves either to ``delete`` at
    execution time, the former via variable substitution and the latter via
    pathname expansion against a file named ``delete`` in the working
    directory. Since this hook only ever sees the pre-expansion text, it
    cannot statically prove such a token is read-only, so it is treated as
    a write.
    """
    if not positionals:
        return False
    root = positionals[0]
    if root == "call":
        if len(positionals) < 2:
            return False
        return (
            _SHELL_EXPANSION_PATTERN.search(positionals[1]) is not None
            or positionals[1].strip().upper() in WRITE_HTTP_METHODS
        )
    if root in _BRANCHING_ROOTS:
        if len(positionals) < 2:
            return False
        return (
            _SHELL_EXPANSION_PATTERN.search(positionals[1]) is not None
            or positionals[1] in _BRANCHING_WRITE_VERBS
        )
    if root == "proxbox" and len(positionals) >= 2:
        if _SHELL_EXPANSION_PATTERN.search(positionals[1]) is not None or positionals[1] in {
            "sync",
            "tui",
        }:
            return True
    if root == "graphql":
        return any(_SHELL_SUBSTITUTION_PATTERN.search(word) is not None for word in positionals[1:])
    for index in range(len(positionals) - 2):
        if positionals[index] == "dev" and positionals[index + 1] == "http":
            verb = positionals[index + 2]
            return (
                _SHELL_EXPANSION_PATTERN.search(verb) is not None or verb in _DEV_HTTP_WRITE_VERBS
            )
    return any(
        word in WRITE_ACTIONS
        or word.upper() in WRITE_HTTP_METHODS
        or _SHELL_EXPANSION_PATTERN.search(word) is not None
        for word in positionals
    )


def _positionals_support_dry_run(positionals: list[str]) -> bool:
    """Return whether literal positionals identify a no-network dry-run grammar.

    Only the guarded raw ``call`` write surface and generated dynamic
    OpenAPI/Proxbox-catalog write actions support ``--dry-run``. Branching,
    Proxbox ``sync``/``tui``, dev raw HTTP, and GraphQL do not. Any unresolved
    shell expansion fails closed because the hook cannot prove which grammar
    the shell will ultimately execute.
    """
    if not positionals or any(
        _SHELL_EXPANSION_PATTERN.search(word) is not None for word in positionals
    ):
        return False

    root = positionals[0]
    if root == "call":
        return len(positionals) >= 2 and positionals[1].strip().upper() in WRITE_HTTP_METHODS
    if root in _BRANCHING_ROOTS or root == "graphql":
        return False
    if root == "proxbox" and len(positionals) >= 2 and positionals[1] in {"sync", "tui"}:
        return False
    for index in range(len(positionals) - 2):
        if positionals[index] == "dev" and positionals[index + 1] == "http":
            return False
    return any(word in WRITE_ACTIONS or word.upper() in WRITE_HTTP_METHODS for word in positionals)


def _segment_has_unconfirmed_write(tokens: list[str], *, inherited_confirmation: bool) -> bool:
    command_index = _command_token_index(tokens)
    for index, token in enumerate(tokens):
        name = _command_name(token)
        if name == "nbx":
            positionals = _positionals_after_nbx(tokens, index)
            if _positionals_indicate_write(positionals):
                if not (
                    inherited_confirmation
                    or CONFIRMATION in tokens[:index]
                    or CONFIRM_FLAG in tokens[index + 1 :]
                    or (
                        DRY_RUN_FLAG in tokens[index + 1 :]
                        and _positionals_support_dry_run(positionals)
                    )
                ):
                    return True
        elif index == command_index and _SHELL_EXPANSION_PATTERN.search(token) is not None:
            # The command name itself is a shell variable/command
            # substitution (e.g. `tool=nbx; $tool dcim devices delete --id
            # 7`, or `` `resolve_cmd` dcim devices delete --id 7 ``), or a
            # pathname-expansion glob such as `nb?` that the shell resolves
            # against the installed `nbx` binary before exec. This
            # token can never be proven to be, or not be, `nbx` — treat the
            # tokens that follow it exactly like `nbx`'s own positionals and
            # fail closed if they look like a write, instead of silently
            # skipping the whole segment because its literal basename isn't
            # the string "nbx". When nothing follows it at all (e.g.
            # `cmd='nbx dcim devices delete --id 7'; sh -c "$cmd"`, where the
            # entire mutating command is collapsed into this one bare
            # token), there are no positionals to inspect either way, so
            # `_positionals_indicate_write` would otherwise return `False`
            # by its own empty-list short-circuit — fail closed
            # unconditionally instead, since an unprovable token hiding the
            # whole command is strictly less safe than one hiding only part
            # of it.
            positionals = _positionals_after_nbx(tokens, index)
            if not positionals or _positionals_indicate_write(positionals):
                if not (
                    inherited_confirmation
                    or CONFIRMATION in tokens[:index]
                    or CONFIRM_FLAG in tokens[index + 1 :]
                ):
                    return True
        if name == "xargs":
            # Applies in every xargs mode, including replace-string mode
            # (`-I`/`-i`/`--replace`): a placeholder token can occupy the
            # verb/action position itself (e.g. `printf delete | xargs -I {}
            # nbx dcim devices {} --id 7`), so the static positionals never
            # literally contain the write verb even though replace mode
            # substitutes a value there at runtime. The per-token
            # `_positionals_indicate_write` scan above (which fires on the
            # `name == "nbx"` branch for this same "nbx dcim devices {} --id
            # 7" text) cannot see that substituted value either, so it is
            # not a substitute for this check in any xargs mode.
            xargs_command_index = _xargs_command_index(tokens, index)
            if xargs_command_index is not None:
                xargs_command_token = tokens[xargs_command_index]
                invoked_name = _command_name(xargs_command_token)
                if invoked_name == "nbx" or _SHELL_EXPANSION_PATTERN.search(xargs_command_token):
                    if not (
                        inherited_confirmation
                        or CONFIRMATION in tokens[:index]
                        or CONFIRM_FLAG in tokens[xargs_command_index + 1 :]
                    ):
                        return True
        if name in _SHELLS:
            if "-c" in tokens[index + 1 :]:
                option_index = tokens.index("-c", index + 1)
                if option_index + 1 < len(tokens) and command_has_unconfirmed_write(
                    tokens[option_index + 1],
                    inherited_confirmation=(
                        inherited_confirmation or CONFIRMATION in tokens[:index]
                    ),
                ):
                    return True
            elif _shell_reads_stdin(tokens, index):
                # No `-c`: this shell executes whatever reaches its stdin as
                # a command batch. A here-string (`<<<`) carries that content
                # as a literal token right here; a pipe carries it in the
                # preceding segment (see the cross-segment check in
                # `command_has_unconfirmed_write`); a plain unquoted heredoc
                # body is already covered by the `name == "nbx"` branch above
                # since its words tokenize like an ordinary command line.
                here_string_index = _here_string_index(tokens, index)
                if here_string_index is not None and here_string_index + 1 < len(tokens):
                    if command_has_unconfirmed_write(
                        tokens[here_string_index + 1],
                        inherited_confirmation=(
                            inherited_confirmation or CONFIRMATION in tokens[:index]
                        ),
                    ):
                        return True
        if name == "eval":
            # The shell builtin `eval` joins its remaining arguments with a
            # space and re-parses the result as a command, e.g. `eval 'nbx
            # dcim devices delete --id 7'`. Quoting collapses that argument
            # into a single shlex token whose literal basename is never
            # "nbx", so the checks above would silently miss it. Re-run the
            # full detector against the reassembled argument text instead of
            # trusting the pre-eval token shape.
            remaining = tokens[index + 1 :]
            if remaining and command_has_unconfirmed_write(
                " ".join(remaining),
                inherited_confirmation=(inherited_confirmation or CONFIRMATION in tokens[:index]),
            ):
                return True
    return False


def command_has_unconfirmed_write(command: str, *, inherited_confirmation: bool = False) -> bool:
    """Return whether ``command`` contains an unconfirmed mutating nbx invocation."""
    try:
        segments = _segments(command)
    except ValueError:
        # If shell quoting is malformed, fail closed only when the command
        # still plainly names both nbx and a write action. Unrelated malformed
        # Bash remains outside this hook's narrow scope.
        words = re.findall(r"[A-Za-z0-9_.\-/]+", command)
        return any(_command_name(word) == "nbx" for word in words) and any(
            word in _ALL_WRITE_WORDS or word.upper() in WRITE_HTTP_METHODS for word in words
        )
    for position, (separator, tokens) in enumerate(segments):
        if _segment_has_unconfirmed_write(tokens, inherited_confirmation=inherited_confirmation):
            return True
        if separator == "|" and position > 0:
            # Defense in depth only: arbitrary transforms (base64, gzip,
            # generated scripts, and similar producers) make piped shell
            # input impossible to prove safe from source text alone. The
            # executing ``nbx`` process therefore enforces the authoritative
            # NETBOX_SDK_CONFIRM_WRITE=1/--confirm gate before dispatching a
            # live write; this check remains a best-effort early denial.
            # A pipe feeds this segment's stdin. If the segment invokes a
            # shell with no `-c` (see `_shell_reads_stdin`), that shell will
            # execute whatever the previous segment produced as commands —
            # e.g. `printf '%s' 'nbx dcim devices delete --id 7' | bash`.
            # The producer's literal text is visible here even though the
            # consuming shell's own tokens never mention `nbx`.
            command_index = _unwrap_privilege_command_index(tokens, _command_token_index(tokens))
            if (
                command_index is not None
                and _command_name(tokens[command_index]) in _SHELLS
                and _shell_reads_stdin(tokens, command_index)
            ):
                _, producer_tokens = segments[position - 1]
                if command_has_unconfirmed_write(
                    " ".join(producer_tokens), inherited_confirmation=inherited_confirmation
                ):
                    return True
    return False


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
                    f"Pass {CONFIRM_FLAG} or prefix the invocation with {CONFIRMATION} "
                    "after reviewing a dry-run."
                ),
            }
        },
        sys.stdout,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
