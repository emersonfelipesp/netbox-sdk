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
| `.codex/config.toml` | Registers `nbx-mcp` as a project-scoped MCP server | Codex CLI |
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
worktrees). Discovery is not the same as connection: the first time a session
starts in this project, Claude Code prompts for a one-time approval before it
will actually use `netbox-sdk`. If that prompt is dismissed or the terminal
scrolls past it, run `/mcp` inside the session to approve it explicitly; if it
was previously rejected, run `claude mcp reset-project-choices` to clear that
decision so the prompt appears again. Once approved, confirm it is registered
and reachable:

```bash
claude mcp list
```

`netbox-sdk` should show as connected, not `⏸ Pending approval`.

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

### MCP server

Codex CLI supports project-scoped MCP registration through
`.codex/config.toml`, mirroring `.mcp.json` for Claude Code. This repository
ships one:

```toml
[mcp_servers.netbox-sdk]
command = "nbx-mcp"
default_tools_approval_mode = "writes"
```

`.codex/config.toml`, like every other file under `.codex/`, only loads once
the project directory is [trusted](#hooks-require-two-separate-trust-steps).
Keep the server project-scoped rather than registering it globally: `nbx-mcp`
reads the caller's NetBox profile, and a global `codex mcp add` entry in
`~/.codex/config.toml` stays active across every Codex project, including
untrusted ones, which unnecessarily widens the tool's exposure. Only reach for
global registration if you deliberately want `netbox-sdk` available outside
this repository:

```bash
codex mcp add netbox-sdk -- nbx-mcp
codex mcp list
```

### Hooks require two separate trust steps

Codex CLI gates `.codex/` on **project trust**, and gates each hook
definition on a **separate, hash-based review** — both must pass before
`.codex/hooks.json` actually runs.

1. **Project trust.** Codex disables project-local config, hooks, and exec
   policies for any directory that is not marked trusted — only Skills still
   load for an untrusted project. Trust is keyed by the exact directory path,
   so a worktree checked out at a different path than your canonical clone
   needs its own trust entry; trusting only the canonical clone leaves the
   worktree's `.codex/` layer unloaded. Grant trust interactively on first use
   inside each checkout you work from, or non-interactively by adding one
   entry per path to `~/.codex/config.toml`:

   ```toml
   [projects."/path/to/netbox-sdk"]
   trust_level = "trusted"

   [projects."/path/to/netbox-sdk.worktrees/some-branch"]
   trust_level = "trusted"
   ```

2. **Hook review.** Even in a trusted project, Codex requires you to review
   and trust the exact content of a non-managed command hook before it can
   run, via the `/hooks` slash command inside a session. Trust is recorded
   against the hook definition's current content hash, so any future edit to
   `.codex/hooks.json` revokes trust until you re-review it with `/hooks`.

Verify both steps are complete by running a recognizable `nbx` mutation
command through Codex without `--confirm` — it should be blocked by
`check_nbx_write.py` with the `Checking nbx mutation confirmation` status
message, rather than running unchecked. If it runs unchecked, re-check project
trust for the exact path in use and run `/hooks` to confirm the hook is
listed as trusted.

### Skill

`.codex/skills/netbox-sdk-operations/` mirrors the Claude Code Skill byte for
byte and loads regardless of the project's trust level. The Codex-specific
`agents/openai.yaml` in the Claude Code copy is Claude's own
[Agent Skills marketplace metadata](https://docs.claude.com/en/docs/claude-code/skills) —
it has no Codex equivalent and does not need one.

## Verifying the full setup

1. `nbx-mcp --help` exits 0 — the `mcp` extra is installed.
2. From inside this repository, `claude mcp list` shows `netbox-sdk` as
   connected (approve it via `/mcp` first if it still shows pending), and
   `codex mcp list` shows `netbox-sdk` once the project directory is trusted.
3. `nbx capabilities --json` (or the MCP `list_groups`/`list_resources` tools)
   returns the schema-driven tool/resource contract described in
   [MCP Server](index.md#tool-surface).
4. An unconfirmed mutation attempted through a Bash tool call (e.g.
   `nbx dcim devices create ...` without `--confirm`) is blocked by the
   PreToolUse hook in both clients — see
   [Mutation safety](index.md#mutation-safety) for the CLI-level gate this
   hook backstops.
