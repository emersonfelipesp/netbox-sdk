# Toad — Unified AI Agent TUI

**Repository:** https://github.com/batrachianai/toad
**Author:** Will McGugan (creator of Textual, Rich, Toolong)
**Organization:** batrachianai
**Language:** Python
**Framework:** Textual
**Homepage:** https://www.batrachian.ai/
**Stars:** ~2,665

---

## What It Does

Toad is a unified terminal interface for AI coding agents. Instead of switching between Claude Code, Gemini CLI, OpenHands, GitHub Copilot, and others, Toad provides a single TUI that connects to all of them through a standard protocol (ACP — Agent Client Protocol).

It pairs a full interactive shell with an AI prompt editor — so you can run shell commands and issue AI instructions in the same workflow.

---

## Supported Agents

Via the ACP (Agent Client Protocol) standard:
- Claude / Claude Code
- Gemini CLI
- OpenAI Codex CLI
- OpenHands
- GitHub Copilot
- And more via the built-in "AI App Store"

---

## Key Features

### Toad Shell
A fully functional integrated shell — not a subprocess launcher, a real PTY:
- Full-color output
- Interactive commands work (vim, htop, etc.)
- `cd` and environment variables **persist** across commands
- This is the key differentiator: most agent UIs can't do this

### Prompt Editor
- Markdown editor with syntax highlighting for code fences
- Full mouse support
- Configurable keybindings

### File Picker
- Press `@` to trigger a fuzzy file picker
- `Tab` switches to interactive tree view
- Filters as you type
- Selected file paths inserted into prompt

### Beautiful Diffs
- Side-by-side or unified diffs
- Syntax highlighting for most programming languages

### Markdown Rendering
- Streaming Markdown output as agents respond
- Syntax-highlighted code fences
- Tables, block quotes, lists — all rendered correctly in-terminal

### Concurrent Sessions
- Run multiple agents from different providers simultaneously
- `Ctrl+S` shows all active agent states
- `Ctrl+R` resumes previous sessions

### AI App Store
- Browse, install, and launch agent integrations directly from the UI
- Based on ACP (Agent Client Protocol)

### Settings UI
- In-TUI settings editor (no manual JSON/YAML editing)
- Minimal UI mode available
- Highly configurable

### Web Server Mode
```bash
toad serve
```
Exposes Toad as a web application accessible from a browser — useful for remote access without SSH.

---

## Platform Support

| Platform | Support |
|----------|---------|
| Linux | Full |
| macOS | Full |
| Windows | Via WSL (native on roadmap) |
| Recommended terminal | Ghostty |

Linux clipboard requires `xclip`: `sudo apt install xclip`

---

## Installation

```bash
# Quickstart (recommended)
curl -fsSL batrachian.ai/install | sh

# via uv
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install -U batrachian-toad --python 3.14

# via conda-forge / pixi
pixi global install batrachian-toad
```

---

## Usage

```bash
# Launch Toad
toad

# Open with specific project directory
toad ~/projects/my-app

# Skip agent selection, start with specific agent
toad -a open-hands

# Run as web application
toad serve

# Help
toad --help
```

---

## Architecture & Design Decisions

### Framework: Textual
Toad is written by the creator of Textual — it represents the most advanced and idiomatic use of the framework. Study it to understand Textual's limits and best patterns.

### Agent Client Protocol (ACP)
ACP is an open standard for connecting UI clients to AI agents. Toad implements it as both a consumer (UI side) and publisher (agent discovery). This means any ACP-compatible agent automatically works in Toad — no per-agent glue code.

### Real PTY Shell
The shell uses a real pseudo-terminal (PTY) rather than subprocess capture. This enables:
- Interactive programs (vim, fzf, htop work inside it)
- Persistent `cd` and env var state
- Full ANSI escape code support
- No special-casing for interactive vs non-interactive commands

### Streaming Markdown
Response text is rendered incrementally as it streams from agents. The Markdown renderer is designed to handle partially-complete documents gracefully.

### Session Persistence
Sessions are persisted to disk and resumable via `Ctrl+R`. This implies a local session store (likely SQLite or flat files) tracking conversation history and agent state.

### Web Mode Architecture
`toad serve` runs the full TUI as a web app — likely via Textual's built-in web rendering capability (`textual serve` command), which renders the TUI as a web application using a WebSocket-backed canvas.

---

## Roadmap Items

- MCP (Model Context Protocol) server UI
- Model selection in-TUI
- Windows native support
- Built-in code editor
- Sidebar widgets
- Git integration

---

## Textual Code Patterns

### 1. App with `MODES`, `SCREENS`, reactives, and `var(toggle_class=...)`

```python
# src/toad/app.py
class ToadApp(App, inherit_bindings=False):
    CSS_PATH = "toad.tcss"

    # Named screens — pushed via action_settings() / action_sessions()
    SCREENS = {"settings": get_settings_screen, "sessions": get_sessions_screen}
    # Named modes — full screen replacements via switch_mode()
    MODES   = {"store": get_store_screen}

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("ctrl+q",       "quit",              show=False, priority=True),
        Binding("ctrl+c",       "help_quit",         show=False, system=True),
        Binding("ctrl+s",       "sessions",          "Sessions"),
        Binding("f1",           "toggle_help_panel", "Help",     priority=True),
        Binding("f2,ctrl+comma","settings",          "Settings"),
    ]

    # Reactive attributes — changes trigger watch_* methods
    column:       reactive[bool] = reactive(False)
    column_width: reactive[int]  = reactive(100)
    scrollbar:    reactive[str]  = reactive("normal")
    update_required: reactive[bool] = reactive(False)

    # var with toggle_class — auto-toggles a CSS class on the app node
    show_sessions = var(False, toggle_class="-show-sessions-bar")

    HORIZONTAL_BREAKPOINTS = [(0, "-narrow"), (100, "-wide")]
    PAUSE_GC_ON_SCROLL = True
```

**What this shows:** `MODES` vs `SCREENS` distinction — modes replace the entire screen stack (like switching app sections), while `SCREENS` are pushed on top. `var(toggle_class="-show-sessions-bar")` auto-applies/removes a CSS class on the app when the var flips — a declarative way to drive visibility without imperative `add_class`/`remove_class`. `HORIZONTAL_BREAKPOINTS` defines responsive breakpoints that add CSS classes at specified terminal widths.

---

### 2. `on_mount` — async DB init, deferred timers, initial mode

```python
# src/toad/app.py
async def on_load(self) -> None:
    """Runs before the DOM is built — good for loading config/DB."""
    db = await self.get_db()
    await db.create()
    if settings_path.exists():
        settings = json.loads(settings_path.read_text("utf-8"))
    self._settings = settings

async def on_mount(self) -> None:
    self.capture_event("toad-run")
    if mode := self._initial_mode:
        self.switch_mode(mode)     # jump directly to a named mode
    else:
        await self.new_session_screen(self.get_main_screen)
    self.set_timer(1, self.run_version_check)   # deferred version check

@work(exit_on_error=False)
async def run_version_check(self) -> None:
    from toad.version import check_version
    update_required, version_meta = await check_version()
    self.version_meta = version_meta
    self.update_required = update_required   # reactive triggers watch chain
```

**What this shows:** `on_load` fires before mounting — ideal for async I/O that must complete before the DOM builds (config, DB schema creation). `set_timer(1, callback)` delays a non-critical check by 1 second so it doesn't block startup. `exit_on_error=False` on a worker suppresses unhandled exceptions from crashing the app — useful for optional background checks.

---

### 3. Double-Ctrl+C quit guard

```python
# src/toad/app.py
last_ctrl_c_time = reactive(0.0)

def action_help_quit(self) -> None:
    """Require two Ctrl+C presses within 5 seconds to quit."""
    if (time := monotonic()) - self.last_ctrl_c_time <= 5.0:
        self.exit()
    self.last_ctrl_c_time = time
    self.notify(
        "Press [b]ctrl+c[/b] again to quit the app",
        title="Do you want to quit?",
    )
```

**What this shows:** A two-press quit guard using `monotonic()` timestamps stored in a reactive. The first press sets the timestamp and shows a notification; the second press within 5 seconds exits. `system=True` on the binding gives it highest priority so it fires before any child widget can consume `ctrl+c`.

---

### 4. Command palette `Provider` for dynamic AI agent list

```python
# src/toad/screens/main.py
class ModeProvider(Provider):
    """Populates the command palette with available AI agent modes."""

    async def search(self, query: str) -> Hits:
        matcher = self.matcher(query)
        for mode in sorted(screen.conversation.modes.values(), key=lambda m: m.name):
            score = matcher.match(mode.name)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(mode.name),          # Rich-highlighted match
                    partial(screen.conversation.set_mode, mode.id),  # action callback
                    help=mode.description,
                )
```

**What this shows:** `Provider` is the base class for command palette entries. `search()` is an async generator — yield `Hit` objects scored by the fuzzy `matcher`. `matcher.highlight()` returns a Rich `Text` with matched characters highlighted. The third argument to `Hit` is any callable — here a `partial` that switches the agent mode when the user selects it.

---

### 5. `data_bind()` — propagate reactives from screen into child widgets

```python
# src/toad/screens/main.py
class MainScreen(Screen, can_focus=False):
    AUTO_FOCUS = "Conversation Prompt TextArea"
    CSS_PATH   = "main.tcss"
    COMMANDS   = {ModeProvider}

    column       = reactive(False)
    column_width = reactive(100)

    def compose(self) -> ComposeResult:
        with containers.Center():
            yield SideBar(
                SideBar.Panel("Plan",    Plan([])),
                SideBar.Panel("Project", ProjectDirectoryTree(
                    self.project_path, id="project_directory_tree"), flex=True),
            )
            yield Conversation(
                self.project_path, self._agent, self._agent_session_id, self._session_pk,
            ).data_bind(
                # Bind Conversation.project_path ← MainScreen.project_path
                project_path=MainScreen.project_path,
                # Bind Conversation.column ← MainScreen.column
                column=MainScreen.column,
            )
        yield Footer()
```

**What this shows:** `widget.data_bind(child_attr=ParentClass.parent_attr)` creates a one-way reactive link — when `MainScreen.column` changes, `Conversation.column` automatically updates without manual `watch_*` wiring. This is Textual's idiomatic way to propagate shared state down the widget tree.

---

### 6. PTY Terminal widget — `ScrollView` with ANSI state machine

```python
# src/toad/widgets/terminal.py
class Terminal(ScrollView, can_focus=True):
    """Embeds a real PTY as a scrollable Textual widget."""

    hide_cursor = reactive(False)

    @dataclass
    class Finalized(Message):
        terminal: Terminal

    @dataclass
    class AlternateScreenChanged(Message):
        terminal: Terminal
        enabled: bool

    def __init__(self, minimum_terminal_width=0, **kwargs):
        super().__init__(**kwargs)
        self.state = ansi.TerminalState(self.write_process_stdin)
        self._width  = minimum_terminal_width or 80
        self._height = 24
        # LRU cache avoids re-rendering unchanged lines on every scroll
        self._terminal_render_cache: LRUCache[tuple, Strip] = LRUCache(1024)

    def set_write_to_stdin(self, write: Callable[[str], Awaitable]) -> None:
        """Inject the PTY stdin writer — called once the process starts."""
        self._write_to_stdin = write

    def finalize(self) -> None:
        """Process exited — freeze the widget and notify parent."""
        if not self._finalized:
            self._finalized = True
            self.state.show_cursor = False
            self.add_class("-finalized")
            self._terminal_render_cache.clear()
            self.refresh()
            self.blur()
            self.post_message(self.Finalized(self))

    def notify_style_update(self) -> None:
        """Theme changed — invalidate render cache and repaint."""
        self._terminal_render_cache.clear()
        super().notify_style_update()
```

**What this shows:** The terminal extends `ScrollView` (not `Widget`) to get free scrolling. An ANSI state machine (`ansi.TerminalState`) parses raw PTY output into a virtual screen buffer. An LRU cache on `(line_index, style_hash)` avoids re-rendering lines that haven't changed — critical for scroll performance. `Finalized` and `AlternateScreenChanged` are custom `Message` subclasses that bubble up to parent widgets.

---

### 7. Streaming Markdown — `MarkdownStream.write()` for token-by-token output

```python
# src/toad/widgets/agent_response.py
class AgentResponse(ConversationMarkdown):
    """Textual Markdown widget that accepts incremental token writes."""

    DEFAULT_CLASSES = "block"
    block_cursor_offset = var(-1)

    def __init__(self, markdown: str | None = None) -> None:
        super().__init__(markdown)
        self._stream: MarkdownStream | None = None

    @property
    def stream(self) -> MarkdownStream:
        """Lazily create the MarkdownStream on first write."""
        if self._stream is None:
            self._stream = self.get_stream(self)
        return self._stream

    async def append_fragment(self, fragment: str) -> None:
        """Called for each token as the LLM streams its response."""
        self.loading = False          # hide loading indicator on first token
        await self.stream.write(fragment)

    def block_cursor_up(self) -> Widget | None:
        """Navigate up through rendered Markdown blocks (code, paragraphs…)."""
        if self.block_cursor_offset == -1:
            self.block_cursor_offset = len(self.children) - 1
        else:
            self.block_cursor_offset -= 1
        try:
            return self.children[self.block_cursor_offset]
        except IndexError:
            self.block_cursor_offset = -1
            return None
```

**What this shows:** `MarkdownStream` is a Textual built-in that accepts partial Markdown text and re-renders incrementally — ideal for LLM streaming output. `self.loading = False` on the first token hides Textual's built-in spinner. Block cursor navigation (`block_cursor_up/down`) walks the rendered Markdown DOM — each code fence, paragraph, and list is a child widget.

---

## Lessons for NMS-CLI

| Pattern | How Toad Does It | Applicability |
|---------|------------------|--------------|
| Real PTY shell integration | PTY subprocess, persistent env/cwd | Embed a real shell in NMS TUI |
| Protocol-based agent connections | ACP standard | Protocol-based device adapters |
| Streaming output rendering | Incremental Markdown renderer | Streaming command output display |
| Session persistence & resume | `Ctrl+R` session restore | Save/restore NMS sessions |
| Web mode | `toad serve` via Textual web | Remote access to NMS TUI via browser |
| File picker with `@` | Fuzzy picker + tree view | Config/log file selector in NMS |
| Concurrent agent sessions | Multi-pane simultaneous agents | Multi-device simultaneous sessions |
| In-TUI settings | No JSON editing needed | Settings modal in NMS-CLI |
