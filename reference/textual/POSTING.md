# Posting — HTTP Client TUI

**Repository:** https://github.com/darrenburns/posting
**Author:** Darren Burns (Textual core contributor)
**License:** Apache-2.0
**Language:** Python
**Framework:** Textual
**Homepage:** https://posting.sh
**Stars:** ~11,589

---

## What It Does

Posting is a terminal-based HTTP client — the keyboard-driven equivalent of Postman or Insomnia. Requests are stored as plain YAML files, making them version-controllable alongside your code. It runs fully in the terminal, including over SSH.

---

## Key Features

### Request Management
- Create, edit, and organize HTTP requests (GET, POST, PUT, DELETE, PATCH, etc.)
- Requests stored as simple YAML files — commit them alongside your codebase
- Import from Postman collections and OpenAPI specs
- Import curl commands by pasting into the URL bar
- Export requests as cURL commands

### Navigation & UX
- **Jump mode** — keyboard-driven UI navigation: press a key to jump to any widget
- **Command palette** — quick access to all functionality (`Ctrl+P`)
- **Vim keybindings** — plus fully customizable keybindings
- Open requests/responses in `$EDITOR` or `$PAGER`
- Full mouse support

### Editing & Display
- **Syntax highlighting** via tree-sitter integration (request bodies, response bodies)
- **Autocompletion** for headers, methods, environment variables
- User-defined **themes**

### Environments & Variables
- Multiple named environments (dev, staging, prod)
- Variable substitution in URLs, headers, and bodies
- Switch environments without editing files

### Scripting Hooks
Run Python code before and after requests:
```python
# pre_request.py
def before_request(request):
    request.headers["X-Timestamp"] = str(time.time())

# post_request.py
def after_response(response):
    print(f"Response time: {response.elapsed}")
```

### SSH-Ready
Pure terminal, no GUI dependencies — works identically over SSH connections.

---

## Installation

```bash
# via uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install --python 3.13 posting

# via pipx
pipx install posting

# launch
posting
```

---

## Usage

```bash
# Open Posting TUI
posting

# Open with a specific collection directory
posting --collection ./api-requests/

# Specify environment
posting --env production
```

### YAML Request File Format
```yaml
# requests/get-users.yaml
name: Get Users
method: GET
url: "{{ base_url }}/api/users"
headers:
  Authorization: "Bearer {{ token }}"
  Accept: application/json
params:
  limit: "50"
  offset: "0"
```

---

## Architecture & Design Decisions

### Framework: Textual
Full Textual application — reactive components, keyboard-driven layout, CSS-like styling. Darren Burns is a Textual contributor, so Posting demonstrates idiomatic advanced Textual usage.

### YAML Storage
Request files are human-readable YAML — no proprietary binary format, no database. A collection is just a directory of `.yaml` files. This means:
- Git-diff friendly
- Team sharing via any VCS
- Easy programmatic generation
- Works with any text editor

### tree-sitter Syntax Highlighting
Uses tree-sitter for accurate syntax highlighting in request bodies and response panels. More accurate than regex-based highlighting, especially for nested structures (JSON, XML, GraphQL).

### Jump Mode Navigation
A unique UX pattern: press a key (e.g., `j`) to enter jump mode, then a letter overlay appears on every focusable widget. Press the overlay letter to jump directly to that widget. Eliminates the need to Tab through elements.

### Import/Export Strategy
- **In:** Postman collections, OpenAPI specs, curl (paste into URL bar)
- **Out:** cURL export from any request
This makes Posting a drop-in for teams already using Postman — migrate gradually.

---

## Textual Code Patterns

### 1. Screen reactives + `watch_*` handlers driving layout changes

```python
# src/posting/app.py
class MainScreen(Screen[None]):
    AUTO_FOCUS = None
    BINDINGS = [
        Binding("ctrl+j,alt+enter", "send_request",                "Send",             ...),
        Binding("ctrl+o",           "toggle_jump_mode",            "Jump",             ...),
        Binding("ctrl+s",           "save_request",                "Save",             ...),
        Binding("ctrl+P",           "open_request_search_palette", "Search requests",  ...),
    ]

    selected_method:    Reactive[HttpRequestMethod]              = reactive("GET",      init=False)
    current_layout:     Reactive[PostingLayout]                  = reactive("vertical", init=False)
    expanded_section:   Reactive[Literal["request","response"] | None] = reactive(None, init=False)
    _jumping:           Reactive[bool]                           = reactive(False, init=False, bindings=True)

    def watch_current_layout(self, layout: str) -> None:
        # Add a CSS class to the body — layout is controlled purely via CSS
        self.app_body.add_class(f"layout-{layout}")

    def watch_expanded_section(self, section: str | None) -> None:
        # Show/hide panels by toggling the "hidden" class
        self.request_editor.set_class(section == "response", "hidden")
        self.response_area.set_class(section == "request",   "hidden")
```

**What this shows:** `reactive(..., bindings=True)` on `_jumping` automatically refreshes key bindings when jump mode toggles — so the Footer updates without manual calls. Layout switching via `add_class(f"layout-{layout}")` delegates all visual logic to CSS instead of imperative `display` manipulation.

---

### 2. `@work(exclusive=True)` for HTTP requests

```python
# src/posting/app.py
@work(exclusive=True)
async def send_via_worker(self) -> None:
    await self.send_request()

async def send_request(self) -> None:
    async with httpx.AsyncClient(verify=verify, cert=cert, ...) as client:
        response = await client.send(request=request, follow_redirects=...)
        self.post_message(HttpResponseReceived(response))

@on(HttpResponseReceived)
def on_response_received(self, event: HttpResponseReceived) -> None:
    self.response_area.response = event.response
    self.url_bar.response_status_code = event.response.status_code
    self.cookies.update(event.response.cookies)

# Both UI triggers route to the same worker
@on(Button.Pressed, selector="SendRequestButton")
@on(Input.Submitted, selector="UrlInput")
def handle_submit_via_event(self) -> None:
    self.send_via_worker()
```

**What this shows:** `@work(exclusive=True)` cancels any in-flight request before starting a new one — so double-clicking Send doesn't queue two requests. The response flows back via `post_message(HttpResponseReceived(...))` — a clean decoupling of async HTTP work from UI update logic. Two event handlers (`Button.Pressed` and `Input.Submitted`) funneled into one worker call.

---

### 3. File watcher workers with `watchfiles.awatch`

```python
# src/posting/app.py
class Posting(App[None], inherit_bindings=False):
    BINDINGS = [
        Binding("ctrl+p", "command_palette", description="Commands",  ...),
        Binding("ctrl+c", "app.quit",        description="Quit", priority=True),
        Binding("f1",     "help",            "Help",                  ...),
    ]

    def on_mount(self) -> None:
        self.push_screen(MainScreen(collection=self.collection, ...))
        if self.environment_files:
            self.watch_environment_files()

    @work(exclusive=True, group="environment-watcher")
    async def watch_environment_files(self) -> None:
        from watchfiles import awatch
        async for changes in awatch(*self.environment_files):
            load_variables(self.environment_files, ..., avoid_cache=True)
            self.env_changed_signal.publish(None)
            self.notify(
                title="Environment changed",
                message=f"Reloaded {len(changes)} dotenv files",
            )

    @work(exclusive=True, group="collection-watcher")
    async def watch_collection_files(self) -> None:
        from watchfiles import awatch, Change
        async for changes in awatch(self.collection.path):
            for change_type, file_path in changes:
                if file_path.endswith(".py") and change_type in (Change.deleted, Change.modified):
                    uncache_module(file_path)
                    self.notify(f"Reloaded {file_name!r}", title="Script reloaded")
```

**What this shows:** `watchfiles.awatch` is an async file watcher that integrates naturally into a Textual `@work` coroutine — `async for changes in awatch(...)` yields on every filesystem event, keeping the event loop free. `group="environment-watcher"` + `exclusive=True` means hot-reloading restarts cleanly on each change without stacking.

---

### 4. Jump mode — `ModalScreen` that overlays labelled jump targets

```python
# src/posting/jump_overlay.py
class JumpOverlay(ModalScreen[str | Widget | None]):
    """Dismissed with the target widget (or None if cancelled)."""

    DEFAULT_CSS = """\
    JumpOverlay {
        background: black 25%;   /* translucent overlay */
    }
    """
    BINDINGS = [Binding("escape", "dismiss_overlay", "Dismiss", show=False)]

    def on_key(self, key_event: events.Key) -> None:
        # Block tab focus cycling inside the overlay
        if key_event.key in ("tab", "shift+tab"):
            key_event.stop()
            key_event.prevent_default()
        if self.is_active:
            target = self.keys_to_widgets.get(key_event.key)
            if target is not None:
                self.dismiss(target)   # return the target widget to the caller

    def compose(self) -> ComposeResult:
        self._sync()
        for offset, jump_info in self.overlays.items():
            label = Label(jump_info.key, classes="textual-jump-label")
            x, y = offset
            label.styles.margin = y, x    # position by pixel offset from top-left
            yield label
        with Center(id="textual-jump-info"):
            yield Label("Press a key to jump")
```

```python
# src/posting/jumper.py
class Jumper:
    def __init__(self, ids_to_keys: Mapping[str, str], screen: Screen[Any]) -> None:
        self.ids_to_keys = ids_to_keys   # {"url-input": "2", "collection-tree": "tab", ...}
        self.screen = screen

    def get_overlays(self) -> dict[Offset, JumpInfo]:
        """Walk the DOM, map each known widget to its pixel offset."""
        children: list[Widget] = screen.walk_children(Widget)
        overlays: dict[Offset, JumpInfo] = {}
        for child in children:
            try:
                widget_x, widget_y = screen.get_offset(child)
            except NoWidget:
                continue
            if child.id and child.id in self.ids_to_keys:
                overlays[Offset(widget_x, widget_y)] = JumpInfo(
                    self.ids_to_keys[child.id], child.id
                )
        return overlays
```

**What this shows:** `ModalScreen[T]` is parameterized by its return type — `self.dismiss(target)` delivers the widget to the `await self.push_screen_wait(JumpOverlay(...))` call site. `screen.get_offset(child)` returns the widget's absolute pixel position, which is then used as `label.styles.margin = y, x` to place jump-key labels precisely over each widget.

---

### 5. `on_screen_resume` — reinitialise state after returning to a screen

```python
# src/posting/app.py
def on_screen_resume(self) -> None:
    """Called every time this screen becomes active again (e.g. after closing a modal)."""
    self.jumper = Jumper(
        {
            "method-selector":               "1",
            "url-input":                     "2",
            "collection-tree":               "tab",
            "--content-tab-headers-pane":    "q",
            "--content-tab-body-pane":       "w",
            "--content-tab-response-body-pane":    "a",
            "--content-tab-response-headers-pane": "s",
        },
        screen=self,
    )
```

**What this shows:** `on_screen_resume` fires every time the screen returns to the top of the screen stack — not just on first mount. Posting rebuilds the `Jumper` here so jump targets reflect any layout changes that happened while the screen was in the background. Use this over `on_mount` when state needs to stay fresh across screen pushes.

---

## Lessons for NMS-CLI

| Pattern | How Posting Does It | Applicability |
|---------|--------------------|--------------|
| YAML-based config storage | Requests as YAML files in a directory | Device config / templates as files |
| Jump mode navigation | Letter overlays on widgets | Keyboard-first navigation in NMS TUI |
| Command palette | `Ctrl+P` fuzzy finder for all actions | Global action dispatch |
| Vim keybindings | Optional vim mode | Power user mode |
| Environments | Named env files with variable substitution | Multi-site / multi-environment support |
| Pre/post hooks | Python scripts before/after requests | Pre/post command hooks |
| tree-sitter highlighting | Accurate syntax highlighting | CLI output / config highlighting |
| SSH-friendly | Pure terminal, no GUI | NMS-CLI should be fully SSH-usable |
