"""Branch switcher overlay and topbar pill for the main TUI.

Wires the ``netbox-branching`` plugin into the Textual layer:

* :class:`BranchPill` — a small Static widget that lives in the topbar and
  shows the active branch. ``main`` when no branch is active, or
  ``● <schema_id> · <name>`` when one is. Hidden entirely when feature
  detection reports the plugin is not installed.
* :class:`BranchSwitcherScreen` — a modal screen opened by ``Ctrl+B`` that
  lists all branches and lets the user activate one (or revert to ``main``)
  via Enter. Activation persists across worker tasks by writing
  ``X-NetBox-Branch`` onto the client's ``persistent_headers`` dict.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static
from textual.widgets._option_list import Option

if TYPE_CHECKING:
    from textual.widgets import OptionList

    from netbox_sdk.client import NetBoxApiClient

BRANCH_HEADER = "X-NetBox-Branch"
_PILL_INACTIVE_LABEL = "main"


class BranchPill(Static):
    """Topbar pill that reflects the active branch."""

    DEFAULT_CSS = """
    BranchPill {
        padding: 0 1;
        margin: 0 1 0 0;
        color: $text-muted;
        background: transparent;
    }
    BranchPill.-active {
        color: $accent;
        text-style: bold;
    }
    BranchPill.-hidden {
        display: none;
    }
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(_PILL_INACTIVE_LABEL, **kwargs)

    def set_branch(self, schema_id: str | None, name: str | None) -> None:
        if schema_id:
            label = f"● {schema_id}"
            if name:
                label = f"{label} · {name}"
            self.update(label)
            self.add_class("-active")
        else:
            self.update(_PILL_INACTIVE_LABEL)
            self.remove_class("-active")

    def set_available(self, available: bool) -> None:
        # Toggle the widget's visibility entirely so the topbar doesn't
        # reserve space for the pill when the plugin is not installed.
        self.display = available
        if available:
            self.remove_class("-hidden")
        else:
            self.add_class("-hidden")


def apply_branch_to_client(client: NetBoxApiClient, schema_id: str | None) -> None:
    """Set or clear the persistent ``X-NetBox-Branch`` header on the client."""
    if schema_id:
        client.persistent_headers[BRANCH_HEADER] = schema_id
    else:
        client.persistent_headers.pop(BRANCH_HEADER, None)


class BranchSwitcherScreen(ModalScreen[tuple[str | None, str | None] | None]):
    """Modal screen listing branches; dismisses with the selected (schema_id, name)."""

    BINDINGS = [
        Binding("escape", "dismiss_screen", "Cancel", show=False),
    ]

    DEFAULT_CSS = """
    BranchSwitcherScreen {
        align: center middle;
    }
    BranchSwitcherScreen > #branch_switcher_dialog {
        width: 60%;
        max-width: 80;
        height: auto;
        max-height: 70%;
        border: round $accent;
        background: $surface;
        padding: 1 2;
    }
    BranchSwitcherScreen #branch_switcher_title {
        text-style: bold;
    }
    BranchSwitcherScreen #branch_switcher_hint {
        color: $text-muted;
        margin-bottom: 1;
    }
    """

    def __init__(
        self,
        *,
        branches: list[dict[str, Any]],
        active_schema_id: str | None,
    ) -> None:
        super().__init__()
        self._branches = list(branches)
        self._active = active_schema_id

    def compose(self) -> ComposeResult:
        from textual.widgets import OptionList

        options: list[Option] = [Option("main (no active branch)", id="__main__")]
        for branch in self._branches:
            schema_id = str(branch.get("schema_id") or "")
            if not schema_id:
                continue
            name = str(branch.get("name") or "")
            status = ""
            status_value = branch.get("status")
            if isinstance(status_value, dict):
                status = str(status_value.get("value") or status_value.get("label") or "")
            elif status_value:
                status = str(status_value)
            marker = "● " if schema_id == self._active else "  "
            suffix = f" [{status}]" if status else ""
            options.append(Option(f"{marker}{schema_id} · {name}{suffix}", id=schema_id))

        with Vertical(id="branch_switcher_dialog"):
            yield Static("Switch Branch", id="branch_switcher_title")
            yield Static(
                "Enter to activate · Escape to cancel",
                id="branch_switcher_hint",
            )
            yield OptionList(*options, id="branch_switcher_list")

    def on_mount(self) -> None:
        try:
            self.query_one("#branch_switcher_list").focus()
        except Exception:  # noqa: BLE001
            pass

    def on_option_list_option_selected(
        self,
        event: OptionList.OptionSelected,
    ) -> None:
        option_id = event.option.id
        if option_id == "__main__" or option_id is None:
            self.dismiss((None, None))
            return
        for branch in self._branches:
            if str(branch.get("schema_id") or "") == option_id:
                self.dismiss((option_id, str(branch.get("name") or "")))
                return
        self.dismiss((option_id, None))

    def action_dismiss_screen(self) -> None:
        self.dismiss(None)


__all__ = [
    "BRANCH_HEADER",
    "BranchPill",
    "BranchSwitcherScreen",
    "apply_branch_to_client",
]
