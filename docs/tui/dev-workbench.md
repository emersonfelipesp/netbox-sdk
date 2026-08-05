# Developer Workbench

`nbx dev tui` launches the API exploration workspace for NetBox SDK. It is
designed for request inspection, path discovery, and debugging rather than the
standard browse-and-filter workflow of `nbx tui`.

## Launch

```bash
nbx dev tui
nbx dev tui --theme dracula

nbx demo dev tui
nbx demo dev tui --theme dracula
```

## Best use cases

- explore request and response payloads while developing automation
- inspect operation metadata before calling `nbx dev http`
- validate filters, parameters, and response shapes against a live NetBox
- reproduce behavior against the public `demo.netbox.dev` profile

## Relationship to other interfaces

- `nbx tui` is the general-purpose browsing TUI
- `nbx dev tui` is the request workbench
- `nbx cli tui` is the guided command builder
- `nbx logs` is the structured log viewer

## Write confirmation

Every `POST`, `PUT`, `PATCH`, or `DELETE` send opens a confirmation dialog that
shows the resolved method, path, and payload. The request is not dispatched
until you explicitly choose **Confirm write**; cancelling or pressing Escape
leaves NetBox unchanged. This per-request gate also applies when the shared
workbench is launched through `nbx proxbox tui`.

## Screenshots

- [Developer Workbench gallery](screenshots-dev.md)
