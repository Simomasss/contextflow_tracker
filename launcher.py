import threading
from tkinter import filedialog, messagebox
import tkinter
import winreg
import pystray
from PIL import Image
import os
import sys
import customtkinter as ctk
from src.utils.logger_config import setup_logging
import logging

# Importy komponent
from src.core.config import AppSettings
from src.database.db_handler import DatabaseManager
from src.core.indexer import IndexManager
from src.gui.frames.setup_window import SetupWindow
from src.watchers.window_watcher import WindowWatcher
from src.watchers.afk_watcher import AFKWatcher
from src.watchers.file_watcher import FileWatcher
from src.core.engine import ContextEngine
from src.gui.app import ContextFlowGUI

def resource_path(relative_path):
    """ Pomocná funkce pro získání absolutní cesty k prostředkům (pro PyInstaller) """
    # getattr bezpečně zkontroluje, jestli _MEIPASS existuje, jinak použije aktuální složku
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

class ContextFlowLauncher:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.settings = AppSettings()
        
        # 1. KONTROLA CESTY HNED NA STARTU
        if not self.settings.MAIN_FOLDER or not os.path.exists(self.settings.MAIN_FOLDER):
            self.initial_setup()
        
        self.db = DatabaseManager(settings=self.settings)
        self.indexer = IndexManager(self.settings.MAIN_FOLDER)
        self.watcher = WindowWatcher(self.settings.WHITELIST)
        self.afk = AFKWatcher(threshold_seconds=self.settings.AFK_THRESHOLD)
        self.fw = FileWatcher(self.indexer)
        self.engine = ContextEngine(self.watcher, self.indexer, self.db, afk_watcher=self.afk, settings=self.settings)

        self.icon_path = resource_path("src/gui/assets/icon.ico")
        try:
            tray_img = Image.open(self.icon_path)
        except Exception:
            # Fallback na barevný čtverec, kdyby soubor chyběl
            tray_img = Image.new('RGB', (64, 64), color=(31, 83, 141))

        self.icon = pystray.Icon("ContextFlow", tray_img, "ContextFlow", menu=pystray.Menu(
            pystray.MenuItem("Otevřít přehled", self.show_gui),
            pystray.MenuItem("Ukončit", self.quit_app)
        ))

        # 2. VYTVOŘÍME GUI HNED (ale zatím ho nezobrazíme)
        self.icon_path = resource_path("src/gui/assets/icon.ico")
        self.gui = ContextFlowGUI()
        self.gui.withdraw()  # Skryje okno hned po vytvoření
        # Ikona vlevo nahoře v okně
        try:
            self.gui.iconbitmap(self.icon_path)
        except Exception as e:
            logging.info(f"Nepodařilo se načíst ikonu okna: {e}")
        self.gui.protocol("WM_DELETE_WINDOW", self.hide_gui)

        # 3. NASTAVENÍ TRAY IKONKY
        try:
            # PIL umí otevřít .ico a vybrat z něj nejlepší rozlišení
            tray_img = Image.open(self.icon_path)
        except Exception as e:
            logging.info(f"Ikonku v {self.icon_path} se nepodařilo načíst: {e}")
            # Fallback na ten tvůj modrý čtverec, kdyby ikonka chyběla
            tray_img = Image.new('RGB', (64, 64), color=(31, 83, 141))

        self.icon = pystray.Icon("ContextFlow", tray_img, "ContextFlow", menu=pystray.Menu(
            pystray.MenuItem("Otevřít přehled", self.show_gui),
            pystray.MenuItem("Ukončit", self.quit_app)
        ))

    def show_gui(self, icon=None, item=None):
        # Používáme after(), aby se deiconify zavolalo v hlavním vlákně GUI
        self.gui.after(0, self.gui.deiconify)
        self.gui.after(0, self.gui.focus_force)

    def hide_gui(self):
        self.gui.withdraw()

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

        # C. Tray ikona v samostatném vlákně!
        # Používáme daemon=True, aby se vlákno ukončilo s aplikací
        self.tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        self.tray_thread.start()

        # Přidání do registry pro start s Windows (funguje jen pro EXE verzi)
        self.add_to_startup()

        # D. GUI MAINLOOP V HLAVNÍM VLÁKNĚ
        # Tohle musí být poslední řádek, který "drží" aplikaci naživu
        logging.info("✓ ContextFlow běží. GUI v hlavním vlákně, Tray ve vedlejším.")
        self.gui.mainloop()

    def quit_app(self, icon=None, item=None):
        logging.info("Ukončování...")
        
        # 1. Zastavíme tray a engine (věci mimo GUI)
        self.icon.stop()
        self.engine.stop()
        self.fw.stop()
        
        # 2. Pošleme vzkaz GUI, aby přestalo pracovat
        if self.gui:
            # Zrušíme všechny naplánované úkoly (after callbacky)
            # a ukončíme mainloop v hlavním vlákně
            self.gui.after(0, self.gui.quit)
            
        # 3. Počkáme zlomek sekundy, aby mainloop v start() mohl skončit
        # a pak teprve násilně ukončíme proces
        threading.Timer(0.2, lambda: os._exit(0)).start()
        # Důležité: Commit a zavření DB spojení
        # Pokud tvůj db_handler má metodu close(), zavolej ji tady
        
        logging.info("Všechna data uložena. Nashledanou.")
        os._exit(0)

    def initial_setup(self):
        """Spustí onboarding okno z gui/frames."""
        selected_path = []

        def handle_selection(path):
            selected_path.append(path)

        # Spustíme naimportované okno
        setup_win = SetupWindow(on_folder_select=handle_selection)
        setup_win.mainloop()

        if selected_path:
            self.settings.MAIN_FOLDER = selected_path[0]
            # Defaultní whitelist, aby to hned fungovalo
            if not self.settings.WHITELIST:
                self.settings.WHITELIST = ["code.exe", "pycharm64.exe", "notepad++.exe"]
            self.settings.save()
        else:
            # Pokud uživatel zavřel setup bez výběru, nepokračujeme
            sys.exit()

    def add_to_startup(self):
        """Přidá aktuální EXE do registru pro start po zapnutí PC."""
        if getattr(sys, 'frozen', False):
            # Cesta k běžícímu .exe souboru
            app_path = sys.executable
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "ContextFlow", 0, winreg.REG_SZ, app_path)
                winreg.CloseKey(key)
                logging.info("✓ Aplikace přidána do po spuštění.")
            except Exception as e:
                logging.info(f"Nepodařilo se zapsat do registru: {e}")

if __name__ == "__main__":
    setup_logging() # Teď už všechno, co logujeme, půjde do souboru
    try:
        launcher = ContextFlowLauncher()
        launcher.start()
    except Exception as e:
        logging.error(f"Kritická chyba při startu aplikace: {e}", exc_info=True)