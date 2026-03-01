"""Main application window with navigation sidebar."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GLib

from pulsedeck.ui.pages.dashboard import DashboardPage
from pulsedeck.ui.pages.cpu_page import CpuPage
from pulsedeck.ui.pages.memory_page import MemoryPage
from pulsedeck.ui.pages.storage_page import StoragePage
from pulsedeck.ui.pages.thermal_page import ThermalPage
from pulsedeck.ui.pages.apps_page import AppsPage


CSS = b"""
window {
    background-color: @window_bg_color;
}

.gauge-frame {
    background-color: alpha(@card_bg_color, 0.5);
    border-radius: 12px;
    padding: 8px;
}

.nav-sidebar {
    background-color: alpha(@card_bg_color, 0.3);
}

.nav-sidebar row {
    min-height: 44px;
    border-radius: 8px;
    margin: 2px 6px;
}

.nav-sidebar row:selected {
    background-color: alpha(@accent_bg_color, 0.2);
}

.status-ok {
    color: @success_color;
}

.status-warn {
    color: @warning_color;
}

.status-critical {
    color: @error_color;
}
"""


class PulseDeckWindow(Adw.ApplicationWindow):
    """Main application window with sidebar navigation."""

    def __init__(self, app):
        super().__init__(application=app, title="PulseDeck")
        self.set_default_size(950, 650)
        self.set_size_request(700, 450)

        # Load CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self._pages = {}
        self._current_page = None
        self._build_ui()
        self._navigate_to("dashboard")

    def _build_ui(self):
        # Main layout: NavigationSplitView for sidebar + content
        self._split = Adw.NavigationSplitView()
        self.set_content(self._split)

        # ---- Sidebar ----
        sidebar_page = Adw.NavigationPage(title="PulseDeck")
        sidebar_toolbar = Adw.ToolbarView()
        sidebar_header = Adw.HeaderBar()
        sidebar_header.set_show_end_title_buttons(False)
        sidebar_toolbar.add_top_bar(sidebar_header)

        sidebar_scroll = Gtk.ScrolledWindow()
        sidebar_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self._nav_list = Gtk.ListBox()
        self._nav_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._nav_list.add_css_class("navigation-sidebar")
        self._nav_list.add_css_class("nav-sidebar")
        self._nav_list.connect("row-selected", self._on_nav_selected)

        nav_items = [
            ("dashboard", "Dashboard", "computer-symbolic"),
            ("cpu", "Processor", "processor-symbolic"),
            ("memory", "Memory", "drive-harddisk-symbolic"),
            ("storage", "Storage", "drive-multidisk-symbolic"),
            ("thermal", "Thermal & Fans", "weather-clear-symbolic"),
            ("apps", "Applications", "system-software-install-symbolic"),
        ]

        for key, label, icon_name in nav_items:
            row = Adw.ActionRow(title=label)
            row.set_icon_name(icon_name)
            row.set_activatable(True)
            row._nav_key = key
            self._nav_list.append(row)

        sidebar_scroll.set_child(self._nav_list)
        sidebar_toolbar.set_content(sidebar_scroll)
        sidebar_page.set_child(sidebar_toolbar)
        self._split.set_sidebar(sidebar_page)

        # ---- Content area ----
        self._content_page = Adw.NavigationPage(title="Dashboard")
        content_toolbar = Adw.ToolbarView()

        self._content_header = Adw.HeaderBar()

        # About button
        about_btn = Gtk.Button(icon_name="help-about-symbolic")
        about_btn.set_tooltip_text("About PulseDeck")
        about_btn.connect("clicked", self._show_about)
        self._content_header.pack_end(about_btn)

        content_toolbar.add_top_bar(self._content_header)

        # Stack for pages
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self._stack.set_transition_duration(200)
        content_toolbar.set_content(self._stack)

        self._content_page.set_child(content_toolbar)
        self._split.set_content(self._content_page)

        # Select first row
        first_row = self._nav_list.get_row_at_index(0)
        if first_row:
            self._nav_list.select_row(first_row)

    def _on_nav_selected(self, listbox, row):
        if row is None:
            return
        key = row._nav_key
        self._navigate_to(key)

    def _navigate_to(self, key):
        if key == self._current_page:
            return

        # Create page lazily
        if key not in self._pages:
            page = self._create_page(key)
            self._pages[key] = page
            self._stack.add_named(page, key)

        self._stack.set_visible_child_name(key)
        self._current_page = key

        titles = {
            "dashboard": "Dashboard",
            "cpu": "Processor",
            "memory": "Memory",
            "storage": "Storage",
            "thermal": "Thermal & Fans",
            "apps": "Applications",
        }
        self._content_page.set_title(titles.get(key, "PulseDeck"))

    def _create_page(self, key):
        pages = {
            "dashboard": DashboardPage,
            "cpu": CpuPage,
            "memory": MemoryPage,
            "storage": StoragePage,
            "thermal": ThermalPage,
            "apps": AppsPage,
        }
        cls = pages.get(key)
        if cls:
            return cls()
        # Fallback
        box = Gtk.Box()
        box.append(Gtk.Label(label=f"Page: {key}"))
        return box

    def _show_about(self, *args):
        about = Adw.AboutWindow(
            transient_for=self,
            application_name="PulseDeck",
            application_icon="utilities-system-monitor-symbolic",
            version="1.0.0",
            developer_name="PulseDeck Contributors",
            license_type=Gtk.License.MIT_X11,
            website="https://github.com/arif481/PulseDeck",
            issue_url="https://github.com/arif481/PulseDeck/issues",
            comments="Lightweight system monitor & assistant for Linux.\n\n"
                     "Monitor CPU, RAM, Storage, Temperature, Fans, "
                     "and manage installed applications — all without the terminal.",
        )
        about.present()

    def do_close_request(self):
        """Clean up timers when window closes."""
        for page in self._pages.values():
            if hasattr(page, "cleanup"):
                page.cleanup()
        return False
