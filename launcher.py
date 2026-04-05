import threading
import pystray
from PIL import Image
import os
import sys
import time

# Importy tvých komponent (uprav cesty podle potřeby)
from src.core.config import AppSettings
from src.database.db_handler import DatabaseManager
from src.core.indexer import IndexManager
from src.watchers.window_watcher import WindowWatcher
from src.watchers.afk_watcher import AFKWatcher
from src.watchers.file_watcher import FileWatcher
from src.core.engine import ContextEngine # Předpokládám, že jsi třídu Engine přejmenoval/přesunul
from src.gui.app import ContextFlowGUI

class ContextFlowLauncher:
    def __init__(self):
        # 1. NASTAVENÍ A ZÁKLADNÍ SLUŽBY (Stejně jako v main.py)
        self.settings = AppSettings()
        self.db = DatabaseManager(settings=self.settings)
        self.indexer = IndexManager(self.settings.MAIN_FOLDER)
        self.watcher = WindowWatcher(self.settings.WHITELIST)
        self.afk = AFKWatcher(threshold_seconds=self.settings.AFK_THRESHOLD)
        
        # 2. FILE WATCHER
        self.fw = FileWatcher(self.indexer)
        
        # 3. ENGINE
        self.engine = ContextEngine(self.watcher, self.indexer, self.db, afk_watcher=self.afk, settings=self.settings)
        
        # 4. GUI A TRAY INICIALIZACE
        self.gui = None
        # Vytvoření ikonky (prozatím placeholder)
        icon_img = Image.new('RGB', (64, 64), color=(31, 83, 141))
        self.icon = pystray.Icon("ContextFlow", icon_img, "ContextFlow", menu=pystray.Menu(
            pystray.MenuItem("Otevřít přehled", self.show_gui),
            pystray.MenuItem("Ukončit", self.quit_app)
        ))

    def run_engine_loop(self):
        """Metoda pro vlákno enginu."""
        try:
            self.engine.start()
        except Exception as e:
            print(f"Kritická chyba v Enginu: {e}")

    def show_gui(self):
        if self.gui is None or not self.gui.winfo_exists():
            # Předáme existující instance (aggregator si vytvoří app.py sám nebo mu ho můžeme předat)
            self.gui = ContextFlowGUI() 
            self.gui.protocol("WM_DELETE_WINDOW", self.hide_gui)
            self.gui.mainloop()
        else:
            self.gui.focus()

    def hide_gui(self):
        if self.gui:
            self.gui.destroy()
            self.gui = None

    def start(self):
        # A. Spustíme FileWatcher (ten má vlastní vlákno v sobě, jak píšeš)
        self.fw.start()
        print(f"✓ FileWatcher běží na: {self.settings.MAIN_FOLDER}")

        # B. Spustíme Engine v samostatném vlákně
        self.engine_thread = threading.Thread(target=self.run_engine_loop, daemon=True)
        self.engine_thread.start()
        print("✓ Engine běží na pozadí.")
        
        # C. Spustíme Tray ikonku (tato řádka zablokuje hlavní vlákno)
        print("✓ Aplikace je připravena v oznamovací oblasti (System Tray).")
        self.icon.run()

    def quit_app(self):
        print("\nUkončování ContextFlow...")
        self.engine.stop() # Zastaví smyčku v engine.py
        self.fw.stop()     # Zastaví FileWatcher
        self.icon.stop()   # Odstraní ikonku z lišty
        os._exit(0)        # Ukončí celý proces

if __name__ == "__main__":
    launcher = ContextFlowLauncher()
    launcher.start()