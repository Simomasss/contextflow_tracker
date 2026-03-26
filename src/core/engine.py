import time
from datetime import datetime
from typing import Optional

from ..watchers.window_watcher import WindowWatcher
from ..watchers.afk_watcher import AFKWatcher
from .indexer import IndexManager
from ..database.db_handler import DatabaseManager
from ..core.schemas import ContextMatch

class ContextEngine:
    def __init__(self, watcher: WindowWatcher, indexer: IndexManager, db: DatabaseManager, afk_watcher: AFKWatcher, interval: int = 5):
        """
        :param watcher: Instance WindowWatcheru
        :param indexer: Instance IndexManageru
        :param db: Instance DatabaseManageru
        :param afk_watcher: Instance AFKWatcheru
        :param interval: Jak často (v sekundách) se má kontrolovat aktivita
        """
        self.watcher = watcher
        self.indexer = indexer
        self.db = db
        self.afk_watcher = afk_watcher
        self.interval = interval
        self.is_running = False
        self.current_activity: Optional[ContextMatch] = None
        self.pending_match = None
        self.switch_confirm_count = 0
        self.REQUIRED_CONFIRMATIONS = 3 # Musí se 3x potvrdit stejný kontext, aby se přeplo CHCE VIC FOSHO

    def start(self):
        """Spustí hlavní sledovací smyčku."""
        self.is_running = True
        print("Engine ContextFlow byl spuštěn...")
        try:
            while self.is_running:
                self._tick()
                time.sleep(self.interval)
        except KeyboardInterrupt:
            self.stop()

    def _tick(self):
        """Jeden krok cyklu: Seber data -> Vyhodnoť -> Ulož."""
        if self.afk_watcher.watch(): print ("AFK"); return #Jestli je uživatel AFK, nebudeme dělat nic
        # TODO: Později zde pošleme signál do GUI: "Uživatel je AFK"
        
        window_info = self.watcher.watch()
        if not window_info: return
        
        # Indexer vrací dict, my z něj uděláme ContextMatch objekt
        match_dict = self.indexer.match_title(window_info.title)
        
        if match_dict:
            new_match = ContextMatch(
                client_name=match_dict['client'],
                project_name=match_dict['project']
            )
            print(f"Zachycen kontext: {new_match.client_name} / {new_match.project_name} (okno: {window_info.title})")

            # Stejný kontext
            if self.current_activity and new_match.project_name == self.current_activity.project_name:
                self._write_to_db(new_match, window_info.title)
                self.switch_confirm_count = 0
                print("Stejný projekt jako předtím, záznam aktualizován.")
                print(f"Status: ({self.switch_confirm_count}/{self.REQUIRED_CONFIRMATIONS})")
            else:
                # Logika potvrzování změny
                if self.pending_match and new_match.project_name == self.pending_match.project_name:
                    self.switch_confirm_count += 1
                    print(f"NOVÝ Status: ({self.switch_confirm_count}/{self.REQUIRED_CONFIRMATIONS})")
                else:
                    self.pending_match = new_match
                    self.switch_confirm_count = 1
                    print(f"NOVÝ 2 Status: ({self.switch_confirm_count}/{self.REQUIRED_CONFIRMATIONS})")

                
                if self.switch_confirm_count >= self.REQUIRED_CONFIRMATIONS:
                    self.current_activity = new_match
                    self._write_to_db(new_match, window_info.title)
                    print(f"POTVRZENO Status: ({self.switch_confirm_count}/{self.REQUIRED_CONFIRMATIONS})")
                    #TODO: Po změne by to chtelo ten cekaci cas nekde cacheovat 
                    # a pak ho forcenout do db aby se neztratil konverzni cas

    def _write_to_db(self, match: ContextMatch, title: str):
        self.db.log_activity(match.client_name, match.project_name, title, self.interval)

    def stop(self):
        self.is_running = False
        print("Engine se zastavuje...")

''''
    def _tick(self):
        """Jeden krok cyklu: Seber data -> Vyhodnoť -> Ulož."""
        # 1. Nejdřív zjistíme, jestli uživatel u PC vůbec je
        if self.afk_watcher.watch():
            # TODO: Později zde pošleme signál do GUI: "Uživatel je AFK"
            print("[AFK] Uživatel je neaktivní, trackování pozastaveno.")
            return

        # 2. Pokud není AFK, pokračujeme v normální práci
        window_info = self.watcher.watch()
        if not window_info: return

        match_data = self.indexer.match_title(window_info.title)
        
        if match_data:
            self.db.log_activity(
                client=match_data['client'],
                project=match_data['project'],
                window_title=window_info.title,
                duration=self.interval
            )
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Zapsáno: {match_data['project']}")
        else:
            # Okno je na whitelistu, ale nenalezeno v indexu souborů
            print("Okno je na whitelistu, ale nenalezeno v indexu souborů")
            print(f"Zachycené okno: {window_info.title}")
            pass
'''