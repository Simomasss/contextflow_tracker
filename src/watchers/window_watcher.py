import sys
from abc import abstractmethod
from typing import Optional, List
from .base_watcher import BaseWatcher
from ..core.schemas import WindowInfo

class BaseWindowWatcher(BaseWatcher):
    def __init__(self, whitelist: List[str]):
        self.whitelist = [exe.lower() for exe in whitelist]

    @abstractmethod
    def watch(self) -> Optional[WindowInfo]:
        pass

def get_window_watcher(whitelist: List[str]) -> BaseWindowWatcher:
    """Tovární funkce pro vrácení správného watchera podle OS."""
    if sys.platform == "win32":
        from src.watchers.windows_window_watcher import WindowsWindowWatcher
        return WindowsWindowWatcher(whitelist)
    elif sys.platform == "darwin":
        from src.watchers.mac_window_watcher import MacWindowWatcher
        return MacWindowWatcher(whitelist)
    else:
        # Fallback na Linux a další
        from src.watchers.linux_window_watcher import LinuxWindowWatcher
        return LinuxWindowWatcher(whitelist)
