# Toad — Comprehensive Visual & Design Guide

**Source:** `/root/nms/textual-projects/toad/`
**Purpose:** Design reference for NMS-CLI visual language, layout patterns, and component styling

---

## Table of Contents

1. [Color Palette & Theming](#1-color-palette--theming)
2. [Typography & Text Styling](#2-typography--text-styling)
3. [Layout System & Spacing](#3-layout-system--spacing)
4. [Border Styles & Widget Containers](#4-border-styles--widget-containers)
5. [Interactive States](#5-interactive-states)
6. [Screen & Modal Design](#6-screen--modal-design)
7. [Conversation & Content Widgets](#7-conversation--content-widgets)
8. [Input & Prompt Area](#8-input--prompt-area)
9. [Sidebar Design](#9-sidebar-design)
10. [Sessions & Tab Bar](#10-sessions--tab-bar)
11. [Settings Screen](#11-settings-screen)
12. [Store / Launcher Screen](#12-store--launcher-screen)
13. [Notifications & Flash Messages](#13-notifications--flash-messages)
14. [Animations & Motion](#14-animations--motion)
15. [Responsive Design](#15-responsive-design)
16. [Layering & Z-Index](#16-layering--z-index)
17. [Global State CSS Classes](#17-global-state-css-classes)
18. [Component Hierarchy](#18-component-hierarchy)
19. [Design Principles Summary](#19-design-principles-summary)
20. [Design Token Reference](#20-design-token-reference)
21. [Lessons for NMS-CLI](#21-lessons-for-nms-cli)

---

## 1. Color Palette & Theming

### Dracula Terminal Theme

Toad ships a Dracula terminal theme applied to PTY output rendering:

```python
# src/toad/app.py
DRACULA_TERMINAL_THEME = terminal_theme.TerminalTheme(
    background=(40, 42, 54),    # #282A36
    foreground=(248, 248, 242), # #F8F8F2
    normal=[
        (33, 34, 44),    # black   #21222C
        (255, 85, 85),   # red     #FF5555
        (80, 250, 123),  # green   #50FA7B
        (241, 250, 140), # yellow  #F1FA8C
        (189, 147, 249), # blue    #BD93F9
        (255, 121, 198), # magenta #FF79C6
        (139, 233, 253), # cyan    #8BE9FD
        (248, 248, 242), # white   #F8F8F2
    ],
    bright=[
        (98, 114, 164),  # bright black   #6272A4
        (255, 110, 110), # bright red     #FF6E6E
        (105, 255, 148), # bright green   #69FF94
        (255, 255, 165), # bright yellow  #FFFFA5
        (214, 172, 255), # bright blue    #D6ACFF
        (255, 146, 223), # bright magenta #FF92DF
        (164, 255, 255), # bright cyan    #A4FFFF
        (255, 255, 255), # bright white   #FFFFFF
    ],
)
```

### Semantic CSS Variables

Toad relies entirely on Textual's built-in CSS variable system — no hardcoded hex values in TCSS. This makes the entire UI theme-switchable.

| Variable | Usage |
|---|---|
| `$primary` | Main accent: borders, focus rings, headings |
| `$secondary` | Alternate accent: input focus, secondary borders |
| `$success` | Success states, confirmation |
| `$warning` | Warnings, cautions |
| `$error` | Errors, destructive actions |
| `$text` | Primary text |
| `$text-primary` | Emphasized / high-contrast text |
| `$text-secondary` | Muted / supporting text |
| `$text-muted` | Heavily muted, helper text |
| `$text-success` / `$text-warning` / `$text-error` | Semantic text tints |
| `$background` | Screen background |
| `$foreground` | Tint overlay (used with `%` opacity, e.g. `$foreground 10%`) |
| `$panel` | Panel / hover background (slightly lighter than `$background`) |
| `$accent` | Accent for special decorations |
| `$block-cursor-background` | Block cursor highlight |
| `$primary-muted` / `$success-muted` / `$error-muted` | Muted semantic tints |
| `$footer-description-background` | Footer key description background |

### Throbber Gradient Palette

The animated loading bar uses a continuous color sweep:

```python
# src/toad/widgets/throbber.py
COLORS = [
    "#881177", "#aa3355", "#cc6666", "#ee9944", "#eedd00",
    "#99dd55", "#44dd88", "#22ccbb", "#00bbcc", "#0099cc",
    "#3366bb", "#663399", "#881177",  # loops back to start
]
```

---

## 2. Typography & Text Styling

### Text Styles

```tcss
text-style: bold        /* Headers, emphasis */
text-style: italic      /* Subtitles, secondary info, author names */
text-style: dim         /* Disabled, muted content */
text-style: underline   /* Interactive labels, section headers */
text-style: reverse     /* Badge / tag style (border-subtitle-style) */
text-style: not bold    /* Explicitly remove bold in state variants */
```

### Text Overflow

```tcss
text-overflow: ellipsis  /* Truncate with … — default for single-line labels */
text-overflow: fold      /* Fold on expand (used in ToolCallHeader) */
text-wrap: nowrap        /* Prevent wrapping — status bars, paths */
text-wrap: wrap          /* Allow wrapping — content areas */
```

### Text Alignment

```tcss
text-align: center  /* Centered labels, icons */
text-align: right   /* Status values, counts */
```

### Text Opacity for State

```tcss
text-opacity: 100%  /* Active / focused */
text-opacity: 90%   /* Slightly reduced (tool results after completion) */
text-opacity: 30%   /* Placeholder text in prompt */
text-opacity: 0.5   /* Blurred / unfocused input */
```

---

## 3. Layout System & Spacing

### Base Unit

**1 unit = 1 character cell.** All spacing is expressed as integer multiples of this unit. There are no fractional values in practice.

### Margin Convention

The most common margin pattern is `1 1 1 0` — top/right/bottom = 1, left = 0. This creates a visual left-edge flush with a gutter on the other three sides:

```tcss
/* Standard block spacing */
.block        { margin: 1 1 1 0; }
AgentThought  { margin: 1 1 1 0; }
UserInput     { margin: 1 1 1 0; }
ShellResult   { margin: 1 1 1 0; }
ToolCall      { margin: 0 0 0 1 !important; }  /* Indented from left */
```

### Padding Patterns

```tcss
padding: 0 1        /* Tight horizontal pad — input fields, info chips */
padding: 0 1 0 0    /* Right-only — textarea alignment */
padding: 1 1 0 1    /* Three-sided — terminal tool content area */
padding: 1 0        /* Vertical only — session summaries */
padding: 0 2 0 0    /* Wide right — markdown inside user inputs */
```

### Height Strategies

```tcss
height: auto         /* Content-driven — most content widgets */
height: 1            /* Single line — status bars, session tabs */
height: 1fr          /* Fill remaining — main content areas */
height: 2            /* Two-line — tab bar with underline */
max-height: 10       /* Constrain collapsed thought panels */
max-height: 50vh     /* Viewport-relative — prompt textarea */
max-height: 100h     /* Full terminal height — maximized thoughts */
```

### Width Strategies

```tcss
width: auto          /* Content-driven */
width: 1fr           /* Fill available space */
width: 3             /* Fixed icon column */
width: 40            /* Fixed sidebar */
max-width: 45%       /* Responsive sidebar cap */
max-width: 100       /* Column mode conversation cap */
min-width: 40        /* Sidebar minimum */
grid-columns: 24 1fr /* Fixed + flexible grid */
```

---

## 4. Border Styles & Widget Containers

### Border Style Vocabulary

Toad uses Textual's named border styles with a consistent semantic mapping:

```tcss
border: tall $primary          /* Focus rings, active containers */
border: tall transparent       /* Invisible placeholder (preserves space) */
border: round $primary         /* Contained components, help panels */
border: heavy $error           /* Critical errors */
border: wide $error 50%        /* Soft error warnings */
border: panel $primary 50%     /* Tool call containers */
border: panel $error-muted     /* Error tool calls */
border: thick $primary 20%     /* Modal dialogs */
border: blank transparent      /* Space-preserving with no visual */
border: tab $primary           /* Modal-style dialog borders */
border: block black 20%        /* Store title containers */
```

### Directional Borders

Used for left-stripe "category" indicators:

```tcss
border-left: blank $primary    /* Shell results — primary category */
border-left: blank $secondary  /* User input — secondary category */
border-left: outer $text-accent /* Accent markers */
border-right: tall black 10%   /* Sidebar separator */
border-bottom: solid $foreground 10% /* Subtle section dividers */
border-top: ascii $secondary   /* ASCII-style top dividers */
```

### Background Tinting

```tcss
background: $primary 10%       /* Subtle primary tint */
background: $secondary 15%     /* User input area */
background: $foreground 4%     /* Shell result — very subtle */
background: black 10%          /* Dark overlay panels */
background: black 20%          /* Store containers */
background: $background 60%    /* Semi-transparent settings overlay */
background: transparent        /* Clear — no background */

/* Theme-conditional backgrounds */
&:dark  { background: black 10%; }
&:light { background: white 40%; }
```

### Hatch Pattern Fill

```tcss
/* Diagonal hatching for decorative backgrounds */
#container { hatch: right $primary 15%; }
```

---

## 5. Interactive States

### Hover

```tcss
&:hover {
    background: $panel;
    text-style: underline;
}
```

### Focus

```tcss
/* Widget focus */
&:focus {
    border: tall $primary;
    background: $primary 7%;
}

/* Parent receives focus (any child focused) */
&:focus-within {
    border: tall $secondary;
}
```

### Blur (unfocused)

```tcss
&:blur {
    text-opacity: 0.5;
}
```

### Pointer Cursor

```tcss
pointer: pointer;  /* Applied to clickable non-button elements */
```

---

## 6. Screen & Modal Design

### Modal Alignment Pattern

All modals use `align: center middle` on the screen with a constrained `#container`:

```tcss
AgentModal {
    align: center middle;

    #container {
        margin: 2 4 1 4;     /* Breathing room from edges */
        padding: 0 1 0 0;
        max-width: 100;
        height: auto;
        border: thick $primary 20%;
    }
}
```

### Session Resume Modal (with warning variant)

```tcss
SessionResumeModal {
    align: center middle;

    .warning {
        border: round $warning;
        color: $text-warning;
        margin: 0 0 1 1;
    }

    #container {
        margin: 2 4 1 4;
        border: thick $primary 20%;
    }
}
```

### Screen Background Patterns

```tcss
MainScreen    { background: $background; }              /* Solid */
SessionsScreen { background: $background; }
SettingsScreen { background: $background 60%; }         /* Transparent overlay */
StoreScreen    { /* hatch pattern on #container */ }
```

---

## 7. Conversation & Content Widgets

### Conversation Container

```tcss
Conversation {
    height: 1fr;
    layers: base prompt float;
    padding-left: 1;

    /* Column mode — narrowed reading width */
    &.-column {
        max-width: 100;
        background: black 7%;
    }

    /* Scrollbar variants */
    &.-scrollbar-hidden Window {
        scrollbar-size-vertical: 0;
    }
}

/* Scrollable content area — sticks to bottom */
Conversation > Window {
    layout: stream;
    padding: 0 1 0 1;
    height: 1fr;
    align: left bottom;
    scrollbar-size-vertical: 2;
}
```

### User Input Block

Left-stripe in secondary color, slightly tinted background:

```tcss
UserInput {
    border-left: blank $secondary;
    background: $secondary 15%;
    padding: 1 1 1 0;
    margin: 1 1 1 0;

    Markdown    { padding: 0 2 0 0; }
    MarkdownFence { margin: 0 2 1 0; }

    #prompt {
        margin: 0 1 0 0;
        color: $text-secondary;
    }
}
```

### Shell Result Block

Left-stripe in primary color, very subtle background:

```tcss
ShellResult {
    border-left: blank $primary;
    background: $foreground 4%;
    padding: 1 0;
    margin: 1 1 1 0;

    #prompt {
        margin: 0 1 0 0;
        color: $text-primary;
    }
}
```

### Agent Thought Panel

Collapsible, bounded height by default, maximizable:

```tcss
AgentThought {
    background: $primary-muted 20%;
    color: $text-primary;
    min-height: 1;
    margin: 1 1 1 0;
    padding: 0 1 0 1;
    max-height: 10;
    overflow-y: auto;
    scrollbar-visibility: hidden;

    &.-loading {
        background: transparent !important;
        padding: 0;
        margin: 0;
    }

    &.-maximized {
        max-height: 100h;
        margin: 1 2;
        scrollbar-visibility: visible;
    }
}
```

### Tool Call Widget

Expandable/collapsible with modifier classes:

```tcss
ToolCall {
    margin: 0 0 0 1 !important;
    width: 1fr;
    layout: stream;
    height: auto;

    #tool-content { display: none; }

    &.-has-content #tool-content {
        display: block;   /* Show when content exists */
        margin: 1 1 1 0;
    }

    &.-expanded ToolCallHeader {
        text-wrap: wrap;
        text-overflow: fold;
    }

    ToolCallHeader {
        color: $text-secondary;
        pointer: pointer;
        max-width: 1fr;
        text-wrap: nowrap;
        text-overflow: ellipsis;
    }
}
```

### Terminal Tool (Command Execution Block)

Status-driven border and background:

```tcss
TerminalTool {
    border: panel $primary 50%;
    border-title-style: bold;
    border-title-color: $text-primary;
    background: $primary 10%;
    padding: 1 1 0 1;

    &.-success {
        border: panel $success-muted;
        border-title-color: $text-success;
        background: $success 7%;
        opacity: 90%;
        border-title-style: not bold;
    }

    &.-error {
        border: panel $error-muted;
        border-title-color: $text-error;
        background: $error 7%;
        opacity: 90%;
    }
}
```

---

## 8. Input & Prompt Area

### Prompt Container

Transparent border at rest, colored on focus:

```tcss
PromptContainer {
    height: auto;
    margin: 0 0 1 0;
    border: tall transparent;          /* Reserve space, no visual */
    border-subtitle-align: left;
    border-subtitle-style: reverse;    /* Badge style subtitle */

    &:dark  { background: black 10%; }
    &:light { background: white 40%; }

    &:focus-within {
        border: tall $secondary;       /* Glow on focus */

        #prompt {
            text-opacity: 100%;        /* Reveal placeholder */
        }
    }

    #prompt {
        padding: 0 1;
        text-opacity: 30%;             /* Ghost placeholder */
    }

    PromptTextArea {
        padding: 0 1 0 0;
        background: transparent;
        border: none;
        height: auto;
        max-height: 50vh;

        &:blur { text-opacity: 0.5; }
    }
}
```

### Info Bar (below prompt)

One-line info strip with agent name, path, and status:

```tcss
#info-container {
    height: 1;
    margin: 1 1;

    AgentInfo {
        padding: 0 1;
        margin: 0 1 0 0;
        color: $text-primary;
        background: $primary 10%;
        width: auto;
    }

    CondensedPath {
        margin: 0 1;
        width: 1fr;
        height: 1;
        text-wrap: nowrap;
        color: $text-secondary;
    }

    StatusLine {
        color: $secondary 70%;
        margin: 0 1;
        width: auto;
        height: 1;
        text-align: right;
        text-wrap: nowrap;
        text-overflow: ellipsis;
    }

    ModeInfo {
        padding: 0 1;
        color: $text-secondary;
        background: $secondary 10%;
        dock: right;
        display: none;    /* Shown only in special modes */
    }
}
```

---

## 9. Sidebar Design

Fixed-width, slides off-screen when hidden:

```tcss
SideBar {
    dock: left;
    width: 40;
    max-width: 45%;
    min-width: 40;
    height: 1fr;
    border-right: tall black 10%;
    background: transparent;
    overflow: hidden scroll;
    scrollbar-size: 0 0;    /* Hidden scrollbar */

    DirectoryTree {
        height: 1fr;
        background: transparent;
        &:focus { background-tint: transparent; }
    }

    Plan {
        border: none !important;
        margin: 0 !important;
        padding: 0 1 0 0;
        background: transparent;
    }

    Collapsible {
        width: 1fr;
        height: 1fr;
        min-height: 3;

        &.-collapsed { height: auto; }

        Contents {
            height: 1fr;
            padding: 1 0 0 0;
        }
    }
}

/* Slide off-screen when hidden */
App.-hide-sidebar SideBar {
    layer: sidebar;
    offset-x: -100%;

    &:focus-within {
        offset-x: 0;    /* Slide back in when focused */
    }
}
```

---

## 10. Sessions & Tab Bar

### Sessions Tab Bar

Two-line row (labels + underline indicator), hidden by default:

```tcss
SessionsTabs {
    layout: grid;
    grid-columns: auto auto;
    height: 2;
    display: none;
    overflow: scroll scroll;
    scrollbar-size: 0 0;

    Underline {
        width: 1fr;
        height: 1;

        & > .underline--bar {
            color: $block-cursor-background;
            background: $foreground 10%;
        }
    }

    #title-container Label {
        text-style: dim;
        pointer: pointer;
        padding: 0 1;

        &.-current {
            text-style: not dim;    /* Active tab is bright */
        }
    }
}

/* Show when app has multiple sessions */
App.-show-sessions-bar SessionsTabs { display: block; }
App.-show-sessions-bar Throbber     { offset-y: 1; }
```

### Session Summary Card

```tcss
SessionSummary {
    background: black 10%;
    height: auto;
    padding: 1 0 1 0;
    pointer: pointer;
    border: blank transparent;    /* Space for highlight border */

    .icon     { width: 3; text-align: center; color: $text-secondary; }
    .title    { width: 1fr; }
    .subtitle { color: $text-secondary; text-style: italic; }

    &.-highlight { border: round $primary; }    /* Selected */

    /* State variants */
    &.-state-busy  { padding: 0 0 1 0; }
    &.-state-idle  .icon { color: $text-secondary; }

    &.-state-asking .icon { color: $text-accent; }
    &.-state-asking.-blink .icon { opacity: 0.2; }    /* Blink animation */
}
```

---

## 11. Settings Screen

Slides in from the right, semi-transparent overlay:

```tcss
SettingsScreen {
    background: $background 60%;
    align-horizontal: right;
    overflow: hidden;

    #contents {
        width: 50%;
        padding: 0 1;
        background: black 10%;
    }

    &.-narrow #contents { width: 1fr; }    /* Full width on small terminals */

    /* Form control borders */
    Input, Select SelectCurrent, Checkbox, TextArea {
        border: tall black 20%;
        &:focus { border: tall $primary; }
    }

    Input.-invalid { border: tall $error 60%; }

    .setting-object {
        border: tall $secondary-muted;
        padding: 0 1;
        &:focus-within { border: tall $secondary; }
        &:light { border: tall $foreground 20%; }

        .heading .title {
            color: $primary;
            text-style: none;
        }
    }

    .help {
        color: $text-muted;
        padding: 0 0 0 1;
    }
}
```

---

## 12. Store / Launcher Screen

### Background & Title Area

```tcss
StoreScreen #container {
    hatch: right $primary 15%;    /* Diagonal hatch decorative background */
    overflow: hidden auto;
}

#title-grid {
    border: block black 20%;
    background: black 20%;
    grid-size: 2 1;
    grid-columns: 24 1fr;    /* Mandelbrot fractal (24) + content */
    grid-gutter: 1 2;
    min-width: 40;
}
```

### Agent & Launcher Items

```tcss
AgentItem, LauncherItem {
    height: auto;
    border: tall transparent;
    padding: 0 1;
    pointer: pointer;

    &:hover { background: $panel; }

    #description { text-style: dim; }
    #author      { text-style: italic; color: $text-secondary; }
    #type        { text-align: right; }
}

LauncherItem Digits {
    width: auto;
    padding: 0 1 0 0;
    color: $text-success;
}
```

---

## 13. Notifications & Flash Messages

### Toast Notifications

```tcss
Toast {
    margin: 0 0;
    padding: 0 1;
    background: $background;
    color: $text-muted;

    .toast--title { color: $text; }

    &.-information { border: round $primary; }
    &.-warning     { border: round $warning; }
    &.-error       { border: round $error;   }
}
```

### Inline Flash Messages

```tcss
Flash {
    height: 1;
    width: 1fr;
    text-align: center;
    text-wrap: nowrap;
    text-overflow: ellipsis;
    visibility: hidden;    /* Hidden until triggered */

    &.-default  { background: $primary 10%; color: $text-primary; }
    &.-success  { background: $success 10%; color: $text-success;  }
    &.-warning  { background: $warning 10%; color: $text-warning;  }
    &.-error    { background: $error   10%; color: $text-error;    }
}
```

### Danger Warning Widget

```tcss
DangerWarning {
    height: auto;
    padding: 0 1;
    margin: 1 0;

    &.-dangerous    { color: $text-warning; border: round $warning; }
    &.-destructive  { color: $text-error;   border: round $error;   }
}
```

### Footer

```tcss
Footer {
    background: transparent;

    .footer-key--key         { color: $text; background: transparent; padding: 0 1; }
    .footer-key--description { padding: 0 1 0 0; color: $text-muted; background: $footer-description-background; }

    &.-disabled { text-style: dim; }

    &.-compact .footer-key--key         { padding: 0; }
    &.-compact .footer-key--description { padding: 0 0 0 1; }
}
```

---

## 14. Animations & Motion

### Opacity Animation (Modal entry)

```python
# src/toad/screens/agent_modal.py
self.query_one("Footer").styles.animate("opacity", 1.0, duration=500 / 1000)
```

### Blink Timer (Session status indicator)

```python
# src/toad/widgets/session_summary.py
self.blink_timer = self.set_interval(0.5, do_blink)

def do_blink() -> None:
    self.blink = not self.blink
```

TCSS applies the blink via a CSS class toggle:

```tcss
&.-state-asking.-blink .icon { opacity: 0.2; }
&.-state-asking.-blink Rule  { opacity: 0.2; }
```

### Throbber — Scrolling Gradient

```python
# src/toad/widgets/throbber.py
def render_strips(self, width, height, style, options):
    time = self.get_time()
    offset = width - int((time % 1.0) * width)    # Continuous scroll
    segments = segments[offset : offset + width]
    return [Strip(segments, cell_length=width)]
```

### Busy Indicator Auto-Refresh

```python
# src/toad/widgets/session_summary.py
class BusyIndicator(widgets.Static):
    def on_mount(self) -> None:
        self.auto_refresh = 1 / 4    # 4 fps update cycle
```

---

## 15. Responsive Design

### Horizontal Breakpoints

```python
# src/toad/app.py
HORIZONTAL_BREAKPOINTS = [(0, "-narrow"), (100, "-wide")]
```

At < 100 columns: `-narrow` class on `App`
At ≥ 100 columns: `-wide` class on `App`

### Responsive Layout Adjustments

```tcss
/* Settings panel: half width on wide, full on narrow */
SettingsScreen #contents         { width: 50%; }
SettingsScreen.-narrow #contents { width: 1fr; }

/* Sidebar caps at 45% of terminal width */
SideBar { width: 40; max-width: 45%; min-width: 40; }

/* Column mode conversation */
Conversation.-column { max-width: 100; background: black 7%; }
```

---

## 16. Layering & Z-Index

Textual uses named layers; higher declarations appear on top.

```tcss
/* Main screen layer stack */
MainScreen  { layers: sidebar screen base; }
Conversation { layers: base prompt float; }

/* Sidebar slides off-screen on a dedicated layer */
SideBar { layer: sidebar; }

/* Loading indicator stays below content */
Throbber { layer: base; }

/* Autocomplete overlays float above everything */
PathSearch, SlashComplete {
    overlay: screen;
    display: none;
    offset-y: -16;
    height: 16;
}
```

---

## 17. Global State CSS Classes

These classes are toggled on `App` to drive global layout changes:

| Class | Effect |
|---|---|
| `.-narrow` / `.-wide` | Responsive breakpoint classes |
| `.-show-sessions-bar` | Shows multi-session tab bar |
| `.-hide-footer` | Hides the footer bar |
| `.-hide-thoughts` | Hides `AgentThought` widgets |
| `.-hide-sidebar` | Slides sidebar off-screen |
| `.-hide-status-line` | Hides status line |
| `.-hide-agent-title` | Hides agent name chip |
| `.-hide-info-bar` | Hides full info bar |
| `.-compact-input` | Reduces prompt container spacing |

Example of `var(toggle_class=...)` driving a class automatically:

```python
# src/toad/app.py
show_sessions = var(False, toggle_class="-show-sessions-bar")
```

---

## 18. Component Hierarchy

### Main Screen Widget Tree

```
MainScreen
├── Center
│   ├── SideBar
│   │   ├── Collapsible (Plan)
│   │   └── Collapsible (ProjectDirectoryTree)
│   └── Conversation
│       ├── Window (scrollable, layout: stream, align: left bottom)
│       │   ├── UserInput
│       │   ├── AgentResponse
│       │   ├── AgentThought
│       │   ├── ToolCall
│       │   │   ├── ToolCallHeader
│       │   │   └── ToolCallContent (DiffView / Markdown)
│       │   ├── ShellResult
│       │   ├── TerminalTool
│       │   └── Terminal (PTY widget)
│       └── Prompt (docked bottom)
│           ├── PromptContainer
│           │   ├── #prompt (label)
│           │   └── PromptTextArea
│           └── #info-container
│               ├── AgentInfo
│               ├── CondensedPath
│               ├── StatusLine
│               └── ModeInfo
└── Footer
```

### Modal Screen Pattern

```
ModalScreen (align: center middle)
└── #container (border: thick $primary 20%, max-width: 100)
    ├── Content area
    └── Button row / Footer
```

---

## 19. Design Principles Summary

### 1. Semantic Color — Never Hardcode Hex

Every color is a `$variable`. This makes the entire UI theme-switchable (dark/light/custom) with zero TCSS changes.

### 2. Opacity-Based Tinting

Rather than defining many color variants, Toad uses a single color token + opacity percentage to create hierarchy:

- `$primary 10%` — subtle background tint
- `$primary 50%` — medium emphasis border
- `$primary 100%` — full emphasis

### 3. Left-Stripe Visual Categorization

`border-left: blank $color` applies a left-stripe accent with no border space cost — used to visually distinguish message types (user = secondary, shell = primary).

### 4. Transparent Borders as Space Holders

`border: tall transparent` reserves border space so focus/hover state border doesn't cause layout shift.

### 5. CSS Class Toggle State Machine

Widget states (loading, success, error, expanded, maximized) are expressed as CSS class modifiers (e.g., `.-success`, `.-expanded`) — keeping all visual logic in TCSS rather than Python.

### 6. `var(toggle_class=...)` for Reactive Layout

App-level boolean reactives automatically add/remove CSS classes on the `App` node, driving global layout changes declaratively.

### 7. `layout: stream` for Content Feeds

All conversational content uses `layout: stream` (vertical flow) with `align: left bottom` to keep content anchored to the bottom — like a chat UI.

### 8. Consistent Spacing Rhythm

The `1 1 1 0` margin pattern is used everywhere for block content — creating a visual left-edge with uniform breathing room.

### 9. `pointer: pointer` for Non-Button Clickables

Any non-`Button` widget that is clickable gets `pointer: pointer` in TCSS — a crucial usability signal.

### 10. Theme-Conditional Blocks

```tcss
&:dark  { background: black 10%; }
&:light { background: white 40%; }
```

Used sparingly for backgrounds where the same formula (e.g. `black 10%`) would look invisible in light mode.

---

## 20. Design Token Reference

### Spacing

| Value | Meaning |
|---|---|
| `0` | No space |
| `1` | Base unit (1 character cell) |
| `2` | Double unit |
| `4` | Used in modal margins |

### Border Token Mapping

| Border Style | Visual | Typical Use |
|---|---|---|
| `tall` | 1-char sides, no top/bottom | Focus rings, input containers |
| `round` | Rounded corners | Popups, help panels, warnings |
| `heavy` | Bold double border | Critical errors |
| `panel` | Top/bottom solid | Tool execution blocks |
| `thick` | 2-char all sides | Modal dialogs |
| `blank` | No visual, preserves space | Left-stripe accent markers |
| `tab` | Tab-style | Special modals |
| `block` | Block character fill | Store title containers |
| `ascii` | ASCII `+--+` style | Decorative dividers |

### Opacity Scale for Color Tints

| Opacity | Use |
|---|---|
| `4%` | Barely-there background (shell result) |
| `7%` | Very subtle tint (tool success/error bg) |
| `10%` | Standard chip/badge background |
| `15%` | User input background |
| `20%` | Modal/panel overlays |
| `50%` | Border emphasis |
| `60%` | Screen overlays (settings) |
| `70%` | Muted text color |

---

## 21. Lessons for NMS-CLI

| Design Pattern | How Toad Does It | NMS-CLI Application |
|---|---|---|
| Left-stripe message categorization | `border-left: blank $color` | Color-code by NetBox app (DCIM=primary, IPAM=secondary, etc.) |
| Status-driven widget borders | `.-success`/`.-error` CSS classes on blocks | Color-code device status (active/planned/staged/failed) |
| Expandable detail sections | `.-expanded` toggle class + `display: none` → `block` | Expandable device detail panels |
| Ghost placeholder text | `text-opacity: 30%`, full on `:focus-within` | Search bars, filter inputs |
| Transparent focus border (no layout shift) | `border: tall transparent` at rest | All form inputs |
| Opacity-based tinting hierarchy | `$primary 10%` / `50%` / `100%` | Consistent visual hierarchy without new colors |
| Global layout toggle via reactive | `var(toggle_class=...)` | Hide/show sidebar, filter panel, detail panel |
| `layout: stream` + `align: left bottom` | Conversation window | Audit log / event stream views |
| `hatch: right $primary 15%` | Store screen background | Landing/welcome screen decoration |
| Semantic color tokens only | No hex in TCSS | Full dark/light/custom theme support |
| `1 1 1 0` block margin rhythm | All content blocks | Consistent list/feed spacing |
| `max-height` + scrollbar visibility | Collapsed thoughts | Collapsed detail panels with optional scroll |
| Breakpoints via `HORIZONTAL_BREAKPOINTS` | `(0, "-narrow"), (100, "-wide")` | Adjust sidebar/detail panel at narrow terminals |
| Settings as right-side overlay | 50% width, `align-horizontal: right` | NetBox settings / connection config panel |
| Mandelbrot / decorative widget in title | `grid-columns: 24 1fr` + custom widget | ASCII art / sparkline in NMS dashboard header |
