import psutil
from typing import Optional, List
from .window_watcher import BaseWindowWatcher
from ..core.schemas import WindowInfo

class WindowsWindowWatcher(BaseWindowWatcher):
    def watch(self) -> Optional[WindowInfo]:
        import win32gui
        import win32process

        hwnd = win32gui.GetForegroundWindow()
        if not hwnd: return None

        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            exe_name = process.name().lower()

            is_whitelisted = exe_name in self.whitelist
            
            return WindowInfo(
                title=win32gui.GetWindowText(hwnd),
                executable=exe_name,
                is_whitelisted=is_whitelisted
            )

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return None
