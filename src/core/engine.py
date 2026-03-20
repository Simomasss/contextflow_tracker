import time
from datetime import datetime
from typing import Optional

# Importy tvých modulů
from ..watchers.window_watcher import WindowWatcher
from .indexer import IndexManager
from ..database.db_handler import DatabaseManager
from ..core.schemas import ContextMatch

class ContextEngine:
    def __init__(self, watcher: WindowWatcher, indexer: IndexManager, db: DatabaseManager, interval: int = 5):
        """
        :param watcher: Instance WindowWatcheru
        :param indexer: Instance IndexManageru
        :param db: Instance DatabaseManageru (tohle ti chybělo)
        :param interval: Jak často (v sekundách) se má kontrolovat aktivita
        """
        self.watcher = watcher
        self.indexer = indexer
        self.db = db
        self.interval = interval
        self.is_running = False
        self.current_activity: Optional[ContextMatch] = None

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
        window_info = self.watcher.watch()
        
        if not window_info:
            return

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

    def stop(self):
        self.is_running = False
        print("Engine se zastavuje...")