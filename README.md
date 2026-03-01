<div align="center">

# PulseDeck

**Lightweight System Monitor & Assistant for Linux**

A native GTK4/libadwaita system monitoring application for Pop!_OS and other GNOME-based Linux distributions. Real-time resource monitoring with a modern, polished interface — no terminal needed.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-green.svg)](https://python.org)
[![GTK 4](https://img.shields.io/badge/GTK-4.0-orange.svg)](https://gtk.org)
[![libadwaita](https://img.shields.io/badge/libadwaita-1.1+-purple.svg)](https://gnome.pages.gitlab.gnome.org/libadwaita/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

</div>

---

## Features

| Page | Highlights |
|------|-----------|
| **Dashboard** | CPU, RAM, Disk circular gauges · sparkline graphs · temperatures · battery status · uptime |
| **CPU** | Per-core usage bars · frequency tracking · load averages · history graph · top processes · governor control *(root)* · process kill *(root)* |
| **Memory** | RAM & Swap gauges · cached / buffers breakdown · usage history · top consumers · process kill *(root)* |
| **Storage** | Partition usage · real-time disk I/O · SMART health status *(root + smartmontools)* |
| **Network** | Bandwidth graphs · interface listing · connection summary *(root)* · error & drop tracking |
| **Thermal** | Per-sensor temperature graphs · fan RPM · battery info |
| **Apps** | Browse installed apps (apt, Flatpak, Snap) · search & install · uninstall · launch |

> Features marked *(root)* require running with `sudo`. See [SECURITY.md](SECURITY.md) for details.

## Screenshots

<!-- Add screenshots here: ![Dashboard](docs/screenshots/dashboard.png) -->

*Screenshots coming soon — contributions welcome!*

## Requirements

| Dependency | Minimum Version | Notes |
|-----------|:--------------:|-------|
| Python | 3.8+ | |
| GTK | 4.0 | |
| libadwaita | 1.1+ | 1.4+ API is **not** required |
| psutil | 5.9+ | |
| smartmontools | — | *Optional*, for SMART disk health |

### Install System Dependencies

<details>
<summary><strong>Ubuntu / Pop!_OS / Debian</strong></summary>

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 python3-psutil
# Optional: SMART disk health
sudo apt install smartmontools
```

</details>

<details>
<summary><strong>Fedora</strong></summary>

```bash
sudo dnf install python3-gobject gtk4 libadwaita python3-psutil
sudo dnf install smartmontools   # optional
```

</details>

<details>
<summary><strong>Arch Linux</strong></summary>

```bash
sudo pacman -S python-gobject gtk4 libadwaita python-psutil
sudo pacman -S smartmontools   # optional
```

</details>

## Quick Start

```bash
# Clone
git clone https://github.com/arif481/PulseDeck.git
cd PulseDeck

# Run (standard user)
python3 main.py

# Run with root privileges (unlocks governor, SMART, kill, full network)
sudo python3 main.py
```

### Desktop Integration

```bash
make install-desktop   # adds .desktop entry to your app launcher
```

Or manually:

```bash
cp data/com.pulsedeck.app.desktop ~/.local/share/applications/
```

## Project Structure

```
PulseDeck/
├── main.py                          # Entry point
├── pyproject.toml                   # Package metadata & build config
├── Makefile                         # Common tasks (run, install, lint, clean)
├── pulsedeck/
│   ├── __init__.py                  # Package root & version
│   ├── __main__.py                  # python -m pulsedeck support
│   ├── app.py                       # Adw.Application subclass
│   ├── monitors/
│   │   ├── cpu.py                   # CPU metrics, governor, process mgmt
│   │   ├── memory.py                # RAM & Swap monitoring
│   │   ├── storage.py               # Disk partitions, I/O, SMART health
│   │   ├── thermal.py               # Temperature sensors, fans, battery
│   │   └── network.py               # Interfaces, bandwidth, connections
│   ├── managers/
│   │   └── apps.py                  # Package management (apt/flatpak/snap)
│   ├── ui/
│   │   ├── widgets.py               # Cairo-drawn gauges, graphs, bars
│   │   ├── window.py                # Main window, sidebar nav, CSS theme
│   │   └── pages/                   # One module per monitoring page
│   │       ├── dashboard.py
│   │       ├── cpu_page.py
│   │       ├── memory_page.py
│   │       ├── storage_page.py
│   │       ├── network_page.py
│   │       ├── thermal_page.py
│   │       └── apps_page.py
│   └── utils/
│       └── helpers.py               # Formatting & utility functions
├── data/
│   ├── com.pulsedeck.app.desktop    # Freedesktop .desktop entry
│   └── icons/                       # Application icons
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── SECURITY.md
└── LICENSE
```

## Usage

```bash
make run          # Launch PulseDeck
make run-root     # Launch with root access
make lint         # Syntax-check all Python files
make clean        # Remove __pycache__ and build artifacts
make help         # Show all available targets
```

Or run directly:

```bash
python3 main.py                 # standard mode
sudo python3 main.py            # root mode
python3 -m pulsedeck            # module mode
```

## Design Principles

- **Lightweight** — Pure Python + GTK4 native widgets; no Electron, no web stack
- **Broad Compatibility** — Targets libadwaita 1.1+ (ships with Ubuntu 22.04+)
- **Non-intrusive** — Polling at sensible intervals (2–5 s), minimal CPU/RAM footprint
- **Graceful Degradation** — Sensors that fail show clear error banners, not silent zeros
- **Modern UI** — GNOME HIG, dark theme, Cairo-drawn widgets with gradients and glow effects
- **No Terminal Needed** — GUI for everything (install, uninstall, launch, kill, governor)

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT](LICENSE) — see the [LICENSE](LICENSE) file for details.
