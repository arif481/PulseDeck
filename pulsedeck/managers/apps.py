"""Application manager - install, uninstall, list installed apps."""
import subprocess
import threading
import os


def _run_cmd(cmd, timeout=30):
    """Run a command and return (success, output)."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def get_apt_packages():
    """Get list of manually installed apt packages."""
    ok, output = _run_cmd(
        ["apt-mark", "showmanual"], timeout=15
    )
    if ok:
        packages = []
        for line in output.strip().split("\n"):
            name = line.strip()
            if name:
                packages.append({"name": name, "type": "apt"})
        return packages
    return []


def get_flatpak_apps():
    """Get list of installed Flatpak applications."""
    ok, output = _run_cmd(
        ["flatpak", "list", "--app", "--columns=name,application,version,size"],
        timeout=15
    )
    if ok:
        apps = []
        for line in output.strip().split("\n"):
            parts = line.split("\t")
            if len(parts) >= 2:
                apps.append({
                    "name": parts[0].strip(),
                    "app_id": parts[1].strip() if len(parts) > 1 else "",
                    "version": parts[2].strip() if len(parts) > 2 else "",
                    "size": parts[3].strip() if len(parts) > 3 else "",
                    "type": "flatpak",
                })
        return apps
    return []


def get_snap_apps():
    """Get list of installed Snap applications."""
    ok, output = _run_cmd(["snap", "list"], timeout=15)
    if ok:
        apps = []
        lines = output.strip().split("\n")
        for line in lines[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 2:
                apps.append({
                    "name": parts[0],
                    "version": parts[1] if len(parts) > 1 else "",
                    "type": "snap",
                })
        return apps
    return []


def get_all_installed_apps():
    """Get a combined list of user-facing installed apps (Flatpak + .desktop)."""
    apps = []

    # Get Flatpak apps (usually the most user-visible)
    flatpak_apps = get_flatpak_apps()
    apps.extend(flatpak_apps)

    # Get .desktop file apps (apt-installed GUI apps)
    desktop_apps = get_desktop_apps()
    apps.extend(desktop_apps)

    # Deduplicate by name
    seen = set()
    unique = []
    for app in apps:
        key = app["name"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(app)

    unique.sort(key=lambda x: x["name"].lower())
    return unique


def get_desktop_apps():
    """Get installed apps from .desktop files."""
    apps = []
    desktop_dirs = [
        "/usr/share/applications",
        os.path.expanduser("~/.local/share/applications"),
        "/var/lib/flatpak/exports/share/applications",
    ]
    seen = set()

    for d in desktop_dirs:
        if not os.path.isdir(d):
            continue
        try:
            for f in os.listdir(d):
                if not f.endswith(".desktop"):
                    continue
                filepath = os.path.join(d, f)
                try:
                    name = None
                    nodisplay = False
                    exec_cmd = None
                    icon = None
                    pkg_name = f.replace(".desktop", "")

                    with open(filepath, "r", errors="replace") as fp:
                        in_entry = False
                        for line in fp:
                            line = line.strip()
                            if line == "[Desktop Entry]":
                                in_entry = True
                                continue
                            if line.startswith("[") and line.endswith("]"):
                                in_entry = False
                                continue
                            if not in_entry:
                                continue
                            if line.startswith("Name=") and name is None:
                                name = line[5:]
                            elif line.startswith("NoDisplay=true"):
                                nodisplay = True
                            elif line.startswith("Exec="):
                                exec_cmd = line[5:]
                            elif line.startswith("Icon="):
                                icon = line[5:]

                    if name and not nodisplay and name.lower() not in seen:
                        seen.add(name.lower())
                        apps.append({
                            "name": name,
                            "exec": exec_cmd or "",
                            "icon": icon or "",
                            "desktop_file": filepath,
                            "pkg_name": pkg_name,
                            "type": "desktop",
                        })
                except Exception:
                    pass
        except Exception:
            pass

    return apps


def search_apt_packages(query):
    """Search for apt packages."""
    ok, output = _run_cmd(["apt-cache", "search", query], timeout=15)
    if ok:
        results = []
        for line in output.strip().split("\n")[:50]:  # Limit results
            parts = line.split(" - ", 1)
            if len(parts) == 2:
                results.append({
                    "name": parts[0].strip(),
                    "description": parts[1].strip(),
                    "type": "apt",
                })
        return results
    return []


def search_flatpak_apps(query):
    """Search for Flatpak apps."""
    ok, output = _run_cmd(
        ["flatpak", "search", query, "--columns=name,application,description"],
        timeout=15,
    )
    if ok:
        results = []
        for line in output.strip().split("\n")[:30]:
            parts = line.split("\t")
            if len(parts) >= 1:
                results.append({
                    "name": parts[0].strip(),
                    "app_id": parts[1].strip() if len(parts) > 1 else "",
                    "description": parts[2].strip() if len(parts) > 2 else "",
                    "type": "flatpak",
                })
        return results
    return []


def install_apt_package(name, callback=None):
    """Install an apt package (requires pkexec for root)."""
    def _do():
        ok, output = _run_cmd(
            ["pkexec", "apt-get", "install", "-y", name], timeout=300
        )
        if callback:
            callback(ok, output)
    t = threading.Thread(target=_do, daemon=True)
    t.start()
    return t


def uninstall_apt_package(name, callback=None):
    """Uninstall an apt package (requires pkexec for root)."""
    def _do():
        ok, output = _run_cmd(
            ["pkexec", "apt-get", "remove", "-y", name], timeout=300
        )
        if callback:
            callback(ok, output)
    t = threading.Thread(target=_do, daemon=True)
    t.start()
    return t


def install_flatpak_app(app_id, callback=None):
    """Install a Flatpak app."""
    def _do():
        ok, output = _run_cmd(
            ["flatpak", "install", "-y", "flathub", app_id], timeout=600
        )
        if callback:
            callback(ok, output)
    t = threading.Thread(target=_do, daemon=True)
    t.start()
    return t


def uninstall_flatpak_app(app_id, callback=None):
    """Uninstall a Flatpak app."""
    def _do():
        ok, output = _run_cmd(
            ["flatpak", "uninstall", "-y", app_id], timeout=120
        )
        if callback:
            callback(ok, output)
    t = threading.Thread(target=_do, daemon=True)
    t.start()
    return t
