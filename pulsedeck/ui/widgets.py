"""Custom reusable widgets for PulseDeck UI."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Gdk, GLib
import cairo
import math


class UsageBar(Gtk.DrawingArea):
    """A horizontal usage bar with gradient colors."""

    def __init__(self, label="", percent=0, color_start=(0.2, 0.6, 1.0),
                 color_end=(1.0, 0.3, 0.3)):
        super().__init__()
        self._label = label
        self._percent = percent
        self._color_start = color_start
        self._color_end = color_end
        self.set_content_width(200)
        self.set_content_height(32)
        self.set_draw_func(self._draw)

    def _draw(self, area, cr, width, height):
        # Background
        cr.set_source_rgba(0.15, 0.15, 0.18, 1.0)
        _rounded_rect(cr, 0, 0, width, height, 6)
        cr.fill()

        # Fill bar
        pct = max(0, min(100, self._percent))
        bar_width = (pct / 100.0) * width
        if bar_width > 0:
            t = pct / 100.0
            r = self._color_start[0] + t * (self._color_end[0] - self._color_start[0])
            g = self._color_start[1] + t * (self._color_end[1] - self._color_start[1])
            b = self._color_start[2] + t * (self._color_end[2] - self._color_start[2])
            cr.set_source_rgba(r, g, b, 0.85)
            _rounded_rect(cr, 0, 0, bar_width, height, 6)
            cr.fill()

        # Text
        cr.set_source_rgba(1, 1, 1, 0.95)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(12)
        text = f"{self._label}  {pct:.0f}%"
        extents = cr.text_extents(text)
        cr.move_to(8, height / 2 + extents.height / 2)
        cr.show_text(text)

    def set_value(self, label, percent):
        self._label = label
        self._percent = percent
        self.queue_draw()


class CircularGauge(Gtk.DrawingArea):
    """A circular gauge widget (like a speedometer)."""

    def __init__(self, label="", value=0, max_val=100, unit="%",
                 color=(0.2, 0.6, 1.0), size=120):
        super().__init__()
        self._label = label
        self._value = value
        self._max_val = max_val
        self._unit = unit
        self._color = color
        self.set_content_width(size)
        self.set_content_height(size)
        self.set_draw_func(self._draw)

    def _draw(self, area, cr, width, height):
        cx = width / 2
        cy = height / 2
        radius = min(width, height) / 2 - 8
        line_width = 8

        # Background arc
        cr.set_line_width(line_width)
        cr.set_source_rgba(0.2, 0.2, 0.25, 1.0)
        start_angle = 0.75 * math.pi
        end_angle = 2.25 * math.pi
        cr.arc(cx, cy, radius, start_angle, end_angle)
        cr.stroke()

        # Value arc
        if self._max_val > 0:
            frac = min(1.0, max(0, self._value / self._max_val))
        else:
            frac = 0
        val_angle = start_angle + frac * (end_angle - start_angle)
        r, g, b = self._color
        # Shift color towards red for high values
        if frac > 0.7:
            t = (frac - 0.7) / 0.3
            r = r + t * (1.0 - r)
            g = g * (1 - t * 0.7)
            b = b * (1 - t * 0.7)
        cr.set_source_rgba(r, g, b, 1.0)
        cr.set_line_width(line_width)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        if frac > 0.001:
            cr.arc(cx, cy, radius, start_angle, val_angle)
            cr.stroke()

        # Center text - value
        cr.set_source_rgba(1, 1, 1, 0.95)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(18)
        val_text = f"{self._value:.0f}{self._unit}"
        ext = cr.text_extents(val_text)
        cr.move_to(cx - ext.width / 2, cy + 2)
        cr.show_text(val_text)

        # Label text
        cr.set_font_size(10)
        cr.set_source_rgba(1, 1, 1, 0.6)
        ext2 = cr.text_extents(self._label)
        cr.move_to(cx - ext2.width / 2, cy + 18)
        cr.show_text(self._label)

    def set_value(self, value, label=None):
        self._value = value
        if label is not None:
            self._label = label
        self.queue_draw()


class MiniGraph(Gtk.DrawingArea):
    """A small sparkline graph widget for history data."""

    def __init__(self, color=(0.3, 0.7, 1.0), max_points=60, height=40):
        super().__init__()
        self._color = color
        self._data = []
        self._max_points = max_points
        self.set_content_width(200)
        self.set_content_height(height)
        self.set_draw_func(self._draw)

    def _draw(self, area, cr, width, height):
        # Background
        cr.set_source_rgba(0.12, 0.12, 0.15, 1.0)
        _rounded_rect(cr, 0, 0, width, height, 4)
        cr.fill()

        if len(self._data) < 2:
            return

        max_val = max(max(self._data), 1)
        n = len(self._data)
        step = width / max(n - 1, 1)
        pad = 4

        # Fill
        r, g, b = self._color
        cr.set_source_rgba(r, g, b, 0.15)
        cr.move_to(0, height)
        for i, val in enumerate(self._data):
            y = height - pad - (val / max_val) * (height - 2 * pad)
            cr.line_to(i * step, y)
        cr.line_to((n - 1) * step, height)
        cr.close_path()
        cr.fill()

        # Line
        cr.set_source_rgba(r, g, b, 0.9)
        cr.set_line_width(1.5)
        for i, val in enumerate(self._data):
            y = height - pad - (val / max_val) * (height - 2 * pad)
            if i == 0:
                cr.move_to(i * step, y)
            else:
                cr.line_to(i * step, y)
        cr.stroke()

    def add_point(self, value):
        self._data.append(value)
        if len(self._data) > self._max_points:
            self._data.pop(0)
        self.queue_draw()

    def clear(self):
        self._data.clear()
        self.queue_draw()


def _rounded_rect(cr, x, y, w, h, r):
    """Draw a rounded rectangle path."""
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -0.5 * math.pi, 0)
    cr.arc(x + w - r, y + h - r, r, 0, 0.5 * math.pi)
    cr.arc(x + r, y + h - r, r, 0.5 * math.pi, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    cr.close_path()


def create_info_row(label_text, value_text=""):
    """Create a label-value row."""
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    box.set_margin_start(4)
    box.set_margin_end(4)
    box.set_margin_top(2)
    box.set_margin_bottom(2)

    label = Gtk.Label(label=label_text)
    label.set_halign(Gtk.Align.START)
    label.add_css_class("dim-label")
    label.set_hexpand(True)
    label.set_xalign(0)

    value = Gtk.Label(label=value_text)
    value.set_halign(Gtk.Align.END)
    value.add_css_class("caption")

    box.append(label)
    box.append(value)
    return box, value


def create_section_label(text):
    """Create a section header label."""
    label = Gtk.Label(label=text)
    label.set_halign(Gtk.Align.START)
    label.set_margin_top(12)
    label.set_margin_bottom(4)
    label.set_margin_start(4)
    label.add_css_class("heading")
    return label
