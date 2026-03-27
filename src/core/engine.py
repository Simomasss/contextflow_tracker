import time
from datetime import datetime
from typing import Optional

from ..watchers.window_watcher import WindowWatcher
from ..watchers.afk_watcher import AFKWatcher
from .indexer import IndexManager
from ..database.db_handler import DatabaseManager
from ..core.schemas import WindowInfo, ContextMatch

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
        self.pending_start_time = None # Kdy jsme poprvé viděli potencionální změnu
        self.switch_confirm_count = 0
        # NASTAVENÍ
        self.REQUIRED_CONFIRMATIONS = 4 # Musí se potvrdit stejný kontext, aby se přeplo 1*interval
        self.GRACE_PERIOD_SECONDS = 120   # Sekundy grace period při odchodu z práce

    def _write_to_db(self, match: ContextMatch, window: Optional[WindowInfo], custom_start: Optional[datetime] = None):
        """
        Obal pro DB handler, který zvládne i chybějící informace o okně.
        """
        # Pokud nemáme window_info (jsme mimo whitelist), použijeme náhradní texty
        title = window.title if window else "Mimo whitelist"
        exe = window.executable if window else "Unknown"

        self.db.log_activity(
            client_name=match.client_name,
            project_name=match.project_name,
            window_title=title,
            executable=exe,
            interval_sec=self.interval,
            custom_start=custom_start
        )

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
        now = datetime.now()
        if self.afk_watcher.watch():
            self.current_activity = None  # Resetujeme aktuální aktivitu, protože uživatel je pryč
            print("AFK"); return
        
        window_info = self.watcher.watch()
        # Pokud není okno na WHITELIST = match_dict = None -- Potřebné pro grace period
        match_dict = self.indexer.match_title(window_info.title) if window_info else None

        # --- LOGIKA ROZHODOVÁNÍ ---
        if match_dict:
            new_match = ContextMatch(
                client_name=match_dict['client'],
                project_name=match_dict['project']
            )
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Vidíme: {new_match.project_name}")

            # A) JSME VE STEJNÉM PROJEKTU
            if self.current_activity and new_match.project_name == self.current_activity.project_name:
                self._write_to_db(new_match, window_info)
                self.pending_match = None
                self.switch_confirm_count = 0
                print(f"SAME: ({self.switch_confirm_count}/{self.REQUIRED_CONFIRMATIONS})")
                return

            # B) POTENCIÁLNÍ ZMĚNA (Inspirace / Přechod)
            if self.pending_match and new_match.project_name == self.pending_match.project_name:
                self.switch_confirm_count += 1
                print(f"STATUS: ({self.switch_confirm_count}/{self.REQUIRED_CONFIRMATIONS})")
            else:
                self.pending_match = new_match
                self.pending_start_time = now
                self.switch_confirm_count = 1
                print(f"ZMĚNA-PROBÍHÁ: ({self.switch_confirm_count}/{self.REQUIRED_CONFIRMATIONS})")

            # B1) Ještě jsme nepotvrdili změnu -> STÁLE LOGUJEME PŮVODNÍ PROJEKT
            if self.switch_confirm_count < self.REQUIRED_CONFIRMATIONS:
                if self.current_activity:
                    # Během inspirace logujeme čas k původnímu projektu, 
                    # ale NEPOSÍLÁME tam window_info z toho nového okna (necháme None),
                    # aby se v DB nepřepsal Window Title na ten "neznámý".
                    self._write_to_db(self.current_activity, None) #None/window_info
                    print(f"ZMĚNA-LOGUJEME PŮVODNÍ: ({self.switch_confirm_count}/{self.REQUIRED_CONFIRMATIONS})")
            
            # B2) POTVRZENÍ ZMĚNY
            else:
                self.current_activity = new_match
                self._write_to_db(new_match, window_info, custom_start=self.pending_start_time)
                self.switch_confirm_count = 0
                self.pending_match = None
                print(f"ZMĚNA POTVRZENA: ({self.switch_confirm_count}/{self.REQUIRED_CONFIRMATIONS})")

        else:
            # C) NEJSME NA WHITELISTU NEBO ŽÁDNÁ SHODA = GRACE PERIOD
            if self.current_activity:
                # Tady je změna: window_info posíláme jen tehdy, pokud 
                # chceme, aby se přepsal titulek. V Grace periodě raději 
                # pošleme None, aby DB handler věděl, že nemá titulek měnit.
                self._write_to_db(self.current_activity, None)
                print(f"NEJSME V INDEXU/WHITELISTU, LOGUJEME PUVODNI (GRACE): ({self.switch_confirm_count}/{self.REQUIRED_CONFIRMATIONS})")

                # Poznámka: Aby to nebylo nekonečné, musíme v _write_to_db 
                # kontrolovat časový rozdíl (vyřešíme v DB handleru).


    def stop(self):
        self.is_running = False
        print("Engine se zastavuje...")


''''
                print(f"ZAPSÁNO SAME: ({self.switch_confirm_count}/{self.REQUIRED_CONFIRMATIONS})")
                print(f"Status: ({self.switch_confirm_count}/{self.REQUIRED_CONFIRMATIONS})")

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