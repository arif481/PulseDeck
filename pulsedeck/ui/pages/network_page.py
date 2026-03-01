"""Network monitoring page."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

from pulsedeck.monitors.network import (
    get_network_interfaces, get_network_io, get_connection_summary, get_wifi_info,
)
from pulsedeck.ui.widgets import MiniGraph, create_error_banner, show_error_banner, hide_error_banner
from pulsedeck.utils.helpers import format_bytes, is_root


class NetworkPage(Gtk.Box):
    """Network monitoring page with bandwidth, interfaces, and connections."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._timers = []
        self._iface_rows = []
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
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title = Gtk.Label(label="Network")
        title.set_halign(Gtk.Align.START)
        title.add_css_class("section-title")
        header_box.append(title)

        wifi = get_wifi_info()
        if wifi:
            subtitle = Gtk.Label(label=f"Connected to {wifi['ssid']}")
        else:
            subtitle = Gtk.Label(label="Wired / No WiFi detected")
        subtitle.set_halign(Gtk.Align.START)
        subtitle.add_css_class("section-subtitle")
        header_box.append(subtitle)
        content.append(header_box)

        # ── Error banner ──
        self._error_banner = create_error_banner()
        content.append(self._error_banner)

        # ── Root status info ──
        if not is_root():
            root_hint = create_error_banner(
                title="Limited without root",
                detail="Connection tracking requires root. Run with sudo for full details.",
                warning=True,
            )
            root_hint.set_visible(True)
            content.append(root_hint)

        # ── Bandwidth stat pills ──
        pills_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        pills_box.set_homogeneous(True)

        self._dl_pill = self._make_pill("DOWNLOAD", "Measuring...")
        pills_box.append(self._dl_pill)
        self._ul_pill = self._make_pill("UPLOAD", "Measuring...")
        pills_box.append(self._ul_pill)
        self._total_dl_pill = self._make_pill("TOTAL DOWN", "0 B")
        pills_box.append(self._total_dl_pill)
        self._total_ul_pill = self._make_pill("TOTAL UP", "0 B")
        pills_box.append(self._total_ul_pill)
        content.append(pills_box)

        # ── Bandwidth graphs ──
        graphs_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        graphs_box.set_homogeneous(True)

        dl_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        dl_card.add_css_class("graph-card")
        dl_label = Gtk.Label(label="DOWNLOAD BANDWIDTH")
        dl_label.set_halign(Gtk.Align.START)
        dl_label.add_css_class("graph-title")
        dl_card.append(dl_label)
        self._dl_graph = MiniGraph(color=(0.35, 0.65, 1.0), max_points=60, height=60)
        dl_card.append(self._dl_graph)
        self._dl_speed_label = Gtk.Label(label="--")
        self._dl_speed_label.set_halign(Gtk.Align.END)
        self._dl_speed_label.add_css_class("stat-value")
        dl_card.append(self._dl_speed_label)
        graphs_box.append(dl_card)

        ul_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        ul_card.add_css_class("graph-card")
        ul_label = Gtk.Label(label="UPLOAD BANDWIDTH")
        ul_label.set_halign(Gtk.Align.START)
        ul_label.add_css_class("graph-title")
        ul_card.append(ul_label)
        self._ul_graph = MiniGraph(color=(0.4, 0.85, 0.5), max_points=60, height=60)
        ul_card.append(self._ul_graph)
        self._ul_speed_label = Gtk.Label(label="--")
        self._ul_speed_label.set_halign(Gtk.Align.END)
        self._ul_speed_label.add_css_class("stat-value")
        ul_card.append(self._ul_speed_label)
        graphs_box.append(ul_card)

        content.append(graphs_box)

        # ── Network interfaces card ──
        self._iface_card = Adw.PreferencesGroup()
        self._iface_card.set_title("Network Interfaces")
        self._iface_card.set_description("Active network adapters")
        content.append(self._iface_card)

        # ── Connection summary card (root-enhanced) ──
        self._conn_card = Adw.PreferencesGroup()
        self._conn_card.set_title("Connections")
        if is_root():
            self._conn_card.set_description("Active network connections")
        else:
            self._conn_card.set_description("Run as root for connection details")

        self._conn_established_row = Adw.ActionRow(title="Established")
        self._conn_established_row.set_icon_name("network-transmit-receive-symbolic")
        self._conn_established_badge = Gtk.Label(label="--")
        self._conn_established_badge.add_css_class("badge-ok")
        self._conn_established_badge.set_valign(Gtk.Align.CENTER)
        self._conn_established_row.add_suffix(self._conn_established_badge)
        self._conn_card.add(self._conn_established_row)

        self._conn_listen_row = Adw.ActionRow(title="Listening")
        self._conn_listen_row.set_icon_name("network-receive-symbolic")
        self._conn_listen_badge = Gtk.Label(label="--")
        self._conn_listen_badge.add_css_class("badge-ok")
        self._conn_listen_badge.set_valign(Gtk.Align.CENTER)
        self._conn_listen_row.add_suffix(self._conn_listen_badge)
        self._conn_card.add(self._conn_listen_row)

        self._conn_wait_row = Adw.ActionRow(title="Time Wait / Close Wait")
        self._conn_wait_row.set_icon_name("network-offline-symbolic")
        self._conn_wait_badge = Gtk.Label(label="--")
        self._conn_wait_badge.add_css_class("dim-label")
        self._conn_wait_badge.set_valign(Gtk.Align.CENTER)
        self._conn_wait_row.add_suffix(self._conn_wait_badge)
        self._conn_card.add(self._conn_wait_row)

        self._conn_total_row = Adw.ActionRow(title="Total")
        self._conn_total_badge = Gtk.Label(label="--")
        self._conn_total_badge.set_valign(Gtk.Align.CENTER)
        self._conn_total_row.add_suffix(self._conn_total_badge)
        self._conn_card.add(self._conn_total_row)

        # ── Error stats ──
        self._err_card = Adw.PreferencesGroup()
        self._err_card.set_title("Network Errors / Drops")

        self._errin_row = Adw.ActionRow(title="Errors In")
        self._errin_row.set_icon_name("dialog-error-symbolic")
        self._errin_badge = Gtk.Label(label="0")
        self._errin_badge.set_valign(Gtk.Align.CENTER)
        self._errin_row.add_suffix(self._errin_badge)
        self._err_card.add(self._errin_row)

        self._errout_row = Adw.ActionRow(title="Errors Out")
        self._errout_badge = Gtk.Label(label="0")
        self._errout_badge.set_valign(Gtk.Align.CENTER)
        self._errout_row.add_suffix(self._errout_badge)
        self._err_card.add(self._errout_row)

        self._dropin_row = Adw.ActionRow(title="Dropped In")
        self._dropin_badge = Gtk.Label(label="0")
        self._dropin_badge.set_valign(Gtk.Align.CENTER)
        self._dropin_row.add_suffix(self._dropin_badge)
        self._err_card.add(self._dropin_row)

        self._dropout_row = Adw.ActionRow(title="Dropped Out")
        self._dropout_badge = Gtk.Label(label="0")
        self._dropout_badge.set_valign(Gtk.Align.CENTER)
        self._dropout_row.add_suffix(self._dropout_badge)
        self._err_card.add(self._dropout_row)

        content.append(self._conn_card)
        content.append(self._err_card)

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

        # ── Bandwidth ──
        try:
            io = get_network_io()
            total = io["total"]

            if self._prev_io:
                dt = 2.0
                dl_speed = (total["bytes_recv"] - self._prev_io["bytes_recv"]) / dt
                ul_speed = (total["bytes_sent"] - self._prev_io["bytes_sent"]) / dt
                self._dl_pill._value_label.set_label(f"{format_bytes(max(0, dl_speed))}/s")
                self._ul_pill._value_label.set_label(f"{format_bytes(max(0, ul_speed))}/s")
                self._dl_speed_label.set_label(f"{format_bytes(max(0, dl_speed))}/s")
                self._ul_speed_label.set_label(f"{format_bytes(max(0, ul_speed))}/s")
                self._dl_graph.add_point(max(0, dl_speed) / 1024)  # KB/s for graph
                self._ul_graph.add_point(max(0, ul_speed) / 1024)
            else:
                self._dl_pill._value_label.set_label("Measuring...")
                self._ul_pill._value_label.set_label("Measuring...")

            self._total_dl_pill._value_label.set_label(format_bytes(total["bytes_recv"]))
            self._total_ul_pill._value_label.set_label(format_bytes(total["bytes_sent"]))

            # Error counters
            errin = total.get("errin", 0)
            errout = total.get("errout", 0)
            dropin = total.get("dropin", 0)
            dropout = total.get("dropout", 0)

            self._errin_badge.set_label(str(errin))
            self._errout_badge.set_label(str(errout))
            self._dropin_badge.set_label(str(dropin))
            self._dropout_badge.set_label(str(dropout))

            # Color-code errors
            for badge, val in [(self._errin_badge, errin), (self._errout_badge, errout),
                               (self._dropin_badge, dropin), (self._dropout_badge, dropout)]:
                for cls in ["badge-ok", "badge-warn", "badge-critical"]:
                    badge.remove_css_class(cls)
                if val > 100:
                    badge.add_css_class("badge-critical")
                elif val > 0:
                    badge.add_css_class("badge-warn")
                else:
                    badge.add_css_class("badge-ok")

            self._prev_io = total
        except Exception as e:
            errors.append(f"Network I/O: {e}")
            self._dl_graph.set_unavailable(True)
            self._ul_graph.set_unavailable(True)

        # ── Interfaces ──
        try:
            ifaces = get_network_interfaces()
            if len(ifaces) != len(self._iface_rows):
                for r in self._iface_rows:
                    self._iface_card.remove(r)
                self._iface_rows.clear()

                if ifaces:
                    for iface in ifaces:
                        row = Adw.ActionRow(title=iface["name"])
                        icon = "network-wired-symbolic"
                        if iface["name"].startswith("wl"):
                            icon = "network-wireless-symbolic"
                        elif iface["name"].startswith("docker") or iface["name"].startswith("br-"):
                            icon = "network-workgroup-symbolic"
                        row.set_icon_name(icon)

                        ip_text = iface.get("ipv4", "") or "No IP"
                        mac_text = iface.get("mac", "")
                        speed_text = f"{iface['speed']} Mb/s" if iface['speed'] > 0 else ""
                        row.set_subtitle(f"{ip_text}" + (f" | {mac_text}" if mac_text else ""))

                        # Status badge
                        status_badge = Gtk.Label()
                        status_badge.set_valign(Gtk.Align.CENTER)
                        if iface["is_up"]:
                            status_badge.set_label("UP" + (f" {speed_text}" if speed_text else ""))
                            status_badge.add_css_class("badge-ok")
                        else:
                            status_badge.set_label("DOWN")
                            status_badge.add_css_class("badge-critical")
                        row.add_suffix(status_badge)

                        self._iface_card.add(row)
                        self._iface_rows.append(row)
                else:
                    row = Adw.ActionRow(title="No network interfaces found")
                    row.set_icon_name("dialog-warning-symbolic")
                    self._iface_card.add(row)
                    self._iface_rows.append(row)
        except Exception as e:
            errors.append(f"Interfaces: {e}")

        # ── Connections (root-enhanced) ──
        try:
            summary = get_connection_summary()
            if summary is None:
                # Not root — show permission message
                self._conn_established_badge.set_label("N/A")
                self._conn_listen_badge.set_label("N/A")
                self._conn_wait_badge.set_label("N/A")
                self._conn_total_badge.set_label("Need root")
            else:
                self._conn_established_badge.set_label(str(summary["ESTABLISHED"]))
                self._conn_listen_badge.set_label(str(summary["LISTEN"]))
                wait = summary["TIME_WAIT"] + summary["CLOSE_WAIT"]
                self._conn_wait_badge.set_label(str(wait))
                self._conn_total_badge.set_label(str(summary["total"]))
        except Exception as e:
            errors.append(f"Connections: {e}")

        # ── Error banner ──
        if errors:
            show_error_banner(self._error_banner, "Network monitoring error", " | ".join(errors))
        else:
            hide_error_banner(self._error_banner)

        return True

    def cleanup(self):
        for tid in self._timers:
            GLib.source_remove(tid)
        self._timers.clear()
