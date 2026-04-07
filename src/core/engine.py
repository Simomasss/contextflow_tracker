import logging
import time
from datetime import datetime
from typing import Optional

from ..watchers.window_watcher import WindowWatcher
from ..watchers.afk_watcher import AFKWatcher
from .indexer import IndexManager
from ..database.db_handler import DatabaseManager
from ..core.schemas import WindowInfo, ContextMatch
from ..core.config import AppSettings

class ContextEngine:
    def __init__(self, watcher: WindowWatcher, indexer: IndexManager, db: DatabaseManager, afk_watcher: AFKWatcher, settings: AppSettings):
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

        self.current_activity: Optional[ContextMatch] = None # Aktuálně sledovaný projekt (ten, ke kterému logujeme čas)
        self.pending_activity: Optional[ContextMatch] = None # Projekt, který se "rýsuje" jako nový, ale ještě nemáme potvrzeno, že tam opravdu jsme
        self.timer = 0 # Počítadlo ticků pro potvrzení změny

        self.is_running = False

#TODO: pro pripad, kdyz force ukoncovani
    def start(self):
        """Spustí hlavní sledovací smyčku."""
        self.is_running = True
        logging.info(f"Engine ContextFlow byl spuštěn... interval je {self.settings.TICK_INTERVAL} sekund.")
        try:
            while self.is_running:
                self._tick()
                time.sleep(self.settings.TICK_INTERVAL) # Nastavitelný interval mezi tickem (např. 5 sekund)
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
        now_str = datetime.now().strftime('%H:%M:%S')
        
        # 1. AFK KONTROLA
        if self.afk_watcher.watch():
            if self.current_activity:
                logging.info(f"[{now_str}] [AFK] Detekován klid. Resetuji sledování.")
            self.current_activity = None
            self.timer = 0
            return

        # --- VSTUP (Co Engine vidí) ---
        window = self.watcher.watch()
        match_dict = self.indexer.match_title(window.title) if (window and window.is_whitelisted) else None
        
        # Pomocné texty pro hezký print
        win_text = f"'{window.title[:40]}...'" if window else "ŽÁDNÉ OKNO"
        target_text = f"-> {match_dict['project']}" if match_dict else "-> MIMO INDEX"
        
        # TENTO PRINT BĚŽÍ VŽDY:
        logging.info(f"[{now_str}] [TICK] Sleduji: {win_text} {target_text}")

        new_match = None
        if match_dict:
            new_match = ContextMatch(client_name=match_dict['client'], project_name=match_dict['project'])

        # --- AKCE (Co Engine udělá) ---

        # 1. JSME V AKTUÁLNÍM PROJEKTU (Ideální stav)
        if self.current_activity and new_match and new_match.project_name == self.current_activity.project_name:
            if self.timer > 0:
                logging.info(f"[{now_str}] [BACK] Návrat k: {self.current_activity.project_name}")
            
            self.timer = 0 
            self.pending_activity = None
            self._write_to_db(self.current_activity, window)
            # Volitelný print pro potvrzení zápisu:
            # logging.info(f"[{now_str}] [OK] Prodloužen log pro {self.current_activity.project_name}")
            return

        # 2. JSME JINDE (Jiný projekt nebo mimo pracovní nástroje)
        if new_match != self.pending_activity:
            if self.pending_activity or new_match: # Logujeme jen reálné změny
                logging.info(f"[{now_str}] [INFO] Změna kandidáta. Resetuji časovač potvrzení.")
            self.timer = 0
            self.pending_activity = new_match
        
        self.timer += 1

        # A) OCHRANNÁ LHŮTA (Inspirace / Grace)
        if self.timer < self.settings.REQUIRED_CONFIRMATIONS:
            if self.current_activity:
                reason = "INSPIRACE" if new_match else "GRACE"
                logging.info(f"[{now_str}] [{reason}] {self.timer}/{self.settings.REQUIRED_CONFIRMATIONS} | Stále loguji: {self.current_activity.project_name}")
                
                grace_window = WindowInfo(title="Grace Period", executable="Unknown", is_whitelisted=False)
                self._write_to_db(self.current_activity, grace_window)
            else:
                # Nemáme rozdělanou práci a nejsme v indexu
                logging.info(f"[{now_str}] [IDLE] Čekám na pracovní kontext... ({self.timer}/{self.settings.REQUIRED_CONFIRMATIONS})")
        
        # B) LIMIT VYPRŠEL (Čistý řez)
        else:
            if self.pending_activity:
                logging.info(f"[{now_str}] [SWITCH] Přepínám na: {self.pending_activity.project_name}")
                self.current_activity = self.pending_activity
                self._write_to_db(self.current_activity, window)
            else:
                if self.current_activity:
                    logging.info(f"[{now_str}] [STOP] Limit vypršel. Tracking vypnut.")
                self.current_activity = None
            
            self.timer = 0
            self.pending_activity = None

    def stop(self):
        self.is_running = False
        logging.info("Engine se zastavuje...")