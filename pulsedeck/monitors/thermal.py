"""Temperature and Fan monitoring module."""
import os
import glob
import psutil


def get_temperatures():
    """Get temperature readings from all available sensors."""
    temps = []

    # Try psutil first
    try:
        sensor_temps = psutil.sensors_temperatures()
        if sensor_temps:
            for name, entries in sensor_temps.items():
                for entry in entries:
                    temps.append({
                        "sensor": name,
                        "label": entry.label or name,
                        "current": entry.current,
                        "high": entry.high or 0,
                        "critical": entry.critical or 0,
                    })
            return temps
    except (AttributeError, Exception):
        pass

    # Fallback: read from /sys/class/thermal
    try:
        thermal_zones = glob.glob("/sys/class/thermal/thermal_zone*/")
        for zone in sorted(thermal_zones):
            try:
                temp_file = os.path.join(zone, "temp")
                type_file = os.path.join(zone, "type")
                if os.path.exists(temp_file):
                    with open(temp_file, "r") as f:
                        temp_mc = int(f.read().strip())
                    label = "Unknown"
                    if os.path.exists(type_file):
                        with open(type_file, "r") as f:
                            label = f.read().strip()
                    temps.append({
                        "sensor": "thermal_zone",
                        "label": label,
                        "current": temp_mc / 1000.0,
                        "high": 85.0,
                        "critical": 100.0,
                    })
            except (IOError, ValueError):
                pass
    except Exception:
        pass

    return temps


def get_fans():
    """Get fan speed readings from all available sensors."""
    fans = []

    # Try psutil first
    try:
        sensor_fans = psutil.sensors_fans()
        if sensor_fans:
            for name, entries in sensor_fans.items():
                for entry in entries:
                    fans.append({
                        "sensor": name,
                        "label": entry.label or name,
                        "current_rpm": entry.current,
                    })
            return fans
    except (AttributeError, Exception):
        pass

    # Fallback: read from /sys/class/hwmon
    try:
        hwmon_dirs = glob.glob("/sys/class/hwmon/hwmon*/")
        for hwmon in sorted(hwmon_dirs):
            fan_inputs = glob.glob(os.path.join(hwmon, "fan*_input"))
            for fan_file in sorted(fan_inputs):
                try:
                    with open(fan_file, "r") as f:
                        rpm = int(f.read().strip())
                    # Get label
                    label_file = fan_file.replace("_input", "_label")
                    label = "Fan"
                    if os.path.exists(label_file):
                        with open(label_file, "r") as f:
                            label = f.read().strip()
                    # Get name
                    name_file = os.path.join(hwmon, "name")
                    sensor_name = "hwmon"
                    if os.path.exists(name_file):
                        with open(name_file, "r") as f:
                            sensor_name = f.read().strip()
                    fans.append({
                        "sensor": sensor_name,
                        "label": label,
                        "current_rpm": rpm,
                    })
                except (IOError, ValueError):
                    pass
    except Exception:
        pass

    return fans


def get_fan_control_paths():
    """Find controllable fan PWM paths."""
    controls = []
    try:
        hwmon_dirs = glob.glob("/sys/class/hwmon/hwmon*/")
        for hwmon in sorted(hwmon_dirs):
            pwm_files = glob.glob(os.path.join(hwmon, "pwm[0-9]"))
            for pwm_file in sorted(pwm_files):
                enable_file = pwm_file + "_enable"
                if os.path.exists(enable_file):
                    try:
                        with open(enable_file, "r") as f:
                            mode = int(f.read().strip())
                        with open(pwm_file, "r") as f:
                            value = int(f.read().strip())
                        name_file = os.path.join(hwmon, "name")
                        sensor_name = "hwmon"
                        if os.path.exists(name_file):
                            with open(name_file, "r") as f:
                                sensor_name = f.read().strip()
                        controls.append({
                            "path": pwm_file,
                            "enable_path": enable_file,
                            "sensor": sensor_name,
                            "mode": mode,  # 0=full, 1=manual, 2=auto
                            "value": value,  # 0-255
                        })
                    except (IOError, ValueError):
                        pass
    except Exception:
        pass
    return controls


def set_fan_speed(pwm_path, value):
    """Set fan speed via PWM (requires root). value: 0-255."""
    enable_path = pwm_path + "_enable"
    try:
        # Set to manual mode first
        with open(enable_path, "w") as f:
            f.write("1")
        # Set speed
        with open(pwm_path, "w") as f:
            f.write(str(max(0, min(255, int(value)))))
        return True
    except (IOError, PermissionError) as e:
        return False


def set_fan_auto(pwm_path):
    """Set fan back to automatic control."""
    enable_path = pwm_path + "_enable"
    try:
        with open(enable_path, "w") as f:
            f.write("2")
        return True
    except (IOError, PermissionError):
        return False


def get_battery_info():
    """Get battery information if available."""
    try:
        battery = psutil.sensors_battery()
        if battery:
            secs = -1
            if isinstance(battery.secsleft, (int, float)) and battery.secsleft >= 0:
                secs = battery.secsleft
            return {
                "percent": battery.percent,
                "plugged": battery.power_plugged,
                "secs_left": secs,
            }
    except Exception:
        pass
    return None
