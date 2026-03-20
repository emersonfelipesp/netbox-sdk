# Dolphie — MySQL/MariaDB/ProxySQL Monitoring TUI

**Repository:** https://github.com/charles-001/dolphie
**Author:** charles-001
**License:** GPL-3.0
**Language:** Python
**Framework:** Textual
**Stars:** ~1,130

---

## What It Does

Dolphie is a real-time terminal monitoring dashboard for MySQL, MariaDB, and ProxySQL. It provides a single-pane-of-glass view of database health and activity — covering processlist, replication lag, performance schema metrics, metadata locks, and more.

Think of it as a `top`/`htop`-equivalent specifically designed for database engineers.

---

## Supported Databases

| Database | Versions |
|----------|----------|
| MySQL / Percona Server | 5.6, 5.7, 8.x, 9.x |
| AWS RDS / Aurora MySQL | Yes |
| Azure MySQL | Yes |
| MariaDB | 5.5, 10.0, 11.0+ |
| AWS RDS MariaDB | Yes |
| Azure MariaDB | Yes |
| ProxySQL | 2.6+ |

---

## Key Features

### Multi-tab Interface
Connect to multiple database hosts simultaneously — each in its own tab, with color-coding and emoji support per host.

### Monitoring Panels
Toggle panels on/off from the UI or configure which open at startup:
- `dashboard` — high-level stats and KPIs
- `processlist` — active queries with filtering
- `graphs` — time-series metric plots (braille or block characters)
- `replication` — replication lag and slave status
- `metadata_locks` — MDL lock tracking
- `DDL` — in-progress DDL operations
- `pfs_metrics` — Performance Schema metrics
- `statements_summary` — aggregated query stats
- ProxySQL panels: `hostgroup_summary`, `query_rules`, `command_stats`

### Record & Replay
- Records live session data into ZSTD-compressed SQLite files
- Replay controls: step back/forward, play/pause, jump to timestamp
- Useful for post-incident forensics

### Daemon Mode
- Headless background recording (no TUI)
- Integrates with `systemctl` as a service
- Writes structured log messages
- Maintains a 10-minute rolling metrics window

### System Utilization Panel
CPU, memory, swap, load averages, network I/O — only populated when dolphie runs on the same host as the database.

### Authentication Flexibility
Credential resolution order (highest wins):
1. Command-line arguments
2. Credential profile (`-C profile_name`)
3. Environment variables (`DOLPHIE_USER`, `DOLPHIE_PASSWORD`, `DOLPHIE_HOST`, etc.)
4. `dolphie.cnf` config file
5. `~/.mylogin.cnf` (mysql_config_editor)
6. `~/.my.cnf`

### Other Features
- SSL/TLS support (`REQUIRED` / `VERIFY_CA` / `VERIFY_IDENTITY`)
- pt-heartbeat integration for precise replication lag
- Global variable change notifications
- Configurable refresh interval (default: 1 second)

---

## Installation

```bash
# pip
pip install dolphie

# Homebrew (macOS)
brew install dolphie

# Docker
docker pull ghcr.io/charles-001/dolphie:latest
docker run -dit --name dolphie ghcr.io/charles-001/dolphie:latest
docker exec -it dolphie dolphie --tab-setup
```

---

## Usage

```bash
# Basic connection
dolphie -u user -p password -h host

# DSN-style
dolphie mysql://user:password@host:port

# Open host setup modal on start
dolphie --tab-setup

# Enable recording
dolphie --record --replay-dir /path/to/dir

# Headless daemon mode
dolphie --daemon

# Replay a recorded session
dolphie --replay-file /path/to/replay.db
```

---

## Architecture & Design Decisions

### Framework: Textual
Dolphie uses the Textual TUI framework for its reactive, component-based UI. This allows independent panel refresh, keyboard-driven navigation, and multi-tab support.

### Data Storage: SQLite + ZSTD
Replay files are SQLite databases with ZSTD-compressed payloads. This gives random-access replay (jump to timestamp) while keeping file sizes manageable.

### Graph Rendering
Uses braille-character markers by default (Rich-compatible). Alternative markers configurable for terminals without braille support.

### MySQL Grants Required
Minimum permissions for full functionality:
```sql
GRANT PROCESS ON *.* TO 'dolphie'@'%';
GRANT SELECT ON performance_schema.* TO 'dolphie'@'%';
GRANT REPLICATION CLIENT ON *.* TO 'dolphie'@'%';
-- or
GRANT REPLICATION SLAVE ON *.* TO 'dolphie'@'%';
```

---

## Textual Code Patterns

### 1. App class — custom theme + CSS file + command palette

```python
# dolphie/App.py
class DolphieApp(App):
    TITLE = "Dolphie"
    CSS_PATH = "Dolphie.tcss"          # external stylesheet
    COMMANDS = {CommandPaletteCommands} # custom command palette provider
    COMMAND_PALETTE_BINDING = "question_mark"

    def __init__(self, config: Config):
        super().__init__()
        # Register a named theme with custom CSS variable overrides
        theme = TextualTheme(
            name="custom",
            primary="white",
            variables={
                "white": "#e9e9e9",
                "green": "#54efae",
                "yellow": "#f6ff8f",
                "red": "#fd8383",
                "purple": "#b565f3",
                "panel_border": "#6171a6",
                "table_border": "#333f62",
            },
        )
        self.register_theme(theme)
        self.theme = "custom"
```

**What this shows:** `COMMANDS` attaches a custom provider to the built-in command palette. `register_theme()` + `TextualTheme(variables={...})` lets you override CSS design tokens at runtime rather than hardcoding colors — so the whole app re-skins when you call `self.theme = "custom"`.

---

### 2. Named worker groups — separate concurrency lanes

```python
# dolphie/App.py
@work(thread=True, group="replay", exclusive=True)
async def run_worker_replay(self, tab_id: str, manual_control: bool = False):
    await self.worker_manager.run_worker_replay(tab_id, manual_control)

@work(thread=True, group="main")
async def run_worker_main(self, tab_id: str):
    await self.worker_manager.run_worker_main(tab_id)

@work(thread=True, group="replicas")
def run_worker_replicas(self, tab_id: str):
    self.worker_manager.run_worker_replicas(tab_id)

def on_worker_state_changed(self, event: Worker.StateChanged):
    self.worker_manager.on_worker_state_changed(event)
```

**What this shows:** `group=` namespaces workers so you can cancel only the "replay" lane without touching "main" lane workers. `exclusive=True` on the replay group ensures only one replay worker runs at a time (new call cancels the previous one). `on_worker_state_changed` is the standard hook for reacting to worker lifecycle events.

---

### 3. Tab switching with `@on(Tabs.TabActivated, selector)`

```python
# dolphie/App.py
@on(Tabs.TabActivated, "#host_tabs")
def host_tab_changed(self, event: Tabs.TabActivated):
    previous_tab = self.tab_manager.active_tab
    # Cancel previous tab's worker and timer before switching
    if previous_tab and previous_tab.dolphie.replay_file and previous_tab.worker:
        previous_tab.worker.cancel()
        if previous_tab.worker_timer:
            previous_tab.worker_timer.stop()
    self.tab_manager.switch_tab(event.tab.id, set_active=False)

@on(TabbedContent.TabActivated, "#metric_graph_tabs")
def metric_graph_tab_changed(self, event: TabbedContent.TabActivated):
    metric_tab_name = event.pane.name
    if metric_tab_name:
        self.update_graphs(metric_tab_name)
```

**What this shows:** `@on(Event, "#css-selector")` scopes a handler to a specific widget by id — so you can have two `TabActivated` handlers for two different `TabbedContent`/`Tabs` widgets without them interfering. Worker cancellation on tab switch prevents stale background queries updating the wrong panel.

---

### 4. `batch_update()` — freeze repaints during bulk updates

```python
# dolphie/App.py
def update_graphs(self, metric_tab_name: str):
    tab = self.tab_manager.active_tab
    if not tab or not tab.panel_graphs.display:
        return
    with self.batch_update():           # suppress individual repaints
        for graph_name in metric_instance.graphs:
            getattr(tab, graph_name).render_graph(metric_instance, ...)
```

**What this shows:** Wrapping multiple widget updates in `with self.batch_update()` tells Textual to defer all repaints until the block exits — one repaint instead of N. Essential when refreshing many graph widgets simultaneously to avoid flickering.

---

### 5. `query_one()` to cache widget references

```python
# dolphie/Modules/TabManager.py
def save_references_to_components(self):
    app = self.dolphie.app
    # Cache direct references to frequently-updated widgets
    self.processlist_datatable  = app.query_one("#processlist_data", DataTable)
    self.metadata_locks_datatable = app.query_one("#metadata_locks_datatable", DataTable)
    self.dashboard_replay_progressbar = app.query_one("#dashboard_replay_progressbar", ProgressBar)
    self.sparkline = app.query_one("#panel_dashboard_queries_qps", Sparkline)
    self.metric_graph_tabs = app.query_one("#metric_graph_tabs", TabbedContent)
    self.pfs_metrics_radio_set = app.query_one("#pfs_metrics_radio_set", RadioSet)
```

**What this shows:** `query_one(selector, Type)` traverses the DOM once and caches the reference. Dolphie calls this after composing each tab so hot-path code (called every second) does a direct attribute read instead of re-querying the DOM on every refresh.

---

### 6. `DataTable` — dynamic column construction + row updates

```python
# dolphie/Panels/Processlist.py
def create_panel(tab: Tab) -> DataTable:
    columns = [
        {"name": "Thread ID",  "field": "id",              "width": None, "format_number": False},
        {"name": "Username",   "field": "user",            "width": 20,   "format_number": False},
        {"name": "Command",    "field": "command",         "width": 8,    "format_number": False},
        {"name": "State",      "field": "state",           "width": 20,   "format_number": False},
        {"name": "TRX State",  "field": "trx_state",       "width": 9,    "format_number": False},
        {"name": "R-Lock",     "field": "trx_rows_locked", "width": 7,    "format_number": True},
        {"name": "Age",        "field": "formatted_time",  "width": 9,    "format_number": False},
        {"name": "Query",      "field": "formatted_query", "width": None, "format_number": False},
    ]
    processlist_datatable = tab.processlist_datatable
    # Only rebuild columns if count changed (avoids full clear on every refresh)
    if len(processlist_datatable.columns) != len(columns):
        processlist_datatable.clear(columns=True)
    if not processlist_datatable.columns:
        for col in columns:
            processlist_datatable.add_column(col["name"], key=col["name"], width=col["width"])
```

**What this shows:** The guard `if len(...columns) != len(columns)` avoids clearing and rebuilding all columns every refresh cycle — only rebuild when the schema changes. `key=` on `add_column` lets you target columns by name later with `update_cell(row_key, col_key, value)`.

---

### 7. `ModalScreen` with inline CSS + `BINDINGS`

```python
# dolphie/Widgets/CommandModal.py
class CommandModal(ModalScreen):
    CSS = """
        CommandModal {
            & > Vertical {
                background: #131626;
                border: tall #384673;
                height: auto;
                width: auto;
            }
            & Input, Select { width: 60; }
            & #error_response {
                color: #fe5c5c;
                width: 100%;
                content-align: center middle;
            }
        }
    """
    BINDINGS = [Binding("escape", "app.pop_screen", "", show=False)]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"[b]{self.message}[/b]")
            with Vertical(id="filter_container", classes="command_container"):
                yield filter_by_username_input
                yield AutoComplete(
                    filter_by_username_input,
                    id="filter_by_username_dropdown_items",
                    candidates=[],
                )
            with Vertical(id="kill_container", classes="command_container"):
                yield kill_by_id_input
                yield Rule(line_style="heavy")
                yield Checkbox("Include sleeping queries", id="sleeping_queries")
```

**What this shows:** `ModalScreen` with `CSS = """..."""` keeps styling self-contained inside the modal class. `Binding("escape", "app.pop_screen", ...)` is the canonical pattern for closing a modal with Escape — delegating to `app.pop_screen` instead of `self.dismiss()` works anywhere in the stack.

---

## Lessons for NMS-CLI

| Pattern | How Dolphie Does It | Applicability |
|---------|--------------------|--------------|
| Multi-tab layout | One tab per host | Multi-device monitoring |
| Live panel refresh | Textual reactive updates | Real-time metric polling |
| Record & replay | SQLite + ZSTD | Session logging/audit |
| Daemon mode | Background process + structured logs | Headless collectors |
| Credential profiles | Named profiles in config | Multi-environment connections |
| Toggleable panels | Config + keyboard toggle | Customizable dashboard |
