"""Read-only system information."""
import platform
import shutil
from pathlib import Path


def get_system_status():
    lines = [f"OS: {platform.system()} {platform.release()}", f"Python: {platform.python_version()}"]
    try:
        import psutil
        lines += [f"CPU: {psutil.cpu_percent(interval=0.1):.0f}%",
                  f"RAM: {psutil.virtual_memory().percent:.0f}% used",
                  f"Disk: {psutil.disk_usage(str(Path.home().anchor or '/')).percent:.0f}% used"]
        battery = psutil.sensors_battery()
        if battery:
            lines.append(f"Battery: {battery.percent:.0f}%")
    except Exception:
        try:
            _total, _used, free = shutil.disk_usage(Path.home())
            lines.append(f"Disk free: {free // (1024 ** 3)} GB")
        except OSError:
            pass
    return "\n".join(lines)
