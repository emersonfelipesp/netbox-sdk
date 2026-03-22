from __future__ import annotations

from typing import Literal

from textual.containers import Vertical
from textual.widgets import Button, Static

ButtonSize = Literal["small", "medium", "large"]
ThemeTone = Literal["default", "primary", "secondary", "success", "warning", "error", "muted"]
SurfaceTone = Literal["default", "background", "surface", "panel"]
ButtonChrome = Literal["outline", "soft"]


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
