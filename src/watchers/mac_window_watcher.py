import subprocess
from typing import Optional, List
from .window_watcher import BaseWindowWatcher
from ..core.schemas import WindowInfo

class MacWindowWatcher(BaseWindowWatcher):
    def watch(self) -> Optional[WindowInfo]:
        script = """
        tell application "System Events"
            try
                set frontApp to first application process whose frontmost is true
                set frontAppName to name of frontApp
                set windowTitle to ""
                try
                    tell process frontAppName
                        set windowTitle to name of front window
                    end tell
                end try
                return frontAppName & ":::" & windowTitle
            on error
                return ""
            end try
        end tell
        """
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=1
            )
            output = result.stdout.strip()
            
            if not output or ":::" not in output:
                return None
                
            parts = output.split(":::", 1)
            app_name = parts[0]
            window_title = parts[1] if len(parts) > 1 else ""
            
            exe_name = app_name.lower()
            is_whitelisted = exe_name in self.whitelist
            
            return WindowInfo(
                title=window_title,
                executable=exe_name,
                is_whitelisted=is_whitelisted
            )
        except Exception:
            pass
            
        return None
