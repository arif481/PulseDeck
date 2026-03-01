"""Thermal & Fan monitoring page."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

from pulsedeck.monitors.thermal import (
    get_temperatures, get_fans, get_fan_control_paths,
    set_fan_speed, set_fan_auto, get_battery_info,
)
from pulsedeck.ui.widgets import MiniGraph


class ThermalPage(Gtk.Box):
    """Temperature and fan monitoring page with fan control."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._timers = []
        self._temp_rows = []
        self._fan_rows = []
        self._temp_history = {}  # label -> list of temps
        self._build_ui()
        self._start_updates()

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

        # Temperature card
        self._temp_card = Adw.PreferencesGroup()
        self._temp_card.set_title("Temperatures")
        self._temp_card.set_description("Sensor readings from your hardware")
        content.append(self._temp_card)

        # Fan card
        self._fan_card = Adw.PreferencesGroup()
        self._fan_card.set_title("Fans")
        self._fan_card.set_description("Fan speed and control")
        content.append(self._fan_card)

        # Fan control card
        self._control_card = Adw.PreferencesGroup()
        self._control_card.set_title("Fan Speed Control")
        self._control_card.set_description("Adjust fan speeds (requires elevated permissions)")
        self._control_widgets = []
        content.append(self._control_card)

        # Battery card
        bat = get_battery_info()
        if bat is not None:
            bat_card = Adw.PreferencesGroup()
            bat_card.set_title("Battery")
            self._bat_level_row = Adw.ActionRow(title="Level")
            self._bat_level_row.set_icon_name("battery-symbolic")
            bat_card.add(self._bat_level_row)
            self._bat_status_row = Adw.ActionRow(title="Status")
            bat_card.add(self._bat_status_row)
            content.append(bat_card)
        else:
            self._bat_level_row = None
            self._bat_status_row = None

        self._build_fan_controls()

    def _build_fan_controls(self):
        """Build fan control sliders."""
        for w in self._control_widgets:
            self._control_card.remove(w)
        self._control_widgets.clear()

        controls = get_fan_control_paths()
        if not controls:
            row = Adw.ActionRow(title="No controllable fans found")
            row.set_subtitle("Fan control may not be supported or requires root access")
            self._control_card.add(row)
            self._control_widgets.append(row)
            return

        for ctrl in controls:
            row = Adw.ActionRow(title=f"{ctrl['sensor']}")
            mode_text = {0: "Full Speed", 1: "Manual", 2: "Automatic"}.get(ctrl["mode"], "Unknown")
            row.set_subtitle(f"Mode: {mode_text} • PWM: {ctrl['value']}/255")

            # Slider
            scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 255, 5)
            scale.set_value(ctrl["value"])
            scale.set_size_request(150, -1)
            scale.set_valign(Gtk.Align.CENTER)
            pwm_path = ctrl["path"]
            scale.connect("value-changed", self._on_fan_slider_changed, pwm_path)
            row.add_suffix(scale)

            # Auto button
            auto_btn = Gtk.Button(label="Auto")
            auto_btn.set_valign(Gtk.Align.CENTER)
            auto_btn.add_css_class("suggested-action")
            auto_btn.connect("clicked", self._on_fan_auto, pwm_path)
            row.add_suffix(auto_btn)

            self._control_card.add(row)
            self._control_widgets.append(row)

    def _on_fan_slider_changed(self, scale, pwm_path):
        value = int(scale.get_value())
        set_fan_speed(pwm_path, value)

    def _on_fan_auto(self, button, pwm_path):
        set_fan_auto(pwm_path)
        self._build_fan_controls()

    def _start_updates(self):
        tid = GLib.timeout_add(3000, self._update)
        self._timers.append(tid)
        self._update()

    def _update(self):
        try:
            # Temperatures
            temps = get_temperatures()
            if len(temps) != len(self._temp_rows):
                for r in self._temp_rows:
                    self._temp_card.remove(r)
                self._temp_rows.clear()

                for t in temps:
                    row = Adw.ActionRow(title=t["label"])
                    # Color indicator via subtitle
                    graph = MiniGraph(color=(1.0, 0.4, 0.3), max_points=30, height=28)
                    graph.set_content_width(100)
                    graph.set_valign(Gtk.Align.CENTER)
                    row.add_suffix(graph)

                    temp_label = Gtk.Label()
                    temp_label.set_valign(Gtk.Align.CENTER)
                    row.add_suffix(temp_label)

                    self._temp_card.add(row)
                    self._temp_rows.append((row, graph, temp_label))

            for i, t in enumerate(temps):
                if i < len(self._temp_rows):
                    _, graph, lbl = self._temp_rows[i]
                    graph.add_point(t["current"])
                    warning = ""
                    if t["critical"] > 0 and t["current"] >= t["critical"] * 0.9:
                        warning = " ⚠️"
                    lbl.set_text(f"  {t['current']:.1f}°C{warning}")

            # Fans
            fans = get_fans()
            if len(fans) != len(self._fan_rows):
                for r in self._fan_rows:
                    self._fan_card.remove(r)
                self._fan_rows.clear()

                for fan in fans:
                    row = Adw.ActionRow(title=f"{fan['label']}")
                    row.set_subtitle(f"Sensor: {fan['sensor']}")
                    rpm_label = Gtk.Label()
                    rpm_label.set_valign(Gtk.Align.CENTER)
                    row.add_suffix(rpm_label)
                    self._fan_card.add(row)
                    self._fan_rows.append((row, rpm_label))

            if not fans and not self._fan_rows:
                row = Adw.ActionRow(title="No fans detected")
                row.set_subtitle("Fan sensors may not be exposed by your hardware")
                self._fan_card.add(row)
                self._fan_rows.append((row, None))

            for i, fan in enumerate(fans):
                if i < len(self._fan_rows):
                    _, rpm_lbl = self._fan_rows[i]
                    if rpm_lbl:
                        rpm_lbl.set_text(f"  {fan['current_rpm']} RPM")

            # Battery
            if self._bat_level_row:
                bat = get_battery_info()
                if bat:
                    self._bat_level_row.set_subtitle(f"{bat['percent']:.0f}%")
                    status = "Charging" if bat["plugged"] else "On Battery"
                    self._bat_status_row.set_subtitle(status)

        except Exception:
            pass
        return True

    def cleanup(self):
        for tid in self._timers:
            GLib.source_remove(tid)
        self._timers.clear()
