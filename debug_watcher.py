import time
import re
import sys

# Přidáme aktuální složku do cesty, aby fungovaly importy
sys.path.append('.')

from src.watchers.window_watcher import get_window_watcher
from src.core.indexer import IndexManager
from src.core.config import AppSettings

def main():
    print("--- Startuji ContextFlow Debug Watcher ---")
    settings = AppSettings()
    
    watcher = get_window_watcher(settings.WHITELIST)
    indexer = IndexManager(settings.MAIN_FOLDER)
    
    print(f"Index úspěšně načten. Obsahuje {len(indexer.lookup_map)} unikátních klíčů.")
    print("Sleduji okna každých 10 sekund. Pro ukončení stiskni Ctrl+C.\n")
    
    try:
        while True:
            window = watcher.watch()
            print("-" * 60)
            if not window:
                print("Žádné aktivní okno nezachyceno (nebo nelze přečíst).")
            else:
                print(f"[OKNO] Titulek:    '{window.title}'")
                print(f"[OKNO] Proces:     '{window.executable}'")
                print(f"[OKNO] Whitelist:  {window.is_whitelisted}")
                
                if window.is_whitelisted and window.title:
                    title_lower = window.title.lower()
                    matched_candidates = []
                    
                    for key, projects in indexer.lookup_map.items():
                        pattern = r"\b" + re.escape(key) + r"\b"
                        if re.search(pattern, title_lower):
                            rarity_score = 1.0 / len(projects)
                            matched_candidates.append({
                                "key": key, "projects": projects, "rarity": rarity_score, "length": len(key)
                            })
                            
                    if not matched_candidates:
                        print("[MATCH] Žádná shoda s indexem.")
                    else:
                        print(f"[MATCH] Nalezeno kandidátů: {len(matched_candidates)}")
                        matched_candidates.sort(key=lambda x: (x["rarity"], x["length"]), reverse=True)
                        
                        for i, cand in enumerate(matched_candidates):
                            projects_str = ", ".join([f"{p['client']}/{p['project']}" for p in cand['projects']])
                            print(f"  {i+1}. Klíč: '{cand['key']}' | Váha: {cand['rarity']:.2f} | Výskyty ({len(cand['projects'])}): [{projects_str}]")
                            
                        best = indexer.match_title(window.title)
                        if best:
                            print(f"\n[VÍTĚZ] -> Klient: {best['client']} | Projekt: {best['project']} (Klíč: '{best['matched_key']}')")
            
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nUkončeno uživatelem.")

if __name__ == "__main__":
    main()