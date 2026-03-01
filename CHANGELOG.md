# Changelog

All notable changes to PulseDeck will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-03-01

### Added

- **Network Monitor** — Real-time bandwidth graphs, interface listing, connection summary, and error/drop tracking
- **CPU Governor Control** — View and switch CPU frequency governors (requires root)
- **Process Management** — Kill processes directly from CPU and Memory pages (requires root)
- **SMART Disk Health** — View SMART status, temperature, power-on hours, and reallocated sectors for storage devices (requires root + smartmontools)
- **Error State Indicators** — Visual error banners and "UNAVAILABLE" widget states when sensors fail, replacing silent failures
- **Root Access Indicator** — Sidebar shows whether the app is running with root privileges
- Modern UI with Cairo-drawn circular gauges, sparkline graphs, gradient usage bars, and glow effects
- Color-coded badges (OK / Warning / Critical) for temperatures, disk health, and network errors
- Per-section error handling across all pages with descriptive error messages

### Changed

- Ported from libadwaita 1.4+ API to 1.1+ API for broader distro compatibility (NavigationSplitView → Leaflet, NavigationPage → Box, AboutWindow → AboutDialog)
- Complete visual overhaul with custom CSS theme (30+ styled classes)
- Rewrote all six monitoring pages with card-based layouts and stat pills

### Fixed

- App silently exiting on systems with libadwaita < 1.4
- Applications page crash due to `set_placeholder_text()` not available in GTK 4.6
- Ampersand in "Thermal & Fans" causing markup parse errors
- Blanket `except Exception: pass` patterns replaced with granular error handling

## [1.0.0] - 2026-02-28

### Added

- Initial release
- Dashboard with CPU, RAM, Disk gauges and system info
- CPU Monitor with per-core usage, frequency, load averages, and top processes
- Memory Monitor with RAM/Swap breakdown and top memory consumers
- Storage Monitor with partition usage and disk I/O speeds
- Thermal Monitor with temperature sensors, fan speeds, and battery info
- App Manager with browse, search, install, and uninstall (apt, flatpak, snap)
- Dark theme with libadwaita integration
