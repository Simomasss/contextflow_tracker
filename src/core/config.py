import json
import os
from dataclasses import dataclass, field, asdict
from typing import List

@dataclass
class AppSettings:
    # --- VÝCHOZÍ HODNOTY (Defaults) ---
    MAIN_FOLDER: str = "C:/Users/Doplnte/vasi/pracovni/slozku"
    WHITELIST: List[str] = field(default_factory=lambda: ["Code.exe", "WINWORD.EXE", "Excel.exe", "chrome.exe"])
    PROTECTION_MINUTES: float = 1.0
    TICK_INTERVAL: int = 5
    AFK_THRESHOLD: int = 300
    DB_URL: str = "sqlite:///contextflow.db"

    def __post_init__(self):
        """Tato metoda se spustí hned po vytvoření objektu AppSettings()."""
        self.config_path = "settings.json"
        
        # CHYTRÁ LOGIKA:
        if not os.path.exists(self.config_path):
            # Pokud JSON neexistuje, vytvoříme ho z těchto výchozích hodnot
            print(f"首次 spuštění: Vytvářím výchozí {self.config_path}")
            self.save()
        else:
            # Pokud existuje, načteme ho
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
                # print(f"✓ Nastavení načteno ze souboru {path}")
            except Exception as e:
                print(f"⚠ Chyba při načítání settings.json: {e}")

    def save(self, path="settings.json"):
        """Uloží aktuální nastavení do souboru (budeme potřebovat pro GUI)."""
        with open(path, "w", encoding="utf-8") as f:
            # Převedeme dataclass na slovník, ale vynecháme @property
            json.dump(asdict(self), f, indent=4)

    # --- ODVOZENÉ PROMĚNNÉ (Properties zůstávají stejné) ---
    @property
    def REQUIRED_CONFIRMATIONS(self) -> int:
        return int((self.PROTECTION_MINUTES * 60) // self.TICK_INTERVAL)

    @property
    def MAX_GAP_FOR_MERGE(self) -> int:
        return int(self.PROTECTION_MINUTES * 60)



'''
from dataclasses import dataclass, field
from typing import List

@dataclass
class AppSettings:
    # --- CESTY (To uživatel musí zadat) ---
    MAIN_FOLDER: str = "C:/Users/donth/VSE/BAKALARKA/MAIN"
    WHITELIST: List[str] = field(default_factory=lambda: ["Code.exe", "WINWORD.EXE", "Excel.exe"])

    # --- HLAVNÍ NASTAVENÍ (Jediná věc, kterou uživatel ladí) ---
    # Jak dlouho (v minutách) tolerujeme "odskoky" jinam, než to definitivně přepneme
    PROTECTION_MINUTES: float = 3.0
    
    # Jak často aplikace kontroluje okna (sekundy) - technické nastavení
    TICK_INTERVAL: int = 5
    
    # Za jak dlouho se stopne čas při nečinnosti (sekundy)
    AFK_THRESHOLD: int = 300

    # --- ODVOZENÉ PROMĚNNÉ (Matematika, kterou uživatel neřeší) ---
    @property
    def REQUIRED_CONFIRMATIONS(self) -> int:
        """Kolik ticků musí proběhnout pro přepnutí kontextu."""
        return int((self.PROTECTION_MINUTES * 60) // self.TICK_INTERVAL)

    @property
    def MAX_GAP_FOR_MERGE(self) -> int:
        """Maximální mezera v sekundách, kterou v DB ještě spojíme do jednoho bloku."""
        return int(self.PROTECTION_MINUTES * 60)
'''