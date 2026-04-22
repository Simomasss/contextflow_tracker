import json
import logging
import os
from dataclasses import dataclass, field, asdict
import sys
from typing import List

@dataclass
class AppSettings:
    # --- VÝCHOZÍ HODNOTY (Defaults) ---
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
            self.save()
        else:
            self.load()

    def load(self, path="settings.json"):
        """Načte data ze souboru a přepíše výchozí hodnoty."""
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
                # logging.info(f"✓ Nastavení načteno ze souboru {path}")
            except Exception as e:
                logging.info(f"⚠ Chyba při načítání settings.json: {e}")

    def save(self, path="settings.json"):
        """Uloží aktuální nastavení do souboru (budeme potřebovat pro GUI)."""
        with open(path, "w", encoding="utf-8") as f:
            # Převedeme dataclass na slovník, ale vynecháme @property
            json.dump(asdict(self), f, indent=4)

    # --- ODVOZENÉ PROMĚNNÉ (Properties zůstávají stejné) ---
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