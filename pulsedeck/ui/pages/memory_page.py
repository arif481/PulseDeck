"""Memory detail page."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

from pulsedeck.monitors.memory import get_memory_info, get_top_memory_processes
from pulsedeck.ui.widgets import CircularGauge, MiniGraph, UsageBar
from pulsedeck.utils.helpers import format_bytes


class MemoryPage(Gtk.Box):
    """Detailed memory monitoring page."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._timers = []
        self._proc_rows = []
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

        # Gauges
        gauges_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        gauges_box.set_halign(Gtk.Align.CENTER)

        self._ram_gauge = CircularGauge(label="RAM", value=0, max_val=100, unit="%",
                                         color=(0.4, 0.8, 0.4), size=140)
        self._swap_gauge = CircularGauge(label="Swap", value=0, max_val=100, unit="%",
                                          color=(0.8, 0.5, 0.2), size=140)

        for g in [self._ram_gauge, self._swap_gauge]:
            frame = Gtk.Frame()
            frame.set_child(g)
            gauges_box.append(frame)

        content.append(gauges_box)

        # Graph
        graph_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        graph_box.set_halign(Gtk.Align.CENTER)
        self._graph = MiniGraph(color=(0.4, 0.8, 0.4), max_points=90, height=60)
        self._graph.set_content_width(400)
        graph_box.append(self._graph)
        content.append(graph_box)

        # RAM details
        ram_card = Adw.PreferencesGroup()
        ram_card.set_title("Memory Details")

        self._total_row = Adw.ActionRow(title="Total")
        ram_card.add(self._total_row)
        self._used_row = Adw.ActionRow(title="Used")
        ram_card.add(self._used_row)
        self._available_row = Adw.ActionRow(title="Available")
        ram_card.add(self._available_row)
        self._cached_row = Adw.ActionRow(title="Cached")
        ram_card.add(self._cached_row)
        self._buffers_row = Adw.ActionRow(title="Buffers")
        ram_card.add(self._buffers_row)
        content.append(ram_card)

        # Swap details
        swap_card = Adw.PreferencesGroup()
        swap_card.set_title("Swap")
        self._swap_total_row = Adw.ActionRow(title="Total")
        swap_card.add(self._swap_total_row)
        self._swap_used_row = Adw.ActionRow(title="Used")
        swap_card.add(self._swap_used_row)
        self._swap_free_row = Adw.ActionRow(title="Free")
        swap_card.add(self._swap_free_row)
        content.append(swap_card)

        # Top processes
        proc_card = Adw.PreferencesGroup()
        proc_card.set_title("Top Processes (Memory)")
        self._proc_group = proc_card
        content.append(proc_card)

    def _start_updates(self):
        tid = GLib.timeout_add(3000, self._update)
        self._timers.append(tid)
        self._update()

    def _update(self):
        try:
            mi = get_memory_info()
            self._ram_gauge.set_value(mi["percent"], "RAM")
            self._swap_gauge.set_value(mi["swap_percent"], "Swap")
            self._graph.add_point(mi["percent"])

            self._total_row.set_subtitle(format_bytes(mi["total"]))
            self._used_row.set_subtitle(format_bytes(mi["used"]))
            self._available_row.set_subtitle(format_bytes(mi["available"]))
            self._cached_row.set_subtitle(format_bytes(mi["cached"]))
            self._buffers_row.set_subtitle(format_bytes(mi["buffers"]))

            self._swap_total_row.set_subtitle(format_bytes(mi["swap_total"]))
            self._swap_used_row.set_subtitle(format_bytes(mi["swap_used"]))
            self._swap_free_row.set_subtitle(format_bytes(mi["swap_free"]))

            # Top processes
            procs = get_top_memory_processes(8)
            for r in self._proc_rows:
                self._proc_group.remove(r)
            self._proc_rows.clear()

            for p in procs:
                name = p.get("name", "?")
                mem_pct = p.get("memory_percent", 0) or 0
                pid = p.get("pid", 0)
                mem_info = p.get("memory_info")
                rss = format_bytes(mem_info.rss) if mem_info else "N/A"
                row = Adw.ActionRow(
                    title=name,
                    subtitle=f"PID {pid} • {mem_pct:.1f}% • RSS {rss}"
                )
                self._proc_group.add(row)
                self._proc_rows.append(row)
        except Exception:
            pass
        return True

    def cleanup(self):
        for tid in self._timers:
            GLib.source_remove(tid)
        self._timers.clear()
