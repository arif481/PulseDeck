"""Dashboard page - system overview."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

from pulsedeck.monitors import cpu, memory, storage, thermal
from pulsedeck.ui.widgets import CircularGauge, MiniGraph, UsageBar, create_info_row
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

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(16)
        content.set_margin_bottom(16)
        content.set_margin_start(16)
        content.set_margin_end(16)
        scroll.set_child(content)

        # System info header
        info_card = Adw.PreferencesGroup()
        info_card.set_title("System Information")
        info_card.set_description(f"{get_os_name()} • {get_hostname()}")

        kernel_row = Adw.ActionRow(title="Kernel", subtitle=get_kernel_version())
        kernel_row.set_icon_name("computer-symbolic")
        info_card.add(kernel_row)

        self._uptime_row = Adw.ActionRow(title="Uptime", subtitle=format_uptime())
        self._uptime_row.set_icon_name("preferences-system-time-symbolic")
        info_card.add(self._uptime_row)

        cpu_name = cpu.get_cpu_name()
        cpu_row = Adw.ActionRow(title="Processor", subtitle=cpu_name)
        cpu_row.set_icon_name("processor-symbolic")
        info_card.add(cpu_row)

        content.append(info_card)

        # Gauges row
        gauges_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        gauges_box.set_halign(Gtk.Align.CENTER)
        gauges_box.set_margin_top(8)

        self._cpu_gauge = CircularGauge(label="CPU", value=0, max_val=100, unit="%",
                                         color=(0.2, 0.6, 1.0), size=130)
        self._ram_gauge = CircularGauge(label="RAM", value=0, max_val=100, unit="%",
                                         color=(0.4, 0.8, 0.4), size=130)
        self._disk_gauge = CircularGauge(label="Disk", value=0, max_val=100, unit="%",
                                          color=(1.0, 0.6, 0.2), size=130)

        for g in [self._cpu_gauge, self._ram_gauge, self._disk_gauge]:
            frame = Gtk.Frame()
            frame.set_child(g)
            gauges_box.append(frame)

        content.append(gauges_box)

        # Sparkline graphs
        graphs_card = Adw.PreferencesGroup()
        graphs_card.set_title("Live Activity")

        cpu_graph_row = Adw.ActionRow(title="CPU History")
        self._cpu_graph = MiniGraph(color=(0.3, 0.6, 1.0), max_points=60, height=36)
        self._cpu_graph.set_valign(Gtk.Align.CENTER)
        cpu_graph_row.add_suffix(self._cpu_graph)
        graphs_card.add(cpu_graph_row)

        ram_graph_row = Adw.ActionRow(title="RAM History")
        self._ram_graph = MiniGraph(color=(0.4, 0.8, 0.4), max_points=60, height=36)
        self._ram_graph.set_valign(Gtk.Align.CENTER)
        ram_graph_row.add_suffix(self._ram_graph)
        graphs_card.add(ram_graph_row)

        content.append(graphs_card)

        # Temperature card
        self._temp_card = Adw.PreferencesGroup()
        self._temp_card.set_title("Temperatures")
        self._temp_rows = []
        content.append(self._temp_card)

        # Battery card (if available)
        bat = thermal.get_battery_info()
        if bat is not None:
            bat_card = Adw.PreferencesGroup()
            bat_card.set_title("Battery")
            self._bat_row = Adw.ActionRow(title="Battery Level")
            self._bat_row.set_icon_name("battery-symbolic")
            bat_card.add(self._bat_row)
            content.append(bat_card)
        else:
            self._bat_row = None

    def _start_updates(self):
        tid = GLib.timeout_add(2000, self._update)
        self._timers.append(tid)
        self._update()

    def _update(self):
        try:
            # CPU
            ci = cpu.get_cpu_info()
            self._cpu_gauge.set_value(ci["usage_percent"], "CPU")
            self._cpu_graph.add_point(ci["usage_percent"])

            # RAM
            mi = memory.get_memory_info()
            self._ram_gauge.set_value(mi["percent"], "RAM")
            self._ram_graph.add_point(mi["percent"])

            # Disk
            parts = storage.get_disk_partitions()
            if parts:
                root = next((p for p in parts if p["mountpoint"] == "/"), parts[0])
                self._disk_gauge.set_value(root["percent"], "Disk")

            # Uptime
            self._uptime_row.set_subtitle(format_uptime())

            # Temperatures
            temps = thermal.get_temperatures()
            # Rebuild temp rows if count changed
            if len(temps) != len(self._temp_rows):
                for r in self._temp_rows:
                    self._temp_card.remove(r)
                self._temp_rows.clear()
                for t in temps:
                    row = Adw.ActionRow(title=t["label"])
                    row.set_icon_name("temperature-symbolic")
                    self._temp_card.add(row)
                    self._temp_rows.append(row)
            for i, t in enumerate(temps):
                if i < len(self._temp_rows):
                    self._temp_rows[i].set_subtitle(f"{t['current']:.1f}°C")

            # Battery
            if self._bat_row:
                bat = thermal.get_battery_info()
                if bat:
                    status = "Charging" if bat["plugged"] else "Discharging"
                    self._bat_row.set_subtitle(f"{bat['percent']:.0f}% • {status}")

        except Exception:
            pass
        return True  # Keep timer alive

    def cleanup(self):
        for tid in self._timers:
            GLib.source_remove(tid)
        self._timers.clear()
