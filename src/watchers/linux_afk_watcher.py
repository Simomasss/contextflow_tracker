import subprocess
import ctypes
import ctypes.util
from .afk_watcher import BaseAFKWatcher

class XScreenSaverInfo(ctypes.Structure):
    _fields_ = [
        ('window', ctypes.c_ulong),
        ('state', ctypes.c_int),
        ('kind', ctypes.c_int),
        ('til_or_since', ctypes.c_ulong),
        ('idle', ctypes.c_ulong),
        ('event_mask', ctypes.c_ulong)
    ]

class LinuxAFKWatcher(BaseAFKWatcher):
    def get_idle_time(self) -> int:
        """Vrátí počet milisekund od poslední interakce uživatele."""
        
        # Pokus 1: Použití X11 a XScreenSaver (libXss)
        try:
            xlib_path = ctypes.util.find_library('X11') or 'libX11.so.6'
            xss_path = ctypes.util.find_library('Xss') or 'libXss.so.1'
            
            xlib = ctypes.cdll.LoadLibrary(xlib_path)
            xss = ctypes.cdll.LoadLibrary(xss_path)
            
            xlib.XOpenDisplay.restype = ctypes.c_void_p
            display = xlib.XOpenDisplay(None)
            
            if display:
                xlib.XDefaultRootWindow.restype = ctypes.c_ulong
                xlib.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
                root = xlib.XDefaultRootWindow(display)
                
                xss_info = XScreenSaverInfo()
                xss.XScreenSaverQueryInfo(display, root, ctypes.byref(xss_info))
                
                xlib.XCloseDisplay(display)
                
                return int(xss_info.idle)
        except Exception:
            pass

        # Pokus 2: Použití příkazu xprintidle (pokud je dostupný)
        try:
            output = subprocess.check_output(['xprintidle'], stderr=subprocess.DEVNULL)
            return int(output.strip())
        except Exception:
            pass
            
        # Pokus 3: Wayland GNOME (Mutter) přes gdbus (často výchozí v Ubuntu)
        try:
            output = subprocess.check_output(
                ['gdbus', 'call', '--session', '--dest', 'org.gnome.Mutter.IdleMonitor', 
                 '--object-path', '/org/gnome/Mutter/IdleMonitor/Core', 
                 '--method', 'org.gnome.Mutter.IdleMonitor.GetIdletime'], 
                stderr=subprocess.DEVNULL, text=True, errors='replace'
            )
            # Očekávaný výstup např.: (uint64 12345,)
            if output and 'uint64' in output:
                idle_str = output.split('uint64')[1].strip(' ,)\n')
                return int(idle_str)
        except Exception:
            pass

        return 0

    def watch(self) -> bool:
        """
        Vrací True, pokud je uživatel AFK (nečinný déle než threshold).
        """
        return self.get_idle_time() > self.threshold
