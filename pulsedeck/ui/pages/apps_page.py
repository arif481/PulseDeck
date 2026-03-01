"""Apps manager page - browse, install, uninstall applications."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio
import threading

from pulsedeck.managers.apps import (
    get_all_installed_apps, search_apt_packages, search_flatpak_apps,
    install_apt_package, uninstall_apt_package,
    install_flatpak_app, uninstall_flatpak_app,
)


class AppsPage(Gtk.Box):
    """Application manager page with install/uninstall GUI."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._installed_apps = []
        self._app_rows = []
        self._search_rows = []
        self._build_ui()
        # Load apps in background
        self._load_installed_apps()

    def _build_ui(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        scroll.set_hexpand(True)
        self.append(scroll)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(16)
        content.set_margin_bottom(16)
        content.set_margin_start(16)
        content.set_margin_end(16)
        scroll.set_child(content)

        # Search bar for installing new apps
        search_card = Adw.PreferencesGroup()
        search_card.set_title("Find & Install Apps")
        search_card.set_description("Search for new packages to install")

        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        search_box.set_margin_top(8)
        search_box.set_margin_bottom(8)

        self._search_entry = Gtk.SearchEntry()
        self._search_entry.set_placeholder_text("Search packages (e.g., vlc, gimp, firefox)...")
        self._search_entry.set_hexpand(True)
        self._search_entry.connect("activate", self._on_search)
        search_box.append(self._search_entry)

        search_btn = Gtk.Button(label="Search")
        search_btn.add_css_class("suggested-action")
        search_btn.connect("clicked", self._on_search)
        search_box.append(search_btn)

        # Wrap search box
        search_row = Adw.ActionRow()
        search_row.set_child(search_box)
        search_card.add(search_row)
        content.append(search_card)

        # Search results
        self._results_card = Adw.PreferencesGroup()
        self._results_card.set_title("Search Results")
        self._results_spinner = Gtk.Spinner()
        self._results_card.set_header_suffix(self._results_spinner)
        content.append(self._results_card)

        # Installed apps
        self._installed_card = Adw.PreferencesGroup()
        self._installed_card.set_title("Installed Applications")
        self._installed_spinner = Gtk.Spinner()
        self._installed_spinner.start()
        self._installed_card.set_header_suffix(self._installed_spinner)

        # Filter entry
        filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        filter_box.set_margin_top(4)
        filter_box.set_margin_bottom(4)
        self._filter_entry = Gtk.SearchEntry()
        self._filter_entry.set_placeholder_text("Filter installed apps...")
        self._filter_entry.set_hexpand(True)
        self._filter_entry.connect("search-changed", self._on_filter_changed)
        filter_box.append(self._filter_entry)

        self._app_count_label = Gtk.Label(label="Loading...")
        self._app_count_label.add_css_class("dim-label")
        filter_box.append(self._app_count_label)

        filter_row = Adw.ActionRow()
        filter_row.set_child(filter_box)
        self._installed_card.add(filter_row)

        content.append(self._installed_card)

        # Status bar
        self._status_bar = Adw.PreferencesGroup()
        self._status_label = Adw.ActionRow(title="Ready")
        self._status_label.set_icon_name("emblem-ok-symbolic")
        self._status_bar.add(self._status_label)
        content.append(self._status_bar)

    def _load_installed_apps(self):
        """Load installed apps in a background thread."""
        def _do():
            apps = get_all_installed_apps()
            GLib.idle_add(self._on_apps_loaded, apps)

        t = threading.Thread(target=_do, daemon=True)
        t.start()

    def _on_apps_loaded(self, apps):
        self._installed_apps = apps
        self._installed_spinner.stop()
        self._app_count_label.set_text(f"{len(apps)} apps")
        self._show_installed_apps(apps[:100])  # Show first 100

    def _show_installed_apps(self, apps):
        # Remove old rows
        for r in self._app_rows:
            self._installed_card.remove(r)
        self._app_rows.clear()

        for app in apps:
            name = app.get("name", "Unknown")
            app_type = app.get("type", "")
            row = Adw.ActionRow(title=name)
            row.set_subtitle(f"Type: {app_type}")

            # Uninstall button
            btn = Gtk.Button(label="Remove")
            btn.add_css_class("destructive-action")
            btn.set_valign(Gtk.Align.CENTER)
            btn.connect("clicked", self._on_uninstall, app)
            row.add_suffix(btn)

            # Launch button (if .desktop app with exec)
            if app.get("exec"):
                launch_btn = Gtk.Button(label="Launch")
                launch_btn.set_valign(Gtk.Align.CENTER)
                launch_btn.connect("clicked", self._on_launch, app)
                row.add_suffix(launch_btn)

            self._installed_card.add(row)
            self._app_rows.append(row)

    def _on_filter_changed(self, entry):
        query = entry.get_text().strip().lower()
        if not query:
            self._show_installed_apps(self._installed_apps[:100])
            return
        filtered = [a for a in self._installed_apps if query in a.get("name", "").lower()]
        self._show_installed_apps(filtered[:50])

    def _on_search(self, *args):
        query = self._search_entry.get_text().strip()
        if not query:
            return

        self._results_spinner.start()
        # Clear old results
        for r in self._search_rows:
            self._results_card.remove(r)
        self._search_rows.clear()

        def _do():
            # Search both apt and flatpak
            apt_results = search_apt_packages(query)
            flatpak_results = search_flatpak_apps(query)
            all_results = flatpak_results + apt_results  # Prioritize flatpak
            GLib.idle_add(self._on_search_results, all_results[:30])

        t = threading.Thread(target=_do, daemon=True)
        t.start()

    def _on_search_results(self, results):
        self._results_spinner.stop()
        for r in self._search_rows:
            self._results_card.remove(r)
        self._search_rows.clear()

        if not results:
            row = Adw.ActionRow(title="No results found")
            self._results_card.add(row)
            self._search_rows.append(row)
            return

        for res in results:
            name = res.get("name", "Unknown")
            desc = res.get("description", "")
            rtype = res.get("type", "")
            row = Adw.ActionRow(title=name, subtitle=f"[{rtype}] {desc}")

            btn = Gtk.Button(label="Install")
            btn.add_css_class("suggested-action")
            btn.set_valign(Gtk.Align.CENTER)
            btn.connect("clicked", self._on_install, res, btn)
            row.add_suffix(btn)

            self._results_card.add(row)
            self._search_rows.append(row)

    def _on_install(self, button, app_info, btn_ref):
        btn_ref.set_sensitive(False)
        btn_ref.set_label("Installing...")
        self._status_label.set_title(f"Installing {app_info.get('name', '')}...")
        self._status_label.set_icon_name("emblem-synchronizing-symbolic")

        def _callback(success, output):
            def _update():
                if success:
                    btn_ref.set_label("Installed ✓")
                    self._status_label.set_title(f"Installed {app_info.get('name', '')} successfully")
                    self._status_label.set_icon_name("emblem-ok-symbolic")
                    # Refresh installed apps
                    self._load_installed_apps()
                else:
                    btn_ref.set_label("Failed")
                    btn_ref.set_sensitive(True)
                    self._status_label.set_title(f"Failed to install {app_info.get('name', '')}")
                    self._status_label.set_icon_name("dialog-error-symbolic")
            GLib.idle_add(_update)

        app_type = app_info.get("type", "")
        if app_type == "flatpak":
            app_id = app_info.get("app_id", app_info.get("name", ""))
            install_flatpak_app(app_id, callback=_callback)
        else:
            install_apt_package(app_info.get("name", ""), callback=_callback)

    def _on_uninstall(self, button, app_info):
        # Show confirmation dialog
        name = app_info.get("name", "Unknown")
        app_type = app_info.get("type", "")

        button.set_sensitive(False)
        button.set_label("Removing...")
        self._status_label.set_title(f"Removing {name}...")
        self._status_label.set_icon_name("emblem-synchronizing-symbolic")

        def _callback(success, output):
            def _update():
                if success:
                    button.set_label("Removed ✓")
                    self._status_label.set_title(f"Removed {name} successfully")
                    self._status_label.set_icon_name("emblem-ok-symbolic")
                    self._load_installed_apps()
                else:
                    button.set_label("Failed")
                    button.set_sensitive(True)
                    self._status_label.set_title(f"Failed to remove {name}")
                    self._status_label.set_icon_name("dialog-error-symbolic")
            GLib.idle_add(_update)

        if app_type == "flatpak":
            app_id = app_info.get("app_id", app_info.get("name", ""))
            uninstall_flatpak_app(app_id, callback=_callback)
        else:
            pkg = app_info.get("pkg_name", app_info.get("name", ""))
            uninstall_apt_package(pkg, callback=_callback)

    def _on_launch(self, button, app_info):
        """Launch an application."""
        exec_cmd = app_info.get("exec", "")
        if not exec_cmd:
            return
        import subprocess
        import shlex
        try:
            # Clean up Exec field (remove %f, %u, %F, %U etc.)
            cmd = exec_cmd.split("%")[0].strip()
            parts = shlex.split(cmd)
            subprocess.Popen(parts, start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def cleanup(self):
        pass
