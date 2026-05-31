import threading
import time
from tkinter import messagebox
import winreg
import pystray
from PIL import Image
import os
import sys
import customtkinter as ctk
import shutil
import subprocess
import tempfile
from src.utils.logger_config import setup_logging
import logging

if getattr(sys, 'frozen', False):
    # Pokud běžíme jako EXE, nastavíme pracovní adresář na složku s EXE
    os.chdir(os.path.dirname(sys.executable))

# Importy komponent
from src.core.config import AppSettings
from src.database.db_handler import DatabaseManager
from src.core.indexer import IndexManager
from src.gui.frames.setup_window import SetupWindow
from src.watchers.window_watcher import get_window_watcher
from src.watchers.afk_watcher import AFKWatcher
from src.watchers.file_watcher import FileWatcher
from src.core.engine import ContextEngine
from src.gui.app import ContextFlowGUI
from src.utils.paths import get_app_data_dir

def handle_portable_installation():
    """
    Pokud je aplikace spuštěna jako EXE z náhodného místa (např. Stažené soubory),
    přesune se automaticky do LocalAppData a na původním místě zanechá zástupce.
    Tím se zabrání rozbití automatického spouštění po startu systému, pokud
    by uživatel původní EXE přesunul jinam.
    """
    if not getattr(sys, 'frozen', False):
        return # Běžíme ze zdrojáků, nic nepřesouváme

    current_exe = os.path.abspath(sys.executable)
    appdata_dir = get_app_data_dir()
    target_exe = os.path.join(appdata_dir, "ContextFlow.exe")

    # Pokud už běžíme z AppData, nic neděláme
    if os.path.normcase(current_exe) == os.path.normcase(target_exe):
        return

    # Vytvořit cílovou složku
    os.makedirs(appdata_dir, exist_ok=True)

    try:
        logging.info(f"Probíhá instalace EXE do: {target_exe}")
        # 1. Zkopírovat se do AppData
        shutil.copy2(current_exe, target_exe)

        # 2. Vytvořit zástupce na původním místě přes VBScript
        original_dir = os.path.dirname(current_exe)
        original_name = os.path.splitext(os.path.basename(current_exe))[0]
        shortcut_path = os.path.join(original_dir, f"{original_name}.lnk")

        vbs_script = f"""
        Set oWS = WScript.CreateObject("WScript.Shell")
        Set oLink = oWS.CreateShortcut("{shortcut_path}")
        oLink.TargetPath = "{target_exe}"
        oLink.WorkingDirectory = "{appdata_dir}"
        oLink.IconLocation = "{target_exe}"
        oLink.Save
        """
        vbs_path = os.path.join(tempfile.gettempdir(), "create_shortcut.vbs")
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(vbs_script)
        
        subprocess.run(["cscript.exe", "//Nologo", vbs_path], creationflags=subprocess.CREATE_NO_WINDOW)
        
        try:
            os.remove(vbs_path)
        except Exception:
            pass

        # 3. Vytvořit .bat skript pro bezpečné smazání starého EXE a restart aplikace
        bat_path = os.path.join(tempfile.gettempdir(), "cf_migrate.bat")
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write("@echo off\n")
            f.write("timeout /t 2 /nobreak > NUL\n") # Počkat na ukončení starého procesu
            f.write(f'del "{current_exe}"\n')
            f.write(f'start "" "{target_exe}"\n')
            f.write('del "%~f0"\n') # Smazat sám sebe

        # Spustit bat skript na pozadí bez okna
        subprocess.Popen([bat_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        logging.info("Aplikace byla úspěšně přesunuta. Restartuji...")
        # Okamžitě ukončit aktuální proces (odblokuje původní EXE pro smazání)
        os._exit(0)

    except Exception as e:
        logging.error(f"Nepodařilo se přesunout aplikaci do AppData: {e}")
        # V případě chyby prostě pokračujeme v běhu ze stávajícího místa

def resource_path(relative_path):
    """ Pomocná funkce pro získání absolutní cesty k prostředkům (pro PyInstaller) """
    # getattr  zkontroluje, jestli _MEIPASS existuje, jinak použije aktuální složku
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

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
        self.afk = AFKWatcher(threshold_seconds=self.settings.AFK_THRESHOLD)
        self.fw = FileWatcher(self.indexer)
        self.engine = ContextEngine(self.watcher, self.indexer, self.db, afk_watcher=self.afk, settings=self.settings)

        
        # Přidání do registry pro start s Windows (funguje jen pro EXE verzi a aktualizuje cestu)
        self.add_to_startup()
        
        # 2. VYTVOŘÍME GUI HNED (ale nezobrazíme)
        self.icon_path = resource_path("src/gui/assets/icon.ico")
        self.gui = ContextFlowGUI(launcher=self)
        self.gui.withdraw() # Skryje okno

        # Ikona vlevo nahoře v okně
        try:
            self.gui.iconbitmap(self.icon_path)
        except Exception as e:
            logging.info(f"Nepodařilo se načíst ikonu okna: {e}")
        self.gui.protocol("WM_DELETE_WINDOW", self.hide_gui)

        # 3. NASTAVENÍ TRAY IKONKY
        try:
            tray_img = Image.open(self.icon_path)
        except Exception as e:
            logging.info(f"Ikonku v {self.icon_path} se nepodařilo načíst: {e}")
            tray_img = Image.new('RGB', (64, 64), color=(31, 83, 141))

        self.icon = pystray.Icon("ContextFlow", tray_img, "ContextFlow", menu=pystray.Menu(
            pystray.MenuItem("Otevřít přehled", self.show_gui),
            pystray.MenuItem("Ukončit", self.quit_app)
        ))

    def show_gui(self, icon=None, item=None):
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

        # D. GUI MAINLOOP V HLAVNÍM VLÁKNĚ
        logging.info("✓ ContextFlow běží. GUI v hlavním vlákně, Tray ve vedlejším.")
        logging.info(self.indexer.lookup_map) # Pro debugování indexu při startu
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
            if not self.settings.WHITELIST:
                self.settings.WHITELIST = ["code.exe", "pycharm64.exe", "notepad++.exe"]
            self.settings.save()
        else:
            # Pokud uživatel zavřel setup bez výběru, nepokračujeme
            sys.exit()

    def add_to_startup(self):
        """Přidá aktuální EXE do registru pro start po zapnutí PC a aktualizuje cestu, pokud byla aplikace přesunuta."""
        if getattr(sys, 'frozen', False):
            app_path = sys.executable
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ | winreg.KEY_SET_VALUE)
                try:
                    current_val, _ = winreg.QueryValueEx(key, "ContextFlow")
                    if current_val != app_path:
                        winreg.SetValueEx(key, "ContextFlow", 0, winreg.REG_SZ, app_path)
                        logging.info("✓ Cesta v registru aktualizována.")
                except FileNotFoundError:
                    # Key doesn't exist yet, create it
                    winreg.SetValueEx(key, "ContextFlow", 0, winreg.REG_SZ, app_path)
                    logging.info("✓ Aplikace přidána do po spuštění.")
                finally:
                    winreg.CloseKey(key)
            except Exception as e:
                logging.info(f"Nepodařilo se zapsat/číst do registru: {e}")

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
                self.afk = AFKWatcher(threshold_seconds=self.settings.AFK_THRESHOLD)
                
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
    handle_portable_installation() # Provede instalaci/přesun do AppData, pokud je to potřeba
    setup_logging() # Log > soubor
    try:
        launcher = ContextFlowLauncher()
        launcher.start()
    except Exception as e:
        logging.error(f"Kritická chyba při startu aplikace: {e}", exc_info=True)