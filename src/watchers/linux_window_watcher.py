import subprocess
from typing import Optional, List
from .window_watcher import BaseWindowWatcher
from ..core.schemas import WindowInfo

class LinuxWindowWatcher(BaseWindowWatcher):
    def watch(self) -> Optional[WindowInfo]:
        try:
            # Získání ID aktivního okna
            root_prop = subprocess.check_output(
                ['xprop', '-root', '_NET_ACTIVE_WINDOW'], 
                stderr=subprocess.DEVNULL
            ).decode('utf-8').strip()
            
            if 'window id #' not in root_prop:
                return None
                
            window_id = root_prop.split('window id #')[1].strip()
            if window_id == '0x0':
                return None

            # Získání informací o okně
            win_prop = subprocess.check_output(
                ['xprop', '-id', window_id, 'WM_NAME', 'WM_CLASS'], 
                stderr=subprocess.DEVNULL
            ).decode('utf-8')
            
            title = ""
            executable = ""
            
            for line in win_prop.split('\n'):
                if line.startswith('WM_NAME') or line.startswith('_NET_WM_NAME'):
                    parts = line.split(' = ', 1)
                    if len(parts) == 2:
                        title = parts[1].strip().strip('"')
                elif line.startswith('WM_CLASS'):
                    parts = line.split(' = ', 1)
                    if len(parts) == 2:
                        classes = parts[1].split(', ')
                        if len(classes) >= 1:
                            # Poslední položka ve WM_CLASS je obvykle název aplikace/spustitelného souboru
                            executable = classes[-1].strip().strip('"').lower()

            if not executable:
                return None

            is_whitelisted = executable in self.whitelist
            
            return WindowInfo(
                title=title,
                executable=executable,
                is_whitelisted=is_whitelisted
            )
        except Exception:
            pass
            
        return None
