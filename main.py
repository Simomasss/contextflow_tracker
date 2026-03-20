'''
from src.watchers.window_watcher import WindowWatcher
from src.core.indexer import IndexManager
from src.core.engine import ContextEngine
from src.watchers.file_watcher import FileWatcher
from src.database.db_handler import DatabaseManager

def main():
    # 1. Vytvoříme databázi (vytvoří soubor contextflow.db v rootu projektu)
    db = DatabaseManager() 
    
    # 2. Vytvoříme indexer a watcher
    indexer = IndexManager("C:/Users/donth/VSE/BAKALARKA/MAIN" )
    watcher = WindowWatcher(whitelist=["Code.exe", "WINWORD.EXE", "chrome.exe", "Figma.exe"])
    
    # 3. Předáme VŠECHNY tři kousky Enginu
    engine = ContextEngine(watcher, indexer, db, interval=5)
    
    engine.start()

if __name__ == "__main__":
    main()
'''

# main.py
import time
from src.database.db_handler import DatabaseManager
from src.core.indexer import IndexManager
from src.watchers.window_watcher import WindowWatcher
from src.watchers.file_watcher import FileWatcher # Importujeme!
from src.core.engine import ContextEngine

def main():
    # Nastavení
    MAIN_FOLDER = "C:/Users/donth/VSE/BAKALARKA/MAIN"  # Uprav na svou cestu
    WHITELIST = ["Code.exe", "WINWORD.EXE", "chrome.exe", "Excel.exe", "Figma.exe"]

    # 1. Inicializace
    db = DatabaseManager()
    indexer = IndexManager(MAIN_FOLDER)
    watcher = WindowWatcher(whitelist=WHITELIST)
    
    # 2. FILE WATCHER - Musíme ho vytvořit a SPUSTIT
    fw = FileWatcher(indexer)
    fw.start()  # <--- Tady začíná sledovat změny na disku
    print(f"Sleduji změny ve složce: {MAIN_FOLDER}")

    # 3. ENGINE
    engine = ContextEngine(watcher, indexer, db, interval=5)
    
    try:
        print("Aplikace běží. Pro ukončení stiskni Ctrl+C.")
        engine.start()
    except KeyboardInterrupt:
        print("\nUkončování...")
    finally:
        # Důležité: Vždy musíme zastavit file watcher, jinak proces zůstane viset
        fw.stop()
        print("FileWatcher zastaven. Nashledanou!")

if __name__ == "__main__":
    main()