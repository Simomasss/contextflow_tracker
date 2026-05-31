import sys
from abc import abstractmethod
from .base_watcher import BaseWatcher

class BaseAFKWatcher(BaseWatcher):
    def __init__(self, threshold_seconds: int = 300):
        """
        :param threshold_seconds: Po kolika sekundách nečinnosti se uživatel považuje za AFK.
        """
        self.threshold = threshold_seconds * 1000  # Většina OS API pracuje v milisekundách

    @abstractmethod
    def watch(self) -> bool:
        """
        Vrací True, pokud je uživatel AFK (nečinný déle než threshold).
        """
        pass

def get_afk_watcher(threshold_seconds: int = 300) -> BaseAFKWatcher:
    """Tovární funkce pro vrácení správného AFK watchera podle OS."""
    if sys.platform == "win32":
        from src.watchers.windows_afk_watcher import WindowsAFKWatcher
        return WindowsAFKWatcher(threshold_seconds)
    elif sys.platform == "darwin":
        from src.watchers.mac_afk_watcher import MacAFKWatcher
        return MacAFKWatcher(threshold_seconds)
    else:
        # Fallback na Linux a další
        from src.watchers.linux_afk_watcher import LinuxAFKWatcher
        return LinuxAFKWatcher(threshold_seconds)
