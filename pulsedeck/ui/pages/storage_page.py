"""Storage detail page."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

from pulsedeck.monitors.storage import get_disk_partitions, get_disk_io, get_smart_health, get_smart_capable_devices
from pulsedeck.ui.widgets import UsageBar, create_error_banner, show_error_banner, hide_error_banner
from pulsedeck.utils.helpers import format_bytes, is_root


class StoragePage(Gtk.Box):
    """Detailed storage monitoring page."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._timers = []
        self._partition_rows = []
        self._smart_rows = []
        self._prev_io = None
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
        header = Gtk.Label(label="Storage")
        header.set_halign(Gtk.Align.START)
        header.add_css_class("section-title")
        content.append(header)

        # ── Error banner (hidden by default) ──
        self._error_banner = create_error_banner()
        content.append(self._error_banner)

        # ── I/O stat pills ──
        io_pills = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        io_pills.set_homogeneous(True)

        self._read_pill = self._make_pill("READ SPEED", "Measuring...")
        io_pills.append(self._read_pill)
        self._write_pill = self._make_pill("WRITE SPEED", "Measuring...")
        io_pills.append(self._write_pill)
        self._total_read_pill = self._make_pill("TOTAL READ", "0 B")
        io_pills.append(self._total_read_pill)
        self._total_write_pill = self._make_pill("TOTAL WRITTEN", "0 B")
        io_pills.append(self._total_write_pill)

        content.append(io_pills)

        # ── Partitions card ──
        self._part_card = Adw.PreferencesGroup()
        self._part_card.set_title("Disk Partitions")
        content.append(self._part_card)

        # ── SMART Health card ── (root-enhanced)
        self._smart_card = Adw.PreferencesGroup()
        self._smart_card.set_title("Disk Health (SMART)")
        if is_root():
            self._smart_card.set_description("S.M.A.R.T. diagnostics (root access enabled)")
        else:
            self._smart_card.set_description("Run as root and install smartmontools for full health data")
        content.append(self._smart_card)

        self._smart_loaded = False

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
        tid = GLib.timeout_add(5000, self._update)
        self._timers.append(tid)
        self._update()

    def _update(self):
        errors = []

        # ── Partitions ──
        try:
            parts = get_disk_partitions()
            if len(parts) != len(self._partition_rows):
                for r in self._partition_rows:
                    self._part_card.remove(r)
                self._partition_rows.clear()

                if parts:
                    for p in parts:
                        row = Adw.ActionRow(
                            title=f"{p['mountpoint']}",
                            subtitle=f"{p['device']} ({p['fstype']})"
                        )
                        row.set_icon_name("drive-harddisk-symbolic")

                        pct_label = Gtk.Label()
                        pct_label.set_valign(Gtk.Align.CENTER)
                        row.add_suffix(pct_label)

                        size_label = Gtk.Label()
                        size_label.set_valign(Gtk.Align.CENTER)
                        size_label.add_css_class("dim-label")
                        row.add_suffix(size_label)

                        self._part_card.add(row)
                        self._partition_rows.append((row, pct_label, size_label))
                else:
                    row = Adw.ActionRow(title="No partitions detected")
                    row.set_subtitle("Disk partition data is not available")
                    row.set_icon_name("dialog-warning-symbolic")
                    self._part_card.add(row)
                    self._partition_rows.append((row, None, None))

            for i, p in enumerate(parts):
                if i < len(self._partition_rows):
                    _, pct_lbl, size_lbl = self._partition_rows[i]
                    if pct_lbl is None:
                        continue
                    pct = p['percent']
                    pct_lbl.set_text(f"{pct:.0f}%")
                    for cls in ["badge-ok", "badge-warn", "badge-critical"]:
                        pct_lbl.remove_css_class(cls)
                    if pct >= 90:
                        pct_lbl.add_css_class("badge-critical")
                    elif pct >= 75:
                        pct_lbl.add_css_class("badge-warn")
                    else:
                        pct_lbl.add_css_class("badge-ok")

                    used = format_bytes(p["used"])
                    total = format_bytes(p["total"])
                    size_lbl.set_text(f"  {used} / {total}")
        except Exception as e:
            errors.append(f"Partitions: {e}")

        # ── I/O stats ──
        try:
            io = get_disk_io()
            if self._prev_io:
                dt = 5.0
                read_speed = (io["read_bytes"] - self._prev_io["read_bytes"]) / dt
                write_speed = (io["write_bytes"] - self._prev_io["write_bytes"]) / dt
                self._read_pill._value_label.set_label(f"{format_bytes(max(0, read_speed))}/s")
                self._write_pill._value_label.set_label(f"{format_bytes(max(0, write_speed))}/s")
            else:
                self._read_pill._value_label.set_label("Measuring...")
                self._write_pill._value_label.set_label("Measuring...")

            self._total_read_pill._value_label.set_label(format_bytes(io["read_bytes"]))
            self._total_write_pill._value_label.set_label(format_bytes(io["write_bytes"]))
            self._prev_io = io
        except Exception as e:
            errors.append(f"I/O stats: {e}")
            self._read_pill._value_label.set_label("--")
            self._write_pill._value_label.set_label("--")

        # ── SMART Health (load once, requires root + smartctl) ──
        if not self._smart_loaded:
            self._smart_loaded = True
            try:
                for old_row in self._smart_rows:
                    self._smart_card.remove(old_row)
                self._smart_rows.clear()

                devices = get_smart_capable_devices()
                found_smart = False

                for dev in devices:
                    health = get_smart_health(dev)
                    if health is None:
                        continue
                    found_smart = True

                    # Device header
                    dev_row = Adw.ActionRow(
                        title=health.get("model", dev),
                        subtitle=f"{dev}" + (f" | S/N: {health['serial']}" if health.get("serial") else "")
                    )
                    dev_row.set_icon_name("drive-harddisk-symbolic")

                    status_badge = Gtk.Label(label=health["smart_status"])
                    status_badge.set_valign(Gtk.Align.CENTER)
                    if health["smart_status"] == "PASSED":
                        status_badge.add_css_class("badge-ok")
                    elif health["smart_status"] == "FAILED":
                        status_badge.add_css_class("badge-critical")
                    else:
                        status_badge.add_css_class("badge-warn")
                    dev_row.add_suffix(status_badge)
                    self._smart_card.add(dev_row)
                    self._smart_rows.append(dev_row)

                    # Key metrics
                    if health.get("temperature") is not None:
                        temp_row = Adw.ActionRow(title="Temperature")
                        temp_row.set_icon_name("temperature-symbolic")
                        temp_val = health["temperature"]
                        temp_lbl = Gtk.Label(label=f"{temp_val}\u00b0C")
                        temp_lbl.set_valign(Gtk.Align.CENTER)
                        if temp_val >= 55:
                            temp_lbl.add_css_class("badge-critical")
                        elif temp_val >= 45:
                            temp_lbl.add_css_class("badge-warn")
                        else:
                            temp_lbl.add_css_class("badge-ok")
                        temp_row.add_suffix(temp_lbl)
                        self._smart_card.add(temp_row)
                        self._smart_rows.append(temp_row)

                    if health.get("power_on_hours") is not None:
                        hours = health["power_on_hours"]
                        days = hours // 24
                        poh_row = Adw.ActionRow(title="Power-On Time",
                                                subtitle=f"{hours} hours ({days} days)")
                        poh_row.set_icon_name("preferences-system-time-symbolic")
                        self._smart_card.add(poh_row)
                        self._smart_rows.append(poh_row)

                    if health.get("power_cycle_count") is not None:
                        pcc_row = Adw.ActionRow(title="Power Cycles",
                                                subtitle=str(health["power_cycle_count"]))
                        self._smart_card.add(pcc_row)
                        self._smart_rows.append(pcc_row)

                    if health.get("reallocated_sectors") is not None:
                        realloc = health["reallocated_sectors"]
                        rs_row = Adw.ActionRow(title="Reallocated Sectors")
                        rs_row.set_icon_name("dialog-warning-symbolic")
                        rs_badge = Gtk.Label(label=str(realloc))
                        rs_badge.set_valign(Gtk.Align.CENTER)
                        if realloc > 10:
                            rs_badge.add_css_class("badge-critical")
                        elif realloc > 0:
                            rs_badge.add_css_class("badge-warn")
                        else:
                            rs_badge.add_css_class("badge-ok")
                        rs_row.add_suffix(rs_badge)
                        self._smart_card.add(rs_row)
                        self._smart_rows.append(rs_row)

                if not found_smart:
                    hint_row = Adw.ActionRow(title="SMART data unavailable")
                    if is_root():
                        hint_row.set_subtitle("Install smartmontools: sudo apt install smartmontools")
                    else:
                        hint_row.set_subtitle("Requires root + smartmontools installed")
                    hint_row.set_icon_name("dialog-information-symbolic")
                    self._smart_card.add(hint_row)
                    self._smart_rows.append(hint_row)

            except Exception:
                pass  # Non-critical — SMART is optional

        # ── Error banner ──
        if errors:
            show_error_banner(self._error_banner, "Storage monitoring error", " | ".join(errors))
        else:
            hide_error_banner(self._error_banner)

        return True

    def cleanup(self):
        for tid in self._timers:
            GLib.source_remove(tid)
        self._timers.clear()
