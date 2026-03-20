# Toolong — Terminal Log File Viewer

**Repository:** https://github.com/Textualize/toolong
**Author:** Will McGugan (Textualize / creator of Textual & Rich)
**License:** MIT
**Language:** Python
**Framework:** Textual
**Stars:** ~3,892

---

## What It Does

Toolong is a terminal application for viewing, tailing, merging, and searching log files. It replaces the `tail -f | grep | less` workflow with a single, fast TUI that handles multi-gigabyte files instantly, auto-detects timestamps, and merges multiple log files into a unified chronological view.

Previously named **Tailless** (a portmanteau of `tail` + `less`).

---

## Supported File Types

| Format | Support |
|--------|---------|
| Plain text logs | Full |
| JSON Lines (JSONL) | Pretty-printed per line |
| `.bz` / `.bz2` compressed | Auto-decompressed |
| Piped stdin | Full (`tree / | tl`) |

---

## Key Features

### Speed at Any Size
Opens multi-gigabyte log files as fast as small ones. File reading is designed for constant-time random access regardless of file size — no loading the entire file into memory.

### Live Tailing
Watches log files for new content in real time. Equivalent to `tail -f` but with full TUI navigation.

### JSONL Support
JSON Lines files are auto-detected and each line is pretty-printed in the viewer. No manual piping through `jq` needed.

### Log Format Highlighting
Automatically highlights common web server log formats (Apache/Nginx access logs, etc.) using Rich markup.

### Multi-file Merge
```bash
tl access.log* --merge
```
Merges multiple log files into a single chronological view by auto-detecting timestamps. Timestamp regex patterns are borrowed from the LogMerger project.

### Multiple Files in Tabs
```bash
tl access.log error.log debug.log
```
Each file opens in its own tab. Switch between them without leaving the TUI.

### Pipe Support
```bash
tree / | tl
dmesg | tl
kubectl logs my-pod | tl
```
Any piped output goes directly into the viewer.

### Compressed File Support
`.bz` and `.bz2` files are opened and decompressed automatically — no manual `bzcat` piping.

### In-App Help
Press `F1` for keyboard shortcut reference.

---

## Installation

```bash
# pipx (recommended)
pipx install toolong

# pip
pip install toolong
```

Installs the `tl` command into PATH.

---

## Usage

```bash
# Open TUI
tl

# Open single file
tl mylogfile.log

# Open multiple files in tabs
tl access.log error.log

# Merge multiple files chronologically
tl access.log* --merge

# Pipe into viewer
tree / | tl
kubectl logs my-pod --follow | tl
dmesg | tl
```

---

## Architecture & Design Decisions

### Framework: Textual + Rich
Built by Will McGugan (creator of both), so it uses Textual and Rich in their most idiomatic form. The rendering leverages Rich's markup for log syntax highlighting.

### Constant-Time File Access
The file reader does not load files into memory. It maintains an index of line offsets allowing O(1) random access to any line — this is how gigabyte files open instantly.

### Timestamp Detection for Merging
Timestamp regex patterns are adapted from the LogMerger project. The merger:
1. Scans each file to detect the timestamp format
2. Reads lines from all files
3. Merges them into a single stream sorted by timestamp

### Format: JSON Lines (JSONL)
Toolong treats each line as an independent record. JSONL is a natural fit — one JSON object per line, auto-pretty-printed. No streaming JSON parser needed.

### No Search Server
All search is done in-process — no indexing, no external search engine. Fast enough for typical log sizes; very large files may be slow to search.

---

## Comparison with Alternatives

| Tool | Strengths | Weaknesses vs Toolong |
|------|-----------|----------------------|
| `lnav` | More mature, SQL queries, many formats | Heavier, less pretty |
| `tail + grep + less` | Universal, no install | No TUI, no merge, no JSONL |
| `glogg` | Fast search on huge files | GUI (not terminal) |
| Toolong | Pretty, fast open, merge, JSONL, Textual | Less mature than lnav |

---

## Textual Code Patterns

### 1. App + Screen — `TabbedContent` with `Lazy()` loading and tab-bar visibility

```python
# src/toolong/ui.py
class LogScreen(Screen):
    BINDINGS = [Binding("f1", "help", "Help")]
    CSS = """
    LogScreen {
        layers: overlay;
        & TabPane { padding: 0; }
        & Tabs:focus Underline > .underline--bar { color: $accent; }
        Underline > .underline--bar { color: $panel; }
    }
    """

    def compose(self) -> ComposeResult:
        with TabbedContent():
            if self.app.merge and len(self.app.file_paths) > 1:
                # Merge mode: all files in one tab
                tab_name = " + ".join(Path(path).name for path in self.app.file_paths)
                with TabPane(tab_name):
                    yield Lazy(LogView(self.app.file_paths, self.app.watcher, can_tail=False))
            else:
                # One tab per file
                for path in self.app.file_paths:
                    with TabPane(path):
                        yield Lazy(LogView([path], self.app.watcher, can_tail=True))

    def on_mount(self) -> None:
        # Hide the tab bar when there is only one file — no clutter
        self.query("TabbedContent Tabs").set(display=len(self.query(TabPane)) > 1)
        # Auto-focus the log content, not the tabs
        active_pane = self.query_one(TabbedContent).active_pane
        if active_pane is not None:
            active_pane.query("LogView > LogLines").focus()
```

**What this shows:** `Lazy(widget)` defers widget mounting until the tab is first selected — so opening 20 log files doesn't scan all 20 at startup. Tab bar visibility is controlled in `on_mount` with `self.query("TabbedContent Tabs").set(display=N > 1)` — a single CSS query that hides the bar when there's nothing to switch between.

---

### 2. App lifecycle — watcher start/stop tied to `on_mount`/`on_unmount`

```python
# src/toolong/ui.py
class UI(App):
    def __init__(self, file_paths: list[str], merge: bool = False,
                 save_merge: str | None = None):
        self.file_paths = self.sort_paths(file_paths)
        self.merge      = merge
        self.watcher    = get_watcher()   # OS-level file watcher
        super().__init__()

    async def on_mount(self) -> None:
        self.ansi_theme_dark = terminal_theme.DIMMED_MONOKAI
        await self.push_screen(LogScreen())
        self.screen.query("LogLines").focus()
        self.watcher.start()              # start OS file watcher after mount

    def on_unmount(self) -> None:
        self.watcher.close()              # always clean up
```

**What this shows:** The file watcher is started in `on_mount` (after the screen is ready to receive events) and stopped in `on_unmount` (guaranteed even on exception). `self.screen.query("LogLines")` queries into the just-pushed screen immediately — Textual makes the screen available synchronously after `push_screen`.

---

### 3. Custom `ScrollView` — background scan worker + `post_message` from thread

```python
# src/toolong/log_lines.py
class LogLines(ScrollView, inherit_bindings=False):
    BINDINGS = [
        Binding("up,w,k",   "scroll_up",   show=False),
        Binding("down,s,j", "scroll_down", show=False),
        Binding("home,G",   "scroll_home", show=False),
        Binding("end,g",    "scroll_end",  show=False),
        Binding("m",        "navigate(+1, 'm')"),   # jump to next minute boundary
        Binding("o",        "navigate(+1, 'h')"),   # jump to next hour boundary
    ]
    DEFAULT_CSS = """
    LogLines {
        scrollbar-gutter: stable;
        .loglines--filter-highlight { background: $secondary; }
        .loglines--pointer-highlight { background: $primary; }
        &:focus { border: heavy $accent; }
        &.-scanning { tint: $background 30%; }
    }
    """

    show_find    = reactive(False)
    find         = reactive("")
    pointer_line: reactive[int | None] = reactive(None, repaint=False)
    tail:         reactive[bool]       = reactive(True)
    can_tail:     reactive[bool]       = reactive(True)

    def on_mount(self) -> None:
        self.loading = True
        self.add_class("-scanning")          # dim the widget while scanning
        self._line_reader.start()            # start background line-reader thread
        self.initial_scan_worker = self.run_scan(self.app.save_merge)

    @work(thread=True)
    def run_scan(self, save_merge: str | None = None) -> None:
        """Scan line break offsets; post progress messages back to the event loop."""
        worker = get_current_worker()
        for position, breaks in self.log_file.scan_line_breaks():
            self.post_message(ScanProgress(message, 1 - (position / size), position))
            if breaks:
                self.post_message(NewBreaks(self.log_file, breaks))
            if worker.is_cancelled:
                break
        self.post_message(ScanComplete(size, position))
```

**What this shows:** `reactive(None, repaint=False)` marks a reactive that should not trigger a repaint on change — `pointer_line` is used for internal logic only. `add_class("-scanning")` / `remove_class("-scanning")` uses a CSS tint to visually indicate background work. `get_current_worker()` inside a `@work` method gives access to the worker's cancellation flag — the `if worker.is_cancelled: break` pattern is the correct way to cooperatively cancel a CPU-bound scan.

---

### 4. Background `Thread` as a line-reading queue

```python
# src/toolong/log_lines.py
class LineReader(Thread):
    """Reads raw bytes from file offsets without blocking the Textual event loop."""

    def __init__(self, log_lines: LogLines):
        self.queue:      Queue[tuple[LogFile | None, int, int, int]] = Queue(maxsize=1000)
        self.exit_event: Event = Event()
        self.pending:    set   = set()

    def request_line(self, log_file, index, start, end) -> None:
        """Enqueue a line-read request (deduplicated)."""
        request = (log_file, index, start, end)
        if request not in self.pending:
            self.pending.add(request)
            self.queue.put(request)

    def run(self) -> None:
        while not self.exit_event.is_set():
            try:
                request = self.queue.get(timeout=0.2)
            except Empty:
                continue
            log_file, index, start, end = request
            self.pending.discard(request)
            data = log_file.get_line(start, end)
            # Thread-safe delivery back to the Textual event loop
            self.log_lines.post_message(LineRead(index, log_file, start, end, data))
```

**What this shows:** `Queue(maxsize=1000)` provides natural backpressure — if the UI scrolls faster than the reader, the queue fills and `request_line` blocks. The `pending` set deduplicates requests so rapid scrolling doesn't enqueue the same line 50 times. `post_message()` is the thread-safe bridge back to Textual.

---

### 5. Live tail — file watcher callback → `post_message`

```python
# src/toolong/log_lines.py
def start_tail(self) -> None:
    """Register with the OS file watcher to receive new-line notifications."""

    def size_changed(size: int, breaks: list[int]) -> None:
        """Called from the watcher thread when the file grows."""
        with self._lock:
            for offset, _ in enumerate(breaks, 1):
                self.get_line_from_index(self.line_count - offset)
        self.post_message(NewBreaks(self.log_file, breaks, size, tail=True))
        # Apply backpressure: if the message queue is too deep, wait
        if self.message_queue_size > 10:
            while self.message_queue_size > 2:
                time.sleep(0.1)

    self.watcher.add(self.log_file, size_changed, watch_error)
```

**What this shows:** The watcher callback is called from a background thread — `post_message()` safely delivers `NewBreaks` to the event loop. The `message_queue_size` backpressure check is a practical pattern for high-throughput tailing: if the event loop can't keep up, the watcher thread yields until the queue drains.

---

### 6. Timestamp-based multi-file merge

```python
# src/toolong/log_lines.py
def merge_log_files(self) -> None:
    """Merge multiple log files into one chronological line list."""
    for log_file in self.log_files:
        meta: list[tuple[float, int, LogFile]] = []
        for timestamps in log_file.scan_timestamps():
            for line_no, break_position, timestamp in timestamps:
                meta.append((timestamp, line_no, log_file))
        self._merge_lines.extend(meta)
    # Sort all (timestamp, line_no, file) tuples globally
    self._merge_lines.sort(key=lambda x: x[0])
```

**What this shows:** Merge is a straightforward sort of `(timestamp, line_no, file)` tuples. `scan_timestamps()` uses regexes (borrowed from LogMerger) to detect common timestamp formats and returns `(line_no, byte_offset, unix_timestamp)` triples. The sorted list is then used by `render_line()` to look up which file and offset to read for each virtual line number.

---

## Lessons for NMS-CLI

| Pattern | How Toolong Does It | Applicability |
|---------|--------------------|--------------|
| Constant-time large file access | Line offset index, no full load | Log/capture file viewing in NMS |
| Live tailing | File watcher integration | Live CLI output tailing |
| Pipe support | Accept stdin as a virtual file | `nms-cli some-cmd | tl`-style piping |
| Multi-file tabs | Each file = one tab | Multi-device logs in tabs |
| Timestamp-based merge | Regex detection + sort merge | Correlate logs across devices |
| JSONL pretty-print | Per-line JSON detection | Structured log rendering |
| Compressed file transparent open | Auto-detect `.bz`/`.bz2` | Compressed capture file support |
| F1 in-app help | Key binding reference modal | Help overlay in NMS TUI |
