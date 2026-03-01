"""CPU detail page."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

from pulsedeck.monitors.cpu import (
    get_cpu_info, get_cpu_name, get_top_processes,
    kill_process, renice_process,
    get_available_governors, get_current_governor, set_governor,
)
from pulsedeck.ui.widgets import CircularGauge, MiniGraph, UsageBar, create_error_banner, show_error_banner, hide_error_banner
from pulsedeck.utils.helpers import is_root


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
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title = Gtk.Label(label="Processor")
        title.set_halign(Gtk.Align.START)
        title.add_css_class("section-title")
        header_box.append(title)
        subtitle = Gtk.Label(label=get_cpu_name())
        subtitle.set_halign(Gtk.Align.START)
        subtitle.add_css_class("section-subtitle")
        subtitle.set_ellipsize(3)
        header_box.append(subtitle)
        content.append(header_box)

        # ── Error banner (hidden by default) ──
        self._error_banner = create_error_banner()
        content.append(self._error_banner)

        # ── Top stats: gauge + graph side by side ──
        top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        top_box.set_halign(Gtk.Align.CENTER)

        # Gauge card
        gauge_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        gauge_card.add_css_class("gauge-card")
        self._gauge = CircularGauge(label="Total CPU", value=0, max_val=100,
                                     unit="%", color=(0.35, 0.65, 1.0), size=150)
        gauge_card.append(self._gauge)
        lbl = Gtk.Label(label="TOTAL")
        lbl.add_css_class("gauge-label")
        gauge_card.append(lbl)
        top_box.append(gauge_card)

        # Graph card
        graph_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        graph_card.add_css_class("graph-card")
        graph_card.set_hexpand(True)
        gl = Gtk.Label(label="CPU USAGE HISTORY")
        gl.set_halign(Gtk.Align.START)
        gl.add_css_class("graph-title")
        graph_card.append(gl)
        self._graph = MiniGraph(color=(0.35, 0.65, 1.0), max_points=90, height=90)
        graph_card.append(self._graph)
        top_box.append(graph_card)
        content.append(top_box)

        # ── Quick stat pills ──
        ci = get_cpu_info()
        pills_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        pills_box.set_homogeneous(True)

        self._freq_pill = self._make_pill("FREQUENCY", f"{ci['freq_current']:.0f} MHz")
        pills_box.append(self._freq_pill)

        cores_pill = self._make_pill("CORES",
            f"{ci['core_count_physical']}P / {ci['core_count_logical']}L")
        pills_box.append(cores_pill)

        self._load_pill = self._make_pill("LOAD AVG",
            f"{ci['load_1']:.2f} / {ci['load_5']:.2f} / {ci['load_15']:.2f}")
        pills_box.append(self._load_pill)

        content.append(pills_box)

        # ── Per-core bars ──
        cores_card = Adw.PreferencesGroup()
        cores_card.set_title("Per-Core Usage")
        self._cores_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        self._cores_list.set_margin_top(4)
        self._cores_list.set_margin_bottom(4)

        n_cores = ci["core_count_logical"]
        for i in range(n_cores):
            bar = UsageBar(label=f"Core {i}", percent=0,
                           color_start=(0.35, 0.65, 1.0), color_end=(1.0, 0.35, 0.35))
            self._core_bars.append(bar)
            self._cores_list.append(bar)

        cores_row_widget = Adw.ActionRow()
        cores_row_widget.set_child(self._cores_list)
        cores_card.add(cores_row_widget)
        content.append(cores_card)

        # ── Top processes ──
        proc_card = Adw.PreferencesGroup()
        proc_card.set_title("Top Processes (CPU)")
        self._proc_group = proc_card
        content.append(proc_card)

        # ── CPU Governor Control ── (root-enhanced)
        governors = get_available_governors()
        if governors:
            gov_card = Adw.PreferencesGroup()
            gov_card.set_title("CPU Frequency Governor")
            if is_root():
                gov_card.set_description("Select performance profile (root enabled)")
            else:
                gov_card.set_description("Requires root to change governor")

            current_gov = get_current_governor()

            self._gov_row = Adw.ActionRow(title="Current Governor")
            self._gov_row.set_icon_name("speedometer-symbolic")

            self._gov_badge = Gtk.Label(label=current_gov.upper() or "N/A")
            self._gov_badge.add_css_class("badge-ok")
            self._gov_badge.set_valign(Gtk.Align.CENTER)
            self._gov_row.add_suffix(self._gov_badge)
            gov_card.add(self._gov_row)

            self._gov_buttons = []
            gov_btn_row = Adw.ActionRow(title="Set Governor")
            gov_btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            gov_btn_box.set_valign(Gtk.Align.CENTER)

            for gov in governors:
                btn = Gtk.Button(label=gov.capitalize())
                btn.add_css_class("pill-button")
                if gov == current_gov:
                    btn.add_css_class("suggested-action")
                btn.set_sensitive(is_root())
                btn.connect("clicked", self._on_set_governor, gov)
                gov_btn_box.append(btn)
                self._gov_buttons.append((gov, btn))

            gov_btn_row.add_suffix(gov_btn_box)
            gov_card.add(gov_btn_row)

            if not is_root():
                hint_row = Adw.ActionRow(title="Run with sudo for governor control")
                hint_row.set_icon_name("dialog-warning-symbolic")
                hint_row.set_subtitle("sudo python3 main.py")
                gov_card.add(hint_row)

            content.append(gov_card)
            self._has_governor = True
        else:
            self._has_governor = False

    def _make_pill(self, label, value):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.add_css_class("stat-pill")
        lbl = Gtk.Label(label=label)
        lbl.add_css_class("stat-label")
        lbl.set_halign(Gtk.Align.START)
        box.append(lbl)
        val = Gtk.Label(label=value)
        val.add_css_class("dim-label")
        val.set_halign(Gtk.Align.START)
        val.set_ellipsize(3)
        box.append(val)
        box._value_label = val
        return box

    def _start_updates(self):
        tid = GLib.timeout_add(2000, self._update)
        self._timers.append(tid)
        self._update()

    def _update(self):
        errors = []

        # ── CPU info ──
        try:
            ci = get_cpu_info()
            self._gauge.set_value(ci["usage_percent"])
            self._graph.set_unavailable(False)
            self._graph.add_point(ci["usage_percent"])

            self._freq_pill._value_label.set_label(f"{ci['freq_current']:.0f} MHz")
            self._load_pill._value_label.set_label(
                f"{ci['load_1']:.2f} / {ci['load_5']:.2f} / {ci['load_15']:.2f}"
            )

            per_core = ci["per_core_percent"]
            for i, bar in enumerate(self._core_bars):
                if i < len(per_core):
                    bar.set_value(f"Core {i}", per_core[i])
        except Exception as e:
            errors.append(f"CPU data: {e}")
            self._gauge.set_unavailable(True)
            self._graph.set_unavailable(True)
            self._freq_pill._value_label.set_label("--")
            self._load_pill._value_label.set_label("--")

        # ── Top processes ──
        try:
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
                    subtitle=f"PID {pid} \u2022 CPU {cpu_pct:.1f}% \u2022 RAM {mem_pct:.1f}%"
                )
                row.add_css_class("process-row")

                # Kill button (works better with root)
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
            show_error_banner(self._error_banner, "CPU monitoring error", " | ".join(errors))
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

    def _on_set_governor(self, button, governor):
        """Set CPU frequency governor."""
        success, msg = set_governor(governor)
        if success:
            # Update badges
            self._gov_badge.set_label(governor.upper())
            for gov, btn in self._gov_buttons:
                btn.remove_css_class("suggested-action")
                if gov == governor:
                    btn.add_css_class("suggested-action")

    def cleanup(self):
        for tid in self._timers:
            GLib.source_remove(tid)
        self._timers.clear()
