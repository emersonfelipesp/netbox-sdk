# Logs Viewer

`netbox-sdk` exposes two log views:

- `nbx tui logs` launches the full-screen Textual logs viewer
- `nbx logs` prints a plain CLI tail of the same shared log file

Both read the structured JSON log written by the SDK, CLI, and TUI runtime.

## Launch

```bash
nbx tui logs
nbx tui logs --theme dracula
nbx logs
nbx logs --limit 500
```

## What it shows

- timestamp
- level
- logger name
- message body
- optional exception details

Use `nbx logs --source` in the plain CLI view when you also want module,
function, and line information. Use `nbx tui logs --theme` to list available
themes for the Textual viewer.

## Storage

The log viewer reads from the shared log directory under the NetBox SDK config
root. New installs use `~/.config/netbox-sdk/logs/netbox-sdk.log`, while older
`netbox-cli` log files are still read automatically for compatibility.

## Screenshots

- [Logs Viewer gallery](screenshots-logs.md)
- [Launch command output](../reference/tui/launch-examples/index.md)
