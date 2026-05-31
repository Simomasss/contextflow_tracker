import sys
from abc import ABC, abstractmethod

class BasePlatformHandler(ABC):
    @abstractmethod
    def setup_autostart(self) -> bool:
        pass

    @abstractmethod
    def remove_autostart(self) -> bool:
        pass

    @abstractmethod
    def handle_installation(self) -> bool:
        pass

    @abstractmethod
    def uninstall(self, backup_diagnostics: bool = True) -> bool:
        pass

def get_platform_handler() -> BasePlatformHandler:
    if sys.platform == "win32":
        from src.utils.windows_handler import WindowsPlatformHandler
        return WindowsPlatformHandler()
    elif sys.platform == "darwin":
        from src.utils.mac_handler import MacPlatformHandler
        return MacPlatformHandler()
    else:
        from src.utils.linux_handler import LinuxPlatformHandler
        return LinuxPlatformHandler()
