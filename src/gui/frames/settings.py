import customtkinter as ctk
from tkinter import messagebox

from src.utils.uninstaller import run_contextflow_uninstaller

class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master, settings, launcher, **kwargs):
        super().__init__(master, **kwargs)
        self.settings = settings
        self.launcher = launcher
        self.entries = {} # Slovník pro snadný přístup k polím

        # Nadpis
        ctk.CTkLabel(self, text="Konfigurace systému", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(10, 20))

        # Vytvoření skrolovací oblasti, kdyby se nastavení nevešla na obrazovku
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # --- SEKCE: CESTY A DATABÁZE ---
        self._add_section_header("Cesty a Systém")
        self._create_setting_field("MAIN_FOLDER", "Složka s projekty (Path):", "Cesta k hlavní složce s vaší prací.")
        self._create_setting_field("DB_URL", "Databázové spojení (URL):", "sqlite:///contextflow.db")

        # --- SEKCE: LOGIKA SLEDOVÁNÍ ---
        self._add_section_header("Logika sledování")
        self._create_setting_field("ENTRY_MINUTES", "Vstupní lhůta (min):", "Jak dlouho čekat, než potvrdíme vstup do kontextu.")
        self._create_setting_field("PROTECTION_MINUTES", "Ochranná lhůta (min):", "Jak dlouho čekat, než potvrdíme změnu kontextu.")
        self._create_setting_field("AFK_THRESHOLD", "AFK limit (sec):", "Doba nečinnosti, po které se stopne měření.")

        # --- SEKCE: FILTRY ---
        self._add_section_header("Filtry procesů")
        self._create_setting_field("WHITELIST", "Povolené procesy (Whitelist):", "Seznam .exe souborů oddělených čárkou.")

        # --- TLAČÍTKO ULOŽIT ---
        self.save_btn = ctk.CTkButton(
            self, 
            text="Uložit všechna nastavení", 
            command=self.save_settings,
            font=ctk.CTkFont(weight="bold"),
            height=40
        )
        self.save_btn.pack(pady=20)

        # Tlačítko odinstalace (dáme ho dospod)
        self.uninstall_btn = ctk.CTkButton(
            self, 
            text="ODINSTALOVAT APLIKACI", 
            fg_color="#721c24", # Tmavě červená (nebezpečí)
            hover_color="#a71d2a",
            command=self.confirm_uninstall
        )
        self.uninstall_btn.pack(pady=(10), side="bottom")

    def _add_section_header(self, text):
        """Pomocná metoda pro vizuální oddělení sekcí."""
        lbl = ctk.CTkLabel(self.scroll_frame, text=text.upper(), font=ctk.CTkFont(size=12, weight="bold"), text_color="gray")
        lbl.pack(anchor="w", pady=(15, 5), padx=5)

    def _create_setting_field(self, key, label_text, placeholder):
        """Vytvoří popisek a vstupní pole pro daný klíč nastavení."""
        container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        container.pack(fill="x", pady=5)

        lbl = ctk.CTkLabel(container, text=label_text, width=200, anchor="w")
        lbl.pack(side="left", padx=5)

        entry = ctk.CTkEntry(container, placeholder_text=placeholder)
        
        # Načtení aktuální hodnoty ze settings objektu
        current_val = getattr(self.settings, key)
        
        # Pokud je to list (Whitelist), převedeme ho na string s čárkami
        if isinstance(current_val, list):
            entry.insert(0, ", ".join(current_val))
        else:
            entry.insert(0, str(current_val))
            
        entry.pack(side="right", fill="x", expand=True, padx=5)
        self.entries[key] = entry

    def save_settings(self):
        """Přečte data z polí, zkonvertuje typy a uloží do JSONu."""
        try:
            # 1. Načtení a konverze dat
            self.settings.MAIN_FOLDER = self.entries["MAIN_FOLDER"].get()
            self.settings.DB_URL = self.entries["DB_URL"].get()
            
            e_min = float(self.entries["ENTRY_MINUTES"].get())
            p_min = float(self.entries["PROTECTION_MINUTES"].get())
            afk_t = int(self.entries["AFK_THRESHOLD"].get())
            
            if e_min <= 0 or p_min <= 0 or afk_t <= 0:
                messagebox.showerror("Chyba", "Časové hodnoty musí být větší než 0.")
                return
                
            self.settings.ENTRY_MINUTES = e_min
            self.settings.PROTECTION_MINUTES = p_min
            self.settings.AFK_THRESHOLD = afk_t
            
            # 2. Zpracování Whitelistu (string -> list)
            whitelist_raw = self.entries["WHITELIST"].get()
            self.settings.WHITELIST = [item.strip() for item in whitelist_raw.split(",") if item.strip()]

            # 3. Uložení do souboru
            self.settings.save()
            
            # 4. Aplikování změn za běhu (pokud byl předán launcher)
            if self.launcher:
                self.launcher.apply_settings()
            else:
                messagebox.showinfo("Úspěch", "Nastavení uloženo. (Pro propsání je nutný restart)")

        except ValueError as e:
            messagebox.showerror("Chyba", "Zkontrolujte číselné hodnoty (Vstupní lhůta, Ochranná lhůta, AFK musí být čísla).")
        except Exception as e:
            messagebox.showerror("Chyba", f"Nepodařilo se uložit nastavení: {e}")

    def confirm_uninstall(self):
        # Dvojité potvrzení, aby se tester neuklikl
        msg = (
            "Opravdu chcete ContextFlow odinstalovat?\n\n"
            "• Aplikace se smaže (EXE)\n"
            "• Nastavení se vymaže\n"
            "• Automatické spouštění se zruší\n\n"
            "Poznámka:\nDatabáze a logy zůstanou zachovány pro účely analýzy.\n"
            "Po odinstalaci pěkně prosím o poslání databáze a logů\n"
            "Pokud máte i nějakou zpětnou vazbu, budu rád, když se o ni podělíte!\n\n"
            "Děkuji moc za testování a pomoc s vývojem! 🙏"
        )
        
        answer = messagebox.askyesno("Potvrdit odinstalaci", msg)
        if answer:
            run_contextflow_uninstaller()