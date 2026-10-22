# PulseDeck

A system monitor for Pop!_OS and other GNOME-based Linux desktops, written in Python with GTK4 and libadwaita. It puts CPU, memory, disk, network and temperature readings in one native window, along with a few controls that usually need a terminal: switching the CPU governor, killing a process, setting fan speed, and installing or removing apps.

## Pages

| Page | What it shows |
|------|---------------|
| Dashboard | CPU, RAM and disk gauges, sparklines, temperatures, battery, uptime |
| CPU | Per-core usage, frequency, load averages, history, top processes; governor switching and process kill (root) |
| Memory | RAM and swap, cached and buffers, history, top consumers; process kill (root) |
| Storage | Partition usage, live disk I/O; SMART health (root and smartmontools) |
| Network | Bandwidth graphs, interface list, errors and drops; connection summary (root) |
| Thermal | Temperature per sensor, fan RPM, battery; PWM fan speed (root, on hardware that exposes it) |
| Apps | Installed apt, Flatpak and Snap apps; search, install, uninstall, launch |

Pages refresh every 2 to 5 seconds. A sensor that can't be read shows an error banner rather than a zero. [SECURITY.md](SECURITY.md) explains what the root features do.

## Requirements

Python 3.8 or newer, GTK 4, libadwaita 1.1 or newer (the version in Ubuntu 22.04) and psutil 5.9 or newer. smartmontools is optional.

```bash
# Ubuntu, Pop!_OS, Debian
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 python3-psutil smartmontools

# Fedora
sudo dnf install python3-gobject gtk4 libadwaita python3-psutil smartmontools

# Arch
sudo pacman -S python-gobject gtk4 libadwaita python-psutil smartmontools
```

## Running it

```bash
git clone https://github.com/arif481/PulseDeck.git
cd PulseDeck
python3 main.py          # or: make run
sudo python3 main.py     # with root features; or: make run-root
make install-desktop     # add it to the app launcher
```

`make help` lists the other targets (`lint`, `clean`, `uninstall-desktop`).

## Code layout

`pulsedeck/monitors/` reads the numbers from psutil, `/proc` and `/sys`. `pulsedeck/managers/apps.py` wraps apt, flatpak and snap. `pulsedeck/ui/` has one module per page under `pages/`, and `widgets.py` draws the gauges and graphs with Cairo.

## License

[MIT](LICENSE)
