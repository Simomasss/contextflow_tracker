import logging
import os

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ..core.indexer import IndexManager

class IndexUpdateHandler(FileSystemEventHandler):
    """Reaguje na změny v souborovém systému."""
    def __init__(self, indexer: IndexManager):
        self.indexer = indexer

    def on_any_event(self, event):
        # Pokud se vytvoří/smaže/přejmenuje složka, přegenerujeme index
        if event.is_directory:
            self.indexer.reindex()

class FileWatcher:
    """Obal pro watchdog observer."""
    def __init__(self, indexer: IndexManager):
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

    def stop(self):
        self.observer.stop()
        self.observer.join()