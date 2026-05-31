import logging
import threading
from datetime import datetime
from typing import Optional

from ..watchers.window_watcher import BaseWindowWatcher
from ..watchers.afk_watcher import AFKWatcher
from .indexer import IndexManager
from ..database.db_handler import DatabaseManager
from ..core.schemas import WindowInfo, ContextMatch
from ..core.config import AppSettings

class ContextEngine:
    def __init__(self, watcher: BaseWindowWatcher, indexer: IndexManager, db: DatabaseManager, afk_watcher: AFKWatcher, settings: AppSettings):
        """
        :param watcher: Instance WindowWatcheru
        :param indexer: Instance IndexManageru
        :param db: Instance DatabaseManageru
        :param afk_watcher: Instance AFKWatcheru
        :param settings: Instance globálního nastavení
        """
        self.watcher = watcher
        self.indexer = indexer
        self.db = db
        self.afk_watcher = afk_watcher
        self.settings = settings

        self.current_activity: Optional[ContextMatch] = None # Aktuálně sledovaný projekt
        self.pending_activity: Optional[ContextMatch] = None # Možná nový kontext, který čeká na potvrzení
        self.timer = 0 

        self._stop_event = threading.Event()
        self.is_running = False

    def start(self):
        """Spustí hlavní sledovací smyčku."""
        self.is_running = True 
        logging.info(f"Engine ContextFlow byl spuštěn... interval je {self.settings.TICK_INTERVAL} sekund.")
        try:
            while self.is_running:
                self._tick()
                self._stop_event.wait(self.settings.TICK_INTERVAL)
        except KeyboardInterrupt:
            self.stop()
    
    def _write_to_db(self, match: ContextMatch, window: Optional[WindowInfo]):
        """
        Pomocník pro zápis, který ošetřuje chybějící window_info.
        """
        title = window.title if (window and window.title) else "Mimo whitelist/index"
        exe = window.executable if (window and window.executable) else "Unknown"

        self.db.log_activity(
            client_name=match.client_name,
            project_name=match.project_name,
            window_title=title,
            executable=exe,
        )

    def _tick(self):
        """
        Hlavní logika, heartbeat engine, který přiřazuje kontext a zapisuje do DB. Je volán každých TICK_INTERVAL sekund.
        Logika: 1) Kontrola AFK, 2) Získání aktuálního okna a pokus o match, 3) Rozhodnutí, jestli jsme v IDLE nebo EXIT režimu, 4) Inkrementace timeru, 5) Pokud timer překročí limit, potvrdíme změnu kontextu.
        """
        now_str = datetime.now().strftime('%H:%M:%S')
        
        # --- A. AFK KONTROLA ---
        if self.afk_watcher.watch():
            # Logujeme jen pokud jsme nejsme AFK
            if self.current_activity or self.timer > 0:
                status = f"relaci {self.current_activity.project_name}" if self.current_activity else "čekání na potvrzení"
                logging.info(f"[{now_str}] [AFK] Detekován klid. Ruším {status}.")
            
            # Reset všeho
            self.current_activity = None
            self.timer = 0
            self.pending_activity = None
            return

        # --- B. VSTUP A MATCHING ---
        window = self.watcher.watch()

        if window:
            match_dict = self.indexer.match_title(window.title) if window.is_whitelisted else None
            
            new_match = None
            if match_dict:
                new_match = ContextMatch(client_name=match_dict['client'], project_name=match_dict['project'])
                logging.info(f"[MATCH] '{window.title}'") # ({window.executable}) -> [KLIENT]: {new_match.client_name} [PROJEKT]: {new_match.project_name}
        else:
            match_dict = None
            new_match = None

        # --- C. NÁVRAT DOMŮ (Záchranná brzda) ---
        # Pokud jsme v rozdělané práci, okamžitě resetujeme timer a jedeme dál
        if self.current_activity and new_match and new_match.project_name == self.current_activity.project_name:
            if self.timer > 0:
                logging.info(f"[{now_str}] [BACK] Návrat k hlavní práci: {self.current_activity.project_name}")
            self.timer = 0 
            self.pending_activity = None
            self._write_to_db(self.current_activity, window)
            return

        # --- D. LOGIKA RESETOVÁNÍ TIMERU (Klíčová změna) ---
        if self.current_activity is None:
            # Režim START:
            # Pokud nic neděláme, každá změna okna musí resetovat timer, 
            # abychom potvrdili, že na tom novém okně fakt jsme (např. 1 minutu).
            if new_match != self.pending_activity:
                logging.info(f"[{now_str}] [IDLE] Změna cíle na: {new_match.project_name if new_match else 'NIC'}. Reset timeru.")
                self.timer = 0
                self.pending_activity = new_match
        else:
            # Režim EXIT:
            # Pokud jsme mimo hlavní projekt. Jen si poznamenáme, co je "pending", 
            # aby SWITCH věděl, kam pak případně skočit.
            if new_match != self.pending_activity:
                logging.info(f"[{now_str}] [INFO] Změna aktivity během exitu: {self.pending_activity.project_name if self.pending_activity else 'GRACE'} -> {new_match.project_name if new_match else 'GRACE'}")
                self.pending_activity = new_match
                # TIMER TADY NESMÍ BÝT RESETOVÁN NA 0

        # Inkrementace timeru (společná pro oba režimy)
        self.timer += 1

        # --- E. URČENÍ LIMITU ---
        limit = self.settings.CONFIRM_EXIT_TICKS if self.current_activity else self.settings.CONFIRM_START_TICKS

        # --- F. ČEKACÍ LHŮTA (Vykreslování stavu) ---
        if self.timer < limit:
            if self.current_activity:
                # Režim OCHRANY (Grace/Inspirace)
                reason = "INSPIRACE" if new_match else "GRACE"
                logging.info(f"[{now_str}] [{reason}] {self.timer}/{limit} | Stále držím: {self.current_activity.project_name}")
                
                # Zápis do DB pod původním projektem (dokud nevyprší limit)
                grace_window = WindowInfo(title="Grace Period", executable="Unknown", is_whitelisted=False)
                self._write_to_db(self.current_activity, grace_window)
            else:
                # Čekáme na první potvrzení nové práce
                target = self.pending_activity.project_name if self.pending_activity else "něco z indexu"
                logging.info(f"[{now_str}] [IDLE] Čekám na potvrzení: {target} ({self.timer}/{limit})")
        
        # --- G. LIMIT VYPRŠEL (Akce) ---
        else:
            if self.pending_activity:
                logging.info(f"[{now_str}] [SWITCH] Potvrzeno. Přepínám na: {self.pending_activity.project_name}")
                self.current_activity = self.pending_activity
                self._write_to_db(self.current_activity, window)
            else:
                if self.current_activity:
                    logging.info(f"[{now_str}] [STOP] Čas vypršel. Uživatel definitivně opustil kontext.")
                self.current_activity = None
            
            # Kompletní úklid
            self.timer = 0
            self.pending_activity = None

    def stop(self):
        self.is_running = False
        self._stop_event.set()
        logging.info("Engine se zastavuje...")