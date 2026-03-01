# PulseDeck

**Lightweight System Monitor & Assistant for Linux**

PulseDeck is a native GTK4/libadwaita system monitoring application designed for Pop!_OS and other GNOME-based Linux distributions. It provides real-time monitoring of your system resources with a clean, modern interface — all without touching the terminal.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![GTK](https://img.shields.io/badge/GTK-4.0-orange.svg)

## Features

- **Dashboard** — System overview with CPU, RAM, and Disk gauges, live sparkline graphs, temperature readouts, and battery status
- **CPU Monitor** — Per-core usage bars, frequency tracking, load averages, usage history graph, and top CPU-consuming processes
- **Memory Monitor** — RAM & Swap gauges, detailed breakdown (cached, buffers), usage history, and top memory-consuming processes
- **Storage Monitor** — All mounted partitions with usage, real-time disk I/O speed (read/write), and total I/O stats
- **Thermal & Fans** — Live temperature graphs per sensor, fan RPM readings, fan speed control sliders (PWM), and battery info
- **App Manager** — Browse installed apps (Flatpak + system), search & install new packages, uninstall apps, and launch apps — all with a graphical interface, no terminal needed

## Requirements

- Python 3.8+
- GTK 4.0 / libadwaita 1.0
- psutil

These are pre-installed on Pop!_OS 22.04+. On other distros:

```bash
# Ubuntu/Debian
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 python3-psutil

# Fedora
sudo dnf install python3-gobject gtk4 libadwaita python3-psutil

# Arch
sudo pacman -S python-gobject gtk4 libadwaita python-psutil
```

## Installation & Running

```bash
# Clone the repository
git clone https://github.com/arif481/PulseDeck.git
cd PulseDeck

# Run directly
python3 main.py

# Or install the .desktop file for app launcher
cp data/com.pulsedeck.app.desktop ~/.local/share/applications/
```

## Project Structure

```
PulseDeck/
├── main.py                          # Entry point
├── pulsedeck/
│   ├── __init__.py
│   ├── app.py                       # Adw.Application
│   ├── monitors/
│   │   ├── cpu.py                   # CPU metrics
│   │   ├── memory.py                # RAM/Swap metrics
│   │   ├── storage.py               # Disk partitions & I/O
│   │   └── thermal.py               # Temperature, fans, battery
│   ├── managers/
│   │   └── apps.py                  # App install/uninstall/search
│   ├── ui/
│   │   ├── widgets.py               # Custom drawing widgets
│   │   ├── window.py                # Main window with sidebar
│   │   └── pages/
│   │       ├── dashboard.py         # Overview page
│   │       ├── cpu_page.py          # CPU detail page
│   │       ├── memory_page.py       # Memory detail page
│   │       ├── storage_page.py      # Storage detail page
│   │       ├── thermal_page.py      # Thermal & fans page
│   │       └── apps_page.py         # App manager page
│   └── utils/
│       └── helpers.py               # Formatting utilities
├── data/
│   ├── com.pulsedeck.app.desktop    # Desktop entry
│   └── icons/
└── README.md
```

## Design Principles

- **Lightweight** — Pure Python + GTK4 native widgets, no Electron or web frameworks
- **Non-intrusive** — Uses polling with sensible intervals (2-5s), minimal CPU/RAM footprint
- **Modern UI** — Follows GNOME HIG with libadwaita, dark theme by default
- **No terminal needed** — All operations (install, uninstall, launch) via GUI with polkit for privilege escalation

## License

MIT License — see [LICENSE](LICENSE) for details.
