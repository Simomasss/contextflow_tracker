import customtkinter as ctk
from tkinter import filedialog
import os
import sys

def resource_path(relative_path):
    """Pomocná funkce pro získání absolutní cesty k prostředkům."""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

class SetupWindow(ctk.CTk):
    def __init__(self, on_folder_select):
        super().__init__()
        self.title("ContextFlow - Průvodce nastavením")
        self.geometry("550x500")
        self.on_folder_select = on_folder_select
        
        # Ikona okna
        try:
            icon_path = resource_path("src/gui/assets/icon.ico")
            self.iconbitmap(icon_path)
        except:
            pass

        # --- UI OBSAH ---
        ctk.CTkLabel(self, text="Vítejte v ContextFlow!", font=("Arial", 26, "bold")).pack(pady=(30, 10))
        
        # Varování o rané verzi
        warning_frame = ctk.CTkFrame(self, fg_color="#3d2b1f") # Lehce do oranžova
        warning_frame.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(warning_frame, text="⚠️ Aplikace je v rané fázi vývoje", font=("Arial", 12, "bold")).pack(pady=5)

        # Diagram struktury
        diag_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", border_width=1, border_color="#555555")
        diag_frame.pack(fill="x", padx=40, pady=20)
        
        struct_text = (
            "📂 MAIN_SLOZKA (tu vyberete za chvíli)\n"
            " ┗━ 📁 Klient_A\n"
            "     ┗━ 📁 Projekt_X\n"
            "         ┗━ 📄 práce.py  <-- ZDE SE TRACKUJE"
        )
        ctk.CTkLabel(diag_frame, text=struct_text, justify="left", font=("Consolas", 12), padx=20, pady=15).pack()

        # Instrukce
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=40, pady=10)
        
        instr_text = (
            "💡 TIP: Aplikace trackuje pouze programy, které povolíte.\n"
            "Po spuštění běžte do 'Nastavení' a přidejte například:\n"
            "• code.exe (pro VS Code)\n"
            "• pycharm64.exe (pro PyCharm)\n"
            "• chrome.exe (pro web)\n"
            "Pro zjištění .exe názvu stačí napsat do vyhledávače 'aplikace exe name'\n"
            "a tam bude název, který přidáte do whitelistu."
        )
        ctk.CTkLabel(info_frame, text=instr_text, justify="left", font=("Arial", 11), text_color="#bbbbbb").pack()

        # Tlačítko
        self.btn = ctk.CTkButton(
            self, text="POCHOPIL JSEM, VYBRAT SLOŽKU", 
            command=self.select_folder, 
            height=50, font=("Arial", 14, "bold")
        )
        self.btn.pack(pady=40)

    def select_folder(self):
        path = filedialog.askdirectory(title="Vyberte vaši hlavní složku projektů (MAIN)")
        if path:
            self.on_folder_select(path)
            # Nejdříve zastavíme mainloop okna
            self.quit() 
            # A pak ho teprve zničíme - tohle většinou ty errory eliminuje
            self.destroy()