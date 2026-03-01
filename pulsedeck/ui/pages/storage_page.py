"""Storage detail page."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

from pulsedeck.monitors.storage import get_disk_partitions, get_disk_io
from pulsedeck.ui.widgets import UsageBar
from pulsedeck.utils.helpers import format_bytes


class StoragePage(Gtk.Box):
    """Detailed storage monitoring page."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._timers = []
        self._partition_rows = []
        self._prev_io = None
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

        # Partitions card
        self._part_card = Adw.PreferencesGroup()
        self._part_card.set_title("Disk Partitions")
        content.append(self._part_card)

        # I/O card
        io_card = Adw.PreferencesGroup()
        io_card.set_title("Disk I/O")
        self._read_row = Adw.ActionRow(title="Read Speed")
        self._read_row.set_icon_name("go-down-symbolic")
        io_card.add(self._read_row)
        self._write_row = Adw.ActionRow(title="Write Speed")
        self._write_row.set_icon_name("go-up-symbolic")
        io_card.add(self._write_row)
        self._total_read_row = Adw.ActionRow(title="Total Read")
        io_card.add(self._total_read_row)
        self._total_write_row = Adw.ActionRow(title="Total Written")
        io_card.add(self._total_write_row)
        content.append(io_card)

    def _start_updates(self):
        tid = GLib.timeout_add(5000, self._update)
        self._timers.append(tid)
        self._update()

    def _update(self):
        try:
            # Partitions
            parts = get_disk_partitions()
            # Rebuild if count changed
            if len(parts) != len(self._partition_rows):
                for r in self._partition_rows:
                    self._part_card.remove(r)
                self._partition_rows.clear()

                for p in parts:
                    row = Adw.ActionRow(
                        title=f"{p['mountpoint']}",
                        subtitle=f"{p['device']} ({p['fstype']})"
                    )
                    # Add a usage indicator suffix
                    pct_label = Gtk.Label()
                    pct_label.set_valign(Gtk.Align.CENTER)
                    row.add_suffix(pct_label)

                    size_label = Gtk.Label()
                    size_label.set_valign(Gtk.Align.CENTER)
                    size_label.add_css_class("dim-label")
                    row.add_suffix(size_label)

                    self._part_card.add(row)
                    self._partition_rows.append((row, pct_label, size_label))

            for i, p in enumerate(parts):
                if i < len(self._partition_rows):
                    _, pct_lbl, size_lbl = self._partition_rows[i]
                    pct_lbl.set_text(f"{p['percent']:.0f}%")
                    used = format_bytes(p["used"])
                    total = format_bytes(p["total"])
                    size_lbl.set_text(f"  {used} / {total}")

            # I/O
            io = get_disk_io()
            if self._prev_io:
                dt = 5.0  # update interval
                read_speed = (io["read_bytes"] - self._prev_io["read_bytes"]) / dt
                write_speed = (io["write_bytes"] - self._prev_io["write_bytes"]) / dt
                self._read_row.set_subtitle(f"{format_bytes(max(0, read_speed))}/s")
                self._write_row.set_subtitle(f"{format_bytes(max(0, write_speed))}/s")
            else:
                self._read_row.set_subtitle("Measuring...")
                self._write_row.set_subtitle("Measuring...")

            self._total_read_row.set_subtitle(format_bytes(io["read_bytes"]))
            self._total_write_row.set_subtitle(format_bytes(io["write_bytes"]))
            self._prev_io = io

        except Exception:
            pass
        return True

    def cleanup(self):
        for tid in self._timers:
            GLib.source_remove(tid)
        self._timers.clear()
