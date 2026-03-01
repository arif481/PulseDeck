# Security Policy

## Root Access

PulseDeck can optionally be run with root privileges (`sudo python3 main.py`) to unlock advanced features:

| Feature | Root Required |
|---------|:------------:|
| CPU / Memory / Disk / Thermal monitoring | No |
| Application management | No |
| Network bandwidth & interface monitoring | No |
| Full network connection details | **Yes** |
| CPU governor control | **Yes** |
| Process kill (signal sending) | **Yes** |
| SMART disk health (via `smartctl`) | **Yes** |

### What root access does

- **Reads** CPU governor settings from `/sys/devices/system/cpu/`
- **Writes** governor changes to `/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor`
- **Sends** POSIX signals (SIGTERM/SIGKILL) to processes via `os.kill()`
- **Executes** `smartctl` (from smartmontools) to read disk SMART data
- **Reads** network connections via `psutil.net_connections()`

### What root access does NOT do

- No network requests are made — all data is collected locally
- No data is stored, transmitted, or logged outside the application
- No system files are modified beyond CPU governor settings

## Reporting a Vulnerability

If you discover a security issue, please open a private report via [GitHub Security Advisories](https://github.com/arif481/PulseDeck/security/advisories) or email the maintainer directly. Do not open a public issue for security vulnerabilities.
