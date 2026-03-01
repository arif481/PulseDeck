"""Memory monitoring module."""
import psutil


def get_memory_info():
    """Get RAM usage information."""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        "total": mem.total,
        "available": mem.available,
        "used": mem.used,
        "percent": mem.percent,
        "cached": getattr(mem, "cached", 0),
        "buffers": getattr(mem, "buffers", 0),
        "swap_total": swap.total,
        "swap_used": swap.used,
        "swap_free": swap.free,
        "swap_percent": swap.percent,
    }


def format_bytes(b):
    """Format bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def get_top_memory_processes(n=10):
    """Get top N memory-consuming processes."""
    procs = []
    for p in psutil.process_iter(["pid", "name", "memory_percent", "memory_info"]):
        try:
            info = p.info
            procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    procs.sort(key=lambda x: x.get("memory_percent", 0) or 0, reverse=True)
    return procs[:n]
