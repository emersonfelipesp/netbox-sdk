"""Shared Textual widget primitives with prop-style sizing and theme semantics."""

from __future__ import annotations

from typing import Literal

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, OptionList, Static

ButtonSize = Literal["small", "medium", "large"]
ThemeTone = Literal["default", "primary", "secondary", "success", "warning", "error", "muted"]
SurfaceTone = Literal["default", "background", "surface", "panel"]
ButtonChrome = Literal["outline", "soft"]
SPONSOR_URL = "https://github.com/sponsors/emersonfelipesp"


def _compose_classes(*tokens: str, classes: str | None = None) -> str:
    class_names = [token for token in tokens if token]
    if classes:
        class_names.append(classes)
    return " ".join(class_names)


class NbxButton(Button):
    """Project-standard Textual button with prop-like size and theme controls."""

    def __init__(
        self,
        label: str | None = None,
        variant: Button.ButtonVariant = "default",
        *,
        size: ButtonSize = "medium",
        tone: ThemeTone = "default",
        chrome: ButtonChrome = "outline",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        tooltip: object | None = None,
        action: str | None = None,
        compact: bool = False,
        flat: bool = False,
    ) -> None:
        super().__init__(
            label,
            variant,
            name=name,
            id=id,
            classes=_compose_classes(
                "nbx-button",
                f"nbx-button--{size}",
                f"nbx-tone--{tone}",
                f"nbx-button--{chrome}",
                classes=classes,
            ),
            disabled=disabled,
            tooltip=tooltip,
            action=action,
            compact=compact,
            flat=flat,
        )


class NbxPanelHeader(Vertical):
    """Reusable panel header with prop-like theme tone."""

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        *,
        tone: ThemeTone = "primary",
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            classes=_compose_classes("nbx-panel-header", f"nbx-tone--{tone}", classes=classes),
        )
        self._title = title
        self._subtitle = subtitle

    def compose(self):
        yield Static(self._title, classes="panel-title")
        if self._subtitle:
            yield Static(self._subtitle, classes="panel-subtitle")


class NbxPanelBody(Vertical):
    """Body container for panel composition with prop-like surface selection."""

    def __init__(
        self,
        *,
        surface: SurfaceTone = "default",
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            classes=_compose_classes(
                "nbx-panel-body",
                f"nbx-surface--{surface}",
                classes=classes,
            ),
        )


class _CrumbButton(Button):
    """Internal breadcrumb navigation button. Do not instantiate outside ContextBreadcrumb."""

    def __init__(
        self,
        label: str,
        *,
        crumb_label: str,
        nav_group: str,
        nav_resource: str,
        classes: str | None = None,
    ) -> None:
        super().__init__(label, classes=classes)
        self.crumb_label = crumb_label
        self.nav_group = nav_group
        self.nav_resource = nav_resource


class ContextBreadcrumb(Horizontal):
    """Clickable breadcrumb widget for the top navigation context bar.

    Call ``set_crumbs(crumbs)`` to rebuild the display. Each crumb is a
    ``(label, group_or_None, resource_or_None)`` tuple. The last entry is
    always the current page (rendered as static text). Earlier entries that
    carry a group and resource are rendered as clickable buttons; pressing
    one emits a ``CrumbSelected`` message.
    """

    class CrumbSelected(Message):
        """Emitted when a clickable breadcrumb segment is pressed."""

        ALLOW_SELECTOR_MATCH = True

        def __init__(
            self,
            widget: ContextBreadcrumb,
            *,
            label: str,
            group: str,
            resource: str,
            button: _CrumbButton,
        ) -> None:
            super().__init__()
            self._widget = widget
            self.label = label
            self.group = group
            self.resource = resource
            self.button = button

        @property
        def control(self) -> ContextBreadcrumb:
            return self._widget

    class MenuOptionSelected(Message):
        """Emitted when a breadcrumb dropdown option is chosen."""

        ALLOW_SELECTOR_MATCH = True

        def __init__(self, widget: ContextBreadcrumb, *, group: str, resource: str) -> None:
            super().__init__()
            self._widget = widget
            self.group = group
            self.resource = resource

        @property
        def control(self) -> ContextBreadcrumb:
            return self._widget

    def __init__(self, *children, **kwargs) -> None:
        super().__init__(*children, **kwargs)
        self._menu_targets: list[tuple[str, str]] = []
        self._menu_anchor_key: str | None = None

    def compose(self) -> ComposeResult:
        yield Static("Context:", classes="breadcrumb-prefix")
        yield Static("<none>", classes="breadcrumb-crumb breadcrumb-current")
        yield OptionList(id="context_breadcrumb_menu", classes="hidden")

    def set_crumbs(self, crumbs: list[tuple[str, str | None, str | None]]) -> None:
        """Rebuild breadcrumb from crumbs list and remount children."""
        self.close_menu()
        for widget in self.query(".breadcrumb-crumb,.breadcrumb-sep"):
            widget.remove()

        if not crumbs:
            self.mount(Static("<none>", classes="breadcrumb-crumb breadcrumb-current"))
            return

        last_idx = len(crumbs) - 1
        to_mount = []
        for i, (label, group, resource) in enumerate(crumbs):
            if i > 0:
                to_mount.append(Static("/", classes="breadcrumb-sep"))
            is_last = i == last_idx
            if is_last or not group or not resource:
                to_mount.append(Static(label, classes="breadcrumb-crumb breadcrumb-current"))
            else:
                to_mount.append(
                    _CrumbButton(
                        label,
                        crumb_label=label,
                        nav_group=group,
                        nav_resource=resource,
                        classes="breadcrumb-crumb breadcrumb-link",
                    )
                )
        self.mount(*to_mount)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if isinstance(event.button, _CrumbButton):
            self.post_message(
                self.CrumbSelected(
                    widget=self,
                    label=event.button.crumb_label,
                    group=event.button.nav_group,
                    resource=event.button.nav_resource,
                    button=event.button,
                )
            )
            event.stop()

    def open_menu(
        self,
        *,
        anchor: _CrumbButton,
        options: list[tuple[str, str, str]],
    ) -> None:
        """Show a theme-aware dropdown menu beneath the selected crumb."""
        option_list = self.query_one("#context_breadcrumb_menu", OptionList)
        anchor_key = f"{anchor.crumb_label}:{anchor.nav_group}:{anchor.nav_resource}"
        if "hidden" not in option_list.classes and self._menu_anchor_key == anchor_key:
            self.close_menu()
            return

        prompts = [label for label, _, _ in options]
        self._menu_targets = [(group, resource) for _, group, resource in options]
        self._menu_anchor_key = anchor_key
        option_list.set_options(prompts)
        option_list.styles.width = max(len(prompt) for prompt in prompts) + 4
        option_list.styles.display = "block"
        option_list.styles.offset = (
            anchor.region.x - self.region.x,
            self.region.height,
        )
        option_list.remove_class("hidden")
        option_list.highlighted = 0 if prompts else None
        option_list.focus(scroll_visible=False)

    def close_menu(self) -> None:
        option_list = self.query_one("#context_breadcrumb_menu", OptionList)
        option_list.styles.display = "none"
        option_list.add_class("hidden")
        option_list.set_options([])
        self._menu_targets = []
        self._menu_anchor_key = None

    @property
    def menu_open(self) -> bool:
        option_list = self.query_one("#context_breadcrumb_menu", OptionList)
        return "hidden" not in option_list.classes

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id != "context_breadcrumb_menu":
            return
        option_index = getattr(event, "option_index", getattr(event, "index", -1))
        if option_index < 0 or option_index >= len(self._menu_targets):
            self.close_menu()
            return
        group, resource = self._menu_targets[option_index]
        self.close_menu()
        self.post_message(self.MenuOptionSelected(widget=self, group=group, resource=resource))
        event.stop()


class SupportModal(ModalScreen[None]):
    """Shared sponsor modal for the main and dev TUIs."""

    def compose(self) -> ComposeResult:
        with Vertical(id="support_modal_dialog"):
            yield Static("⭐ Support netbox-cli", id="support_modal_title")
            yield Static(
                "If this project helps you, you can ⭐ support ongoing work on GitHub Sponsors.",
                id="support_modal_copy",
            )
            yield Static(SPONSOR_URL, id="support_modal_url")
            with Horizontal(id="support_modal_actions"):
                yield NbxButton("Close", id="support_modal_close", size="small", tone="muted")
                yield NbxButton(
                    "Open Sponsors Page",
                    id="support_modal_open",
                    size="small",
                    tone="primary",
                )

    def on_mount(self) -> None:
        theme_name = str(getattr(self.app, "theme_name", "") or getattr(self.app, "theme", ""))
        if theme_name:
            for class_name in tuple(self.classes):
                if class_name.startswith("theme-"):
                    self.remove_class(class_name)
            self.add_class(f"theme-{theme_name}")
        self.query_one("#support_modal_open", Button).focus()

    @on(Button.Pressed, "#support_modal_close")
    def close_modal(self) -> None:
        self.dismiss()

    @on(Button.Pressed, "#support_modal_open")
    def open_sponsor_page(self) -> None:
        self.app.open_url(SPONSOR_URL)
        self.dismiss()
