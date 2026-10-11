"""Read-only system information and lightweight live telemetry."""
import platform
import shutil
from pathlib import Path


def get_system_status():
    lines = [f"OS: {platform.system()} {platform.release()}",
             f"Python: {platform.python_version()}"]
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(str(Path.home().anchor or "/"))
        lines.extend([
            f"CPU: {cpu:.0f}%",
            f"RAM: {memory.percent:.0f}% used ({memory.used // (1024 ** 3)} / {memory.total // (1024 ** 3)} GB)",
            f"Disk: {disk.percent:.0f}% used ({disk.free // (1024 ** 3)} GB free)",
            f"Processes: {len(psutil.pids())}",
        ])
        battery = psutil.sensors_battery()
        if battery:
            lines.append(f"Battery: {battery.percent:.0f}%" + (" (charging)" if battery.power_plugged else ""))
        try:
            uptime = max(0, int(__import__("time").time() - psutil.boot_time()))
            hours, rem = divmod(uptime, 3600)
            lines.append(f"Uptime: {hours}h {rem // 60}m")
        except Exception:
            pass
    except Exception:
        try:
            _total, _used, free = shutil.disk_usage(Path.home())
            lines.append(f"Disk free: {free // (1024 ** 3)} GB")
        except OSError:
            pass
    return "\n".join(lines)
