"""Theme-aware Rich renderables for the NetBox CLI wordmark."""

from __future__ import annotations

from rich.style import Style
from rich.text import Text

from netbox_tui.theme_registry import ThemeDefinition


def build_netbox_logo(theme: ThemeDefinition) -> Text:
    """Render a compact NetBox wordmark suitable for terminal headers.

    The full SVG logo is too dense for a small Textual top bar, and image-protocol
    widgets would not degrade reliably across generic terminals and SSH sessions.
    This keeps the official brand palette and a clean horizontal silhouette.
    """
    variables = theme.variables
    accent_color = variables.get("nb-logo-accent", theme.colors["primary"])
    default_wordmark = theme.colors["surface"] if theme.dark else theme.colors["background"]
    wordmark_color = variables.get("nb-logo-wordmark", default_wordmark)

    accent_style = Style(color=accent_color, bold=True)
    wordmark_style = Style(color=wordmark_color, bold=True)

    logo = Text(no_wrap=True)
    logo.append("● ", style=accent_style)
    logo.append("Net", style=wordmark_style)
    logo.append("Box", style=accent_style)
    return logo
