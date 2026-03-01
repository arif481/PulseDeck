"""Memory detail page."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

from pulsedeck.monitors.memory import get_memory_info, get_top_memory_processes
from pulsedeck.monitors.cpu import kill_process
from pulsedeck.ui.widgets import CircularGauge, MiniGraph, UsageBar, create_error_banner, show_error_banner, hide_error_banner
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
        header = Gtk.Label(label="Memory")
        header.set_halign(Gtk.Align.START)
        header.add_css_class("section-title")
        content.append(header)

        # ── Error banner (hidden by default) ──
        self._error_banner = create_error_banner()
        content.append(self._error_banner)

        # ── Gauges row ──
        gauges_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        gauges_box.set_halign(Gtk.Align.CENTER)

        self._ram_gauge = CircularGauge(label="RAM", value=0, max_val=100, unit="%",
                                         color=(0.4, 0.85, 0.5), size=150)
        self._swap_gauge = CircularGauge(label="Swap", value=0, max_val=100, unit="%",
                                          color=(0.9, 0.55, 0.25), size=150)

        for gauge, name in [(self._ram_gauge, "RAM"), (self._swap_gauge, "SWAP")]:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            card.add_css_class("gauge-card")
            card.append(gauge)
            lbl = Gtk.Label(label=name)
            lbl.add_css_class("gauge-label")
            card.append(lbl)
            gauges_box.append(card)

        content.append(gauges_box)

        # ── Graph ──
        graph_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        graph_card.add_css_class("graph-card")
        gl = Gtk.Label(label="MEMORY USAGE HISTORY")
        gl.set_halign(Gtk.Align.START)
        gl.add_css_class("graph-title")
        graph_card.append(gl)
        self._graph = MiniGraph(color=(0.4, 0.85, 0.5), max_points=90, height=70)
        graph_card.append(self._graph)
        content.append(graph_card)

        # ── RAM details ──
        ram_card = Adw.PreferencesGroup()
        ram_card.set_title("Memory Details")

        self._total_row = Adw.ActionRow(title="Total")
        self._total_row.set_icon_name("drive-harddisk-symbolic")
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

        # ── Swap details ──
        swap_card = Adw.PreferencesGroup()
        swap_card.set_title("Swap")
        self._swap_total_row = Adw.ActionRow(title="Total")
        swap_card.add(self._swap_total_row)
        self._swap_used_row = Adw.ActionRow(title="Used")
        swap_card.add(self._swap_used_row)
        self._swap_free_row = Adw.ActionRow(title="Free")
        swap_card.add(self._swap_free_row)
        content.append(swap_card)

        # ── Top processes ──
        proc_card = Adw.PreferencesGroup()
        proc_card.set_title("Top Processes (Memory)")
        self._proc_group = proc_card
        content.append(proc_card)

    def _start_updates(self):
        tid = GLib.timeout_add(3000, self._update)
        self._timers.append(tid)
        self._update()

    def _update(self):
        errors = []

        # ── Memory info ──
        try:
            mi = get_memory_info()
            self._ram_gauge.set_value(mi["percent"], "RAM")
            self._swap_gauge.set_value(mi["swap_percent"], "Swap")
            self._graph.set_unavailable(False)
            self._graph.add_point(mi["percent"])

            self._total_row.set_subtitle(format_bytes(mi["total"]))
            self._used_row.set_subtitle(format_bytes(mi["used"]))
            self._available_row.set_subtitle(format_bytes(mi["available"]))
            self._cached_row.set_subtitle(format_bytes(mi["cached"]))
            self._buffers_row.set_subtitle(format_bytes(mi["buffers"]))

            self._swap_total_row.set_subtitle(format_bytes(mi["swap_total"]))
            self._swap_used_row.set_subtitle(format_bytes(mi["swap_used"]))
            self._swap_free_row.set_subtitle(format_bytes(mi["swap_free"]))
        except Exception as e:
            errors.append(f"Memory data: {e}")
            self._ram_gauge.set_unavailable(True)
            self._swap_gauge.set_unavailable(True)
            self._graph.set_unavailable(True)

        # ── Top processes ──
        try:
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
                    subtitle=f"PID {pid} \u2022 {mem_pct:.1f}% \u2022 RSS {rss}"
                )
                row.add_css_class("process-row")

                # Kill button
                kill_btn = Gtk.Button(icon_name="process-stop-symbolic")
                kill_btn.set_valign(Gtk.Align.CENTER)
                kill_btn.add_css_class("destructive-action")
                kill_btn.add_css_class("pill-button")
                kill_btn.set_tooltip_text(f"Kill PID {pid}")
                kill_btn.connect("clicked", self._on_kill_process, pid, name)
                row.add_suffix(kill_btn)

                self._proc_group.add(row)
                self._proc_rows.append(row)
        except Exception as e:
            errors.append(f"Process list: {e}")

        # ── Error banner ──
        if errors:
            show_error_banner(self._error_banner, "Memory monitoring error", " | ".join(errors))
        else:
            hide_error_banner(self._error_banner)

        return True

    def _on_kill_process(self, button, pid, name):
        """Kill a process."""
        import signal as sig_mod
        success, msg = kill_process(pid, sig_mod.SIGTERM)
        button.set_sensitive(False)
        if success:
            button.set_tooltip_text(f"Killed {name}")
        else:
            button.set_tooltip_text(msg)

    def cleanup(self):
        for tid in self._timers:
            GLib.source_remove(tid)
        self._timers.clear()
