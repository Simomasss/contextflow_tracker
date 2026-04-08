import customtkinter as ctk
from .frames.home import HomeFrame
from .frames.clients import ClientsFrame
from .frames.settings import SettingsFrame
from ..core.config import AppSettings
from ..database.db_handler import DatabaseManager
from ..core.aggregator import ActivityAggregator

class ContextFlowGUI(ctk.CTk):
    def __init__(self, launcher):
        super().__init__()

        self.launcher = launcher
        self.settings = launcher.settings 
        self.db = launcher.db
        self.aggregator = ActivityAggregator(self.db)

        # --- 1. NASTAVENÍ A DATABÁZE --- TODO: meli bychom nacitat z configu
        # Tady definujeme stejná nastavení jako v testu
        #self.settings = AppSettings()
        
        # Připojíme se k databázi
        #self.db = DatabaseManager(settings=self.settings, db_url="sqlite:///contextflow.db")
        #self.aggregator = ActivityAggregator(self.db)
        

        # --- 2. ZÁKLADNÍ OKNO ---
        self.title("ContextFlow") # TODO: pridat verzi
        self.geometry("1100x700")

        # Konfigurace gridu
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- 3. SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="ContextFlow", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(pady=20, padx=20)

        self.home_btn = ctk.CTkButton(self.sidebar, text="Home", command=self.show_home)
        self.home_btn.pack(pady=10, padx=20)

        self.clients_btn = ctk.CTkButton(self.sidebar, text="Clients", command=self.show_clients)
        self.clients_btn.pack(pady=10, padx=20)

        self.settings_btn = ctk.CTkButton(self.sidebar, text="Settings", command=self.show_settings)
        self.settings_btn.pack(pady=10, padx=20)

        # --- 4. HLAVNÍ PLOCHA ---
        self.main_view = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_view.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # Spustíme domovskou stránku
        self.show_home()

    def show_home(self):
        self.clear_main_view()
        # Předáme Master, Aggregator a barvu
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