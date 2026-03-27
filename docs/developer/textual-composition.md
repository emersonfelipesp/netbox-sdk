# Textual Composition Pattern

`netbox-sdk` uses a React-style composition pattern for Textual UI work: build screens from small reusable widgets, pass configuration through constructor arguments, and compose behavior by nesting widgets instead of building deep inheritance trees.

## Why

- keeps layout readable in `compose()`
- makes theme and styling rules reusable
- lets small widgets evolve independently
- reduces fragile base-class coupling
- maps well to NetBox's own Python-side UI composition model

## Core Rule

Prefer composition over inheritance for UI structure.

Use inheritance when:

- extending a Textual primitive with a narrow, reusable behavior such as `NbxButton`
- creating a self-contained stateful widget with a clear public API

Prefer composition when:

- assembling headers, bodies, toolbars, and content regions
- sharing visual structure across multiple screens
- expressing "slots" such as header/body/footer areas

## React Mapping

React pattern:

```tsx
<Panel>
  <PanelHeader title="Object Attributes" subtitle="NetBox detail-style panel" />
  <PanelBody>
    <Status />
    <Table />
    <Trace />
  </PanelBody>
</Panel>
```

Textual pattern in this repo:

```python
class ObjectAttributesPanel(Vertical):
    def compose(self):
        yield NbxPanelHeader("Object Attributes", "NetBox detail-style panel")
        with NbxPanelBody(id="detail_panel_body"):
            yield Static("Ready", id="detail_status")
            yield DataTable(id="detail_table")
            yield Static("Cable Trace", id="detail_trace_title", classes="hidden")
            yield Static("", id="detail_trace", classes="hidden")
```

## Standard Building Blocks

Current shared composition primitives live in `netbox_tui/widgets.py`:

| Primitive | Role |
|-----------|------|
| `NbxButton` | Themed button with `tone`, `size`, `chrome` semantic props |
| `NbxPanelHeader` | Panel title bar |
| `NbxPanelBody` | Panel content container with optional `tone` / `surface` |
| `ContextBreadcrumb` | Clickable topbar breadcrumb with scoped dropdown menus; emits `CrumbSelected` / `MenuOptionSelected` |
| `SupportModal` | Self-contained `ModalScreen` shared by main and dev TUIs; inherits active theme via CSS class on mount |

These should be the default starting point for new reusable UI pieces.

## Guidelines

### 1. Compose screens from leaf widgets

Keep `App.compose()` focused on arranging major regions.

- app shell
- top bar
- sidebar
- main workspace
- overlays

Move repeated subtrees into dedicated widgets once they have meaning.

### 2. Treat constructor args like React props

Widget inputs should be explicit and semantic.

Good:

```python
NbxButton("Send", size="medium", tone="primary")
NbxButton("Close", size="small", tone="error")
NbxPanelHeader("Object Attributes", "NetBox detail-style panel", tone="primary")
NbxPanelBody(surface="background")
```

Avoid passing styling intent indirectly through ad-hoc class strings when a semantic argument would be clearer.

### 2.1 Theme values should also be props

Theme-aware reusable widgets should receive semantic styling inputs through constructor arguments, similar to React props.

Preferred:

```python
NbxButton("Send", size="medium", tone="primary")
NbxPanelHeader("Danger Zone", tone="error")
NbxPanelBody(surface="panel")
```

Avoid:

```python
Button("Send", classes="custom-primary custom-medium")
Static("Danger Zone", classes="red-header")
```

Use semantic props such as:

- `size`
- `tone`
- `surface`
- `chrome`

Theme-aware composition also includes surface propagation. If a reusable widget mounts nested Textual primitives internally, the parent widget must carry semantic theme intent down to those children and verify the final rendered surfaces.

Important examples:

- modal widgets must theme the dialog container and action buttons, not only the `ModalScreen`
- tabbed widgets must theme `TabbedContent`, `ContentTabs`, `ContentSwitcher`, and the active `TabPane`
- editor/list widgets must theme both their outer container and the framework-owned inner parts that paint backgrounds in focus or ANSI paths

### 3. Use nested widgets as slots

When a widget has recognizable regions, model them as child widgets instead of one large monolith.

- header
- body
- footer
- toolbar
- empty state

### 4. Keep public methods behavior-focused

A composed widget should expose intent-level methods such as:

- `set_loading()`
- `set_object()`
- `set_trace()`

Avoid leaking internal child structure unless the caller truly owns that structure.

### 5. Keep styling in TCSS

Composition defines structure. TCSS defines appearance.

- use semantic classes on reusable widgets
- keep theme logic in TCSS and theme JSON
- avoid runtime color decisions in widget constructors

Exception:

- when Textual runtime defaults still override the selected theme in terminal-only paths such as ANSI-mode `Screen` / `ModalScreen` or mounted internal subwidgets, add a narrow runtime surface sync in the owning widget or app
- if you take this escape hatch, also document the reason in the relevant theme/design docs and keep the runtime override limited to semantic theme tokens

Practical rule:

- first fix the theme palette if the structural tokens themselves are wrong
- then fix recursive TCSS selectors for framework-owned internals
- only then add runtime surface syncing for the specific widgets that still escape the theme contract

### 6. Keep inheritance shallow

Do not create long widget inheritance chains for layout reuse.

Preferred:

- `ObjectAttributesPanel(Vertical)` composed from `NbxPanelHeader` and `NbxPanelBody`

Avoid:

- `BasePanel -> PanelCard -> DetailPanel -> ObjectAttributesPanel -> SpecializedPanel`

## Project-Wide Standard

For new Textual work in `netbox-sdk`:

1. Start with composition.
2. Pass theme/styling intent as semantic props on reusable widgets.
3. Extract reusable visual primitives into `netbox_tui/widgets.py`.
4. Document new primitives in contributor docs if they become project-standard.
5. Only add inheritance when the widget is truly a behavior-specialized primitive.
