import win32gui
import win32process
import psutil
from typing import Optional, List
from .base_watcher import BaseWatcher
from ..core.schemas import WindowInfo

class WindowWatcher(BaseWatcher):
    def __init__(self, whitelist: List[str]):
        self.whitelist = [exe.lower() for exe in whitelist]

    def watch(self) -> Optional[WindowInfo]:
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
                is_whitelisted=is_whitelisted # Ted watcher bude vracet i info o whitelistu, místo None
            )

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return None