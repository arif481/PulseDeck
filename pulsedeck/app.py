"""PulseDeck GTK Application."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio

from pulsedeck.ui.window import PulseDeckWindow


class PulseDeckApp(Adw.Application):
    """Main Adw.Application for PulseDeck."""

    def __init__(self):
        super().__init__(
            application_id="com.pulsedeck.app",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self._window = None

    def do_activate(self):
        if self._window is None:
            self._window = PulseDeckWindow(self)
        self._window.present()

    def do_startup(self):
        Adw.Application.do_startup(self)
        # Force dark color scheme for a sleek monitoring look
        style_manager = Adw.StyleManager.get_default()
        style_manager.set_color_scheme(Adw.ColorScheme.PREFER_DARK)
