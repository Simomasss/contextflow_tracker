import json
import logging
import os
from dataclasses import dataclass, field, asdict
import sys
from typing import List

@dataclass
class AppSettings:
    # --- VÝCHOZÍ HODNOTY  ---
    MAIN_FOLDER: str = "C:/Users/Doplnte/vasi/pracovni/slozku"
    WHITELIST: List[str] = field(default_factory=lambda: ["Code.exe", "WINWORD.EXE", "Excel.exe", "chrome.exe", "msedge.exe", "powerpnt.exe", "rstudio.exe"])
    ENTRY_MINUTES: float = 1.0
    PROTECTION_MINUTES: float = 5.0
    TICK_INTERVAL: int = 5
    AFK_THRESHOLD: int = 360 # 6 minut nečinnosti = AFK, prodlouženo jako závěr z testování
    DB_URL: str = "sqlite:///contextflow.db"

    def __post_init__(self):
        """Tato metoda se spustí hned po vytvoření objektu AppSettings()."""
        # Najde složku, kde leží spuštěný .exe (nebo .py skript)
        if getattr(sys, 'frozen', False):
            # Režim EXE - složka u .exe
            application_path = os.path.dirname(sys.executable)
        else:
            # Režim skript - skočíme z src/core o dvě úrovně výš do kořene projektu
            current_dir = os.path.dirname(os.path.abspath(__file__)) # src/core
            application_path = os.path.abspath(os.path.join(current_dir, "..", ".."))

        self.config_path = os.path.join(application_path, "settings.json")
        
        if not os.path.exists(self.config_path):
            logging.info(f"Vytvářím výchozí json soubor v: {self.config_path}")
            self.save(self.config_path)
        else:
            self.load(self.config_path)

    def load(self, path="settings.json"):
        """Načte data ze souboru a přepíše výchozí hodnoty."""
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

    def save(self, path="settings.json"):
        """Uloží aktuální nastavení do souboru (budeme potřebovat pro GUI)."""
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