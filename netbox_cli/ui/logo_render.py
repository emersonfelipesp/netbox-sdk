from __future__ import annotations

from rich.style import Style
from rich.text import Text

from netbox_cli.theme_registry import ThemeDefinition

_NETBOX_BRIGHT_TEAL = "#00F2D4"
_NETBOX_DARK_TEAL = "#00857D"
_NETBOX_DARK_WORDMARK = "#FFFFFF"
_NETBOX_LIGHT_WORDMARK = "#001423"


def build_netbox_logo(theme: ThemeDefinition) -> Text:
    """Render a compact NetBox wordmark suitable for terminal headers.

    The full SVG logo is too dense for a small Textual top bar, and image-protocol
    widgets would not degrade reliably across generic terminals and SSH sessions.
    This keeps the official brand palette and a clean horizontal silhouette.
    """
    if theme.name == "netbox-light":
        accent_color = _NETBOX_DARK_TEAL
        wordmark_color = _NETBOX_LIGHT_WORDMARK
    elif theme.name == "netbox-dark":
        accent_color = _NETBOX_BRIGHT_TEAL
        wordmark_color = _NETBOX_DARK_WORDMARK
    else:
        accent_color = theme.colors["primary"]
        wordmark_color = _NETBOX_DARK_WORDMARK if theme.dark else _NETBOX_LIGHT_WORDMARK

    accent_style = Style(color=accent_color, bold=True)
    wordmark_style = Style(color=wordmark_color, bold=True)

    logo = Text(no_wrap=True)
    logo.append("● ", style=accent_style)
    logo.append("Net", style=wordmark_style)
    logo.append("Box", style=accent_style)
    return logo
