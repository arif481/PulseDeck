# Security Policy

## Root Access

PulseDeck runs as a normal user. Some features only work when it is started with `sudo python3 main.py`:

| Feature | Root Required |
|---------|:------------:|
| CPU / Memory / Disk / Thermal monitoring | No |
| Application management | No |
| Network bandwidth & interface monitoring | No |
| Full network connection details | Yes |
| CPU governor control | Yes |
| Process kill (signal sending) | Yes |
| SMART disk health (via `smartctl`) | Yes |
| Fan speed (PWM) | Yes |

### What root access does

With root, PulseDeck:

- writes the chosen governor to `/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor`
- writes fan speed values to the hwmon `pwm*` files, and can hand a fan back to automatic control
- sends SIGTERM to a process you choose to kill, using `os.kill()`
- runs `smartctl` from smartmontools to read SMART data
- reads all network connections with `psutil.net_connections()`

It writes no other system files. Everything is read locally: PulseDeck makes no network requests and does not store or send the data it collects. Installing and removing apps does not need root: apt runs through `pkexec` and Flatpak uses its own polkit prompt, so each asks for your password when it needs it.

## Reporting a Vulnerability

If you discover a security issue, please open a private report via [GitHub Security Advisories](https://github.com/arif481/PulseDeck/security/advisories) or email the maintainer directly. Do not open a public issue for security vulnerabilities.
