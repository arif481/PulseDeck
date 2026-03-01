"""Dashboard page - system overview."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

from pulsedeck.monitors import cpu, memory, storage, thermal
from pulsedeck.ui.widgets import CircularGauge, MiniGraph, UsageBar, create_info_row, create_error_banner, show_error_banner, hide_error_banner
from pulsedeck.utils.helpers import format_bytes, format_uptime, get_hostname, get_kernel_version, get_os_name


class DashboardPage(Gtk.Box):
    """Main dashboard with system overview gauges and info."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._timers = []
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

        # ── Welcome header ──
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        header_box.set_margin_bottom(4)

        welcome = Gtk.Label(label=f"{get_os_name()}")
        welcome.set_halign(Gtk.Align.START)
        welcome.add_css_class("section-title")
        header_box.append(welcome)

        subtitle = Gtk.Label(label=f"{get_hostname()} \u2022 {get_kernel_version()}")
        subtitle.set_halign(Gtk.Align.START)
        subtitle.add_css_class("section-subtitle")
        header_box.append(subtitle)
        content.append(header_box)

        # ── Error banner (hidden by default) ──
        self._error_banner = create_error_banner()
        content.append(self._error_banner)

        # ── Stat pills row (Uptime, CPU Name) ──
        pills_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        pills_box.set_homogeneous(True)

        cpu_name = cpu.get_cpu_name()
        # Truncate long CPU names
        if len(cpu_name) > 30:
            cpu_name = cpu_name[:28] + "\u2026"

        self._uptime_pill = self._make_pill("UPTIME", format_uptime())
        pills_box.append(self._uptime_pill)

        cpu_pill = self._make_pill("PROCESSOR", cpu_name)
        pills_box.append(cpu_pill)

        content.append(pills_box)

        # ── Gauges row ──
        gauges_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        gauges_box.set_halign(Gtk.Align.CENTER)
        gauges_box.set_margin_top(4)
        gauges_box.set_margin_bottom(4)

        self._cpu_gauge = CircularGauge(label="CPU", value=0, max_val=100, unit="%",
                                         color=(0.35, 0.65, 1.0), size=140)
        self._ram_gauge = CircularGauge(label="RAM", value=0, max_val=100, unit="%",
                                         color=(0.4, 0.85, 0.5), size=140)
        self._disk_gauge = CircularGauge(label="Disk", value=0, max_val=100, unit="%",
                                          color=(1.0, 0.65, 0.25), size=140)

        for gauge, name in [(self._cpu_gauge, "CPU"), (self._ram_gauge, "RAM"), (self._disk_gauge, "Disk")]:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            card.add_css_class("gauge-card")
            card.set_halign(Gtk.Align.CENTER)
            card.append(gauge)
            lbl = Gtk.Label(label=name)
            lbl.add_css_class("gauge-label")
            card.append(lbl)
            gauges_box.append(card)

        content.append(gauges_box)

        # ── Live activity graphs ──
        graphs_header = Gtk.Label(label="Live Activity")
        graphs_header.set_halign(Gtk.Align.START)
        graphs_header.add_css_class("section-title")
        graphs_header.set_margin_top(8)
        content.append(graphs_header)

        graphs_grid = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        graphs_grid.set_homogeneous(True)

        # CPU graph card
        cpu_graph_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        cpu_graph_card.add_css_class("graph-card")
        cpu_gl = Gtk.Label(label="CPU USAGE")
        cpu_gl.set_halign(Gtk.Align.START)
        cpu_gl.add_css_class("graph-title")
        cpu_graph_card.append(cpu_gl)
        self._cpu_graph = MiniGraph(color=(0.35, 0.65, 1.0), max_points=60, height=60)
        cpu_graph_card.append(self._cpu_graph)
        self._cpu_graph_value = Gtk.Label(label="0%")
        self._cpu_graph_value.set_halign(Gtk.Align.END)
        self._cpu_graph_value.add_css_class("stat-value")
        cpu_graph_card.append(self._cpu_graph_value)
        graphs_grid.append(cpu_graph_card)

        # RAM graph card
        ram_graph_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        ram_graph_card.add_css_class("graph-card")
        ram_gl = Gtk.Label(label="MEMORY USAGE")
        ram_gl.set_halign(Gtk.Align.START)
        ram_gl.add_css_class("graph-title")
        ram_graph_card.append(ram_gl)
        self._ram_graph = MiniGraph(color=(0.4, 0.85, 0.5), max_points=60, height=60)
        ram_graph_card.append(self._ram_graph)
        self._ram_graph_value = Gtk.Label(label="0%")
        self._ram_graph_value.set_halign(Gtk.Align.END)
        self._ram_graph_value.add_css_class("stat-value")
        ram_graph_card.append(self._ram_graph_value)
        graphs_grid.append(ram_graph_card)

        content.append(graphs_grid)

        # ── System info card ──
        info_card = Adw.PreferencesGroup()
        info_card.set_title("System Information")

        kernel_row = Adw.ActionRow(title="Kernel", subtitle=get_kernel_version())
        kernel_row.set_icon_name("computer-symbolic")
        info_card.add(kernel_row)

        self._uptime_row = Adw.ActionRow(title="Uptime", subtitle=format_uptime())
        self._uptime_row.set_icon_name("preferences-system-time-symbolic")
        info_card.add(self._uptime_row)

        cpu_info_row = Adw.ActionRow(title="Processor", subtitle=cpu.get_cpu_name())
        cpu_info_row.set_icon_name("processor-symbolic")
        info_card.add(cpu_info_row)

        content.append(info_card)

        # ── Temperature card ──
        self._temp_card = Adw.PreferencesGroup()
        self._temp_card.set_title("Temperatures")
        self._temp_rows = []
        content.append(self._temp_card)

        # ── Battery card (if available) ──
        bat = thermal.get_battery_info()
        if bat is not None:
            bat_card = Adw.PreferencesGroup()
            bat_card.set_title("Battery")
            self._bat_row = Adw.ActionRow(title="Battery Level")
            self._bat_row.set_icon_name("battery-symbolic")

            self._bat_badge = Gtk.Label()
            self._bat_badge.set_valign(Gtk.Align.CENTER)
            self._bat_row.add_suffix(self._bat_badge)

            bat_card.add(self._bat_row)
            content.append(bat_card)
        else:
            self._bat_row = None
            self._bat_badge = None

    def _make_pill(self, label, value):
        """Create a stat pill widget."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.add_css_class("stat-pill")
        lbl = Gtk.Label(label=label)
        lbl.add_css_class("stat-label")
        lbl.set_halign(Gtk.Align.START)
        box.append(lbl)
        val = Gtk.Label(label=value)
        val.add_css_class("dim-label")
        val.set_halign(Gtk.Align.START)
        val.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        box.append(val)
        box._value_label = val
        return box

    def _start_updates(self):
        tid = GLib.timeout_add(2000, self._update)
        self._timers.append(tid)
        self._update()

    def _update(self):
        errors = []

        # ── CPU ──
        try:
            ci = cpu.get_cpu_info()
            cpu_pct = ci["usage_percent"]
            self._cpu_gauge.set_value(cpu_pct, "CPU")
            self._cpu_graph.set_unavailable(False)
            self._cpu_graph.add_point(cpu_pct)
            self._cpu_graph_value.set_label(f"{cpu_pct:.0f}%")
        except Exception as e:
            errors.append(f"CPU: {e}")
            self._cpu_gauge.set_unavailable(True)
            self._cpu_graph.set_unavailable(True)
            self._cpu_graph_value.set_label("--")

        # ── RAM ──
        try:
            mi = memory.get_memory_info()
            ram_pct = mi["percent"]
            self._ram_gauge.set_value(ram_pct, "RAM")
            self._ram_graph.set_unavailable(False)
            self._ram_graph.add_point(ram_pct)
            self._ram_graph_value.set_label(f"{ram_pct:.0f}%")
        except Exception as e:
            errors.append(f"Memory: {e}")
            self._ram_gauge.set_unavailable(True)
            self._ram_graph.set_unavailable(True)
            self._ram_graph_value.set_label("--")

        # ── Disk ──
        try:
            parts = storage.get_disk_partitions()
            if parts:
                root = next((p for p in parts if p["mountpoint"] == "/"), parts[0])
                self._disk_gauge.set_value(root["percent"], "Disk")
            else:
                self._disk_gauge.set_unavailable(True)
        except Exception as e:
            errors.append(f"Disk: {e}")
            self._disk_gauge.set_unavailable(True)

        # ── Uptime ──
        try:
            self._uptime_row.set_subtitle(format_uptime())
            self._uptime_pill._value_label.set_label(format_uptime())
        except Exception:
            pass

        # ── Temperatures ──
        try:
            temps = thermal.get_temperatures()
            if len(temps) != len(self._temp_rows):
                for r in self._temp_rows:
                    self._temp_card.remove(r)
                self._temp_rows.clear()
                if temps:
                    for t in temps:
                        row = Adw.ActionRow(title=t["label"])
                        row.set_icon_name("temperature-symbolic")
                        temp_lbl = Gtk.Label()
                        temp_lbl.set_valign(Gtk.Align.CENTER)
                        row.add_suffix(temp_lbl)
                        self._temp_card.add(row)
                        self._temp_rows.append((row, temp_lbl))
                else:
                    row = Adw.ActionRow(title="No sensors detected")
                    row.set_subtitle("Temperature data is not available on this system")
                    row.set_icon_name("dialog-warning-symbolic")
                    self._temp_card.add(row)
                    self._temp_rows.append((row, None))

            for i, t in enumerate(temps):
                if i < len(self._temp_rows):
                    _, lbl = self._temp_rows[i]
                    if lbl is None:
                        continue
                    temp_val = t['current']
                    lbl.set_text(f"{temp_val:.1f}\u00b0C")
                    for cls in ["badge-ok", "badge-warn", "badge-critical"]:
                        lbl.remove_css_class(cls)
                    if t["critical"] > 0 and temp_val >= t["critical"] * 0.9:
                        lbl.add_css_class("badge-critical")
                    elif temp_val >= 70:
                        lbl.add_css_class("badge-warn")
                    else:
                        lbl.add_css_class("badge-ok")
        except Exception as e:
            errors.append(f"Thermal: {e}")

        # ── Battery ──
        try:
            if self._bat_row:
                bat = thermal.get_battery_info()
                if bat:
                    pct = bat['percent']
                    status = "Charging" if bat["plugged"] else "Discharging"
                    self._bat_row.set_subtitle(f"{pct:.0f}% \u2022 {status}")
                    if self._bat_badge:
                        for cls in ["badge-ok", "badge-warn", "badge-critical"]:
                            self._bat_badge.remove_css_class(cls)
                        if pct > 50:
                            self._bat_badge.add_css_class("badge-ok")
                        elif pct > 20:
                            self._bat_badge.add_css_class("badge-warn")
                        else:
                            self._bat_badge.add_css_class("badge-critical")
                        self._bat_badge.set_label(f"{pct:.0f}%")
        except Exception:
            pass

        # ── Error banner ──
        if errors:
            show_error_banner(
                self._error_banner,
                f"{'Some sensors' if len(errors) < 3 else 'Multiple sensors'} unavailable",
                " | ".join(errors)
            )
        else:
            hide_error_banner(self._error_banner)

        return True  # Keep timer alive

    def cleanup(self):
        for tid in self._timers:
            GLib.source_remove(tid)
        self._timers.clear()
