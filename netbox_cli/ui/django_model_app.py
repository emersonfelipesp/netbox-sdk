"""Django Model Inspector TUI — browse NetBox Django models, diagrams, and source code."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.events import Click
from textual.timer import Timer
from textual.widgets import (
    Button,
    Footer,
    Input,
    Select,
    Static,
    TabbedContent,
    TabPane,
    Tree,
)

from netbox_cli.api import ConnectionProbe
from netbox_cli.django_models.rich_rendering import (
    clear_all_expansions,
    render_fields_table_rich,
    render_model_diagram_rich,
    render_python_source_rich,
    render_stats_table_rich,
    toggle_dependency_expansion,
)
from netbox_cli.django_models.store import DjangoModelStore
from netbox_cli.logging_runtime import get_logger

from .chrome import (
    SWITCH_TO_CLI_TUI,
    SWITCH_TO_DEV_TUI,
    SWITCH_TO_MAIN_TUI,
    apply_theme,
    badge_state_for_probe,
    initialize_theme_state,
    logo_renderable,
    set_connection_badge_state,
    strip_theme_select_prefix,
    update_clock_widget,
)
from .django_model_state import (
    DjangoModelTuiState,
    load_django_model_tui_state,
    save_django_model_tui_state,
)
from .widgets import NbxButton, SupportModal

logger = get_logger(__name__)

_VIEW_MODE_OPTIONS = (
    ("- TUI", "main"),
    ("- CLI", "cli"),
    ("- Dev", "dev"),
    ("- Models", "django"),
)

_BUILDS_DIR = Path(__file__).resolve().parent.parent.parent / "django_models_builds"


def _discover_versions() -> tuple[tuple[str, str], ...]:
    """Scan ``django_models_builds/`` for versioned build files.

    Returns ``Select``-compatible options sorted newest-first.
    """
    if not _BUILDS_DIR.is_dir():
        return ()
    options: list[tuple[str, str]] = []
    for f in sorted(_BUILDS_DIR.glob("*-django-models-build.json"), reverse=True):
        tag = f.name.replace("-django-models-build.json", "")
        options.append((f"  {tag}", tag))
    return tuple(options)


def _match_version(api_version: str, tags: list[str]) -> str | None:
    """Find the best build tag matching an ``API-Version`` header value.

    ``api_version`` is e.g. ``"4.2"``; tags are e.g. ``["v4.5.5", "v4.2.1"]``.
    """
    prefix = f"v{api_version}."
    for t in tags:
        if t.startswith(prefix):
            return t
    major = api_version.split(".")[0]
    major_prefix = f"v{major}."
    for t in tags:
        if t.startswith(major_prefix):
            return t
    return None


class DjangoModelTuiApp(App[None]):
    """TUI for exploring NetBox Django model relationships and source code."""

    TITLE = "NetBox Django Models"
    CSS_PATH = [
        str(Path(__file__).resolve().parent.parent / "ui_common.tcss"),
        str(Path(__file__).resolve().parent.parent / "django_model_tui.tcss"),
    ]
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("/", "focus_search", "Search"),
        Binding("g", "focus_tree", "Models"),
        Binding("r", "rebuild", "Rebuild"),
        Binding("f", "fetch_version", "Fetch"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        store: DjangoModelStore,
        *,
        theme_name: str | None = None,
    ) -> None:
        super().__init__()
        self.store = store
        self._graph: dict[str, Any] | None = None
        self._all_keys: list[str] = []
        self._current_model_key: str | None = None
        self._version_options = _discover_versions()
        self._active_version: str | None = None
        self._detected_api_version: str | None = None
        self._clock_timer: Timer | None = None
        self._connection_timer: Timer | None = None

        self.state: DjangoModelTuiState = load_django_model_tui_state()
        catalog, self.theme_name, self.theme_options = initialize_theme_state(
            self,
            requested_theme_name=theme_name,
            persisted_theme_name=self.state.theme_name,
        )
        self.theme_catalog = catalog

    # ── Composition ───────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        # ── Topbar (matches dev TUI structure) ────────────────────────────
        with Horizontal(id="dev_topbar"):
            with Horizontal(id="dev_topbar_left"):
                yield Static("\u25cf", id="dev_nav_dot")
                yield Select(
                    options=self.theme_options,
                    value=self.theme_name,
                    prompt="Theme",
                    id="dev_theme_select",
                )
                if self._version_options:
                    yield Select(
                        options=self._version_options,
                        value=self._version_options[0][1],
                        prompt="NetBox",
                        id="version_select",
                    )
                yield Select(
                    options=_VIEW_MODE_OPTIONS,
                    value="django",
                    prompt="View",
                    id="dev_view_select",
                )
            with Horizontal(id="dev_topbar_center"):
                yield Static(self._logo_renderable(), id="dev_logo")
                yield Static(
                    Text(" Django Models", style="dim"),
                    id="dev_topbar_cli_suffix",
                )
            with Horizontal(id="dev_topbar_right"):
                yield Static("", id="dev_clock")
                yield Static("●", id="dev_connection_badge", classes="-checking")
                yield NbxButton(
                    "Liked it? Support me!",
                    id="support_button",
                    size="small",
                    tone="muted",
                    classes="nbx-topbar-control",
                )
                yield NbxButton(
                    "Close",
                    id="dev_close_button",
                    size="small",
                    tone="error",
                    classes="nbx-topbar-control",
                )

        # ── Search bar ────────────────────────────────────────────────────
        with Horizontal(id="query_bar"):
            yield Input(
                placeholder="Search models (e.g. Device, dcim, ForeignKey)...", id="model_search"
            )

        # ── Main shell ────────────────────────────────────────────────────
        with Horizontal(id="dm_shell"):
            # Sidebar
            with Vertical(id="dm_sidebar"):
                yield Static("Django Models", id="dm_sidebar_title")
                yield Tree("NetBox Models", id="dm_nav_tree")
                yield Static("", id="dm_help")

            # Main content
            with Vertical(id="dm_main"):
                with TabbedContent(id="dm_main_tabs"):
                    with TabPane("Diagram", id="dm_diagram_tab"):
                        with VerticalScroll():
                            yield Static("Select a model from the sidebar.", id="dm_diagram")
                    with TabPane("Source Code", id="dm_code_tab"):
                        with VerticalScroll():
                            yield Static(
                                "# Select a model to view its source code.",
                                id="dm_source_code",
                            )
                    with TabPane("Fields", id="dm_fields_tab"):
                        with VerticalScroll():
                            yield Static("Select a model to view its fields.", id="dm_fields")
                    with TabPane("Stats", id="dm_stats_tab"):
                        with VerticalScroll():
                            yield Static("", id="dm_stats")

        yield Footer()

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def on_mount(self) -> None:
        logger.info("django model tui mounted")
        self._apply_theme(self.theme_name)
        self.call_after_refresh(self._strip_theme_select_prefix)
        self._update_clock()
        self._set_connection_badge_checking()
        self._probe_connection_health()
        self._clock_timer = self.set_interval(1.0, self._update_clock, name="dm_clock")
        self._connection_timer = self.set_interval(
            30.0, self._probe_connection_health, name="dm_connection"
        )
        self._auto_detect_version()

    def on_unmount(self) -> None:
        logger.info("django model tui unmounting")
        if self._clock_timer is not None:
            self._clock_timer.stop()
            self._clock_timer = None
        if self._connection_timer is not None:
            self._connection_timer.stop()
            self._connection_timer = None
        self.state.theme_name = self.theme_name
        save_django_model_tui_state(self.state)

    # ── Graph loading ─────────────────────────────────────────────────────

    def _load_graph_from_store(self) -> None:
        """Load graph from the default store (no versioned build selected)."""
        if not self.store.exists():
            self.notify(
                "Model cache not found. Run: nbx dev django-model build",
                severity="warning",
                timeout=10,
            )
            return
        try:
            self._graph = self.store.load()
            self._build_tree()
            self._render_stats()
        except Exception as exc:
            self.notify(f"Error loading cache: {exc}", severity="error")

    def _load_version(self, tag: str) -> None:
        """Load a versioned build from ``django_models_builds/``."""
        build_file = _BUILDS_DIR / f"{tag}-django-models-build.json"
        if not build_file.exists():
            self.notify(f"Build file not found: {build_file.name}", severity="error")
            return
        try:
            self._graph = json.loads(build_file.read_text(encoding="utf-8"))
            self._build_tree()
            self._render_stats()
            models = self._graph.get("stats", {}).get("total_models", 0) if self._graph else 0
            self.notify(f"Loaded {tag} ({models} models)", timeout=5)
        except Exception as exc:
            self.notify(f"Error loading {tag}: {exc}", severity="error")

    @work(group="dm_autodetect", exclusive=True, thread=False)
    async def _auto_detect_version(self) -> None:
        """Probe connected NetBox and auto-select matching build."""
        tags = [opt[1] for opt in self._version_options]
        if not tags:
            self._load_graph_from_store()
            return

        try:
            from netbox_cli.cli import _get_client  # noqa: PLC0415

            client = _get_client()
            probe = await client.probe_connection()
            if probe.ok and probe.version:
                self._detected_api_version = probe.version
                matched = _match_version(probe.version, tags)
                if matched:
                    self._active_version = matched
                    # Update the Select widget
                    try:
                        sel = self.query_one("#version_select", Select)
                        sel.value = matched
                    except Exception:
                        pass
                    self._load_version(matched)
                    self.notify(
                        f"Auto-selected {matched} (NetBox API {probe.version})",
                        timeout=8,
                    )
                    return
                else:
                    # No matching build — offer to fetch
                    self.notify(
                        f"No build for NetBox API {probe.version}. Press 'f' to fetch from GitHub.",
                        severity="warning",
                        timeout=15,
                    )
                    self._load_graph_from_store()
                    return
        except Exception:
            pass  # No config / no connection

        # No auto-match — load default store
        self._load_graph_from_store()

    def _rebuild(self) -> None:
        try:
            self.notify("Rebuilding model cache...", timeout=10)
            netbox_root = Path("/root/nms/netbox/netbox/")
            if not netbox_root.is_dir():
                self.notify(f"NetBox source not found at {netbox_root}", severity="error")
                return
            self._graph = self.store.build(netbox_root)
            self._build_tree()
            self._render_stats()
            self.notify(
                f"Built {self._graph['stats']['total_models']} models, "
                f"{self._graph['stats']['total_edges']} edges.",
                timeout=5,
            )
        except Exception as exc:
            self.notify(f"Rebuild failed: {exc}", severity="error")

    # ── Version selector ──────────────────────────────────────────────────

    @on(Select.Changed, "#version_select")
    def _on_version_changed(self, event: Select.Changed) -> None:
        if event.value in (None, Select.BLANK) or not isinstance(event.value, str):
            return
        self._active_version = event.value
        self._load_version(event.value)

    # ── Navigation tree ───────────────────────────────────────────────────

    def _build_tree(self) -> None:
        if self._graph is None:
            return
        tree = self.query_one("#dm_nav_tree", Tree)
        tree.clear()
        tree.root.expand()

        models = self._graph.get("models", {})
        self._all_keys = sorted(models.keys())

        # Group by app
        apps: dict[str, list[tuple[str, dict]]] = {}
        for key in self._all_keys:
            model = models[key]
            apps.setdefault(model["app"], []).append((key, model))

        for app_name in sorted(apps):
            app_models = apps[app_name]
            app_node = tree.root.add(f"{app_name}/ ({len(app_models)})", expand=False)
            for key, model in sorted(app_models, key=lambda x: x[1]["name"]):
                fk_count = sum(1 for f in model.get("fields", []) if f.get("target"))
                fk_label = f" [{fk_count} FK]" if fk_count else ""
                label = f"{model['name']}{fk_label}"
                app_node.add_leaf(label, data=key)

    # ── Model selection ───────────────────────────────────────────────────

    @on(Tree.NodeSelected, "#dm_nav_tree")
    def _on_model_selected(self, event: Tree.NodeSelected) -> None:
        key = event.node.data
        if key is None or not isinstance(key, str):
            return
        self._show_model(key)

    def _show_model(self, key: str) -> None:
        if self._graph is None:
            return
        models = self._graph.get("models", {})
        model = models.get(key)
        if model is None:
            return

        # Clear expansions if switching to a different model
        if self._current_model_key != key:
            clear_all_expansions()
            self._current_model_key = key

        # Diagram - Rich rendering with colored borders
        try:
            diagram_widget = self.query_one("#dm_diagram", Static)
            diagram_rich = render_model_diagram_rich(key, self._graph)
            diagram_widget.update(diagram_rich)
        except Exception:
            pass

        # Source code - Rich rendering with syntax highlighting
        try:
            source = self._get_model_source(key)
            code_widget = self.query_one("#dm_source_code", Static)
            source_rich = render_python_source_rich(source)
            code_widget.update(source_rich)
        except Exception:
            pass

        # Fields table - Rich Table widget
        try:
            fields_widget = self.query_one("#dm_fields", Static)
            fields_table = render_fields_table_rich(model)
            fields_widget.update(fields_table)
        except Exception:
            pass

        # Update title
        self.title = f"NetBox \u2014 {key}"

    @on(Click, "#dm_diagram")
    def _on_diagram_click(self, event: Click) -> None:
        """Handle clicks on the diagram to expand/collapse dependency sections."""
        if self._current_model_key is None or self._graph is None:
            return

        # Check if we're in the Dependencies or Dependents section area
        # Since we can't easily parse the rendered content, we'll use a simpler approach
        # We'll check if the click is in roughly the right area and toggle sections

        # For now, we'll implement a simple click detection based on position
        # This could be enhanced later with more sophisticated region detection
        click_y = event.offset.y

        # Heuristic: if clicked in the upper half, try Dependencies; lower half, try Dependents
        # This is a simplified approach - in a production app we'd want more precise detection

        models = self._graph.get("models", {})
        model = models.get(self._current_model_key)
        if model is None:
            return

        # Get outgoing and incoming relationships to determine if sections exist
        outgoing_fks = [f for f in model.get("fields", []) if f.get("target")]
        graph_models = self._graph.get("models", {})
        incoming_fks = []
        for other_key, other_model in graph_models.items():
            for field in other_model.get("fields", []):
                if field.get("target") == self._current_model_key:
                    incoming_fks.append((other_key, field))

        # Simple region-based detection
        # If we have both dependencies and dependents, split the area
        has_dependencies = len(outgoing_fks) > 0
        has_dependents = len(incoming_fks) > 0

        if has_dependencies and click_y < 10:  # Upper region - Dependencies
            toggle_dependency_expansion(self._current_model_key, "dependencies")
            self._refresh_current_model()
        elif has_dependents and click_y >= 10:  # Lower region - Dependents
            toggle_dependency_expansion(self._current_model_key, "dependents")
            self._refresh_current_model()

    def _refresh_current_model(self) -> None:
        """Refresh the currently displayed model to show updated expansion states."""
        if self._current_model_key is not None:
            self._show_model(self._current_model_key)

    def _get_model_source(self, key: str) -> str:
        """Get model source — try the store first, then the versioned build's file_path."""
        # If a versioned build is selected, file_path may point to a now-gone temp dir
        if self._active_version:
            model = (self._graph or {}).get("models", {}).get(key)
            if model:
                fp = model.get("file_path", "")
                if fp and Path(fp).exists():
                    return self.store.get_model_source(key)
                return f"# Source not available for {key}\n# (Versioned build — file_path: {fp})"
        return self.store.get_model_source(key)

    def _render_stats(self) -> None:
        """Render statistics using Rich Table widget."""
        if self._graph is None:
            return
        try:
            stats_widget = self.query_one("#dm_stats", Static)
            stats_table = render_stats_table_rich(self._graph)
            stats_widget.update(stats_table)
        except Exception:
            pass

    # ── Search ────────────────────────────────────────────────────────────

    @on(Input.Changed, "#model_search")
    def _on_search_changed(self, event: Input.Changed) -> None:
        query = event.value.strip().lower()
        if not query:
            self._build_tree()
            return

        if self._graph is None:
            return

        tree = self.query_one("#dm_nav_tree", Tree)
        tree.clear()
        tree.root.expand()

        models = self._graph.get("models", {})
        for key in self._all_keys:
            model = models[key]
            searchable = f"{model['app']}.{model['name']}".lower()
            if query in searchable:
                fk_count = sum(1 for f in model.get("fields", []) if f.get("target"))
                fk_label = f" [{fk_count} FK]" if fk_count else ""
                tree.root.add_leaf(
                    f"{model['app']}.{model['name']}{fk_label}",
                    data=key,
                )

    # ── Actions ───────────────────────────────────────────────────────────

    def action_focus_search(self) -> None:
        self.query_one("#model_search", Input).focus()

    def action_focus_tree(self) -> None:
        self.query_one("#dm_nav_tree", Tree).focus()

    def action_rebuild(self) -> None:
        self._rebuild()

    @work(group="dm_fetch", exclusive=True, thread=False)
    async def action_fetch_version(self) -> None:
        """Fetch the matching NetBox release from GitHub and build the model graph."""
        if not self._detected_api_version:
            self.notify(
                "No NetBox version detected. Is your profile configured?", severity="warning"
            )
            return

        from netbox_cli.django_models.fetcher import (  # noqa: PLC0415
            _match_tag,
            available_build_tags,
            build_exists,
            clone_and_build,
            find_github_release_tag,
        )

        api_ver = self._detected_api_version
        tags = available_build_tags()
        matched = _match_tag(api_ver, tags)
        if matched:
            self.notify(f"Build already exists: {matched}", timeout=5)
            return

        self.notify(f"Looking up NetBox {api_ver} on GitHub...", timeout=10)
        tag = find_github_release_tag(api_ver)
        if tag is None:
            self.notify(f"No GitHub release found for API {api_ver}.", severity="error")
            return

        if build_exists(tag):
            self.notify(f"Build already exists: {tag}", timeout=5)
            return

        self.notify(f"Cloning and building {tag} (this may take a minute)...", timeout=60)
        try:
            graph = clone_and_build(tag)
            self._graph = graph
            self._build_tree()
            self._render_stats()
            # Update version selector
            self._version_options = _discover_versions()
            self._active_version = tag
            try:
                sel = self.query_one("#version_select", Select)
                sel.value = tag
            except Exception:
                pass
            stats = graph.get("stats", {})
            self.notify(
                f"Built {stats.get('total_models', 0)} models. Loaded {tag}.",
                timeout=10,
            )
        except Exception as exc:
            self.notify(f"Fetch failed: {exc}", severity="error")

    def action_cancel(self) -> None:
        pass

    # ── View switching ────────────────────────────────────────────────────

    @on(Select.Changed, "#dev_view_select")
    def _on_view_changed(self, event: Select.Changed) -> None:
        if event.value == Select.BLANK:
            return
        if str(event.value) == "main":
            self.exit(result=SWITCH_TO_MAIN_TUI)
        if str(event.value) == "cli":
            self.exit(result=SWITCH_TO_CLI_TUI)
        if str(event.value) == "dev":
            self.exit(result=SWITCH_TO_DEV_TUI)

    # ── Theme / chrome ────────────────────────────────────────────────────

    @on(Select.Changed, "#dev_theme_select")
    def _on_theme_changed(self, event: Select.Changed) -> None:
        if event.value == Select.BLANK:
            return
        selected = self.theme_catalog.resolve(str(event.value))
        if not selected or selected == self.theme_name:
            return
        self._apply_theme(selected, notify=True)
        self.call_after_refresh(self._strip_theme_select_prefix)

    @on(Button.Pressed, "#support_button")
    def _on_support(self) -> None:
        self.push_screen(SupportModal())

    @on(Button.Pressed, "#dev_close_button")
    def _on_close(self) -> None:
        self.exit()

    def _logo_renderable(self) -> Text:
        return logo_renderable(self.theme_catalog, self.theme_name)

    def _apply_theme(self, theme_name: str, notify: bool = False) -> None:
        self.theme_name = apply_theme(
            self,
            theme_catalog=self.theme_catalog,
            theme_options=self.theme_options,
            current_theme_name=self.theme_name,
            new_theme_name=theme_name,
            state=self.state,
            logo_widget_id="#dev_logo",
            notify=notify,
        )

    def _strip_theme_select_prefix(self) -> None:
        strip_theme_select_prefix(self, selector="#dev_theme_select SelectCurrent Static#label")
        strip_theme_select_prefix(self, selector="#dev_view_select SelectCurrent Static#label")

    # ── Connection badge ──────────────────────────────────────────────────

    def _update_clock(self) -> None:
        update_clock_widget(self, widget_id="#dev_clock")

    def _set_connection_badge_checking(self) -> None:
        set_connection_badge_state(self, badge_id="#dev_connection_badge", state="checking")

    def _render_connection_status(self, probe: ConnectionProbe) -> None:
        set_connection_badge_state(
            self,
            badge_id="#dev_connection_badge",
            state=badge_state_for_probe(probe),
        )

    @work(group="dm_connection_probe", exclusive=True, thread=False)
    async def _probe_connection_health(self) -> None:
        self._set_connection_badge_checking()
        try:
            from netbox_cli.cli import _get_client  # noqa: PLC0415

            client = _get_client()
            probe_fn = getattr(client, "probe_connection", None)
            if callable(probe_fn):
                probe = probe_fn()
                if inspect.isawaitable(probe):
                    probe = await probe
                if isinstance(probe, ConnectionProbe):
                    self._render_connection_status(probe)
                    return
            response = await client.request(
                "GET", "/", headers={"Content-Type": "application/json"}
            )
            headers = getattr(response, "headers", {}) or {}
            version = headers.get("API-Version", "") if isinstance(headers, dict) else ""
            status = int(getattr(response, "status", 0) or 0)
            ok = status < 400 or status == 403
            self._render_connection_status(
                ConnectionProbe(
                    status=status,
                    version=version,
                    ok=ok,
                    error=None if ok else getattr(response, "text", ""),
                )
            )
            return
        except Exception:
            pass
        self._render_connection_status(
            ConnectionProbe(status=0, version="", ok=False, error="no config")
        )


def run_django_model_tui(
    store: DjangoModelStore | None = None,
    *,
    theme_name: str | None = None,
) -> None:
    """Launch the Django Model Inspector TUI with mode-switching support."""
    if store is None:
        store = DjangoModelStore()
    try:
        app = DjangoModelTuiApp(store=store, theme_name=theme_name)
        result = app.run()
        from netbox_cli.cli import _get_client, _get_index  # noqa: PLC0415

        if result == SWITCH_TO_MAIN_TUI:
            from .app import run_tui

            run_tui(
                client=_get_client(),
                index=_get_index(),
                theme_name=app.theme_name,
            )
        elif result == SWITCH_TO_CLI_TUI:
            from .cli_tui import run_cli_tui

            run_cli_tui(
                client=_get_client(),
                index=_get_index(),
                theme_name=app.theme_name,
            )
        elif result == SWITCH_TO_DEV_TUI:
            from .dev_app import run_dev_tui

            run_dev_tui(
                client=_get_client(),
                index=_get_index(),
                theme_name=app.theme_name,
            )
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    except Exception as exc:  # noqa: BLE001
        detail = str(exc).strip() or exc.__class__.__name__
        raise RuntimeError(f"Unable to launch the Django Model TUI: {detail}") from None
