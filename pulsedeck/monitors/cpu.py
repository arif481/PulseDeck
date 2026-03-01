"""CPU monitoring module."""
import psutil
import os
import glob
import signal


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


def kill_process(pid, sig=signal.SIGTERM):
    """Kill a process by PID. Returns (success, message)."""
    try:
        p = psutil.Process(pid)
        name = p.name()
        p.send_signal(sig)
        return True, f"Sent signal to {name} (PID {pid})"
    except psutil.NoSuchProcess:
        return False, f"Process {pid} not found"
    except psutil.AccessDenied:
        return False, f"Access denied for PID {pid} (need root)"
    except Exception as e:
        return False, str(e)


def renice_process(pid, nice_value):
    """Change process priority. Returns (success, message). Negative nice needs root."""
    try:
        p = psutil.Process(pid)
        name = p.name()
        p.nice(nice_value)
        return True, f"Set {name} (PID {pid}) nice to {nice_value}"
    except psutil.NoSuchProcess:
        return False, f"Process {pid} not found"
    except psutil.AccessDenied:
        return False, f"Access denied for PID {pid} (need root for nice < 0)"
    except Exception as e:
        return False, str(e)


def get_available_governors():
    """Get available CPU frequency governors."""
    try:
        path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors"
        if os.path.exists(path):
            with open(path, "r") as f:
                return f.read().strip().split()
    except Exception:
        pass
    return []


def get_current_governor():
    """Get the current CPU frequency governor."""
    try:
        path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
        if os.path.exists(path):
            with open(path, "r") as f:
                return f.read().strip()
    except Exception:
        pass
    return ""


def set_governor(governor):
    """Set CPU frequency governor for all cores. Requires root. Returns (success, message)."""
    try:
        cpufreq_paths = glob.glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor")
        if not cpufreq_paths:
            return False, "No cpufreq governor paths found"
        for path in cpufreq_paths:
            with open(path, "w") as f:
                f.write(governor)
        return True, f"Governor set to '{governor}' on {len(cpufreq_paths)} cores"
    except PermissionError:
        return False, f"Permission denied (need root to change governor)"
    except Exception as e:
        return False, str(e)


def get_energy_performance_preference():
    """Get current energy performance preference (Intel/AMD)."""
    try:
        path = "/sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference"
        if os.path.exists(path):
            with open(path, "r") as f:
                return f.read().strip()
    except Exception:
        pass
    return ""


def get_available_epp():
    """Get available energy performance preferences."""
    try:
        path = "/sys/devices/system/cpu/cpu0/cpufreq/energy_performance_available_preferences"
        if os.path.exists(path):
            with open(path, "r") as f:
                return f.read().strip().split()
    except Exception:
        pass
    return []
