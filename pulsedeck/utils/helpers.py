"""Utility helpers."""
import time


def format_bytes(b):
    """Format bytes to human-readable string."""
    if b is None:
        return "N/A"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def format_uptime():
    """Get system uptime as a formatted string."""
    try:
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.readline().split()[0])
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        mins = int((uptime_seconds % 3600) // 60)
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        parts.append(f"{mins}m")
        return " ".join(parts)
    except Exception:
        return "N/A"


def format_time_seconds(secs):
    """Format seconds to human-readable time string."""
    if secs < 0:
        return "Calculating..."
    hours = int(secs // 3600)
    mins = int((secs % 3600) // 60)
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def clamp(value, min_val, max_val):
    """Clamp a value within a range."""
    return max(min_val, min(max_val, value))


def get_hostname():
    """Get system hostname."""
    try:
        with open("/etc/hostname", "r") as f:
            return f.read().strip()
    except Exception:
        return "unknown"


def get_kernel_version():
    """Get kernel version."""
    try:
        with open("/proc/version", "r") as f:
            parts = f.read().split()
            if len(parts) >= 3:
                return parts[2]
    except Exception:
        pass
    return "unknown"


def get_os_name():
    """Get OS pretty name."""
    try:
        with open("/etc/os-release", "r") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return "Linux"
