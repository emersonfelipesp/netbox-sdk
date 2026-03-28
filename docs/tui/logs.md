# Logs Viewer

`nbx logs` reads the structured JSON log file written by the CLI and TUI
runtime. It is a terminal-first debugging view for recent SDK, CLI, and TUI
activity.

## Launch

```bash
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
function, and line information.

## Storage

The log viewer reads from the shared log directory under the NetBox SDK config
root. New installs use `~/.config/netbox-sdk/logs/netbox-sdk.log`, while older
`netbox-cli` log files are still read automatically for compatibility.

## Screenshots

- [Logs Viewer gallery](screenshots-logs.md)
