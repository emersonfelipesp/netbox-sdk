# CLI Builder

`nbx cli tui` launches an interactive command builder that lets you navigate the
CLI tree visually, assemble a command, execute it, and inspect the result
without leaving the terminal.

## Launch

```bash
nbx cli tui
nbx demo cli tui
```

## What it is for

- learning the command tree without memorizing every branch
- assembling long dynamic commands step by step
- testing `nbx` invocations before copying them into scripts or shell history
- exploring the same command tree against your default or demo profile

## Notes

- The builder executes real `nbx` commands.
- It complements, rather than replaces, the standard CLI docs in
  [CLI](../cli/index.md).
- Theme handling follows the same built-in TUI theme catalog as the other
  Textual apps.

## Screenshots

- [CLI Builder gallery](screenshots-cli.md)
