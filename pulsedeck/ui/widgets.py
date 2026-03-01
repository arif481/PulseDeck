"""Custom reusable widgets for PulseDeck UI."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Gdk, GLib
import cairo
import math


class UsageBar(Gtk.DrawingArea):
    """A horizontal usage bar with gradient fill and rounded design."""

    def __init__(self, label="", percent=0, color_start=(0.2, 0.6, 1.0),
                 color_end=(1.0, 0.3, 0.3)):
        super().__init__()
        self._label = label
        self._percent = percent
        self._color_start = color_start
        self._color_end = color_end
        self.set_content_width(200)
        self.set_content_height(28)
        self.set_draw_func(self._draw)

    def _draw(self, area, cr, width, height):
        radius = height / 2

        # Background track
        cr.set_source_rgba(1, 1, 1, 0.06)
        _rounded_rect(cr, 0, 0, width, height, radius)
        cr.fill()

        # Fill bar with gradient
        pct = max(0, min(100, self._percent))
        bar_width = max(height, (pct / 100.0) * width)  # min width = height for rounded cap
        if pct > 0:
            t = pct / 100.0
            r = self._color_start[0] + t * (self._color_end[0] - self._color_start[0])
            g = self._color_start[1] + t * (self._color_end[1] - self._color_start[1])
            b = self._color_start[2] + t * (self._color_end[2] - self._color_start[2])

            # Gradient along bar
            grad = cairo.LinearGradient(0, 0, bar_width, 0)
            grad.add_color_stop_rgba(0, self._color_start[0], self._color_start[1], self._color_start[2], 0.9)
            grad.add_color_stop_rgba(1, r, g, b, 0.9)
            cr.set_source(grad)
            _rounded_rect(cr, 0, 0, bar_width, height, radius)
            cr.fill()

            # Glossy highlight on top half
            cr.set_source_rgba(1, 1, 1, 0.08)
            _rounded_rect(cr, 1, 1, bar_width - 2, height / 2 - 1, radius)
            cr.fill()

        # Label text (left)
        cr.set_source_rgba(1, 1, 1, 0.95)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(11)
        extents = cr.text_extents(self._label)
        cr.move_to(10, height / 2 + extents.height / 2)
        cr.show_text(self._label)

        # Percentage text (right)
        pct_text = f"{pct:.0f}%"
        ext2 = cr.text_extents(pct_text)
        cr.move_to(width - ext2.width - 10, height / 2 + ext2.height / 2)
        cr.show_text(pct_text)

    def set_value(self, label, percent):
        self._label = label
        self._percent = percent
        self.queue_draw()


class CircularGauge(Gtk.DrawingArea):
    """A modern circular gauge widget with glow effect."""

    def __init__(self, label="", value=0, max_val=100, unit="%",
                 color=(0.2, 0.6, 1.0), size=120):
        super().__init__()
        self._label = label
        self._value = value
        self._max_val = max_val
        self._unit = unit
        self._color = color
        self._unavailable = False
        self.set_content_width(size)
        self.set_content_height(size)
        self.set_draw_func(self._draw)

    def _draw(self, area, cr, width, height):
        cx = width / 2
        cy = height / 2
        radius = min(width, height) / 2 - 12
        line_width = 7

        start_angle = 0.75 * math.pi
        end_angle = 2.25 * math.pi

        if self._unavailable:
            # ── Unavailable state ──
            cr.set_line_width(line_width)
            cr.set_source_rgba(0.97, 0.32, 0.29, 0.1)
            cr.arc(cx, cy, radius, start_angle, end_angle)
            cr.stroke()

            cr.set_dash([3, 3])
            cr.set_line_width(1)
            cr.set_source_rgba(0.97, 0.32, 0.29, 0.2)
            cr.arc(cx, cy, radius, start_angle, end_angle)
            cr.stroke()
            cr.set_dash([])

            cr.set_source_rgba(1, 1, 1, 0.3)
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(22 if width >= 130 else 18)
            val_text = "--"
            ext = cr.text_extents(val_text)
            cr.move_to(cx - ext.width / 2, cy + 2)
            cr.show_text(val_text)

            cr.set_font_size(8)
            cr.set_source_rgba(0.97, 0.32, 0.29, 0.55)
            unavail_text = "UNAVAILABLE"
            ext2 = cr.text_extents(unavail_text)
            cr.move_to(cx - ext2.width / 2, cy + 16)
            cr.show_text(unavail_text)

            cr.set_font_size(10)
            cr.set_source_rgba(1, 1, 1, 0.25)
            ext3 = cr.text_extents(self._label)
            cr.move_to(cx - ext3.width / 2, cy + 28)
            cr.show_text(self._label)
            return

        # Background arc (subtle)
        cr.set_line_width(line_width)
        cr.set_source_rgba(1, 1, 1, 0.06)
        cr.arc(cx, cy, radius, start_angle, end_angle)
        cr.stroke()

        # Tick marks
        cr.set_line_width(1)
        cr.set_source_rgba(1, 1, 1, 0.08)
        for i in range(21):
            angle = start_angle + (i / 20.0) * (end_angle - start_angle)
            tick_len = 4 if i % 5 == 0 else 2
            inner_r = radius - line_width / 2 - 2
            outer_r = inner_r - tick_len
            cr.move_to(cx + inner_r * math.cos(angle), cy + inner_r * math.sin(angle))
            cr.line_to(cx + outer_r * math.cos(angle), cy + outer_r * math.sin(angle))
            cr.stroke()

        # Value arc
        if self._max_val > 0:
            frac = min(1.0, max(0, self._value / self._max_val))
        else:
            frac = 0
        val_angle = start_angle + frac * (end_angle - start_angle)
        r, g, b = self._color

        # Shift color towards red/orange for high values
        if frac > 0.7:
            t = (frac - 0.7) / 0.3
            r = r + t * (1.0 - r)
            g = g * (1 - t * 0.7)
            b = b * (1 - t * 0.7)

        if frac > 0.001:
            # Glow effect (wider, transparent stroke underneath)
            cr.set_source_rgba(r, g, b, 0.15)
            cr.set_line_width(line_width + 8)
            cr.set_line_cap(cairo.LINE_CAP_ROUND)
            cr.arc(cx, cy, radius, start_angle, val_angle)
            cr.stroke()

            # Main arc
            cr.set_source_rgba(r, g, b, 1.0)
            cr.set_line_width(line_width)
            cr.set_line_cap(cairo.LINE_CAP_ROUND)
            cr.arc(cx, cy, radius, start_angle, val_angle)
            cr.stroke()

            # Bright dot at the end
            end_x = cx + radius * math.cos(val_angle)
            end_y = cy + radius * math.sin(val_angle)
            cr.set_source_rgba(r, g, b, 0.5)
            cr.arc(end_x, end_y, 5, 0, 2 * math.pi)
            cr.fill()
            cr.set_source_rgba(1, 1, 1, 0.9)
            cr.arc(end_x, end_y, 2, 0, 2 * math.pi)
            cr.fill()

        # Center value text
        cr.set_source_rgba(1, 1, 1, 0.95)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(22 if width >= 130 else 18)
        val_text = f"{self._value:.0f}"
        ext = cr.text_extents(val_text)
        cr.move_to(cx - ext.width / 2, cy + 2)
        cr.show_text(val_text)

        # Unit text (smaller, next to value)
        cr.set_font_size(11)
        cr.set_source_rgba(1, 1, 1, 0.5)
        cr.move_to(cx + ext.width / 2 + 2, cy + 2)
        cr.show_text(self._unit)

        # Label text below
        cr.set_font_size(10)
        cr.set_source_rgba(1, 1, 1, 0.45)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ext2 = cr.text_extents(self._label)
        cr.move_to(cx - ext2.width / 2, cy + 20)
        cr.show_text(self._label)

    def set_value(self, value, label=None):
        self._value = value
        if label is not None:
            self._label = label
        self._unavailable = False
        self.queue_draw()

    def set_unavailable(self, unavailable=True):
        """Mark gauge as unavailable (no data)."""
        self._unavailable = unavailable
        self.queue_draw()


class MiniGraph(Gtk.DrawingArea):
    """A sparkline graph with gradient fill and smooth curves."""

    def __init__(self, color=(0.3, 0.7, 1.0), max_points=60, height=40):
        super().__init__()
        self._color = color
        self._data = []
        self._max_points = max_points
        self._unavailable = False
        self.set_content_width(200)
        self.set_content_height(height)
        self.set_draw_func(self._draw)

    def _draw(self, area, cr, width, height):
        radius = 6

        # Background with rounded corners
        cr.set_source_rgba(1, 1, 1, 0.03)
        _rounded_rect(cr, 0, 0, width, height, radius)
        cr.fill()

        # Subtle grid lines
        cr.set_source_rgba(1, 1, 1, 0.04)
        cr.set_line_width(0.5)
        for i in range(1, 4):
            y = height * i / 4
            cr.move_to(0, y)
            cr.line_to(width, y)
            cr.stroke()

        if self._unavailable:
            cr.set_source_rgba(0.97, 0.32, 0.29, 0.06)
            _rounded_rect(cr, 0, 0, width, height, radius)
            cr.fill()
            cr.set_dash([4, 3])
            cr.set_line_width(1)
            cr.set_source_rgba(0.97, 0.32, 0.29, 0.2)
            _rounded_rect(cr, 0, 0, width, height, radius)
            cr.stroke()
            cr.set_dash([])
            cr.set_source_rgba(1, 1, 1, 0.25)
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(10)
            text = "NO DATA"
            ext = cr.text_extents(text)
            cr.move_to(width / 2 - ext.width / 2, height / 2 + ext.height / 2)
            cr.show_text(text)
            return

        if len(self._data) < 2:
            return

        max_val = max(max(self._data), 1)
        n = len(self._data)
        step = width / max(n - 1, 1)
        pad = 4

        r, g, b = self._color

        # Compute points
        points = []
        for i, val in enumerate(self._data):
            x = i * step
            y = height - pad - (val / max_val) * (height - 2 * pad)
            points.append((x, y))

        # Gradient fill
        grad = cairo.LinearGradient(0, 0, 0, height)
        grad.add_color_stop_rgba(0, r, g, b, 0.25)
        grad.add_color_stop_rgba(1, r, g, b, 0.02)
        cr.set_source(grad)

        cr.move_to(points[0][0], height)
        for px, py in points:
            cr.line_to(px, py)
        cr.line_to(points[-1][0], height)
        cr.close_path()
        cr.fill()

        # Line with slight glow
        # Glow
        cr.set_source_rgba(r, g, b, 0.3)
        cr.set_line_width(3)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        for i, (px, py) in enumerate(points):
            if i == 0:
                cr.move_to(px, py)
            else:
                cr.line_to(px, py)
        cr.stroke()

        # Crisp line on top
        cr.set_source_rgba(r, g, b, 0.9)
        cr.set_line_width(1.5)
        for i, (px, py) in enumerate(points):
            if i == 0:
                cr.move_to(px, py)
            else:
                cr.line_to(px, py)
        cr.stroke()

        # Current value dot
        if points:
            last_x, last_y = points[-1]
            cr.set_source_rgba(r, g, b, 0.4)
            cr.arc(last_x, last_y, 4, 0, 2 * math.pi)
            cr.fill()
            cr.set_source_rgba(1, 1, 1, 0.9)
            cr.arc(last_x, last_y, 1.5, 0, 2 * math.pi)
            cr.fill()

    def add_point(self, value):
        self._data.append(value)
        if len(self._data) > self._max_points:
            self._data.pop(0)
        self.queue_draw()

    def clear(self):
        self._data.clear()
        self.queue_draw()

    def set_unavailable(self, unavailable=True):
        """Mark graph as unavailable (no data)."""
        self._unavailable = unavailable
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


def create_error_banner(title="Monitoring Error", detail="", warning=False):
    """Create an error / warning banner widget (initially hidden)."""
    css_prefix = "warning-banner" if warning else "error-banner"
    banner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    banner.add_css_class(css_prefix)
    banner.set_visible(False)

    icon_name = "dialog-warning-symbolic" if warning else "dialog-error-symbolic"
    icon = Gtk.Image.new_from_icon_name(icon_name)
    icon.set_pixel_size(20)
    icon.add_css_class(f"{css_prefix}-icon")
    banner.append(icon)

    text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    text_box.set_hexpand(True)

    text_label = Gtk.Label(label=title)
    text_label.set_halign(Gtk.Align.START)
    text_label.add_css_class(f"{css_prefix}-text")
    text_box.append(text_label)

    detail_label = Gtk.Label(label=detail)
    detail_label.set_halign(Gtk.Align.START)
    detail_label.add_css_class(f"{css_prefix}-detail")
    detail_label.set_wrap(True)
    detail_label.set_visible(bool(detail))
    text_box.append(detail_label)

    banner.append(text_box)
    banner._text_label = text_label
    banner._detail_label = detail_label
    return banner


def show_error_banner(banner, title, detail=""):
    """Show an error/warning banner with updated text."""
    banner.set_visible(True)
    banner._text_label.set_label(title)
    banner._detail_label.set_label(detail)
    banner._detail_label.set_visible(bool(detail))


def hide_error_banner(banner):
    """Hide an error/warning banner."""
    banner.set_visible(False)
