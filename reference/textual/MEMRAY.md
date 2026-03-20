# Memray — Python Memory Profiler

**Repository:** https://github.com/bloomberg/memray
**Author:** Bloomberg
**License:** Apache-2.0
**Language:** Python + C extension
**Framework:** Textual (live TUI mode)
**Stars:** ~14,950

---

## What It Does

Memray is a fast, accurate memory profiler for Python. Unlike sampling-based profilers, it traces **every** memory allocation — including those made inside C/C++ extension modules (numpy, pandas, etc.) and the Python interpreter itself.

Developed by Bloomberg's open-source team and widely adopted for diagnosing memory leaks and excessive allocation patterns in production Python code.

---

## Platform Support

| Platform | Supported |
|----------|-----------|
| Linux x86/x64 | Yes |
| macOS | Yes |
| Windows | No |
| Python version | 3.7+ |

---

## Key Features

### Complete Allocation Tracing
Every `malloc`, `calloc`, `realloc` is captured — no sampling. This gives accurate call stacks rather than statistical approximations.

### Native Mode
`--native` flag tracks allocations inside C/C++ extensions (e.g., numpy's internal buffers), not just Python frames. Native frames are displayed in a distinct color in all report types.

### Report Types

| Command | Output | Use Case |
|---------|--------|----------|
| `memray flamegraph` | HTML flame graph | Visualize allocations by call tree |
| `memray table` | HTML table | Tabular allocation breakdown |
| `memray tree` | Terminal tree | Quick terminal inspection |
| `memray summary` | Terminal summary | Overview stats |
| `memray stats` | Terminal stats | Detailed statistics |
| `memray live` | Textual TUI | Real-time monitoring while running |

### Live TUI Mode
Real-time terminal dashboard while a script runs:
- Sort by total memory, own memory, or allocation count
- Navigate threads with `<` / `>` keys
- Built with Textual framework

### Thread Support
Works with both Python threads and native C++ threads spawned inside C extensions.

### Pytest Integration
```bash
pytest --memray tests/
```
- Per-test memory reporting
- Memory limit markers: `@pytest.mark.limit_memory("24 MB")`
- Fails the test if the limit is exceeded

### Programmatic API
```python
import memray

with memray.Tracker("output_file.bin"):
    # all allocations inside here are tracked
    my_function()
```

---

## Installation

```bash
# pip
python3 -m pip install memray

# conda
conda install -c conda-forge memray
```

**Source build dependencies:**
- Linux: `libdebuginfod-dev`, `libunwind`, `liblz4`
- macOS: `lz4` (via Homebrew)

---

## Usage

```bash
# Profile a script → writes output.bin
memray run my_script.py

# Profile a module
memray run -m my_module

# With native C/C++ tracking
memray run --native my_script.py

# Live real-time TUI
memray run --live my_script.py
memray run --live -m my_module

# Generate reports from .bin file
memray flamegraph output.bin      # open output.bin.html
memray table output.bin
memray tree output.bin
memray summary output.bin
memray stats output.bin

# pytest
pytest --memray tests/
```

---

## Architecture & Design Decisions

### C Extension for Low Overhead
The core profiling engine is written in C to intercept allocations at the libc level (`malloc` hooks / `__malloc_hook`). Python wrapper provides the CLI and report generation. This architecture gives "blazing fast" overhead claims.

### Binary Output Format (`.bin`)
Profiling writes a compact binary file. Report commands parse this file independently — enabling deferred analysis (profile in prod, analyze locally).

### Textual for Live Mode
The live TUI is built with Textual. The rest of the tool (CLI, reports) does not require Textual — it's only pulled in for the live subcommand.

### Standalone HTML Reports
Flame graphs and table reports are single self-contained HTML files — no server required, easy to share.

### Contribution Model
Apache-2.0 license with DCO (Developer Certificate of Origin) sign-off required on all commits.

---

## Textual Code Patterns

### 1. Custom widget with `render_line()` → `Strip`

```python
# src/memray/reporters/tui.py
class MemoryGraph(Widget):
    """Braille-block memory graph rendered line-by-line."""

    # 3x3 lookup table mapping left/right sub-block fill levels to braille chars
    _lookup = [
        [" ", "▗", "▐"],
        ["▖", "▄", "▟"],
        ["▌", "▙", "█"],
    ]

    def add_value(self, value: float) -> None:
        if value > self._maxval:
            self._maxval = value
        self._values.append(value)
        self.refresh()          # trigger a repaint

    def render_line(self, y: int) -> Strip:
        """Called by Textual for every visible row of this widget."""
        graph: list[list[str]] = [[] for _ in range(self._height)]
        blocks_by_index = [self._value_to_blocks(value) for value in self._values]
        for left, right in zip(blocks_by_index[::2], blocks_by_index[1::2]):
            for row, char in enumerate(reversed(...)):
                graph[row].append(char)
        data = "".join(graph[y])
        return Strip([Segment(data, self.rich_style)])
```

**What this shows:** `render_line(y)` is the low-level rendering API — Textual calls it once per visible row, passing the row index. You return a `Strip` (list of `Segment` objects). This is the right approach for widgets that need pixel-level control (graphs, sparklines, custom gauges) rather than delegating to Rich renderables.

---

### 2. `DataTable` — reactive-driven live row updates

```python
# src/memray/reporters/tui.py
class AllocationTable(Widget):
    DEFAULT_CSS = """
    AllocationTable .allocationtable--sorted-column-heading {
        text-style: bold underline;
    }
    """
    sort_column_id = reactive(1)
    snapshot      = reactive(_EMPTY_SNAPSHOT)
    current_thread = reactive(0)
    merge_threads  = reactive(False, init=False)

    def compose(self) -> ComposeResult:
        table: DataTable[Text] = DataTable(
            id="body_table",
            header_height=1,
            show_cursor=False,
            zebra_stripes=True,
        )
        table.focus()
        for column_idx in range(len(self.columns)):
            table.add_column(self.get_heading(column_idx), key=str(column_idx))
        table.ordered_columns[0].content_width = 50
        yield table

    # watch_ auto-called whenever reactive changes
    def watch_snapshot(self) -> None:
        self.populate_table()

    def watch_sort_column_id(self, sort_column_id: int) -> None:
        table = self.query_one("#body_table", DataTable)
        table.sort(table.ordered_columns[sort_column_id].key, reverse=True)

    def populate_table(self) -> None:
        table = self.query_one("#body_table", DataTable)
        old_locations = set(table.rows)
        new_locations = set()
        for location, result in sorted_allocations:
            row_key = str((location.function, location.file))
            new_locations.add(RowKey(row_key))
            if row_key not in table.rows:
                table.add_row(Text(location.function), *cells, key=row_key)
            else:
                # Update existing row in-place — avoids full table rebuild
                for col_idx, val in enumerate(cells, 1):
                    table.update_cell(row_key, str(col_idx), val)
        # Remove rows no longer present
        for old_row_key in old_locations - new_locations:
            table.remove_row(old_row_key)
        table.sort(str(self.sort_column_id), reverse=True)
```

**What this shows:** The `add_row / update_cell / remove_row` pattern is the correct way to keep a `DataTable` in sync with live data. It avoids `clear()` + full re-add on every refresh, which causes flickering and loses scroll position. The set diff (`old - new`) cleanly handles disappearing rows.

---

### 3. `Screen` with reactives + watchers + bindings

```python
# src/memray/reporters/tui.py
class TUI(Screen[None]):
    CSS_PATH = "tui.css"
    BINDINGS = [
        Binding("q,esc",   "app.quit",            "Quit"),
        Binding("m",       "toggle_merge_threads", "Merge Threads"),
        Binding("<,left",  "previous_thread",      "Previous Thread"),
        Binding("t",       "sort(1)",              "Sort by Total"),
        Binding("o",       "sort(3)",              "Sort by Own"),
        Binding("a",       "sort(5)",              "Sort by Allocations"),
        Binding("space",   "toggle_pause",         "Pause"),
    ]

    thread_idx   = reactive(0)
    threads      = reactive([0], always_update=True)
    snapshot     = reactive(_EMPTY_SNAPSHOT)
    paused       = reactive(False, init=False)
    disconnected = reactive(False, init=False)

    def compose(self) -> ComposeResult:
        yield Container(
            Label("[b]Memray[/b] live tracking", id="head_title"),
            TimeDisplay(id="head_time_display"),
            id="head",
        )
        yield Header(pid=self.pid, cmd_line=escape(self.cmd_line or ""))
        yield AllocationTable()
        yield Footer()

    def watch_snapshot(self, snapshot: Snapshot) -> None:
        self._latest_snapshot = snapshot
        self.display_snapshot()

    def watch_disconnected(self) -> None:
        self.update_label()
        redraw_footer(self.app)

    def display_snapshot(self) -> None:
        header = self.query_one(Header)
        body   = self.query_one(AllocationTable)
        graph  = self.query_one(MemoryGraph)
        header.n_samples += 1
        header.last_update = datetime.now()
        graph.add_value(snapshot.heap_size)
        if not self.paused:
            body.snapshot = snapshot       # triggers AllocationTable.watch_snapshot
```

**What this shows:** Binding a key to `"sort(1)"` calls `action_sort(1)` — Textual action arguments are passed as strings in binding definitions. The chain `TUI.snapshot` → `watch_snapshot` → `body.snapshot =` → `AllocationTable.watch_snapshot` → `populate_table()` is a clean reactive cascade that flows data from the top of the screen to nested widgets.

---

### 4. Background thread → `post_message()` → reactive update

```python
# src/memray/reporters/tui.py

class UpdateThread(threading.Thread):
    """Pure threading.Thread (not a Textual Worker) feeding snapshots to the app."""

    def run(self) -> None:
        while self._update_requested.wait():
            if self._canceled.is_set():
                return
            self._update_requested.clear()
            records = list(self._reader.get_current_snapshot(merge_threads=False))
            heap_size = sum(record.size for record in records)
            snapshot = Snapshot(
                heap_size=heap_size,
                records=records,
                records_by_location=aggregate_allocations(records, ...),
            )
            # Thread-safe message delivery to the Textual event loop
            self._app.post_message(SnapshotFetched(snapshot, not self._reader.is_active))


class TUIApp(App[None]):
    def on_mount(self) -> None:
        # set_interval fires every poll_interval seconds on the event loop
        self.set_interval(self._poll_interval, self._update_thread.schedule_update)
        self.tui = TUI(pid=self._reader.pid, cmd_line=cmd_line, native=...)
        self.push_screen(self.tui)
        self._update_thread.start()

    def on_unmount(self) -> None:
        self._update_thread.cancel()
        if self._update_thread.is_alive():
            self._update_thread.join()

    def on_snapshot_fetched(self, message: SnapshotFetched) -> None:
        with self.batch_update():
            # Push data into screen's reactive — triggers watch chain
            self.tui.snapshot = message.snapshot
            self.tui.disconnected = message.disconnected
```

**What this shows:** `post_message()` is thread-safe — you can call it from any `threading.Thread` and Textual will deliver the message on its event loop. `set_interval(N, callback)` schedules a repeating call on the event loop (not a raw thread), so `schedule_update` runs safely and signals the C-level thread to do the actual work. `with self.batch_update()` collapses all reactive re-renders into one pass.

---

## Lessons for NMS-CLI

| Pattern | How Memray Does It | Applicability |
|---------|-------------------|--------------|
| Textual only for interactive mode | CLI works without TUI; live mode adds Textual | Keep CLI and TUI concerns separate |
| Binary intermediate format | `.bin` for deferred analysis | Log/metric capture files |
| HTML reports from CLI | `memray flamegraph output.bin` | Offline report generation |
| pytest plugin | `pytest --memray` | Testing integration |
| C extension + Python wrapper | Native performance where it matters | Performance-critical data collection |
| Programmatic API | Context manager `with Tracker(...)` | Embeddable profiling |
