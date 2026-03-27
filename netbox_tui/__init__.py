"""Textual UI package for netbox-cli."""

try:
    from netbox_tui.app import NetBoxTuiApp, available_theme_names, resolve_theme_name, run_tui
    from netbox_tui.cli_tui import NbxCliTuiApp, run_cli_tui
    from netbox_tui.dev_app import NetBoxDevTuiApp, run_dev_tui
    from netbox_tui.django_model_app import DjangoModelTuiApp, run_django_model_tui
    from netbox_tui.logs_app import NetBoxLogsTuiApp, run_logs_tui
except ModuleNotFoundError as exc:
    missing = exc.name or ""
    if missing.startswith("textual"):
        raise ModuleNotFoundError(
            "netbox_tui requires optional TUI dependencies. Install with: pip install 'netbox-sdk[tui]'"
        ) from exc
    raise

__all__ = [
    "DjangoModelTuiApp",
    "NbxCliTuiApp",
    "NetBoxDevTuiApp",
    "NetBoxLogsTuiApp",
    "NetBoxTuiApp",
    "available_theme_names",
    "resolve_theme_name",
    "run_cli_tui",
    "run_dev_tui",
    "run_django_model_tui",
    "run_logs_tui",
    "run_tui",
]
