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
from pulsedeck.ui.pages.network_page import NetworkPage
from pulsedeck.utils.helpers import is_root


CSS = """
/* ----- Base window ----- */
window {
    background-color: @window_bg_color;
}

/* ----- Sidebar ----- */
.nav-sidebar-container {
    background-color: alpha(@card_bg_color, 0.35);
}

.nav-sidebar {
    background: transparent;
}

.nav-sidebar row {
    min-height: 48px;
    border-radius: 10px;
    margin: 3px 8px;
    transition: all 200ms ease;
}

.nav-sidebar row:selected {
    background-color: alpha(@accent_bg_color, 0.25);
}

.nav-sidebar row:hover:not(:selected) {
    background-color: alpha(@card_bg_color, 0.6);
}

.sidebar-title {
    font-weight: 800;
    font-size: 15px;
    letter-spacing: 0.5px;
}

/* ----- Gauge cards ----- */
.gauge-card {
    background-color: alpha(@card_bg_color, 0.55);
    border-radius: 16px;
    padding: 16px 12px 12px 12px;
    border: 1px solid alpha(@borders, 0.12);
    transition: all 200ms ease;
}

.gauge-card:hover {
    background-color: alpha(@card_bg_color, 0.75);
}

.gauge-label {
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.8px;
    opacity: 0.7;
    margin-top: 6px;
}

/* ----- Section headers ----- */
.section-title {
    font-weight: 800;
    font-size: 18px;
    letter-spacing: 0.3px;
}

.section-subtitle {
    font-weight: 400;
    font-size: 12px;
    opacity: 0.55;
}

/* ----- Info cards ----- */
.info-card {
    background-color: alpha(@card_bg_color, 0.45);
    border-radius: 14px;
    padding: 4px;
    border: 1px solid alpha(@borders, 0.08);
}

/* ----- Stat pills ----- */
.stat-pill {
    background-color: alpha(@card_bg_color, 0.6);
    border-radius: 12px;
    padding: 10px 16px;
    border: 1px solid alpha(@borders, 0.1);
}

.stat-value {
    font-weight: 700;
    font-size: 20px;
}

.stat-label {
    font-weight: 500;
    font-size: 11px;
    opacity: 0.55;
    letter-spacing: 0.5px;
}

/* ----- Graph cards ----- */
.graph-card {
    background-color: alpha(@card_bg_color, 0.35);
    border-radius: 14px;
    padding: 12px;
    border: 1px solid alpha(@borders, 0.08);
}

.graph-title {
    font-weight: 600;
    font-size: 12px;
    opacity: 0.6;
    letter-spacing: 0.3px;
}

/* ----- Status badges ----- */
.status-ok {
    color: #56d364;
}

.status-warn {
    color: #e3b341;
}

.status-critical {
    color: #f85149;
}

.badge-ok {
    background-color: alpha(#56d364, 0.15);
    color: #56d364;
    border-radius: 8px;
    padding: 2px 10px;
    font-weight: 600;
    font-size: 12px;
}

.badge-warn {
    background-color: alpha(#e3b341, 0.15);
    color: #e3b341;
    border-radius: 8px;
    padding: 2px 10px;
    font-weight: 600;
    font-size: 12px;
}

.badge-critical {
    background-color: alpha(#f85149, 0.15);
    color: #f85149;
    border-radius: 8px;
    padding: 2px 10px;
    font-weight: 600;
    font-size: 12px;
}

/* ----- Content area ----- */
.content-page {
    margin: 4px;
}

.page-header {
    font-weight: 800;
    font-size: 22px;
    letter-spacing: 0.2px;
}

/* ----- Action buttons ----- */
.pill-button {
    border-radius: 20px;
    padding: 6px 18px;
    font-weight: 600;
}

/* ----- Process rows ----- */
.process-row {
    border-radius: 10px;
    margin: 2px 0;
    transition: background-color 150ms ease;
}

.process-row:hover {
    background-color: alpha(@card_bg_color, 0.4);
}

/* ----- Scrollbar styling ----- */
scrollbar slider {
    border-radius: 100px;
    min-width: 6px;
    min-height: 6px;
}

/* ----- Search entries ----- */
.search-entry-large {
    border-radius: 12px;
    padding: 4px 8px;
    min-height: 40px;
    font-size: 14px;
}

/* ----- Error / Unavailable banners ----- */
.error-banner {
    background-color: alpha(#f85149, 0.10);
    border: 1px solid alpha(#f85149, 0.30);
    border-radius: 12px;
    padding: 10px 16px;
}

.error-banner-icon {
    color: #f85149;
}

.error-banner-text {
    color: #f85149;
    font-weight: 700;
    font-size: 13px;
}

.error-banner-detail {
    color: alpha(#f85149, 0.65);
    font-size: 11px;
}

.warning-banner {
    background-color: alpha(#e3b341, 0.10);
    border: 1px solid alpha(#e3b341, 0.30);
    border-radius: 12px;
    padding: 10px 16px;
}

.warning-banner-text {
    color: #e3b341;
    font-weight: 700;
    font-size: 13px;
}

.warning-banner-detail {
    color: alpha(#e3b341, 0.65);
    font-size: 11px;
}

.warning-banner-icon {
    color: #e3b341;
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
        css_provider.load_from_data(CSS.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self._pages = {}
        self._current_page = None
        self._build_ui()
        self._navigate_to("dashboard")

    def _build_ui(self):
        # Main layout: use Adw.Leaflet for sidebar + content (works on libadwaita 1.1+)
        outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(outer_box)

        self._leaflet = Adw.Leaflet()
        self._leaflet.set_can_navigate_back(True)

        # ---- Sidebar ----
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar_box.set_size_request(260, -1)
        sidebar_box.add_css_class("nav-sidebar-container")

        sidebar_header = Adw.HeaderBar()
        sidebar_header.set_show_end_title_buttons(False)
        title_label = Gtk.Label(label="PulseDeck")
        title_label.add_css_class("sidebar-title")
        sidebar_header.set_title_widget(title_label)
        sidebar_box.append(sidebar_header)

        sidebar_scroll = Gtk.ScrolledWindow()
        sidebar_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sidebar_scroll.set_vexpand(True)

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
            ("network", "Network", "network-wired-symbolic"),
            ("thermal", "Thermal", "weather-clear-symbolic"),
            ("apps", "Applications", "system-software-install-symbolic"),
        ]

        for key, label, icon_name in nav_items:
            row = Adw.ActionRow(title=label)
            row.set_icon_name(icon_name)
            row.set_activatable(True)
            row._nav_key = key
            self._nav_list.append(row)

        sidebar_scroll.set_child(self._nav_list)
        sidebar_box.append(sidebar_scroll)

        # Root status indicator at bottom of sidebar
        root_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        root_box.set_margin_start(16)
        root_box.set_margin_end(16)
        root_box.set_margin_bottom(10)
        root_box.set_margin_top(4)

        root_icon = Gtk.Image.new_from_icon_name(
            "security-high-symbolic" if is_root() else "security-low-symbolic"
        )
        root_icon.set_pixel_size(14)
        root_box.append(root_icon)

        root_label = Gtk.Label(label="Root Access" if is_root() else "Limited Mode")
        root_label.add_css_class("caption")
        if is_root():
            root_label.add_css_class("status-ok")
        else:
            root_label.add_css_class("dim-label")
        root_box.append(root_label)

        sidebar_box.append(root_box)

        self._leaflet.append(sidebar_box)

        # Separator between sidebar and content
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        self._leaflet.append(sep)

        # ---- Content area ----
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_hexpand(True)

        self._content_header = Adw.HeaderBar()
        self._content_title = Gtk.Label(label="Dashboard")
        self._content_title.add_css_class("page-header")
        self._content_header.set_title_widget(self._content_title)

        # Back button for narrow/folded mode
        back_btn = Gtk.Button(icon_name="go-previous-symbolic")
        back_btn.connect("clicked", self._on_back)
        self._content_header.pack_start(back_btn)
        self._back_btn = back_btn

        # About button
        about_btn = Gtk.Button(icon_name="help-about-symbolic")
        about_btn.set_tooltip_text("About PulseDeck")
        about_btn.connect("clicked", self._show_about)
        self._content_header.pack_end(about_btn)

        content_box.append(self._content_header)

        # Stack for pages
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self._stack.set_transition_duration(200)
        self._stack.set_vexpand(True)
        content_box.append(self._stack)

        self._leaflet.append(content_box)

        outer_box.append(self._leaflet)

        # Track folded state for back button visibility
        self._leaflet.connect("notify::folded", self._on_folded_changed)
        self._on_folded_changed(None, None)

        # Select first row
        first_row = self._nav_list.get_row_at_index(0)
        if first_row:
            self._nav_list.select_row(first_row)

    def _on_folded_changed(self, *args):
        folded = self._leaflet.get_folded()
        self._back_btn.set_visible(folded)

    def _on_back(self, *args):
        self._leaflet.navigate(Adw.NavigationDirection.BACK)

    def _on_nav_selected(self, listbox, row):
        if row is None:
            return
        key = row._nav_key
        self._navigate_to(key)
        # In folded mode, navigate forward to content
        if self._leaflet.get_folded():
            self._leaflet.navigate(Adw.NavigationDirection.FORWARD)

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
            "network": "Network",
            "thermal": "Thermal",
            "apps": "Applications",
        }
        self._content_title.set_label(titles.get(key, "PulseDeck"))

    def _create_page(self, key):
        pages = {
            "dashboard": DashboardPage,
            "cpu": CpuPage,
            "memory": MemoryPage,
            "storage": StoragePage,
            "network": NetworkPage,
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
        about = Gtk.AboutDialog(
            transient_for=self,
            modal=True,
            program_name="PulseDeck",
            logo_icon_name="utilities-system-monitor-symbolic",
            version="1.0.0",
            license_type=Gtk.License.MIT_X11,
            website="https://github.com/arif481/PulseDeck",
            comments="Lightweight system monitor for Linux.\n\n"
                     "Monitor CPU, RAM, Storage, Temperature, Fans, "
                     "and manage installed applications.",
        )
        about.present()

    def do_close_request(self):
        """Clean up timers when window closes."""
        for page in self._pages.values():
            if hasattr(page, "cleanup"):
                page.cleanup()
        return False
