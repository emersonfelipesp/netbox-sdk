# Textual Framework — Documentation Summary

> Source: https://textual.textualize.io/
> Summarized: 2026-03-19

## High-Level Overview

**Textual** is a Rapid Application Development (RAD) framework for Python by [Textualize.io](https://www.textualize.io). It builds richly styled terminal UIs (TUIs) that run in any terminal and can also be served as web apps over HTTP or SSH. MIT-licensed, Python 3.9+, inspired by web technologies (CSS, DOM, reactive attributes).

**Key capabilities:**
- CSS-like styling with `.tcss` files and inline styles
- A DOM tree of widgets composed via Python `compose()` methods
- Reactive attributes that auto-refresh the UI on change
- An event/message bus with bubbling, custom messages, and the `@on` decorator
- Built-in async workers for background tasks
- Command palette, animations, modal screens, and snapshot testing
- `textual serve` turns any TUI into a web app instantly

---

## URL Index

### Entry Points
| URL | Description |
|-----|-------------|
| https://textual.textualize.io/ | Homepage: framework overview, features, notable apps |
| https://textual.textualize.io/getting_started/ | Installation (`pip install textual`, conda), requirements, devtools setup |
| https://textual.textualize.io/tutorial/ | Full stopwatch app tutorial: App, CSS, reactives, timers, dynamic widgets |
| https://textual.textualize.io/widget_gallery/ | Visual gallery of all 40+ built-in widgets |

### Guide Pages
| URL | Description |
|-----|-------------|
| https://textual.textualize.io/guide/ | Guide index |
| https://textual.textualize.io/guide/devtools/ | `textual run/serve/console`, live CSS reloading, logging |
| https://textual.textualize.io/guide/app/ | App class: `compose()`, `run()`, `mount()`, `exit()`, `suspend()`, lifecycle events |
| https://textual.textualize.io/guide/styles/ | Inline styling via `widget.styles.*`, box model, color formats, FR units |
| https://textual.textualize.io/guide/CSS/ | TCSS syntax, selectors, pseudo-classes, differences from web CSS |
| https://textual.textualize.io/guide/queries/ | `query()`, `query_one()`, `DOMQuery` methods |
| https://textual.textualize.io/guide/layout/ | Vertical/horizontal/grid layouts, docking, layers, offsets |
| https://textual.textualize.io/guide/events/ | Event system, handler naming, `@on` decorator, bubbling, `stop()`, custom messages |
| https://textual.textualize.io/guide/input/ | Keyboard/mouse events, focus management, `BINDINGS`, `Binding` class |
| https://textual.textualize.io/guide/actions/ | `action_*` methods, built-in actions, `check_action()`, action strings in links |
| https://textual.textualize.io/guide/reactivity/ | `reactive()`, `var()`, `watch_*`, `compute_*`, `validate_*`, `data_bind()` |
| https://textual.textualize.io/guide/screens/ | Screen stack (`push_screen`, `pop_screen`, `switch_screen`), `ModalScreen`, MODES |
| https://textual.textualize.io/guide/widgets/ | Custom widgets, `render()`, `Static`, `update()`, border titles, tooltips, Line API |
| https://textual.textualize.io/guide/content/ | Markup syntax `[bold]text[/bold]`, `Content` class, Rich renderables |
| https://textual.textualize.io/guide/animation/ | `animate()`, easing functions, `duration`, `delay`, `on_complete` |
| https://textual.textualize.io/guide/workers/ | `@work` decorator, `Worker` class, `WorkerState`, thread workers, `call_from_thread()` |
| https://textual.textualize.io/guide/command_palette/ | Ctrl+P palette, `Provider` subclass, `search()`, `discover()`, `SystemCommand` |
| https://textual.textualize.io/guide/testing/ | `run_test()`, `Pilot` class, `press()`, `click()`, snapshot testing |

### Widget Reference Pages
| URL | Widget | Key Events / Notes |
|-----|--------|--------------------|
| https://textual.textualize.io/widgets/ | Index | All 37+ built-in widgets listed |
| https://textual.textualize.io/widgets/button/ | Button | `Button.Pressed`; variants: default/primary/success/warning/error |
| https://textual.textualize.io/widgets/input/ | Input | `Input.Changed`, `Input.Submitted`; validators, placeholder, password mode, `restrict` regex, auto-suggest |
| https://textual.textualize.io/widgets/text_area/ | TextArea | `TextArea.Changed`; syntax highlighting (tree-sitter), undo/redo, selection |
| https://textual.textualize.io/widgets/data_table/ | DataTable | Sorting, cursor types (cell/row/column/none), zebra stripes, fixed rows/columns |
| https://textual.textualize.io/widgets/list_view/ | ListView | `ListView.Highlighted`, `ListView.Selected`; scrollable `ListItem` list |
| https://textual.textualize.io/widgets/option_list/ | OptionList | `OptionHighlighted`, `OptionSelected`; Rich-renderable options |
| https://textual.textualize.io/widgets/selection_list/ | SelectionList | Multi-select; `select_all()`, `deselect_all()`, `SelectedChanged` |
| https://textual.textualize.io/widgets/tree/ | Tree | `NodeSelected`; `TreeNode` add/add_leaf/expand/collapse |
| https://textual.textualize.io/widgets/directory_tree/ | DirectoryTree | `FileSelected`, `DirectorySelected`; `filter_paths()` override |
| https://textual.textualize.io/widgets/tabbed_content/ | TabbedContent | `TabActivated`; `add_pane()`, `remove_pane()` |
| https://textual.textualize.io/widgets/content_switcher/ | ContentSwitcher | Show/hide children by ID; `current` reactive |
| https://textual.textualize.io/widgets/collapsible/ | Collapsible | `Collapsible.Toggled`, `Collapsed`, `Expanded` |
| https://textual.textualize.io/widgets/select/ | Select | `Select.Changed`; dropdown with overlay, `type_to_search` |
| https://textual.textualize.io/widgets/checkbox/ | Checkbox | `Checkbox.Changed`; inherits from `ToggleButton` |
| https://textual.textualize.io/widgets/switch/ | Switch | `Switch.Changed`; animated on/off toggle |
| https://textual.textualize.io/widgets/progress_bar/ | ProgressBar | Determinate/indeterminate; `advance()`, `update()` |
| https://textual.textualize.io/widgets/rich_log/ | RichLog | Append-only Rich log; `write()`, `clear()`, `auto_scroll`, `max_lines` |
| https://textual.textualize.io/widgets/log/ | Log | Plain-text log; `write_line()`, `write_lines()`, `clear()` |
| https://textual.textualize.io/widgets/markdown/ | Markdown | GFM rendering; `update()`, `append()`, `load()`, `LinkClicked` |
| https://textual.textualize.io/widgets/label/ | Label | Simple text display; inherits from Static |
| https://textual.textualize.io/widgets/static/ | Static | Base for static content/Rich renderables; `update()` |
| https://textual.textualize.io/widgets/sparkline/ | Sparkline | Numerical bar chart; `data` and `summary_function` reactives |
| https://textual.textualize.io/widgets/toast/ | Toast | Short-lived notification via `App.notify()` with severity levels |
| https://textual.textualize.io/widgets/placeholder/ | Placeholder | Layout prototyping; cycles variants on click |
| https://textual.textualize.io/widgets/loading_indicator/ | LoadingIndicator | Pulsating animation; triggered via widget `loading` reactive |

### API Reference Pages
| URL | Module | Description |
|-----|--------|-------------|
| https://textual.textualize.io/api/ | Index | All ~45 API modules |
| https://textual.textualize.io/api/app/ | textual.app | `App` class: screen management, notify, run, exit |
| https://textual.textualize.io/api/widget/ | textual.widget | `Widget` base: lifecycle, rendering, scrolling, focus, animation |
| https://textual.textualize.io/api/screen/ | textual.screen | `Screen`, `ModalScreen`: focus, dismiss, maximize, `AUTO_FOCUS` |
| https://textual.textualize.io/api/dom_node/ | textual.dom | `DOMNode`: DOM traversal, `data_bind()`, `run_worker()`, `walk_children()` |
| https://textual.textualize.io/api/events/ | textual.events | All event classes: mouse, keyboard, focus, lifecycle, resize |
| https://textual.textualize.io/api/reactive/ | textual.reactive | `reactive`, `var`, `Reactive` descriptor |
| https://textual.textualize.io/api/message/ | textual.message | `Message` base: `control`, `stop()`, `prevent_default()`, `handler_name` |
| https://textual.textualize.io/api/binding/ | textual.binding | `Binding` dataclass: key, action, description, show, priority, tooltip |
| https://textual.textualize.io/api/containers/ | textual.containers | `Vertical`, `Horizontal`, `Grid`, `VerticalScroll`, `Center`, `Middle`, `ItemGrid` |
| https://textual.textualize.io/api/geometry/ | textual.geometry | `Offset`, `Region`, `Size`, `Spacing`, `clamp()` |
| https://textual.textualize.io/api/color/ | textual.color | `Color` (RGBA): `parse()`, `blend()`, `lighten()`, `darken()` |
| https://textual.textualize.io/api/query/ | textual.css.query | `DOMQuery`: filter, exclude, add_class, set_styles, focus, remove |
| https://textual.textualize.io/api/on/ | textual.on | `@on(MessageType, selector)` decorator with CSS selector filtering |
| https://textual.textualize.io/api/work/ | textual.work | `@work` decorator: name, group, exclusive, exit_on_error, thread |
| https://textual.textualize.io/api/worker/ | textual.worker | `Worker` class, `WorkerState` enum, `cancel()`, `wait()` |
| https://textual.textualize.io/api/validation/ | textual.validation | `Validator`, `ValidationResult`, built-ins: `Number`, `Integer`, `Length`, `Regex`, `URL`, `Function` |
| https://textual.textualize.io/api/pilot/ | textual.pilot | `Pilot`: `click()`, `press()`, `hover()`, `pause()`, `resize_terminal()` |
| https://textual.textualize.io/api/suggester/ | textual.suggester | `Suggester` (abstract), `SuggestFromList` for Input auto-completion |
| https://textual.textualize.io/api/types/ | textual.types | Type aliases: `AnimationLevel`, `EasingFunction`, `CallbackType`, `Direction` |

### Reference Pages
| URL | Description |
|-----|-------------|
| https://textual.textualize.io/styles/ | Full CSS styles reference — all properties alphabetically |
| https://textual.textualize.io/events/ | All 27 event types listed with links |
| https://textual.textualize.io/css_types/ | CSS data types: border, color, scalar, text-align, etc. |

### How-To Guides
| URL | Description |
|-----|-------------|
| https://textual.textualize.io/how-to/center-things/ | Centering widgets in layouts |
| https://textual.textualize.io/how-to/design-a-layout/ | Layout design strategies |
| https://textual.textualize.io/how-to/render-and-compose/ | Render vs compose techniques |
| https://textual.textualize.io/how-to/style-inline-apps/ | Styling inline (non-fullscreen) apps |
| https://textual.textualize.io/how-to/use-containers/ | Efficient container usage |
| https://textual.textualize.io/how-to/package-with-hatch/ | Packaging with Hatch |

---

## Key Concepts

### Application Structure

Every Textual app subclasses `App`. The `compose()` method yields widgets. CSS is declared via `CSS` (inline string) or `CSS_PATH` (`.tcss` file). `on_mount()` fires after the DOM is ready.

```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Label

class MyApp(App):
    CSS_PATH = "my_app.tcss"      # external .tcss stylesheet
    TITLE    = "My Application"
    BINDINGS = [
        ("q", "quit",        "Quit"),
        ("d", "toggle_dark", "Toggle dark"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()             # auto-shows TITLE + clock
        yield Label("Hello, world!")
        yield Footer()             # auto-shows BINDINGS

    def on_mount(self) -> None:
        """Fires after all widgets are mounted and the DOM is ready."""
        self.query_one(Label).focus()

if __name__ == "__main__":
    MyApp().run()
```

**Lifecycle order:** `on_load` (before DOM, async safe) → `compose()` → `on_mount` (DOM ready) → `on_unmount` (app exit).

---

### The DOM and Widget Tree

Widgets form a tree: `App` → `Screen` → widgets → child widgets. Navigate with `query(selector)` and `query_one(selector, type)`. `DOMNode` provides `walk_children()`, `ancestors`, and `data_bind()`.

```python
# CSS selector query — returns a DOMQuery (lazy list of matching widgets)
all_buttons = self.query("Button")
all_buttons.set(disabled=True)           # bulk operation on all matches

# Type-safe single-widget lookup — raises NoMatches / TooManyMatches
label = self.query_one("#status-label", Label)
label.update("Connected")

# Walk the entire subtree (breadth-first by default)
for widget in self.walk_children(Widget):
    if isinstance(widget, DataTable):
        widget.clear()

# Selector syntax quick reference:
# "#my-id"       → by id attribute
# ".my-class"    → by CSS class
# "Button"       → by widget type (matches subclasses too)
# "Screen Label" → descendant combinator
# "Input:focus"  → pseudo-class
# "Label, Button"→ comma = OR
```

---

### TCSS Styling

TCSS files use the `.tcss` extension. Type selectors match Python class names (including subclasses). Pseudo-classes: `:hover`, `:focus`, `:disabled`, `:dark`, `:light`, `:first-child`, `:last-child`, `:even`, `:odd`. No browser-style cascade — most specific rule wins.

```css
/* my_app.tcss */

/* Type selector — applies to all Label widgets */
Label {
    color: $text;
    padding: 1 2;
}

/* ID selector */
#status-label {
    background: $panel;
    border: round $accent;
}

/* Class + pseudo-class */
.card:hover {
    background: $panel-lighten-1;
}

/* Nesting with & (Textual supports CSS nesting) */
DataTable {
    & > .datatable--header {
        text-style: bold;
        background: $primary;
    }
    &:focus {
        border: heavy $accent;
    }
}

/* Design token variables — always prefer these for theme compatibility */
/* $primary, $secondary, $accent, $background, $panel, $text, $error  */
/* Modifiers: $primary-lighten-1, $primary-darken-2, $primary-muted    */
```

```python
# Inline style mutations — immediate, no file required
widget.styles.background = "darkblue"
widget.styles.border      = ("heavy", "white")
widget.styles.width       = "1fr"
widget.styles.height      = "100%"
widget.styles.display     = "none"       # hide; removes from layout
widget.styles.visibility  = "hidden"     # hide; preserves layout space

# CSS class helpers
widget.add_class("active")
widget.remove_class("active")
widget.toggle_class("active")
widget.set_class(condition, "active")    # add if True, remove if False
```

---

### Reactive Attributes

```python
from textual.reactive import reactive, var

class StatusPanel(Widget):
    # reactive — triggers repaint + watcher on every change
    status:    reactive[str]  = reactive("idle")
    # init=False — watcher NOT called on first mount
    connected: reactive[bool] = reactive(False, init=False)
    # repaint=False — watcher fires but no visual refresh
    _cache:    reactive[str]  = reactive("", repaint=False)
    # var — no repaint; use for non-visual state
    last_poll: var[float]     = var(0.0)
    # always_update=True — watcher fires even if value unchanged
    tick:      reactive[int]  = reactive(0, always_update=True)

    def watch_status(self, old: str, new: str) -> None:
        """Both old and new values provided."""
        self.add_class(f"status-{new}")
        self.remove_class(f"status-{old}")

    def watch_connected(self, connected: bool) -> None:
        """Single-argument watcher — only new value."""
        self.border_title = "● Connected" if connected else "○ Disconnected"

    def compute_display_status(self) -> str:
        """Computed reactive — recalculated whenever any reactive it reads changes."""
        return f"{'●' if self.connected else '○'} {self.status.upper()}"

    def validate_status(self, value: str) -> str:
        """Validator — runs before watcher; return corrected value."""
        return value if value in {"idle", "polling", "error"} else "idle"

    # Mutable reactive (list/dict) requires mutate_reactive() to trigger update
    items: reactive[list] = reactive(list)

    def add_item(self, item: str) -> None:
        self.items.append(item)
        self.mutate_reactive(StatusPanel.items)   # force watcher + repaint

# data_bind — one-way link: parent reactive → child attribute
class ParentScreen(Screen):
    is_dark: reactive[bool] = reactive(False)

    def compose(self) -> ComposeResult:
        # StatusPanel.connected will mirror ParentScreen.is_dark
        yield StatusPanel().data_bind(connected=ParentScreen.is_dark)
```

`data_bind()` links a parent reactive to a child attribute (unidirectional). `mutate_reactive()` forces a refresh when a mutable object (list, dict) is modified in-place.

---

### Events and Messages

```python
from textual import on, events
from textual.widgets import Button, Input

class SearchBar(Widget):
    # Custom message as an inner class — idiomatic Textual pattern
    class Submitted(Message):
        def __init__(self, query: str) -> None:
            self.query = query
            super().__init__()

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search...", id="search-input")
        yield Button("Go", id="go-btn")

    # Handler by naming convention: on_<widget>_<event>
    def on_button_pressed(self, event: Button.Pressed) -> None:
        query = self.query_one("#search-input", Input).value
        self.post_message(self.Submitted(query))  # bubble up to parent

    # @on with CSS selector — scoped to a specific widget
    @on(Input.Submitted, "#search-input")
    def handle_enter(self, event: Input.Submitted) -> None:
        self.post_message(self.Submitted(event.value))
        event.stop()             # stop bubbling up the DOM
        event.prevent_default()  # suppress default Input behaviour


class ResultsScreen(Screen):
    # Handler for custom message: on_<OuterClass>_<MessageClass> (snake_case)
    def on_search_bar_submitted(self, event: SearchBar.Submitted) -> None:
        self.run_search(event.query)

    def on_key(self, event: events.Key) -> None:
        if event.key == "ctrl+r":
            self.refresh()
```

**Handler naming:** `Button.Pressed` → `on_button_pressed`. `SearchBar.Submitted` → `on_search_bar_submitted`. Events bubble up the DOM. `event.stop()` halts bubbling; `event.prevent_default()` suppresses base-class handlers.

---

### Screens and Modal Dialogs

```python
from textual.screen import Screen, ModalScreen

# --- Standard Screen parameterized by return type ---
class DeviceScreen(Screen[str]):
    BINDINGS  = [("escape", "app.pop_screen", "Back")]
    AUTO_FOCUS = "ListView"   # CSS selector auto-focused on activation

    def compose(self) -> ComposeResult:
        yield Header()
        yield ListView(id="device-list")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.dismiss(str(event.item.id))   # pop screen, deliver value to caller


# --- Modal Screen — blocks parent bindings, dims background ---
class ConfirmDialog(ModalScreen[bool]):
    DEFAULT_CSS = """
    ConfirmDialog {
        align: center middle;
        & > Vertical {
            background: $panel;
            border: thick $warning;
            width: 60;
            height: auto;
            padding: 1 2;
        }
    }
    """
    BINDINGS = [("escape", "dismiss_false", "Cancel")]

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"[bold]{self.message}[/bold]")
            with Horizontal():
                yield Button("Confirm", id="confirm", variant="warning")
                yield Button("Cancel",  id="cancel",  variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm")

    def action_dismiss_false(self) -> None:
        self.dismiss(False)


# --- Using screens from App ---
class MyApp(App):
    SCREENS = {"devices": DeviceScreen}       # push by name: self.push_screen("devices")
    MODES   = {"monitor": MonitorScreen,      # switch_mode swaps the entire stack
               "config":  ConfigScreen}

    async def select_device(self) -> None:
        # push_screen_wait: push and await the dismissed value
        device_id = await self.push_screen_wait(DeviceScreen())
        if device_id:
            self.connect(device_id)

    async def confirm_delete(self, name: str) -> None:
        ok = await self.push_screen_wait(ConfirmDialog(f"Delete {name!r}?"))
        if ok:
            self.delete_device(name)
```

---

### Actions

```python
from textual.binding import Binding

class MyApp(App):
    BINDINGS = [
        ("q",       "quit",          "Quit"),
        Binding("ctrl+s", "save",    "Save",        show=True, priority=True),
        Binding("f5",     "refresh", "Refresh"),
        # Action with argument — calls action_sort("name")
        Binding("n",      "sort('name')", "Sort by name"),
    ]

    def action_save(self) -> None:
        self.save_state()
        self.notify("Saved", severity="information")

    def action_sort(self, column: str) -> None:
        self.query_one(DataTable).sort(column)

    def check_action(self, action: str, parameters: tuple) -> bool | None:
        """Return False to disable, None/True to enable."""
        if action == "save" and not self._has_changes:
            return False
        return True

# Actions in markup — clickable links inside Label / Markdown:
# yield Label("[link=app.refresh]Click to refresh[/link]")
# yield Label("[@click=app.sort('name')]Sort by name[/@click]")
```

Built-in actions: `action_quit`, `action_toggle_dark`, `action_push_screen`, `action_focus_next`, `action_bell`.

---

### Workers (Background Tasks)

```python
from textual.worker import get_current_worker, Worker, WorkerState
from textual import work
import time, threading

class PollingWidget(Widget):

    # --- Async worker (event loop; use for async I/O) ---
    @work(exclusive=True)           # cancels previous call before starting new
    async def fetch_data(self) -> None:
        async with httpx.AsyncClient() as client:
            response = await client.get(self.url)
        # Already on the event loop — update UI directly
        self.query_one(Label).update(response.text)

    # --- Thread worker (OS thread; use for blocking I/O) ---
    @work(thread=True, group="polling", exit_on_error=False)
    def poll_device(self) -> None:
        worker = get_current_worker()
        while not worker.is_cancelled:     # cooperative cancellation check
            data = self.device.snmp_get(self.oid)
            self.post_message(self.DataReceived(data))   # thread-safe
            time.sleep(self.interval)

    class DataReceived(Message):
        def __init__(self, data: dict) -> None:
            self.data = data
            super().__init__()

    def on_polling_widget_data_received(self, msg: DataReceived) -> None:
        self.update_display(msg.data)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state == WorkerState.ERROR:
            self.notify(str(event.worker.error), severity="error")

    def on_mount(self) -> None:
        self.set_interval(5, self.fetch_data)          # repeat every 5s
        self.poll_device()                              # start thread

    def on_unmount(self) -> None:
        self.workers.cancel_group(self, "polling")     # clean up threads

# call_from_thread — schedule a UI call from a plain threading.Thread
@work(thread=True)
def blocking_work(self) -> None:
    result = slow_computation()
    self.app.call_from_thread(self.on_result, result)
```

**States:** `PENDING → RUNNING → SUCCESS | ERROR | CANCELLED`

---

### Layout and Containers

```python
from textual.containers import (
    Vertical, Horizontal, Grid,
    VerticalScroll, HorizontalScroll,
    Center, Middle,
)

class LayoutDemo(Screen):
    CSS = """
    /* FR units split remaining space proportionally */
    .sidebar { width: 30%; min-width: 20; }
    .main    { width: 1fr; }
    .header  { height: 3; dock: top; }    /* docked: outside normal flow */
    .footer  { height: 1; dock: bottom; }

    /* Grid */
    #metric-grid {
        layout: grid;
        grid-size: 3 2;           /* 3 columns × 2 rows */
        grid-columns: 1fr 1fr 1fr;
        grid-gutter: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Title", classes="header")
            with Horizontal():
                with VerticalScroll(classes="sidebar"):
                    yield DeviceList()
                with Vertical(classes="main"):
                    yield MetricsPanel()
            yield StatusBar(classes="footer")

        # Center horizontally + vertically
        with Center():
            with Middle():
                yield LoadingIndicator()

        # Auto grid of widgets
        with Grid(id="metric-grid"):
            for metric in self.metrics:
                yield MetricCard(metric)
```

| Container | Layout | Scrollable |
|-----------|--------|-----------|
| `Vertical` | top-to-bottom | no |
| `Horizontal` | left-to-right | no |
| `Grid` | grid | no |
| `VerticalScroll` | vertical | Y-axis |
| `HorizontalScroll` | horizontal | X-axis |
| `Center` | — | no (horizontal centering) |
| `Middle` | — | no (vertical centering) |
| `ItemGrid` | grid | no (auto columns with `min_column_width`) |

---

### DataTable

```python
from textual.widgets import DataTable
from rich.text import Text

class ProcessTable(Widget):
    def compose(self) -> ComposeResult:
        yield DataTable(
            id="proc-table",
            zebra_stripes=True,
            show_cursor=True,
            cursor_type="row",     # "cell", "row", "column", or "none"
            header_height=1,
        )

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_column("PID",     key="pid",     width=8)
        table.add_column("Command", key="command",  width=None)  # flexible
        table.add_column("CPU%",    key="cpu",      width=6)
        table.add_column("Status",  key="status",   width=10)

    def refresh_rows(self, processes: list[dict]) -> None:
        table = self.query_one(DataTable)
        current_keys = set(table.rows)
        new_keys = set()

        for proc in processes:
            row_key = str(proc["pid"])
            new_keys.add(row_key)

            # Rich Text for coloured cells
            status_text = Text(proc["status"])
            status_text.stylize("green" if proc["status"] == "running" else "red")

            if row_key not in current_keys:
                # add_row: key= enables update_cell later
                table.add_row(
                    proc["pid"], proc["command"],
                    f"{proc['cpu']:.1f}", status_text,
                    key=row_key,
                )
            else:
                # In-place update — avoids flicker and preserves scroll
                table.update_cell(row_key, "cpu",    f"{proc['cpu']:.1f}")
                table.update_cell(row_key, "status", status_text)

        # Remove rows that no longer exist
        for stale in current_keys - new_keys:
            table.remove_row(stale)

        table.sort("cpu", reverse=True)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.post_message(self.ProcessSelected(str(event.row_key)))
```

---

### Command Palette

```python
from textual.command import Provider, Hit, Hits, DiscoveryHit
from functools import partial

class DeviceProvider(Provider):
    """Adds device commands to the Ctrl+P command palette."""

    async def startup(self) -> None:
        """Called once when the palette opens — load expensive data here."""
        self._devices = await self.app.fetch_devices()

    async def search(self, query: str) -> Hits:
        """Async generator — yield Hit for each matching result."""
        matcher = self.matcher(query)
        for device in self._devices:
            score = matcher.match(device.name)
            if score > 0:
                yield Hit(
                    score,                               # higher = ranked first
                    matcher.highlight(device.name),      # Rich Text with match chars highlighted
                    partial(self.app.connect, device),   # callable on selection
                    help=f"{device.ip} — {device.type}",
                )

    async def discover(self) -> Hits:
        """Shown before user types anything — surface top-level shortcuts."""
        for device in self._devices[:5]:
            yield DiscoveryHit(
                device.name,
                partial(self.app.connect, device),
                help=device.ip,
            )


class MyApp(App):
    COMMANDS = {DeviceProvider}            # multiple providers are merged
    COMMAND_PALETTE_BINDING = "ctrl+p"     # default; override here if needed
```

---

### Animation

```python
class AnimatedPanel(Widget):
    def slide_in(self) -> None:
        self.animate(
            "offset_x",        # CSS property name (underscores not hyphens)
            value=0,
            duration=0.3,
            easing="out_cubic",
        )

    def fade_out(self) -> None:
        self.animate(
            "opacity",
            value=0.0,
            duration=0.2,
            easing="in_expo",
            on_complete=self.remove,   # callback fires after animation ends
        )

    def pulse(self) -> None:
        # Chain via on_complete
        def step2():
            self.animate("opacity", value=1.0, duration=0.2)
        self.animate("opacity", value=0.3, duration=0.2, on_complete=step2)

# Available easing functions:
# "linear", "in_cubic", "out_cubic", "in_out_cubic"
# "in_expo", "out_expo", "in_back", "out_back", "in_bounce", "out_bounce"
```

---

### Testing

```python
import pytest

async def test_search_submit():
    async with MyApp().run_test(size=(120, 40)) as pilot:
        await pilot.press("tab")             # move focus
        await pilot.press("n", "m", "s")     # type characters
        await pilot.press("enter")           # submit

        await pilot.click("#go-button")      # click by CSS selector
        await pilot.pause(0.1)               # wait for async workers / animations

        label = pilot.app.query_one("#status", Label)
        assert "Connected" in str(label.renderable)

        await pilot.resize_terminal(80, 24)
        await pilot.pause()

# Snapshot testing (requires pytest-textual-snapshot)
def test_main_screen_snapshot(snap_compare):
    """Run with --snapshot-update to create/update the reference SVG."""
    assert snap_compare(MyApp())
```

**Pilot methods:** `press(*keys)`, `click(selector, offset, times)`, `double_click()`, `hover(selector)`, `pause(delay)`, `resize_terminal(w, h)`, `wait_for_animation()`, `exit(result)`.

---

## Important Classes — Key Members

### `App`
| Member | Description |
|--------|-------------|
| `CSS` / `CSS_PATH` | Inline CSS or path to `.tcss` |
| `BINDINGS` | List of `Binding` or `(key, action, desc)` tuples |
| `SCREENS` | Named screens available app-wide |
| `MODES` | Named mode → screen mapping |
| `COMMANDS` | Set of `CommandProvider` subclasses |
| `title` / `sub_title` | Displayed in Header |
| `run(inline=False)` | Start the app |
| `exit(result, return_code)` | Terminate gracefully |
| `push_screen(screen, callback)` | Push onto screen stack |
| `pop_screen()` | Remove top screen |
| `switch_screen(screen)` | Replace top screen |
| `push_screen_wait(screen)` | Push and await dismiss result |
| `switch_mode(mode)` | Switch named mode |
| `notify(message, severity, timeout)` | Show Toast notification |
| `suspend()` | Context manager: pause for subprocess |

### `Widget`
| Member | Description |
|--------|-------------|
| `DEFAULT_CSS` | Embedded default CSS |
| `BINDINGS` | Widget-level key bindings |
| `can_focus` | Whether widget accepts focus |
| `loading` | Show/hide LoadingIndicator overlay |
| `disabled` | Disable interaction |
| `compose()` | Define child widgets |
| `render()` | Return widget content |
| `mount(*widgets)` | Dynamically add children |
| `remove()` | Remove from DOM |
| `focus()` / `blur()` | Set/clear focus |
| `animate(attr, value, duration, easing)` | Animate a style property |
| `query(selector)` | Return `DOMQuery` of descendants |
| `query_one(selector, type)` | Return single matching widget |
| `post_message(msg)` | Send message to this widget |
| `add_class(*names)` / `remove_class(*names)` | Modify CSS classes |
| `data_bind(**bindings)` | Bind parent reactives |
| `scroll_visible()` | Ensure widget is in view |

### `Screen`
| Member | Description |
|--------|-------------|
| `AUTO_FOCUS` | CSS selector for auto-focused widget on activation |
| `TITLE` / `SUB_TITLE` | Override app title for this screen |
| `dismiss(result)` | Pop screen, pass result to callback |
| `maximize(widget)` | Expand widget to fill screen |
| `focus_next/previous(selector)` | Navigate focus |

---

## CSS Properties Quick Reference

### Layout
| Property | Values |
|----------|--------|
| `layout` | `vertical`, `horizontal`, `grid` |
| `display` | `block`, `none` |
| `dock` | `top`, `right`, `bottom`, `left` |
| `position` | `relative`, `absolute` |
| `offset` | `<scalar> <scalar>` |
| `layers` | `<name>...` |
| `layer` | `<name>` |
| `align` | `<horizontal> <vertical>` |
| `content-align` | `<horizontal> <vertical>` |

### Grid
| Property | Values |
|----------|--------|
| `grid-size` | `<int> [<int>]` (columns × rows) |
| `grid-columns` | `<scalar>...` (fr, %, auto, px) |
| `grid-rows` | `<scalar>...` |
| `grid-gutter` | `<scalar> [<scalar>]` |
| `column-span` / `row-span` | `<integer>` |

### Dimensions
`width`, `height`, `min-width`, `max-width`, `min-height`, `max-height` — supports px, %, fr, vw/vh, auto.
`box-sizing`: `border-box` (default) or `content-box`.

### Spacing
`padding`, `margin` — 1–4 values (top right bottom left).

### Visual
| Property | Description |
|----------|-------------|
| `background` | Hex, rgb(), hsl(), named, `transparent` |
| `color` | Text foreground |
| `opacity` | 0.0–1.0 widget opacity |
| `text-opacity` | Text-only opacity |
| `visibility` | `visible` or `hidden` (preserves layout space) |

### Border
| Property | Description |
|----------|-------------|
| `border` | `<border-type> <color>` — outer, takes space |
| `outline` | `<border-type> <color>` — drawn inside, no space taken |
| `border-title-align` | `left`, `center`, `right` |

Border types: `ascii`, `blank`, `dashed`, `double`, `heavy`, `hidden`, `hkey`, `inner`, `none`, `outer`, `panel`, `round`, `solid`, `tall`, `thick`, `vkey`, `wide`.

### Text
| Property | Values |
|----------|--------|
| `text-align` | `left`, `center`, `right`, `justify`, `start`, `end` |
| `text-style` | `bold`, `italic`, `underline`, `reverse`, `strike` |
| `text-overflow` | `fold`, `ellipsis`, `ignore` |
| `text-wrap` | `wrap`, `nowrap` |

### Scrolling
| Property | Values |
|----------|--------|
| `overflow` | `auto`, `hidden`, `scroll` |
| `overflow-x` / `overflow-y` | Per-axis |
| `scrollbar-size` | Width/height of scrollbar |
| `scrollbar-gutter` | `auto` or `stable` |

---

## Events System Overview

### Handler Naming Convention
`on_<message_class_snake_case>` — e.g., `on_button_pressed` for `Button.Pressed`.
Use `@on(MessageType, "css-selector")` decorator for precise targeting.

### Built-in Event Categories

**Lifecycle:** `Load`, `Mount`, `Unmount`, `Show`, `Hide`, `Ready`, `Compose`
**Focus:** `Focus`, `Blur`, `DescendantFocus`, `DescendantBlur`, `AppFocus`, `AppBlur`
**Keyboard:** `Key` (`.key`, `.character`, `.name`, `.is_printable`, `.aliases`), `Paste`
**Mouse:** `MouseMove`, `MouseDown`, `MouseUp`, `Click` (`.chain` for multi-click), `Enter`, `Leave`, `MouseScrollUp/Down/Left/Right`
**Screen:** `Resize`, `ScreenSuspend`, `ScreenResume`
**Other:** `Print`, `Idle`, `Timer`, `TextSelected`

### Custom Messages

```python
class MyWidget(Widget):
    class StatusChanged(Message):
        def __init__(self, status: str):
            self.status = status
            super().__init__()

    def change_status(self, s: str):
        self.post_message(self.StatusChanged(s))

# Parent handler:
def on_my_widget_status_changed(self, event: MyWidget.StatusChanged): ...
```

---

## Container Widgets

| Container | Layout | Scrollable |
|-----------|--------|-----------|
| `Vertical` | vertical | no |
| `Horizontal` | horizontal | no |
| `Grid` | grid | no |
| `VerticalScroll` | vertical | Y-axis |
| `HorizontalScroll` | horizontal | X-axis |
| `ScrollableContainer` | vertical | both |
| `Center` | — | no (horizontal centering) |
| `Middle` | — | no (vertical centering) |
| `ItemGrid` | grid | no (auto columns with `min_column_width`) |

---

## Validation (textual.validation)

| Validator | Description |
|-----------|-------------|
| `Number(minimum, maximum)` | Numeric value in range |
| `Integer(minimum, maximum)` | Integer value in range |
| `Length(minimum, maximum)` | String length in range |
| `Regex(regex, flags)` | Full regex match |
| `URL()` | Valid URL with scheme |
| `Function(callable)` | Custom validation logic |

---

## Testing

```python
async def test_my_app():
    async with MyApp().run_test(size=(80, 24)) as pilot:
        await pilot.press("tab")
        await pilot.click("#submit-button")
        await pilot.pause()
        assert app.result == "expected"
```

**Pilot methods:** `press(*keys)`, `click(selector, offset, times)`, `double_click()`, `hover(selector)`, `pause(delay)`, `resize_terminal(w, h)`, `wait_for_animation()`, `exit(result)`.

Snapshot testing via `pytest-textual-snapshot` — generates SVG screenshots for visual regression.

---

## Devtools

| Command | Description |
|---------|-------------|
| `textual run app.py` | Run a Textual app |
| `textual run --dev app.py` | Dev mode with live CSS reload |
| `textual serve app.py` | Serve as web application |
| `textual console` | Open debug console |
| `textual console -v` | Verbose (all events) |
| `from textual import log; log(data)` | Pretty-print to debug console |
| `self.log(data)` | Log from within App/Widget |
