# Textual Project Reference — NMS-CLI Guide

This directory contains comprehensive reference guides for notable open-source projects built with the [Textual](https://github.com/Textualize/textual) TUI framework. These guides are intended to inform the architecture, design patterns, and UX decisions of **nms-cli**.

---

## Project Index

| Guide | Project | Author | Stars | Category |
|-------|---------|--------|-------|----------|
| [NMS-CLI.md](NMS-CLI.md) | nms-cli | Local project | n/a | NMS operations CLI + Textual console |
| [DOLPHIE.md](DOLPHIE.md) | [Dolphie](https://github.com/charles-001/dolphie) | charles-001 | ~1,130 | Database monitoring TUI |
| [MEMRAY.md](MEMRAY.md) | [Memray](https://github.com/bloomberg/memray) | Bloomberg | ~14,950 | Memory profiler + Textual live mode |
| [POSTING.md](POSTING.md) | [Posting](https://github.com/darrenburns/posting) | Darren Burns | ~11,589 | HTTP client TUI |
| [TOAD.md](TOAD.md) | [Toad](https://github.com/batrachianai/toad) | Will McGugan | ~2,665 | AI agent unified TUI |
| [TOOLONG.md](TOOLONG.md) | [Toolong](https://github.com/Textualize/toolong) | Will McGugan | ~3,892 | Log file viewer TUI |

---

## What These Projects Have in Common

These references cover the major patterns you'll encounter when building nms-cli:

- **Monitoring dashboards** with live data refresh → Dolphie
- **CLI tools that optionally launch a TUI** → Memray
- **Keyboard-first productivity tools** with jump mode, command palette → Posting
- **Real PTY shell integration + streaming output** → Toad
- **Large-file and streaming data viewers** → Toolong
- **In-repo production Typer+Textual architecture** → NMS-CLI

---

## Cross-Project Patterns for NMS-CLI

### 1. Multi-tab Layout (Dolphie, Toolong)
Both Dolphie and Toolong open multiple targets (hosts/files) as tabs. For NMS-CLI:
- One tab per monitored device
- Color-coded tabs per device type or group

### 2. YAML-Based Config Storage (Posting)
Posting stores every HTTP request as a plain YAML file. NMS-CLI should store:
- Device inventories as YAML
- Named connection profiles as YAML
- Templates and playbooks as YAML
All committed alongside infrastructure code in VCS.

### 3. Environments & Variable Substitution (Posting)
Named environments (dev/staging/prod) with variable substitution in URLs/commands maps directly to NMS-CLI's multi-site/multi-environment use case.

### 4. Record & Replay (Dolphie)
Dolphie records sessions to SQLite + ZSTD for forensic replay. NMS-CLI should support:
- Session recording for audit trails
- Replay for incident post-mortems
- ZSTD compression to keep files small

### 5. Daemon / Headless Mode (Dolphie)
Dolphie runs as a background `systemctl` service for recording. NMS-CLI's collector should:
- Run headlessly without the TUI
- Write structured logs
- Integrate with systemd

### 6. Constant-Time File Access (Toolong)
Toolong's line-offset index enables instant opening of huge files. NMS-CLI log/capture viewers should never load entire files into memory.

### 7. Real PTY Shell Integration (Toad)
Toad embeds a real PTY — `cd` and env vars persist, interactive programs work. If NMS-CLI needs an embedded shell pane, use a PTY (not `subprocess.run`).

### 8. CLI-First, TUI-Optional (Memray)
Memray's core CLI works without Textual; the TUI is one subcommand. NMS-CLI should:
- Keep all features available from the CLI
- Make the TUI an optional interactive layer on top

### 9. Pipe Support (Toolong)
`tree / | tl` works because Toolong accepts stdin as a file. NMS-CLI commands should be pipeable: `nms show route | tl`, `nms capture | tl`.

### 10. Jump Mode & Command Palette (Posting)
Posting's jump mode (letter overlays) and command palette (`Ctrl+P`) minimize mouse dependency. Essential for NMS engineers working over SSH or on headless servers.

---

## Textual Patterns Per Project

Quick lookup for "where did I see that pattern?"

### [DOLPHIE.md](DOLPHIE.md) — 7 patterns
| # | Pattern | Key API |
|---|---------|---------|
| 1 | App class — custom `TextualTheme` with CSS variable overrides | `register_theme()`, `TextualTheme(variables={...})` |
| 2 | Named worker groups for separate concurrency lanes | `@work(thread=True, group="name", exclusive=True)` |
| 3 | Scoped tab handlers for multiple `TabbedContent` widgets | `@on(Tabs.TabActivated, "#host_tabs")` |
| 4 | Freeze repaints during bulk graph refresh | `with self.batch_update():` |
| 5 | Widget reference caching for hot-path access | `app.query_one("#id", DataTable)` stored as attribute |
| 6 | Live `DataTable` rows without flicker | `add_row` / `update_cell` / `remove_row` set-diff pattern |
| 7 | Self-contained modal with inline CSS | `ModalScreen` + `CSS = """..."""` + `Binding("escape", "app.pop_screen")` |

### [MEMRAY.md](MEMRAY.md) — 4 patterns
| # | Pattern | Key API |
|---|---------|---------|
| 1 | Pixel-level custom widget (braille graph) | `render_line(y: int) -> Strip`, `Segment` |
| 2 | Reactive-driven `DataTable` with set-diff lifecycle | `watch_snapshot` → `populate_table` → `add_row/update_cell/remove_row` |
| 3 | Screen with multi-key bindings and reactive cascade | `Binding("q,esc", ...)`, `watch_snapshot` → child `body.snapshot =` |
| 4 | Thread → event loop bridge + batched repaint | `threading.Thread` + `post_message()` + `set_interval()` + `batch_update()` |

### [POSTING.md](POSTING.md) — 5 patterns
| # | Pattern | Key API |
|---|---------|---------|
| 1 | Reactive auto-refreshes footer; CSS-class layout switching | `reactive(..., bindings=True)`, `widget.add_class(f"layout-{x}")` |
| 2 | Exclusive HTTP worker + multi-event → single handler | `@work(exclusive=True)`, `@on(Button.Pressed, ...)` + `@on(Input.Submitted, ...)` |
| 3 | File watcher hot-reload in named worker group | `watchfiles.awatch` inside `@work(exclusive=True, group="...")` |
| 4 | Jump mode: pixel-offset label overlay on `ModalScreen` | `screen.get_offset(child)` → `label.styles.margin = y, x` |
| 5 | Reinitialise state when returning to a screen | `on_screen_resume` vs `on_mount` |

### [TOAD.md](TOAD.md) — 7 patterns
| # | Pattern | Key API |
|---|---------|---------|
| 1 | App modes, auto CSS class toggle, responsive breakpoints | `MODES`, `var(toggle_class="-cls")`, `HORIZONTAL_BREAKPOINTS` |
| 2 | Pre-DOM async init + deferred check + silent worker | `on_load`, `set_timer(1, fn)`, `@work(exit_on_error=False)` |
| 3 | Double Ctrl+C quit guard | `monotonic()` timestamp + `self.notify()` |
| 4 | Command palette with async fuzzy-search hits | `Provider.search()` async generator, `matcher.highlight()` |
| 5 | One-way reactive propagation down the widget tree | `widget.data_bind(child_attr=ParentClass.attr)` |
| 6 | PTY terminal as `ScrollView` with LRU render cache | `ansi.TerminalState`, `LRUCache[tuple, Strip]`, `Finalized(Message)` |
| 7 | Token-by-token streaming Markdown | `MarkdownStream.write(fragment)`, `self.loading = False` |

### [TOOLONG.md](TOOLONG.md) — 6 patterns
| # | Pattern | Key API |
|---|---------|---------|
| 1 | Deferred tab content + conditional tab bar | `Lazy(widget)`, `query("TabbedContent Tabs").set(display=N > 1)` |
| 2 | OS watcher lifetime tied to App lifecycle | `watcher.start()` in `on_mount`, `watcher.close()` in `on_unmount` |
| 3 | Cooperative worker cancellation during file scan | `get_current_worker().is_cancelled`, `add_class("-scanning")` |
| 4 | Deduplicated queue-based background reader | `Queue(maxsize=1000)` + `pending: set` + `post_message()` |
| 5 | File-tail backpressure from watcher thread | `self.message_queue_size > 10` → sleep until queue drains |
| 6 | Multi-file chronological merge | Sort `(timestamp, line_no, LogFile)` tuples from `scan_timestamps()` |

---

## Framework Notes

All referenced projects with TUI components use **Textual**. Key Textual capabilities demonstrated:

| Feature | Demonstrated In |
|---------|----------------|
| Multi-tab `TabbedContent` | Dolphie, Toolong |
| Reactive data refresh | Dolphie, Memray live |
| Streaming text rendering | Toad |
| CSS-like theming | Posting (user themes) |
| Web mode (`textual serve`) | Toad |
| Worker threads for I/O | Dolphie, Memray, Toolong |
| DataTable widget | Dolphie (processlist) |
| Command palette | Posting |

---

## See Also

- [Textual Reference Notes](TEXTUAL.md)
- [Textual vs prompt_toolkit Comparison](../TEXTUAL_VS_PROMPT_TOOLKIT.md)
- [prompt_toolkit Documentation Summary](../prompt-toolkit-docs-summary.md)
