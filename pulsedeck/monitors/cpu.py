"""CPU monitoring module."""
import psutil
import os


def get_cpu_info():
    """Get comprehensive CPU information."""
    freq = psutil.cpu_freq()
    load_avg = os.getloadavg()

    return {
        "usage_percent": psutil.cpu_percent(interval=0),
        "per_core_percent": psutil.cpu_percent(interval=0, percpu=True),
        "core_count_physical": psutil.cpu_count(logical=False) or 0,
        "core_count_logical": psutil.cpu_count(logical=True) or 0,
        "freq_current": freq.current if freq else 0,
        "freq_min": freq.min if freq else 0,
        "freq_max": freq.max if freq else 0,
        "load_1": load_avg[0],
        "load_5": load_avg[1],
        "load_15": load_avg[2],
    }


def get_cpu_name():
    """Get CPU model name."""
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "model name" in line:
                    return line.split(":")[1].strip()
    except Exception:
        pass
    return "Unknown CPU"


def get_top_processes(n=10):
    """Get top N CPU-consuming processes."""
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = p.info
            procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    procs.sort(key=lambda x: x.get("cpu_percent", 0) or 0, reverse=True)
    return procs[:n]
