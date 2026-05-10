import win32api
from .base_watcher import BaseWatcher

class AFKWatcher(BaseWatcher):
    def __init__(self, threshold_seconds: int = 300):
        """
        :param threshold_seconds: Po kolika sekundách nečinnosti se uživatel považuje za AFK.
        """
        self.threshold = threshold_seconds * 1000  # Win32 API pracuje v milisekundách

    def get_idle_time(self) -> int:
        """Vrátí počet milisekund od poslední interakce uživatele."""
        # GetTickCount() vrací čas od spuštění systému
        # GetLastInputInfo() vrací čas posledního stisku klávesy/pohybu myši
        try:
            last_input_info = win32api.GetLastInputInfo()
            current_tick = win32api.GetTickCount()
            
            return (current_tick - last_input_info) % (1 << 32)
        except Exception:
            # Ochrana pro případ zamknuté obrazovky
            return 0

    def watch(self) -> bool:
        """
        Vrací True, pokud je uživatel AFK (nečinný déle než threshold).
        """
        return self.get_idle_time() > self.threshold