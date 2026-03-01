# Contributing to PulseDeck

Thank you for your interest in contributing to PulseDeck! This guide will help you get started.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/PulseDeck.git
   cd PulseDeck
   ```
3. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Python 3.8+
- GTK 4.0 / libadwaita 1.0+
- psutil

### Install Dependencies

```bash
# Ubuntu / Pop!_OS / Debian
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 python3-psutil

# Fedora
sudo dnf install python3-gobject gtk4 libadwaita python3-psutil

# Arch
sudo pacman -S python-gobject gtk4 libadwaita python-psutil
```

### Running the App

```bash
python3 main.py

# With root access (enables governor control, SMART health, full network info)
sudo python3 main.py
```

## Project Structure

```
pulsedeck/
├── app.py                # Adw.Application subclass
├── monitors/             # System data collection (psutil, /sys, /proc)
│   ├── cpu.py            # CPU metrics, governor, process management
│   ├── memory.py         # RAM & swap monitoring
│   ├── storage.py        # Disk partitions, I/O, SMART health
│   ├── thermal.py        # Temperature sensors, fans, battery
│   └── network.py        # Network interfaces, bandwidth, connections
├── managers/
│   └── apps.py           # Package management (apt, flatpak, snap)
├── ui/
│   ├── widgets.py        # Custom Cairo-drawn widgets (gauges, graphs)
│   ├── window.py         # Main window, sidebar navigation, CSS theme
│   └── pages/            # Individual monitoring pages
└── utils/
    └── helpers.py        # Formatting utilities
```

## How to Contribute

### Reporting Bugs

- Use the [GitHub Issues](https://github.com/arif481/PulseDeck/issues) tracker
- Include your distro, libadwaita version (`apt show libadwaita-1-0`), and Python version
- Paste the full error traceback if applicable
- Describe steps to reproduce the issue

### Suggesting Features

- Open an issue with the **enhancement** label
- Describe the use case and expected behavior
- If possible, outline a proposed implementation

### Submitting Pull Requests

1. Ensure your code follows the existing style (PEP 8)
2. Add docstrings to new functions, classes, and modules
3. Test your changes on at least one GTK4/libadwaita system
4. Keep commits focused — one logical change per commit
5. Write a clear PR description explaining what and why

### Code Style

- **Python**: PEP 8, 4-space indentation
- **Docstrings**: Google-style (`"""Brief description."""`)
- **Imports**: stdlib → third-party → local, separated by blank lines
- **GTK/Adw**: Target libadwaita 1.1+ API (avoid 1.4+ features for broader compatibility)

## Adding a New Monitor Page

1. Create a data module in `pulsedeck/monitors/` (e.g., `gpu.py`)
2. Create a page in `pulsedeck/ui/pages/` (e.g., `gpu_page.py`)
3. Register the page in `pulsedeck/ui/window.py`:
   - Add it to `nav_items`
   - Import and instantiate the page
   - Add it to the page stack
4. Export from `pulsedeck/ui/pages/__init__.py`

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
