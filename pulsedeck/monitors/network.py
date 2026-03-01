"""Network monitoring module."""
import os
import glob
import psutil


def get_network_interfaces():
    """Get all network interfaces with their addresses and status."""
    interfaces = []
    try:
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        for name, addr_list in addrs.items():
            if name == "lo":
                continue
            info = {
                "name": name,
                "is_up": False,
                "speed": 0,
                "mtu": 0,
                "ipv4": "",
                "ipv6": "",
                "mac": "",
            }
            if name in stats:
                s = stats[name]
                info["is_up"] = s.isup
                info["speed"] = s.speed
                info["mtu"] = s.mtu

            for addr in addr_list:
                if addr.family.name == "AF_INET":
                    info["ipv4"] = addr.address
                elif addr.family.name == "AF_INET6":
                    if not addr.address.startswith("fe80"):
                        info["ipv6"] = addr.address
                elif addr.family.name == "AF_PACKET":
                    info["mac"] = addr.address

            interfaces.append(info)
    except Exception:
        pass
    return interfaces


def get_network_io():
    """Get network I/O counters (total and per-interface)."""
    result = {
        "total": {"bytes_sent": 0, "bytes_recv": 0, "packets_sent": 0,
                  "packets_recv": 0, "errin": 0, "errout": 0, "dropin": 0, "dropout": 0},
        "per_iface": {},
    }
    try:
        total = psutil.net_io_counters()
        if total:
            result["total"] = {
                "bytes_sent": total.bytes_sent,
                "bytes_recv": total.bytes_recv,
                "packets_sent": total.packets_sent,
                "packets_recv": total.packets_recv,
                "errin": total.errin,
                "errout": total.errout,
                "dropin": total.dropin,
                "dropout": total.dropout,
            }
        per_nic = psutil.net_io_counters(pernic=True)
        if per_nic:
            for name, counters in per_nic.items():
                if name == "lo":
                    continue
                result["per_iface"][name] = {
                    "bytes_sent": counters.bytes_sent,
                    "bytes_recv": counters.bytes_recv,
                    "packets_sent": counters.packets_sent,
                    "packets_recv": counters.packets_recv,
                    "errin": counters.errin,
                    "errout": counters.errout,
                }
    except Exception:
        pass
    return result


def get_connections(kind="inet"):
    """Get active network connections. Requires root for full info."""
    connections = []
    try:
        for conn in psutil.net_connections(kind=kind):
            entry = {
                "fd": conn.fd,
                "family": conn.family.name if hasattr(conn.family, "name") else str(conn.family),
                "type": conn.type.name if hasattr(conn.type, "name") else str(conn.type),
                "laddr": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "",
                "raddr": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "",
                "status": conn.status,
                "pid": conn.pid,
            }
            connections.append(entry)
    except (psutil.AccessDenied, PermissionError):
        # Without root, we get limited info
        pass
    except Exception:
        pass
    return connections


def get_connection_summary():
    """Get a summary of network connections by status."""
    summary = {"ESTABLISHED": 0, "LISTEN": 0, "TIME_WAIT": 0,
               "CLOSE_WAIT": 0, "OTHER": 0, "total": 0}
    try:
        conns = psutil.net_connections(kind="inet")
        for c in conns:
            summary["total"] += 1
            if c.status in summary:
                summary[c.status] += 1
            else:
                summary["OTHER"] += 1
    except (psutil.AccessDenied, PermissionError):
        return None  # Signals that root is needed
    except Exception:
        pass
    return summary


def get_wifi_info():
    """Get WiFi info (SSID, signal) if available."""
    try:
        import subprocess
        result = subprocess.run(
            ["iwconfig"], capture_output=True, text=True, timeout=5
        )
        output = result.stdout + result.stderr
        info = {"ssid": "", "signal": "", "bitrate": "", "interface": ""}
        for line in output.split("\n"):
            if "ESSID:" in line:
                parts = line.split("ESSID:")
                if len(parts) > 1:
                    info["ssid"] = parts[1].strip().strip('"')
                    info["interface"] = line.split()[0] if line.split() else ""
            elif "Signal level=" in line:
                parts = line.split("Signal level=")
                if len(parts) > 1:
                    info["signal"] = parts[1].split()[0]
            elif "Bit Rate=" in line:
                parts = line.split("Bit Rate=")
                if len(parts) > 1:
                    info["bitrate"] = parts[1].split()[0]
        if info["ssid"]:
            return info
    except Exception:
        pass
    return None
