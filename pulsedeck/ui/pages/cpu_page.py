"""CPU detail page."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

from pulsedeck.monitors.cpu import get_cpu_info, get_cpu_name, get_top_processes
from pulsedeck.ui.widgets import CircularGauge, MiniGraph, UsageBar


class CpuPage(Gtk.Box):
    """Detailed CPU monitoring page."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._timers = []
        self._core_bars = []
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

        # CPU info card
        info_card = Adw.PreferencesGroup()
        info_card.set_title("Processor")
        info_card.set_description(get_cpu_name())

        ci = get_cpu_info()
        self._freq_row = Adw.ActionRow(title="Frequency")
        self._freq_row.set_subtitle(f"{ci['freq_current']:.0f} MHz")
        info_card.add(self._freq_row)

        cores_row = Adw.ActionRow(title="Cores")
        cores_row.set_subtitle(f"{ci['core_count_physical']}P / {ci['core_count_logical']}L")
        info_card.add(cores_row)

        self._load_row = Adw.ActionRow(title="Load Average")
        self._load_row.set_subtitle(f"{ci['load_1']:.2f} / {ci['load_5']:.2f} / {ci['load_15']:.2f}")
        info_card.add(self._load_row)

        content.append(info_card)

        # Overall gauge + graph
        top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        top_box.set_halign(Gtk.Align.CENTER)

        self._gauge = CircularGauge(label="Total CPU", value=0, max_val=100,
                                     unit="%", color=(0.2, 0.6, 1.0), size=140)
        frame = Gtk.Frame()
        frame.set_child(self._gauge)
        top_box.append(frame)

        graph_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        graph_label = Gtk.Label(label="Usage History")
        graph_label.add_css_class("caption")
        graph_box.append(graph_label)
        self._graph = MiniGraph(color=(0.3, 0.6, 1.0), max_points=90, height=80)
        self._graph.set_content_width(280)
        graph_box.append(self._graph)
        top_box.append(graph_box)
        content.append(top_box)

        # Per-core bars
        cores_card = Adw.PreferencesGroup()
        cores_card.set_title("Per-Core Usage")
        self._cores_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self._cores_list.set_margin_top(4)
        self._cores_list.set_margin_bottom(4)

        n_cores = ci["core_count_logical"]
        for i in range(n_cores):
            bar = UsageBar(label=f"Core {i}", percent=0,
                           color_start=(0.2, 0.6, 1.0), color_end=(1.0, 0.3, 0.3))
            self._core_bars.append(bar)
            self._cores_list.append(bar)

        # Wrap in a row for the preferences group
        cores_row_widget = Adw.ActionRow()
        cores_row_widget.set_child(self._cores_list)
        cores_card.add(cores_row_widget)
        content.append(cores_card)

        # Top processes
        proc_card = Adw.PreferencesGroup()
        proc_card.set_title("Top Processes (CPU)")
        self._proc_group = proc_card
        content.append(proc_card)

    def _start_updates(self):
        tid = GLib.timeout_add(2000, self._update)
        self._timers.append(tid)
        self._update()

    def _update(self):
        try:
            ci = get_cpu_info()
            self._gauge.set_value(ci["usage_percent"])
            self._graph.add_point(ci["usage_percent"])
            self._freq_row.set_subtitle(f"{ci['freq_current']:.0f} MHz")
            self._load_row.set_subtitle(
                f"{ci['load_1']:.2f} / {ci['load_5']:.2f} / {ci['load_15']:.2f}"
            )

            # Per-core
            per_core = ci["per_core_percent"]
            for i, bar in enumerate(self._core_bars):
                if i < len(per_core):
                    bar.set_value(f"Core {i}", per_core[i])

            # Top processes - rebuild rows
            procs = get_top_processes(8)
            for r in self._proc_rows:
                self._proc_group.remove(r)
            self._proc_rows.clear()

            for p in procs:
                name = p.get("name", "?")
                cpu_pct = p.get("cpu_percent", 0) or 0
                mem_pct = p.get("memory_percent", 0) or 0
                pid = p.get("pid", 0)
                row = Adw.ActionRow(
                    title=name,
                    subtitle=f"PID {pid} • CPU {cpu_pct:.1f}% • RAM {mem_pct:.1f}%"
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
