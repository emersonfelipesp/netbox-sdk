# Agent Client Setup

This page wires the components documented in [MCP Server](index.md) into two
concrete agent clients: Claude Code and Codex CLI. It assumes `netbox-sdk` is
already installed with the `mcp` extra:

```bash
pip install 'netbox-sdk[mcp]'
```

or, from a checkout of this repository:

```bash
pipx install '.[mcp]'
```

Either path must put `nbx-mcp` on `PATH` — confirm with `nbx-mcp --help`
before continuing.

## What ships in the repository

| Path | Purpose | Client |
|---|---|---|
| `.mcp.json` | Registers `nbx-mcp` as a project-scoped stdio MCP server | Claude Code |
| `.claude/settings.json` | `PreToolUse` hook that runs `scripts/check_nbx_write.py` before Bash | Claude Code |
| `.codex/hooks.json` | Same hook, mirrored for Codex's hook format | Codex CLI |
| `.claude/skills/netbox-sdk-operations/` | The `netbox-sdk-operations` Skill (introspect → preview → execute → verify) | Claude Code |
| `.codex/skills/netbox-sdk-operations/` | Same Skill content, mirrored for Codex | Codex CLI |

None of these files contain credentials. The MCP server reads NetBox
credentials from the existing `netbox_sdk.config` profile at run time (see
[Authentication](index.md#authentication)); the hook only inspects the Bash
command about to run, it does not touch NetBox itself.

## Claude Code

### MCP server

Claude Code auto-discovers project-scoped MCP servers from `.mcp.json` the
moment a session's working directory is inside this repository (or one of its
worktrees) — no extra step is required once `nbx-mcp` is on `PATH`. To confirm
it is registered and reachable:

```bash
claude mcp list
```

`.mcp.json` was generated with `claude mcp add -s project netbox-sdk --
nbx-mcp` and looks like this:

```json
{
  "mcpServers": {
    "netbox-sdk": {
      "type": "stdio",
      "command": "nbx-mcp",
      "args": [],
      "env": {}
    }
  }
}
```

To register the same server outside this repository (for example, against a
different checkout, or with a non-default transport), use `-s user` for a
machine-wide registration instead of `-s project`:

```bash
claude mcp add -s user netbox-sdk -- nbx-mcp
```

### Hooks

`.claude/settings.json` is loaded automatically for any Claude Code session
whose working directory is this repository — there is no separate trust or
registration step. The `PreToolUse` hook runs before every Bash tool call and
blocks unconfirmed `nbx` mutation commands (see
[Mutation safety](index.md#mutation-safety) and
[`scripts/check_nbx_write.py`](https://github.com/emersonfelipesp/netbox-sdk/blob/main/scripts/check_nbx_write.py)).

### Skill

The `netbox-sdk-operations` Skill under `.claude/skills/` is discovered the
same way — no installation step. Invoke it explicitly with
`/netbox-sdk-operations` or let Claude Code select it automatically based on
its `description` frontmatter when a NetBox task is in scope.

## Codex CLI

Codex CLI has no per-project MCP registration file equivalent to `.mcp.json`;
MCP servers are always registered globally in `~/.codex/config.toml`:

```bash
codex mcp add netbox-sdk -- nbx-mcp
codex mcp list
```

### Hooks require project trust

Unlike Claude Code, Codex CLI disables **project-local config, hooks, and
exec policies** for any directory that is not marked trusted — only Skills
still load for an untrusted project. This means `.codex/hooks.json` silently
does nothing until the project directory is trusted. Grant trust either
interactively on first use inside the repository, or non-interactively by
adding an entry to `~/.codex/config.toml`:

```toml
[projects."/path/to/netbox-sdk"]
trust_level = "trusted"
```

Use the path to your actual checkout (the canonical clone, not a throwaway
worktree). Verify the hook is active by running a recognizable `nbx` mutation
command through Codex without `--confirm` — it should be blocked by
`check_nbx_write.py` with the `Checking nbx mutation confirmation` status
message, rather than running unchecked.

### Skill

`.codex/skills/netbox-sdk-operations/` mirrors the Claude Code Skill byte for
byte and loads regardless of the project's trust level. The Codex-specific
`agents/openai.yaml` in the Claude Code copy is Claude's own
[Agent Skills marketplace metadata](https://docs.claude.com/en/docs/claude-code/skills) —
it has no Codex equivalent and does not need one.

## Verifying the full setup

1. `nbx-mcp --help` exits 0 — the `mcp` extra is installed.
2. `claude mcp list` (from inside this repository) and `codex mcp list` both
   show `netbox-sdk` as `enabled`.
3. `nbx capabilities --json` (or the MCP `list_groups`/`list_resources` tools)
   returns the schema-driven tool/resource contract described in
   [MCP Server](index.md#tool-surface).
4. An unconfirmed mutation attempted through a Bash tool call (e.g.
   `nbx dcim devices create ...` without `--confirm`) is blocked by the
   PreToolUse hook in both clients — see
   [Mutation safety](index.md#mutation-safety) for the CLI-level gate this
   hook backstops.
