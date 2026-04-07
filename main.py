import logging
import time
from src.database.db_handler import DatabaseManager
from src.core.indexer import IndexManager
from src.watchers.afk_watcher import AFKWatcher
from src.watchers.window_watcher import WindowWatcher
from src.watchers.file_watcher import FileWatcher
from src.core.engine import ContextEngine
from src.core.config import AppSettings

def main():
    # Nastavení
    settings = AppSettings()

    # 1. Inicializace a předání nastavení
    db = DatabaseManager(settings=settings)
    indexer = IndexManager(settings.MAIN_FOLDER)
    watcher = WindowWatcher(settings.WHITELIST)
    afk = AFKWatcher(threshold_seconds=settings.AFK_THRESHOLD)
    
    # 2. FILE WATCHER - Musíme ho vytvořit a SPUSTIT
    fw = FileWatcher(indexer)
    fw.start()  # <--- Tady začíná sledovat změny na disku
    logging.info(f"Sleduji změny ve složce: {settings.MAIN_FOLDER}")

    # 3. ENGINE
    engine = ContextEngine(watcher, indexer, db, afk_watcher=afk, settings=settings)
    
    try:
        logging.info("Aplikace běží. Pro ukončení stiskni Ctrl+C.")
        engine.start()
    except KeyboardInterrupt:
        logging.info("\nUkončování...")
    finally:
        # Důležité: Vždy musíme zastavit file watcher, jinak proces zůstane viset
        fw.stop()
        logging.info("FileWatcher zastaven. Nashledanou!")

if __name__ == "__main__":
    main()