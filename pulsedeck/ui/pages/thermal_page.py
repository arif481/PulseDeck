"""Thermal & Fan monitoring page."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

from pulsedeck.monitors.thermal import (
    get_temperatures, get_fans, get_fan_control_paths,
    set_fan_speed, set_fan_auto, get_battery_info,
)
from pulsedeck.ui.widgets import MiniGraph, create_error_banner, show_error_banner, hide_error_banner


class ThermalPage(Gtk.Box):
    """Temperature and fan monitoring page with fan control."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._timers = []
        self._temp_rows = []
        self._fan_rows = []
        self._temp_history = {}
        self._build_ui()
        self._start_updates()

    def _build_ui(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        scroll.set_hexpand(True)
        self.append(scroll)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(900)
        clamp.set_tightening_threshold(600)
        scroll.set_child(clamp)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.set_margin_top(20)
        content.set_margin_bottom(24)
        content.set_margin_start(20)
        content.set_margin_end(20)
        clamp.set_child(content)

        # ── Header ──
        header = Gtk.Label(label="Thermal and Fans")
        header.set_halign(Gtk.Align.START)
        header.add_css_class("section-title")
        content.append(header)

        # ── Error banner (hidden by default) ──
        self._error_banner = create_error_banner()
        content.append(self._error_banner)

        # ── Temperature card ──
        self._temp_card = Adw.PreferencesGroup()
        self._temp_card.set_title("Temperatures")
        self._temp_card.set_description("Sensor readings from your hardware")
        content.append(self._temp_card)

        # ── Fan card ──
        self._fan_card = Adw.PreferencesGroup()
        self._fan_card.set_title("Fans")
        self._fan_card.set_description("Fan speed readings")
        content.append(self._fan_card)

        # ── Fan control card ──
        self._control_card = Adw.PreferencesGroup()
        self._control_card.set_title("Fan Speed Control")
        self._control_card.set_description("Adjust fan speeds (requires elevated permissions)")
        self._control_widgets = []
        content.append(self._control_card)

        # ── Battery card ──
        bat = get_battery_info()
        if bat is not None:
            bat_card = Adw.PreferencesGroup()
            bat_card.set_title("Battery")

            self._bat_level_row = Adw.ActionRow(title="Level")
            self._bat_level_row.set_icon_name("battery-symbolic")
            self._bat_level_badge = Gtk.Label()
            self._bat_level_badge.set_valign(Gtk.Align.CENTER)
            self._bat_level_row.add_suffix(self._bat_level_badge)
            bat_card.add(self._bat_level_row)

            self._bat_status_row = Adw.ActionRow(title="Status")
            bat_card.add(self._bat_status_row)
            content.append(bat_card)
        else:
            self._bat_level_row = None
            self._bat_status_row = None
            self._bat_level_badge = None

        self._build_fan_controls()

    def _build_fan_controls(self):
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
            row.set_subtitle(f"Mode: {mode_text} \u2022 PWM: {ctrl['value']}/255")

            scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 255, 5)
            scale.set_value(ctrl["value"])
            scale.set_size_request(150, -1)
            scale.set_valign(Gtk.Align.CENTER)
            pwm_path = ctrl["path"]
            scale.connect("value-changed", self._on_fan_slider_changed, pwm_path)
            row.add_suffix(scale)

            auto_btn = Gtk.Button(label="Auto")
            auto_btn.set_valign(Gtk.Align.CENTER)
            auto_btn.add_css_class("suggested-action")
            auto_btn.add_css_class("pill-button")
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
        errors = []

        # ── Temperatures ──
        try:
            temps = get_temperatures()
            if len(temps) != len(self._temp_rows):
                for r in self._temp_rows:
                    self._temp_card.remove(r)
                self._temp_rows.clear()

                if temps:
                    for t in temps:
                        row = Adw.ActionRow(title=t["label"])
                        row.set_icon_name("temperature-symbolic")

                        graph = MiniGraph(color=(1.0, 0.4, 0.3), max_points=30, height=28)
                        graph.set_content_width(100)
                        graph.set_valign(Gtk.Align.CENTER)
                        row.add_suffix(graph)

                        temp_label = Gtk.Label()
                        temp_label.set_valign(Gtk.Align.CENTER)
                        row.add_suffix(temp_label)

                        self._temp_card.add(row)
                        self._temp_rows.append((row, graph, temp_label))
                else:
                    row = Adw.ActionRow(title="No temperature sensors detected")
                    row.set_subtitle("Temperature data is not available on this system")
                    row.set_icon_name("dialog-warning-symbolic")
                    self._temp_card.add(row)
                    self._temp_rows.append((row, None, None))

            for i, t in enumerate(temps):
                if i < len(self._temp_rows):
                    _, graph, lbl = self._temp_rows[i]
                    if graph is None or lbl is None:
                        continue
                    graph.add_point(t["current"])
                    temp_val = t["current"]

                    for cls in ["badge-ok", "badge-warn", "badge-critical"]:
                        lbl.remove_css_class(cls)

                    if t["critical"] > 0 and temp_val >= t["critical"] * 0.9:
                        lbl.add_css_class("badge-critical")
                    elif temp_val >= 70:
                        lbl.add_css_class("badge-warn")
                    else:
                        lbl.add_css_class("badge-ok")

                    lbl.set_text(f"  {temp_val:.1f}\u00b0C")
        except Exception as e:
            errors.append(f"Temperature sensors: {e}")

        # ── Fans ──
        try:
            fans = get_fans()
            if len(fans) != len(self._fan_rows):
                for r in self._fan_rows:
                    self._fan_card.remove(r)
                self._fan_rows.clear()

                if fans:
                    for fan in fans:
                        row = Adw.ActionRow(title=f"{fan['label']}")
                        row.set_subtitle(f"Sensor: {fan['sensor']}")
                        row.set_icon_name("preferences-system-power-symbolic")
                        rpm_label = Gtk.Label()
                        rpm_label.set_valign(Gtk.Align.CENTER)
                        row.add_suffix(rpm_label)
                        self._fan_card.add(row)
                        self._fan_rows.append((row, rpm_label))
                else:
                    row = Adw.ActionRow(title="No fans detected")
                    row.set_subtitle("Fan sensors may not be exposed by your hardware")
                    row.set_icon_name("dialog-information-symbolic")
                    self._fan_card.add(row)
                    self._fan_rows.append((row, None))

            for i, fan in enumerate(fans):
                if i < len(self._fan_rows):
                    _, rpm_lbl = self._fan_rows[i]
                    if rpm_lbl:
                        rpm_lbl.set_text(f"  {fan['current_rpm']} RPM")
        except Exception as e:
            errors.append(f"Fan sensors: {e}")

        # ── Battery ──
        try:
            if self._bat_level_row:
                bat = get_battery_info()
                if bat:
                    pct = bat['percent']
                    self._bat_level_row.set_subtitle(f"{pct:.0f}%")
                    status = "Charging" if bat["plugged"] else "On Battery"
                    self._bat_status_row.set_subtitle(status)

                    if self._bat_level_badge:
                        for cls in ["badge-ok", "badge-warn", "badge-critical"]:
                            self._bat_level_badge.remove_css_class(cls)
                        if pct > 50:
                            self._bat_level_badge.add_css_class("badge-ok")
                        elif pct > 20:
                            self._bat_level_badge.add_css_class("badge-warn")
                        else:
                            self._bat_level_badge.add_css_class("badge-critical")
                        self._bat_level_badge.set_label(f"{pct:.0f}%")
        except Exception:
            pass

        # ── Error banner ──
        if errors:
            show_error_banner(self._error_banner, "Sensor reading error", " | ".join(errors))
        else:
            hide_error_banner(self._error_banner)

        return True

    def cleanup(self):
        for tid in self._timers:
            GLib.source_remove(tid)
        self._timers.clear()
