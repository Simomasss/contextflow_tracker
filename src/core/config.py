import json
import logging
import os
from dataclasses import dataclass, field, asdict
import sys
from typing import List

from src.utils.paths import get_app_data_dir

@dataclass
class AppSettings:
    # --- VÝCHOZÍ HODNOTY  ---
    MAIN_FOLDER: str = "C:/Users/Doplnte/vasi/pracovni/slozku"
    WHITELIST: List[str] = field(default_factory=lambda: ["Code.exe", "WINWORD.EXE", "Excel.exe", "chrome.exe", "msedge.exe", "powerpnt.exe", "rstudio.exe"])
    ENTRY_MINUTES: float = 1.0
    PROTECTION_MINUTES: float = 5.0
    TICK_INTERVAL: int = 5
    AFK_THRESHOLD: int = 360 # 6 minut nečinnosti = AFK, prodlouženo jako závěr z testování
    DB_URL: str = "" # Nastaví se v post_init

    def __post_init__(self):
        """Tato metoda se spustí hned po vytvoření objektu AppSettings()."""
        app_data_dir = get_app_data_dir()
        os.makedirs(app_data_dir, exist_ok=True)
        
        # Nastavení defaultní DB_URL, pokud není v json (nebo nastavíme základní)
        default_db_path = os.path.join(app_data_dir, "contextflow.db")
        # Pro SQLAlchemy sqlite url potřebuje trojité lomítko pro relativní nebo absolutní cesty na Unixu, na Windows čtyřité nebo trojité
        # Lepší je formát `sqlite:///{absolutni_cesta}`
        self.DB_URL = f"sqlite:///{default_db_path}"

        self.config_path = os.path.join(app_data_dir, "settings.json")
        
        if not os.path.exists(self.config_path):
            logging.info(f"Vytvářím výchozí json soubor v: {self.config_path}")
            self.save(self.config_path)
        else:
            self.load(self.config_path)

    def load(self, path=None):
        """Načte data ze souboru a přepíše výchozí hodnoty."""
        if path is None:
            path = self.config_path
            
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    # Validace a bezpečné přiřazení
                    if "MAIN_FOLDER" in data and isinstance(data["MAIN_FOLDER"], str):
                        self.MAIN_FOLDER = data["MAIN_FOLDER"]
                    if "DB_URL" in data and isinstance(data["DB_URL"], str):
                        self.DB_URL = data["DB_URL"]
                    if "WHITELIST" in data and isinstance(data["WHITELIST"], list):
                        self.WHITELIST = [str(item) for item in data["WHITELIST"]]
                        
                    # Ošetření čísel a záporných hodnot/nul
                    if "ENTRY_MINUTES" in data and isinstance(data["ENTRY_MINUTES"], (int, float)):
                        self.ENTRY_MINUTES = max(0.1, float(data["ENTRY_MINUTES"]))
                    if "PROTECTION_MINUTES" in data and isinstance(data["PROTECTION_MINUTES"], (int, float)):
                        self.PROTECTION_MINUTES = max(0.1, float(data["PROTECTION_MINUTES"]))
                    if "TICK_INTERVAL" in data and isinstance(data["TICK_INTERVAL"], (int, float)):
                        self.TICK_INTERVAL = max(1, int(data["TICK_INTERVAL"]))
                    if "AFK_THRESHOLD" in data and isinstance(data["AFK_THRESHOLD"], (int, float)):
                        self.AFK_THRESHOLD = max(10, int(data["AFK_THRESHOLD"]))
                        
                # logging.info(f"✓ Nastavení načteno ze souboru {path}")
            except Exception as e:
                logging.warning(f"⚠ Chyba při načítání settings.json: {e}")

    def save(self, path=None):
        """Uloží aktuální nastavení do souboru (budeme potřebovat pro GUI)."""
        if path is None:
            path = self.config_path
        with open(path, "w", encoding="utf-8") as f:
            # Převedeme dataclass na slovník, ale vynecháme @property
            json.dump(asdict(self), f, indent=4)

    # --- ODVOZENÉ PROMĚNNÉ ---
    @property
    def CONFIRM_START_TICKS(self) -> int:
        ticks = (self.ENTRY_MINUTES * 60) / self.TICK_INTERVAL
        return max(1, int(round(ticks)))

    @property
    def CONFIRM_EXIT_TICKS(self) -> int:
        ticks = (self.PROTECTION_MINUTES * 60) / self.TICK_INTERVAL
        return max(1, int(round(ticks)))
    # Přidáno zaokrouhlení a zajištění, že to bude alespoň 1 tick, aby se předešlo dělení nulou nebo příliš krátkým intervalům.

    @property
    def MAX_GAP_FOR_MERGE(self) -> int:
        return int(self.PROTECTION_MINUTES * 60) + 10 # 10sekund jako buffer