import threading
import time
from tkinter import messagebox
import os
import sys
import customtkinter as ctk
import logging

from src.utils.logger_config import setup_logging

if getattr(sys, 'frozen', False):
    # Pokud běžíme jako EXE, nastavíme pracovní adresář na složku s EXE
    os.chdir(os.path.dirname(sys.executable))

# Importy komponent
from src.core.config import AppSettings
from src.database.db_handler import DatabaseManager
from src.core.indexer import IndexManager
from src.gui.frames.setup_window import SetupWindow
from src.watchers.window_watcher import get_window_watcher
from src.watchers.afk_watcher import get_afk_watcher
from src.watchers.file_watcher import FileWatcher
from src.core.engine import ContextEngine
from src.gui.app import ContextFlowGUI
from src.utils.platform_handler import get_platform_handler

class ContextFlowLauncher:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.settings = AppSettings()
        self.restart_lock = threading.Lock() # Zámek proti vícenásobnému restartu
        
        # 1. KONTROLA CESTY HNED NA STARTU
        if not self.settings.MAIN_FOLDER or not os.path.exists(self.settings.MAIN_FOLDER):
            self.initial_setup()
        
        self.db = DatabaseManager(settings=self.settings)
        self.indexer = IndexManager(self.settings.MAIN_FOLDER)
        self.watcher = get_window_watcher(self.settings.WHITELIST)
        self.afk = get_afk_watcher(threshold_seconds=self.settings.AFK_THRESHOLD)
        self.fw = FileWatcher(self.indexer)
        self.engine = ContextEngine(self.watcher, self.indexer, self.db, afk_watcher=self.afk, settings=self.settings)

        # Přidání do registry pro start se systémem
        handler = get_platform_handler()
        handler.setup_autostart()
        
        # 2. VYTVOŘÍME GUI HNED (ale nezobrazíme)
        self.gui = ContextFlowGUI(launcher=self)
        self.gui.withdraw() # Skryje okno

    def run_engine_loop(self):
        try:
            self.engine.start()
        except Exception as e:
            logging.info(f"Engine Error: {e}")

    def start(self):
        # A. Engine ve vlákně
        self.engine_thread = threading.Thread(target=self.run_engine_loop, daemon=True)
        self.engine_thread.start()

        # B. FileWatcher ve vlákně
        self.fw.start()

        # C. GUI MAINLOOP V HLAVNÍM VLÁKNĚ
        logging.info("✓ ContextFlow běží. GUI v hlavním vlákně.")
        logging.info(self.indexer.lookup_map) # Pro debugování indexu při startu
        
        self.gui.mainloop()

        # D. Cleanup po ukončení GUI mainloopu
        self.shutdown_cleanup()

    def quit_app(self):
        logging.info("Ukončování...")
        
        # Zastavíme engine a file watcher
        if self.engine:
            self.engine.stop()
        if self.fw:
            self.fw.stop()
        
        # Pošleme vzkaz GUI, aby přestalo pracovat a ukončilo mainloop
        if self.gui:
            self.gui.after(0, self.gui.quit)

    def shutdown_cleanup(self):
        """Volá se bezprostředně po ukončení self.gui.mainloop() pro bezpečné zavření."""
        logging.info("Zavírám databázi a ukládám stav...")
        if hasattr(self, 'db') and hasattr(self.db, 'engine'):
            self.db.engine.dispose()
            
        logging.info("Všechna data uložena. Nashledanou.")

    def initial_setup(self):
        """Spustí onboarding okno z gui/frames."""
        selected_path = []

        def handle_selection(path):
            selected_path.append(path)

        setup_win = SetupWindow(on_folder_select=handle_selection)
        setup_win.mainloop()

        if selected_path:
            self.settings.MAIN_FOLDER = selected_path[0]
            if not self.settings.WHITELIST:
                self.settings.WHITELIST = ["code.exe", "pycharm64.exe", "notepad++.exe"]
            self.settings.save()
        else:
            # Pokud uživatel zavřel setup bez výběru, nepokračujeme
            sys.exit()

    def apply_settings(self):
        """Tato metoda se volá z GUI. Jen spustí vlákno a hned vrátí řízení GUI."""
        if self.restart_lock.locked():
            logging.warning("Restart již probíhá, prosím čekejte...")
            return
            
        logging.info("Spouštím bezpečný reaktivní restart...")
        threading.Thread(target=self._do_apply_settings_background, daemon=True).start()

    def _do_apply_settings_background(self):
        with self.restart_lock: # Zamkneme proces restartu
            try:
                # 1. Zastavení starých služeb
                if hasattr(self, 'engine'):
                    self.engine.stop()
                if hasattr(self, 'fw'):
                    self.fw.stop()
                
                time.sleep(1)

                # 2. Reinicializace komponent
                self.watcher = get_window_watcher(self.settings.WHITELIST)
                self.indexer = IndexManager(self.settings.MAIN_FOLDER)
                self.fw = FileWatcher(self.indexer)
                self.afk = get_afk_watcher(threshold_seconds=self.settings.AFK_THRESHOLD)
                
                self.engine = ContextEngine(
                    self.watcher, 
                    self.indexer, 
                    self.db, 
                    afk_watcher=self.afk, 
                    settings=self.settings
                )

                # 3. Start nových služeb
                self.fw.start()
                self.engine_thread = threading.Thread(target=self.run_engine_loop, daemon=True)
                self.engine_thread.start()
                
                logging.info("--- Engine úspěšně restartován (všechny staré procesy ukončeny) ---")
                
                # 4. Úspěšná zpráva do GUI
                self.gui.after(0, lambda: messagebox.showinfo("Hotovo", "Nastavení bylo aplikováno.\nAplikace běží s novým nastavením."))
                
            except Exception as e:
                logging.error(f"Chyba při reaktivním restartu: {e}", exc_info=True)
                self.gui.after(0, lambda: messagebox.showerror("Chyba", f"Restart selhal: {e}"))

if __name__ == "__main__":
    handler = get_platform_handler()
    handler.handle_installation() # Provede instalaci/přesun do AppData, pokud je to potřeba
    setup_logging() # Log > soubor
    try:
        launcher = ContextFlowLauncher()
        launcher.start()
    except Exception as e:
        logging.error(f"Kritická chyba při startu aplikace: {e}", exc_info=True)
