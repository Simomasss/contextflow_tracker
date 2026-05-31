import subprocess
from .afk_watcher import BaseAFKWatcher

class MacAFKWatcher(BaseAFKWatcher):
    def get_idle_time(self) -> int:
        """Vrátí počet milisekund od poslední interakce uživatele."""
        try:
            output = subprocess.check_output(
                ["ioreg", "-c", "IOHIDSystem"],
                text=True,
                stderr=subprocess.DEVNULL
            )
            for line in output.splitlines():
                if "HIDIdleTime" in line:
                    idle_time_ns = int(line.split("=")[-1].strip())
                    return idle_time_ns // 1_000_000
            return 0
        except Exception:
            return 0

    def watch(self) -> bool:
        """
        Vrací True, pokud je uživatel AFK (nečinný déle než threshold).
        """
        return self.get_idle_time() > self.threshold
