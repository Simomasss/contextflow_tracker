import logging
import os
from pathlib import Path
import threading

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class IndexUpdateHandler(FileSystemEventHandler):
    """Reaguje na změny v souborovém systému s využitím debouncingu."""
    def __init__(self, indexer, delay=2.0):
        self.indexer = indexer
        self.delay = delay
        self.timer = None

    def on_any_event(self, event):
        raw_path = event.src_path
        
        if isinstance(raw_path, (bytes, bytearray)):
            clean_path = raw_path.decode('utf-8', errors='replace')
        else:
            clean_path = str(raw_path)

        path = Path(clean_path)
        
        # 1. FILTR: Ignorujeme contextflow
        if "contextflow" in path.name.lower():
            return

        # 2. FILTR: Ignorujeme vnitřní soubory
        if path.suffix in ['.log', '.db', '.json']:
            return

        # 3. FILTR: Ignorujeme skryté složky
        if any(part.startswith('.') for part in path.parts):
            return

        # 4. AKCE: Pokud se změnilo cokoliv jiného a je to složka
        if event.is_directory:
            self._schedule_reindex(path.name)

    def _schedule_reindex(self, folder_name):
        """Zruší předchozí časovač a spustí nový."""
        if self.timer is not None:
            self.timer.cancel()
        
        # Vytvoříme nový časovač. Po uplynutí self.delay zavolá self._do_reindex
        self.timer = threading.Timer(self.delay, self._do_reindex, [folder_name])
        self.timer.start()

    def _do_reindex(self, folder_name):
        """Samotná operace reindexace po uplynutí klidového intervalu."""
        logging.info(f"[FILE_WATCHER] Klidový interval vypršel (změna v: {folder_name}). Reindexuji...")
        self.indexer.reindex()
        self.timer = None

class FileWatcher:
    """Obal pro watchdog observer."""
    def __init__(self, indexer):
        self.indexer = indexer
        self.observer = Observer()
        self.handler = IndexUpdateHandler(self.indexer)

    def start(self):
        path_to_watch = str(self.indexer.root_path)
        if not os.path.exists(path_to_watch):
            logging.info(f"⚠️ VAROVÁNÍ: Složka {path_to_watch} neexistuje. FileWatcher se nespustí.")
            return

        self.observer.schedule(self.handler, path_to_watch, recursive=True)
        self.observer.start()
        logging.info(f"[FILE_WATCHER] Sledování spuštěno pro: {path_to_watch}")

    def stop(self):
        self.observer.stop()
        self.observer.join()