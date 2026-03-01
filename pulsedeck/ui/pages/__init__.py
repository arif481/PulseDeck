"""PulseDeck UI pages package."""

from pulsedeck.ui.pages.dashboard import DashboardPage
from pulsedeck.ui.pages.cpu_page import CPUPage
from pulsedeck.ui.pages.memory_page import MemoryPage
from pulsedeck.ui.pages.storage_page import StoragePage
from pulsedeck.ui.pages.network_page import NetworkPage
from pulsedeck.ui.pages.thermal_page import ThermalPage
from pulsedeck.ui.pages.apps_page import AppsPage

__all__ = [
    "DashboardPage",
    "CPUPage",
    "MemoryPage",
    "StoragePage",
    "NetworkPage",
    "ThermalPage",
    "AppsPage",
]
