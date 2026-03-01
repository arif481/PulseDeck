"""Storage monitoring module."""
import psutil
import os
import subprocess
import json


def get_disk_partitions():
    """Get all mounted disk partitions with usage info."""
    partitions = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            partitions.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent,
            })
        except (PermissionError, OSError):
            pass
    return partitions


def get_disk_io():
    """Get disk I/O statistics."""
    try:
        io = psutil.disk_io_counters()
        if io:
            return {
                "read_bytes": io.read_bytes,
                "write_bytes": io.write_bytes,
                "read_count": io.read_count,
                "write_count": io.write_count,
                "read_time": io.read_time,
                "write_time": io.write_time,
            }
    except Exception:
        pass
    return {
        "read_bytes": 0, "write_bytes": 0,
        "read_count": 0, "write_count": 0,
        "read_time": 0, "write_time": 0,
    }


def format_bytes(b):
    """Format bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def get_largest_dirs(path="/home", n=5):
    """Get largest directories (non-recursive, quick scan)."""
    dirs = []
    try:
        for entry in os.scandir(path):
            if entry.is_dir(follow_symlinks=False):
                try:
                    total = sum(
                        f.stat(follow_symlinks=False).st_size
                        for f in os.scandir(entry.path)
                        if f.is_file(follow_symlinks=False)
                    )
                    dirs.append({"name": entry.name, "path": entry.path, "size": total})
                except (PermissionError, OSError):
                    pass
    except (PermissionError, OSError):
        pass
    dirs.sort(key=lambda x: x["size"], reverse=True)
    return dirs[:n]


def get_smart_health(device="/dev/sda"):
    """Get SMART health info for a disk. Requires root for full access.
    Returns dict with health status, or None if unavailable."""
    try:
        result = subprocess.run(
            ["smartctl", "-j", "-a", device],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(result.stdout)
        health = {
            "device": device,
            "model": data.get("model_name", "Unknown"),
            "serial": data.get("serial_number", ""),
            "firmware": data.get("firmware_version", ""),
            "smart_status": "PASSED",
            "temperature": None,
            "power_on_hours": None,
            "power_cycle_count": None,
            "reallocated_sectors": None,
            "attributes": [],
        }

        # Health assessment
        smart_status = data.get("smart_status", {})
        if smart_status.get("passed") is False:
            health["smart_status"] = "FAILED"
        elif smart_status.get("passed") is True:
            health["smart_status"] = "PASSED"
        else:
            health["smart_status"] = "UNKNOWN"

        # Temperature
        temp_data = data.get("temperature", {})
        if "current" in temp_data:
            health["temperature"] = temp_data["current"]

        # Power on hours
        power_on = data.get("power_on_time", {})
        if "hours" in power_on:
            health["power_on_hours"] = power_on["hours"]

        # SMART attributes
        ata_attrs = data.get("ata_smart_attributes", {}).get("table", [])
        for attr in ata_attrs:
            entry = {
                "id": attr.get("id", 0),
                "name": attr.get("name", ""),
                "value": attr.get("value", 0),
                "worst": attr.get("worst", 0),
                "thresh": attr.get("thresh", 0),
                "raw_value": attr.get("raw", {}).get("value", 0),
                "status": "ok",
            }
            # Flag failing attributes
            if entry["value"] <= entry["thresh"] and entry["thresh"] > 0:
                entry["status"] = "failing"
            elif entry["value"] <= entry["thresh"] + 10 and entry["thresh"] > 0:
                entry["status"] = "warn"

            # Extract key metrics
            if attr.get("id") == 5:
                health["reallocated_sectors"] = entry["raw_value"]
            elif attr.get("id") == 9:
                if health["power_on_hours"] is None:
                    health["power_on_hours"] = entry["raw_value"]
            elif attr.get("id") == 12:
                health["power_cycle_count"] = entry["raw_value"]

            health["attributes"].append(entry)

        return health
    except FileNotFoundError:
        return None  # smartctl not installed
    except subprocess.TimeoutExpired:
        return None
    except (json.JSONDecodeError, KeyError, Exception):
        return None


def get_smart_capable_devices():
    """List block devices that might support SMART."""
    devices = []
    try:
        for part in psutil.disk_partitions(all=False):
            dev = part.device
            # Extract base device (e.g., /dev/sda from /dev/sda1)
            import re
            base = re.sub(r'p?\d+$', '', dev)
            if base not in devices and os.path.exists(base):
                devices.append(base)
    except Exception:
        pass
    if not devices:
        # Try common paths
        for d in ["/dev/sda", "/dev/nvme0n1", "/dev/vda"]:
            if os.path.exists(d):
                devices.append(d)
    return devices
