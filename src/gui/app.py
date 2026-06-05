import pystray
from PIL import Image
import threading
import os
import sys
import logging
import customtkinter as ctk
from .frames.home import HomeFrame
from .frames.clients import ClientsFrame
from .frames.settings import SettingsFrame
from ..core.aggregator import ActivityAggregator

def resource_path(relative_path):
    """ Pomocná funkce pro získání absolutní cesty k prostředkům (pro PyInstaller) """
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

class ContextFlowGUI(ctk.CTk):
    def __init__(self, launcher):
        super().__init__()

        self.launcher = launcher
        self.settings = launcher.settings 
        self.db = launcher.db
        self.aggregator = ActivityAggregator(self.db)

        # --- 2. ZÁKLADNÍ OKNO ---
        self.title("ContextFlow")
        self.geometry("1100x700")

        # Konfigurace gridu
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- 3. SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="ContextFlow", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(pady=20, padx=20)

        self.home_btn = ctk.CTkButton(self.sidebar, text="Domů", command=self.show_home)
        self.home_btn.pack(pady=10, padx=20)

        self.clients_btn = ctk.CTkButton(self.sidebar, text="Klienti", command=self.show_clients)
        self.clients_btn.pack(pady=10, padx=20)

        self.settings_btn = ctk.CTkButton(self.sidebar, text="Nastavení", command=self.show_settings)
        self.settings_btn.pack(pady=10, padx=20)

        # --- 4. HLAVNÍ PLOCHA ---
        self.main_view = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_view.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # --- 5. TRAY IKONA A OKNO EVENTY ---
        self.icon_path = resource_path(os.path.join("src", "gui", "assets", "icon.ico"))
        try:
            self.iconbitmap(self.icon_path)
        except Exception as e:
            logging.info(f"Nepodařilo se načíst ikonu okna: {e}")
            
        # macOS → minimize, Linux/Win → hide
        if sys.platform == "darwin":
            self.protocol("WM_DELETE_WINDOW", self.iconify)
        else:
            self.protocol("WM_DELETE_WINDOW", self.hide_gui)
            self.setup_tray()

        # Spustíme domovskou stránku
        self.show_home()

    def setup_tray(self):
        try:
            tray_img = Image.open(self.icon_path)
        except Exception as e:
            logging.info(f"Ikonku v {self.icon_path} se nepodařilo načíst: {e}")
            tray_img = Image.new('RGB', (64, 64), color=(31, 83, 141))

        self.tray_icon = pystray.Icon("ContextFlow", tray_img, "ContextFlow", menu=pystray.Menu(
            pystray.MenuItem("Otevřít přehled", self.show_gui),
            pystray.MenuItem("Ukončit", self.quit_app)
        ))
        
        self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self.tray_thread.start()

    def show_gui(self, icon=None, item=None):
        self.after(0, self.deiconify)
        self.after(0, self.focus_force)

    def hide_gui(self):
        self.withdraw()

    def quit_app(self, icon=None, item=None):
        if hasattr(self, 'tray_icon'):
            self.tray_icon.stop()
        self.launcher.quit_app()

    def show_home(self):
        self.clear_main_view()
        self.home_page = HomeFrame(self.main_view, self.aggregator, fg_color="transparent")
        self.home_page.pack(fill="both", expand=True)

    def show_clients(self):
        self.clear_main_view()
        self.clients_page = ClientsFrame(self.main_view, self.aggregator, fg_color="transparent")
        self.clients_page.pack(fill="both", expand=True)

    def show_settings(self):
        self.clear_main_view()
        self.settings_page = SettingsFrame(self.main_view, self.settings, self.launcher, fg_color="transparent")
        self.settings_page.pack(fill="both", expand=True)

    def clear_main_view(self):
        for widget in self.main_view.winfo_children():
            widget.destroy()
