"""Storage monitoring module."""
import psutil
import os


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
