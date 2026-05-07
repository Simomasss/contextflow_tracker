import logging
from pathlib import Path
import re
from typing import Dict, Optional

class IndexManager:
    # TODO: Přidat do configu
    IGNORED_DIR_NAMES = {
        '.git', '.svn', '.hg',              # Verzování
        'node_modules', 'venv', '.venv',    # Závislosti
        '__pycache__', '.pytest_cache',     # Python balast
        '.vscode', '.idea',                 # IDE
        'dist', 'build', 'target',          # Build složky
        'bin', 'obj', 'log'                        # Binární výstupy
    }
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        # Mapa: "jmeno_souboru_nebo_slozky" -> (klient, projekt)
        self.lookup_map: Dict[str, dict] = {}
        self.reindex()

    def reindex(self):
        if not self.root_path.exists(): return
        new_map = {}
        
        for client_dir in self.root_path.iterdir():
            # Ignorujeme skryté složky klientů (začínající tečkou)
            if not client_dir.is_dir() or client_dir.name.startswith('.'):
                continue
            
            for project_dir in client_dir.iterdir():
                # KLÍČOVÝ FIX: Ignorujeme skryté složky projektů (.git, .venv) hned tady
                if not project_dir.is_dir() or project_dir.name.startswith('.') or project_dir.name in self.IGNORED_DIR_NAMES:
                    continue
                
                p_info = {"client": client_dir.name, "project": project_dir.name}
                p_name_key = project_dir.name.lower()
                
                if p_name_key not in new_map: new_map[p_name_key] = []
                new_map[p_name_key].append(p_info)
                
                for item in project_dir.rglob("*"):
                    # Filtry pro soubory uvnitř projektů
                    if any(part.startswith('.') or part in self.IGNORED_DIR_NAMES for part in item.parts):
                        continue
                    
                    if item.is_file():
                        f_key = item.name.lower()
                        if len(f_key) < 4: continue
                        
                        if f_key not in new_map: new_map[f_key] = []
                        if p_info not in new_map[f_key]:
                            new_map[f_key].append(p_info)

        self.lookup_map = new_map
        logging.info(f"Index aktualizován: {len(self.lookup_map)} unikátních klíčů.")

    def match_title(self, window_title: str) -> Optional[dict]:
        if not window_title: 
            return None
            
        title_lower = window_title.lower()
        # Explicitně řekneme, že jde o seznam slovníků
        best_match_projects: list[dict] = []
        max_key_len = 0

        # 1. Najdeme kandidáty (Regex + délka)
        for key, projects in self.lookup_map.items():
            # Regex pro hranice slov (řeší 'Ružu')
            pattern = r"\b" + re.escape(key) + r"\b"
            if re.search(pattern, title_lower):
                if len(key) > max_key_len:
                    max_key_len = len(key)
                    # FIX: Vytvoříme NOVÝ seznam, aby extend neházal chybu
                    # a abychom si neupravili lookup_map
                    best_match_projects = list(projects) 
                elif len(key) == max_key_len and max_key_len > 0:
                    # Tady už extend funguje, protože best_match_projects je zaručeně list
                    best_match_projects.extend(projects)

        if not best_match_projects:
            return None

        # 2. TIE-BREAKER: Pokud je kandidátů víc, zkusíme najít název projektu v titulku
        # snaha o rozlišení mezi projekty, který mají stejný klíč (prace1.docx v projektA + prace1.docx v projektB)
        if len(best_match_projects) > 1:
            for p in best_match_projects:
                if p['project'].lower() in title_lower:
                    return p

        # 3. Vrátíme první nalezený (vždy to bude dict ze seznamu)
        return best_match_projects[0]