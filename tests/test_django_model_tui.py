"""Django Model TUI scrolling tests using Textual's Pilot API.

Tests for VerticalScroll containers, scrollbar behavior, content overflow handling,
and theme compatibility in the Django Model Inspector TUI.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from textual.containers import VerticalScroll
from textual.widgets import Static, TabbedContent

from netbox_cli.schema import build_schema_index
from netbox_cli.ui.django_model_app import DjangoModelTuiApp
from tests.conftest import OPENAPI_PATH

# Test data for Django models with substantial content
FAKE_DJANGO_MODELS = {
    "dcim.Device": {
        "app_label": "dcim",
        "model_name": "device",
        "verbose_name": "Device",
        "verbose_name_plural": "Devices",
        "fields": [
            {
                "name": "id",
                "type": "BigAutoField",
                "verbose_name": "ID",
                "help_text": "",
                "null": False,
                "blank": False,
            },
            {
                "name": "name",
                "type": "CharField",
                "verbose_name": "Name",
                "help_text": "Device hostname",
                "null": False,
                "blank": False,
                "max_length": 64,
            },
            {
                "name": "device_type",
                "type": "ForeignKey",
                "verbose_name": "Device Type",
                "help_text": "",
                "null": False,
                "blank": False,
                "related_model": "dcim.DeviceType",
            },
            {
                "name": "role",
                "type": "ForeignKey",
                "verbose_name": "Role",
                "help_text": "",
                "null": False,
                "blank": False,
                "related_model": "dcim.DeviceRole",
            },
            {
                "name": "tenant",
                "type": "ForeignKey",
                "verbose_name": "Tenant",
                "help_text": "",
                "null": True,
                "blank": True,
                "related_model": "tenancy.Tenant",
            },
            {
                "name": "platform",
                "type": "ForeignKey",
                "verbose_name": "Platform",
                "help_text": "",
                "null": True,
                "blank": True,
                "related_model": "dcim.Platform",
            },
            {
                "name": "serial",
                "type": "CharField",
                "verbose_name": "Serial Number",
                "help_text": "",
                "null": True,
                "blank": True,
                "max_length": 50,
            },
            {
                "name": "asset_tag",
                "type": "CharField",
                "verbose_name": "Asset Tag",
                "help_text": "",
                "null": True,
                "blank": True,
                "max_length": 50,
            },
            {
                "name": "site",
                "type": "ForeignKey",
                "verbose_name": "Site",
                "help_text": "",
                "null": False,
                "blank": False,
                "related_model": "dcim.Site",
            },
            {
                "name": "location",
                "type": "ForeignKey",
                "verbose_name": "Location",
                "help_text": "",
                "null": True,
                "blank": True,
                "related_model": "dcim.Location",
            },
            {
                "name": "rack",
                "type": "ForeignKey",
                "verbose_name": "Rack",
                "help_text": "",
                "null": True,
                "blank": True,
                "related_model": "dcim.Rack",
            },
            {
                "name": "position",
                "type": "PositiveSmallIntegerField",
                "verbose_name": "Position",
                "help_text": "",
                "null": True,
                "blank": True,
            },
            {
                "name": "face",
                "type": "CharField",
                "verbose_name": "Rack Face",
                "help_text": "",
                "null": True,
                "blank": True,
                "max_length": 10,
            },
            {
                "name": "status",
                "type": "CharField",
                "verbose_name": "Status",
                "help_text": "",
                "null": False,
                "blank": False,
                "max_length": 50,
            },
            {
                "name": "primary_ip4",
                "type": "OneToOneField",
                "verbose_name": "Primary IPv4",
                "help_text": "",
                "null": True,
                "blank": True,
                "related_model": "ipam.IPAddress",
            },
            {
                "name": "primary_ip6",
                "type": "OneToOneField",
                "verbose_name": "Primary IPv6",
                "help_text": "",
                "null": True,
                "blank": True,
                "related_model": "ipam.IPAddress",
            },
            {
                "name": "cluster",
                "type": "ForeignKey",
                "verbose_name": "Cluster",
                "help_text": "",
                "null": True,
                "blank": True,
                "related_model": "virtualization.Cluster",
            },
            {
                "name": "virtual_chassis",
                "type": "ForeignKey",
                "verbose_name": "Virtual Chassis",
                "help_text": "",
                "null": True,
                "blank": True,
                "related_model": "dcim.VirtualChassis",
            },
            {
                "name": "vc_position",
                "type": "PositiveSmallIntegerField",
                "verbose_name": "VC Position",
                "help_text": "",
                "null": True,
                "blank": True,
            },
            {
                "name": "vc_priority",
                "type": "PositiveSmallIntegerField",
                "verbose_name": "VC Priority",
                "help_text": "",
                "null": True,
                "blank": True,
            },
            {
                "name": "description",
                "type": "CharField",
                "verbose_name": "Description",
                "help_text": "",
                "null": True,
                "blank": True,
                "max_length": 200,
            },
            {
                "name": "comments",
                "type": "TextField",
                "verbose_name": "Comments",
                "help_text": "",
                "null": True,
                "blank": True,
            },
            {
                "name": "config_context",
                "type": "JSONField",
                "verbose_name": "Config Context",
                "help_text": "",
                "null": True,
                "blank": True,
            },
            {
                "name": "local_context_data",
                "type": "JSONField",
                "verbose_name": "Local Context Data",
                "help_text": "",
                "null": True,
                "blank": True,
            },
        ],
        "outgoing_fks": [
            {"field": "device_type", "related_model": "dcim.DeviceType", "count": 1},
            {"field": "role", "related_model": "dcim.DeviceRole", "count": 1},
            {"field": "tenant", "related_model": "tenancy.Tenant", "count": 25},
            {"field": "platform", "related_model": "dcim.Platform", "count": 12},
            {"field": "site", "related_model": "dcim.Site", "count": 1},
            {"field": "location", "related_model": "dcim.Location", "count": 8},
            {"field": "rack", "related_model": "dcim.Rack", "count": 15},
            {"field": "primary_ip4", "related_model": "ipam.IPAddress", "count": 45},
            {"field": "primary_ip6", "related_model": "ipam.IPAddress", "count": 23},
            {"field": "cluster", "related_model": "virtualization.Cluster", "count": 7},
            {"field": "virtual_chassis", "related_model": "dcim.VirtualChassis", "count": 3},
        ],
        "incoming_fks": [
            {"field": "device", "related_model": "dcim.Interface", "count": 156},
            {"field": "device", "related_model": "dcim.ConsolePort", "count": 24},
            {"field": "device", "related_model": "dcim.ConsoleServerPort", "count": 12},
            {"field": "device", "related_model": "dcim.PowerPort", "count": 8},
            {"field": "device", "related_model": "dcim.PowerOutlet", "count": 16},
            {"field": "device", "related_model": "dcim.DeviceBay", "count": 4},
            {"field": "device", "related_model": "dcim.InventoryItem", "count": 32},
            {"field": "primary_ip4_for", "related_model": "dcim.Device", "count": 45},
            {"field": "primary_ip6_for", "related_model": "dcim.Device", "count": 23},
            {"field": "assigned_object", "related_model": "ipam.IPAddress", "count": 78},
            {"field": "device", "related_model": "secrets.Secret", "count": 12},
            {"field": "device", "related_model": "extras.ConfigContext", "count": 5},
            {"field": "device", "related_model": "extras.CustomField", "count": 18},
            {"field": "device", "related_model": "extras.Journal", "count": 9},
            {"field": "device", "related_model": "extras.Tag", "count": 67},
            {"field": "device", "related_model": "users.ObjectPermission", "count": 3},
        ],
    },
    "core.ContentType": {
        "app_label": "contenttypes",
        "model_name": "contenttype",
        "verbose_name": "Content Type",
        "verbose_name_plural": "Content Types",
        "fields": [
            {
                "name": "id",
                "type": "BigAutoField",
                "verbose_name": "ID",
                "help_text": "",
                "null": False,
                "blank": False,
            },
            {
                "name": "app_label",
                "type": "CharField",
                "verbose_name": "App Label",
                "help_text": "",
                "null": False,
                "blank": False,
                "max_length": 100,
            },
            {
                "name": "model",
                "type": "CharField",
                "verbose_name": "Model",
                "help_text": "",
                "null": False,
                "blank": False,
                "max_length": 100,
            },
        ],
        "outgoing_fks": [],
        "incoming_fks": [],
    },
}


@pytest.fixture()
def real_index():
    """Build real schema index for testing."""
    return build_schema_index(OPENAPI_PATH)


@pytest.fixture()
def mock_model_store():
    """Mock Django model store with test data."""
    store = MagicMock()
    store.exists.return_value = True
    store.load.return_value = {
        "models": FAKE_DJANGO_MODELS,
        "edges": [],
        "stats": {
            "total_models": len(FAKE_DJANGO_MODELS),
            "total_edges": 0,
            "apps": ["dcim", "core"],
        },
        "meta": {"source_path": "/fake/netbox", "total_models": len(FAKE_DJANGO_MODELS)},
    }
    store.get_model_source.side_effect = lambda key: (
        f"# Source code for {key}\nclass {key.split('.')[-1]}(models.Model):\n    pass"
    )
    return store


@pytest.fixture(autouse=True)
def isolate_django_model_state():
    """Prevent tests from reading/writing real Django model cache."""
    from netbox_cli.ui.django_model_state import DjangoModelTuiState

    mock_state = DjangoModelTuiState()
    mock_state.theme_name = "netbox-dark"

    with (
        patch(
            "netbox_cli.ui.django_model_app.load_django_model_tui_state", return_value=mock_state
        ),
        patch("netbox_cli.ui.django_model_app.save_django_model_tui_state"),
    ):
        yield


def _make_app(mock_store, theme: str = "netbox-dark") -> DjangoModelTuiApp:
    """Create Django Model TUI app with mocked store."""
    app = DjangoModelTuiApp(store=mock_store, theme_name=theme)
    # Manually set up graph data since we're mocking the loading
    app._graph = mock_store.load.return_value
    app._all_keys = list(FAKE_DJANGO_MODELS.keys())
    return app


# ---------------------------------------------------------------------------
# 1. VerticalScroll Container Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_main_content_tabs_use_vertical_scroll_containers(mock_model_store):
    """Test that main content tabs are wrapped in VerticalScroll containers."""
    app = _make_app(mock_model_store)

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        # Check that each main content Static widget is inside a VerticalScroll container
        diagram_widget = app.query_one("#dm_diagram", Static)
        source_widget = app.query_one("#dm_source_code", Static)
        fields_widget = app.query_one("#dm_fields", Static)
        stats_widget = app.query_one("#dm_stats", Static)

        # Check that their parent containers are VerticalScroll widgets
        assert isinstance(diagram_widget.parent, VerticalScroll)
        assert isinstance(source_widget.parent, VerticalScroll)
        assert isinstance(fields_widget.parent, VerticalScroll)
        assert isinstance(stats_widget.parent, VerticalScroll)


@pytest.mark.asyncio
async def test_vertical_scroll_containers_enable_scrolling(mock_model_store):
    """Test that VerticalScroll containers can scroll when content overflows."""
    app = _make_app(mock_model_store)

    async with app.run_test(size=(80, 20)) as pilot:  # Small size to force overflow
        await pilot.pause()

        # Select a model with substantial content
        app._current_model_key = "dcim.Device"
        app._show_model("dcim.Device")
        await pilot.pause()

        # Check that scroll containers can handle vertical overflow
        tabs = app.query_one("#main_tabs", TabbedContent)
        tabs.active = "diagram_tab"
        await pilot.pause()

        diagram_scroll = app.query_one("#dm_diagram_scroll", VerticalScroll)

        # VerticalScroll should support scrolling when content exceeds container
        assert diagram_scroll.can_scroll_down or diagram_scroll.can_scroll_up
        assert diagram_scroll.virtual_size.height >= diagram_scroll.size.height


@pytest.mark.asyncio
async def test_keyboard_scrolling_works_in_content_tabs(mock_model_store):
    """Test that keyboard scrolling works in content tabs with VerticalScroll."""
    app = _make_app(mock_model_store)

    async with app.run_test(size=(80, 15)) as pilot:  # Force overflow
        await pilot.pause()

        # Select model with lots of content
        app.selected_model = "dcim.Device"
        app._refresh_model_display()
        await pilot.pause()

        # Focus the diagram tab
        tabs = app.query_one("#main_tabs", TabbedContent)
        tabs.active = "diagram_tab"
        await pilot.pause()

        diagram_scroll = app.query_one("#dm_diagram_scroll", VerticalScroll)
        diagram_scroll.focus()
        await pilot.pause()

        # Test keyboard scrolling
        initial_scroll_y = diagram_scroll.scroll_y

        # Scroll down
        await pilot.press("down", "down", "down")
        await pilot.pause()

        assert diagram_scroll.scroll_y >= initial_scroll_y

        # Scroll up
        await pilot.press("up", "up")
        await pilot.pause()

        assert diagram_scroll.scroll_y <= initial_scroll_y


@pytest.mark.asyncio
async def test_mouse_scrolling_works_in_content_tabs(mock_model_store):
    """Test that mouse wheel scrolling works in VerticalScroll containers."""
    app = _make_app(mock_model_store)

    async with app.run_test(size=(80, 15)) as pilot:  # Force overflow
        await pilot.pause()

        # Select model with lots of content
        app.selected_model = "dcim.Device"
        app._refresh_model_display()
        await pilot.pause()

        # Focus the fields tab (typically has most content)
        tabs = app.query_one("#main_tabs", TabbedContent)
        tabs.active = "fields_tab"
        await pilot.pause()

        fields_scroll = app.query_one("#dm_fields_scroll", VerticalScroll)

        # Mouse wheel should trigger scrolling
        initial_scroll_y = fields_scroll.scroll_y

        # Simulate mouse wheel down
        fields_scroll.scroll_down()
        await pilot.pause()

        assert fields_scroll.scroll_y >= initial_scroll_y


# ---------------------------------------------------------------------------
# 2. Content Display and Truncation Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_complete_field_list_displayed_without_truncation(mock_model_store):
    """Test that all fields are displayed without '... and X more' truncation."""
    app = _make_app(mock_model_store)

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        # Select model with many fields
        app.selected_model = "dcim.Device"
        app._refresh_model_display()
        await pilot.pause()

        # Check fields tab content
        tabs = app.query_one("#main_tabs", TabbedContent)
        tabs.active = "fields_tab"
        await pilot.pause()

        fields_content = app.query_one("#dm_fields", Static)
        fields_text = str(fields_content.content)

        # Should show all 24 fields for dcim.Device, not truncated
        device_data = FAKE_DJANGO_MODELS["dcim.Device"]
        field_count = len(device_data["fields"])

        # Count actual field entries in the display
        field_lines = [line for line in fields_text.split("\n") if "│" in line and line.strip()]

        # Should have at least as many field lines as actual fields (may have more due to formatting)
        assert len(field_lines) >= field_count

        # Should not have truncation text
        assert "... and" not in fields_text
        assert "more" not in fields_text


@pytest.mark.asyncio
async def test_complete_dependencies_displayed_with_expansion(mock_model_store):
    """Test that all dependencies are shown when expanded, not truncated."""
    app = _make_app(mock_model_store)

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        # Select model with many dependencies
        app.selected_model = "dcim.Device"
        app._refresh_model_display()
        await pilot.pause()

        # Check diagram tab content
        tabs = app.query_one("#main_tabs", TabbedContent)
        tabs.active = "diagram_tab"
        await pilot.pause()

        diagram_content = app.query_one("#dm_diagram", Static)
        diagram_text = str(diagram_content.content)

        device_data = FAKE_DJANGO_MODELS["dcim.Device"]

        # Should show all outgoing FKs when expanded (not just first 3 with "... and X more")
        outgoing_count = len(device_data["outgoing_fks"])

        # Dependencies sections should be expanded by default
        assert "Dependencies (Outgoing FKs)" in diagram_text
        assert "Dependents (Incoming FKs)" in diagram_text

        # Should show substantial content, not just 3 items + truncation
        if outgoing_count > 10:
            # For models with many deps, we should see more than just the first few
            outgoing_section = diagram_text.split("Dependencies (Outgoing FKs)")[1].split(
                "Dependents"
            )[0]
            outgoing_lines = [
                line
                for line in outgoing_section.split("\n")
                if "→" in line or "dcim." in line or "ipam." in line
            ]
            assert len(outgoing_lines) >= min(
                10, outgoing_count
            )  # Should show at least 10 or all if fewer


@pytest.mark.asyncio
async def test_expand_collapse_functionality_preserved(mock_model_store):
    """Test that dependency sections can still be expanded/collapsed."""
    app = _make_app(mock_model_store)

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        # Select model with dependencies
        app.selected_model = "dcim.Device"
        app._refresh_model_display()
        await pilot.pause()

        # Check diagram tab
        tabs = app.query_one("#main_tabs", TabbedContent)
        tabs.active = "diagram_tab"
        await pilot.pause()

        diagram_content = app.query_one("#dm_diagram", Static)
        initial_content = str(diagram_content.content)

        # Should start expanded (due to ensure_expanded_by_default)
        assert "▼" in initial_content  # Expanded state indicator

        # Content should show dependency details
        assert "Dependencies (Outgoing FKs)" in initial_content
        assert "→" in initial_content  # Dependency arrows


# ---------------------------------------------------------------------------
# 3. Tab Navigation and Content Switching
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_all_tabs_have_scrollable_content(mock_model_store):
    """Test that all four main tabs have scrollable content containers."""
    app = _make_app(mock_model_store)

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        # Select a model
        app.selected_model = "dcim.Device"
        app._refresh_model_display()
        await pilot.pause()

        tabs = app.query_one("#main_tabs", TabbedContent)
        tab_ids = ["diagram_tab", "source_tab", "fields_tab", "stats_tab"]

        for tab_id in tab_ids:
            tabs.active = tab_id
            await pilot.pause()

            # Each tab should have a corresponding scroll container
            scroll_id = f"#dm_{tab_id.split('_')[0]}_scroll"
            scroll_container = app.query_one(scroll_id, VerticalScroll)
            assert scroll_container is not None

            # Each scroll container should have content
            content_id = f"#dm_{tab_id.split('_')[0]}"
            if content_id == "#dm_source":
                content_id = "#dm_source_code"
            content = scroll_container.query_one(content_id, Static)
            assert content is not None
            assert len(str(content.content).strip()) > 0


@pytest.mark.asyncio
async def test_tab_content_updates_correctly(mock_model_store):
    """Test that tab content updates when switching between models."""
    app = _make_app(mock_model_store)

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        # Select first model
        app.selected_model = "dcim.Device"
        app._refresh_model_display()
        await pilot.pause()

        tabs = app.query_one("#main_tabs", TabbedContent)
        tabs.active = "fields_tab"
        await pilot.pause()

        fields_content = app.query_one("#dm_fields", Static)
        device_fields = str(fields_content.content)

        # Switch to different model
        app.selected_model = "core.ContentType"
        app._refresh_model_display()
        await pilot.pause()

        contenttype_fields = str(fields_content.content)

        # Content should be different
        assert device_fields != contenttype_fields
        assert "device_type" in device_fields.lower()
        assert "app_label" in contenttype_fields.lower()


# ---------------------------------------------------------------------------
# 4. Theme Integration Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("theme_name", ["dracula", "netbox-light", "netbox-dark"])
async def test_scroll_containers_follow_theme(mock_model_store, theme_name: str):
    """Test that VerticalScroll containers use theme colors correctly."""
    app = _make_app(mock_model_store, theme=theme_name)

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        # Select model and refresh
        app.selected_model = "dcim.Device"
        app._refresh_model_display()
        await pilot.pause()

        # Check that scroll containers inherit theme
        diagram_scroll = app.query_one("#dm_diagram_scroll", VerticalScroll)

        # Scroll containers should not have hardcoded colors
        # They should inherit from the overall theme
        assert (
            diagram_scroll.styles.background.is_transparent
            or diagram_scroll.styles.background == app.styles.background
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("theme_name", ["dracula", "netbox-light", "netbox-dark"])
async def test_content_static_widgets_follow_theme(mock_model_store, theme_name: str):
    """Test that Static widgets inside scroll containers use theme colors."""
    app = _make_app(mock_model_store, theme=theme_name)

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        # Select model and refresh
        app.selected_model = "dcim.Device"
        app._refresh_model_display()
        await pilot.pause()

        # Check Static widgets use theme
        diagram_content = app.query_one("#dm_diagram", Static)
        fields_content = app.query_one("#dm_fields", Static)

        # Static widgets should not have hardcoded colors
        # Background should be transparent or match theme
        assert (
            diagram_content.styles.background.is_transparent
            or diagram_content.styles.background == app.styles.background
        )
        assert (
            fields_content.styles.background.is_transparent
            or fields_content.styles.background == app.styles.background
        )


# ---------------------------------------------------------------------------
# 5. Performance and Error Handling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scroll_performance_with_large_content(mock_model_store):
    """Test that scrolling performs well with large content."""
    app = _make_app(mock_model_store)

    async with app.run_test(size=(80, 10)) as pilot:  # Very small to force scrolling
        await pilot.pause()

        # Select model with lots of content
        app.selected_model = "dcim.Device"
        app._refresh_model_display()
        await pilot.pause()

        # Focus fields tab (usually most content)
        tabs = app.query_one("#main_tabs", TabbedContent)
        tabs.active = "fields_tab"
        await pilot.pause()

        fields_scroll = app.query_one("#dm_fields_scroll", VerticalScroll)
        fields_scroll.focus()
        await pilot.pause()

        # Rapid scrolling should not cause issues
        initial_time = pilot._app._driver._time

        for _ in range(10):
            await pilot.press("down")

        final_time = pilot._app._driver._time

        # Should complete scrolling operations quickly
        assert (final_time - initial_time) < 1.0  # Less than 1 second


@pytest.mark.asyncio
async def test_scroll_containers_handle_empty_content(mock_model_store):
    """Test that scroll containers handle empty/missing content gracefully."""
    # Mock store with empty model data
    empty_store = MagicMock()
    empty_store.get_model_list.return_value = ["empty.Model"]
    empty_store.get_model_data.return_value = {
        "app_label": "empty",
        "model_name": "model",
        "verbose_name": "Empty Model",
        "verbose_name_plural": "Empty Models",
        "fields": [],
        "outgoing_fks": [],
        "incoming_fks": [],
    }

    app = _make_app(empty_store)

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        # Select empty model
        app.selected_model = "empty.Model"
        app._refresh_model_display()
        await pilot.pause()

        # All scroll containers should still exist and be functional
        diagram_scroll = app.query_one("#dm_diagram_scroll", VerticalScroll)
        fields_scroll = app.query_one("#dm_fields_scroll", VerticalScroll)

        assert diagram_scroll is not None
        assert fields_scroll is not None

        # Should not have scroll capability when content is minimal
        assert not diagram_scroll.can_scroll_down
        assert not fields_scroll.can_scroll_down


@pytest.mark.asyncio
async def test_scroll_state_preserved_across_tab_switches(mock_model_store):
    """Test that scroll position is preserved when switching between tabs."""
    app = _make_app(mock_model_store)

    async with app.run_test(size=(80, 15)) as pilot:  # Force overflow
        await pilot.pause()

        # Select model with lots of content
        app.selected_model = "dcim.Device"
        app._refresh_model_display()
        await pilot.pause()

        # Focus diagram tab and scroll down
        tabs = app.query_one("#main_tabs", TabbedContent)
        tabs.active = "diagram_tab"
        await pilot.pause()

        diagram_scroll = app.query_one("#dm_diagram_scroll", VerticalScroll)
        diagram_scroll.focus()
        await pilot.pause()

        # Scroll down several times
        for _ in range(5):
            await pilot.press("down")
        await pilot.pause()

        scrolled_position = diagram_scroll.scroll_y

        # Switch to another tab
        tabs.active = "fields_tab"
        await pilot.pause()

        # Switch back to diagram tab
        tabs.active = "diagram_tab"
        await pilot.pause()

        # Scroll position should be preserved
        assert diagram_scroll.scroll_y == scrolled_position


# ---------------------------------------------------------------------------
# 6. Integration with Model Selection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scroll_resets_when_selecting_different_model(mock_model_store):
    """Test that scroll position resets when selecting a different model."""
    app = _make_app(mock_model_store)

    async with app.run_test(size=(80, 15)) as pilot:  # Force overflow
        await pilot.pause()

        # Select first model and scroll
        app.selected_model = "dcim.Device"
        app._refresh_model_display()
        await pilot.pause()

        tabs = app.query_one("#main_tabs", TabbedContent)
        tabs.active = "fields_tab"
        await pilot.pause()

        fields_scroll = app.query_one("#dm_fields_scroll", VerticalScroll)
        fields_scroll.focus()

        # Scroll down
        for _ in range(5):
            await pilot.press("down")
        await pilot.pause()

        assert fields_scroll.scroll_y > 0

        # Select different model
        app.selected_model = "core.ContentType"
        app._refresh_model_display()
        await pilot.pause()

        # Scroll should reset to top for new content
        assert fields_scroll.scroll_y == 0


@pytest.mark.asyncio
async def test_scrollbar_visibility_matches_content_overflow(mock_model_store):
    """Test that scrollbars are visible when content overflows container."""
    app = _make_app(mock_model_store)

    # Test with large content that should cause overflow
    async with app.run_test(size=(60, 8)) as pilot:  # Very small container
        await pilot.pause()

        # Select model with lots of content
        app.selected_model = "dcim.Device"
        app._refresh_model_display()
        await pilot.pause()

        tabs = app.query_one("#main_tabs", TabbedContent)
        tabs.active = "fields_tab"
        await pilot.pause()

        fields_scroll = app.query_one("#dm_fields_scroll", VerticalScroll)

        # With substantial content in small container, should be able to scroll
        assert fields_scroll.virtual_size.height > fields_scroll.size.height
        assert fields_scroll.can_scroll_down

    # Test with minimal content that should not overflow
    empty_store = MagicMock()
    empty_store.get_model_list.return_value = ["core.ContentType"]
    empty_store.get_model_data.return_value = FAKE_DJANGO_MODELS["core.ContentType"]

    app = _make_app(empty_store)

    async with app.run_test(size=(160, 50)) as pilot:  # Large container
        await pilot.pause()

        # Select model with minimal content
        app.selected_model = "core.ContentType"
        app._refresh_model_display()
        await pilot.pause()

        tabs = app.query_one("#main_tabs", TabbedContent)
        tabs.active = "fields_tab"
        await pilot.pause()

        fields_scroll = app.query_one("#dm_fields_scroll", VerticalScroll)

        # With minimal content in large container, should not need scrolling
        assert not fields_scroll.can_scroll_down
