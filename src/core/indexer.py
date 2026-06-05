import logging
from pathlib import Path
import re
from typing import Dict, Optional

class IndexManager:
    # TODO: Přidat do configu?
    IGNORED_DIR_NAMES = {
        '.git', '.svn', '.hg',
        'node_modules', 'venv', '.venv',
        '__pycache__', '.pytest_cache',
        '.vscode', '.idea',
        'dist', 'build', 'target',
        'bin', 'obj', 'log'
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
            if not client_dir.is_dir() or client_dir.name.startswith('.'):
                continue
            
            for project_dir in client_dir.iterdir():
                if not project_dir.is_dir() or project_dir.name.startswith('.') or project_dir.name.lower() in self.IGNORED_DIR_NAMES:
                    continue
                
                p_info = {"client": client_dir.name, "project": project_dir.name}
                p_name_key = project_dir.name.lower()
                
                if p_name_key not in new_map: new_map[p_name_key] = []
                new_map[p_name_key].append(p_info)
                
                import os
                for root, dirs, files in os.walk(str(project_dir)):
                    # Modifikace dirs in-place způsobí, že os.walk do nich nevstoupí
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d.lower() not in self.IGNORED_DIR_NAMES]
                    
                    for file in files:
                        if file.startswith('.'):
                            continue
                        f_key = file.lower()
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
        best_match_projects: list[dict] = []
        max_key_len = 0
        best_key = None

        # 1. Najdeme kandidáty (Regex + délka)
        for key, projects in self.lookup_map.items():
            pattern = r"\b" + re.escape(key) + r"\b"
            if re.search(pattern, title_lower):
                if len(key) > max_key_len:
                    max_key_len = len(key)
                    best_match_projects = list(projects) 
                    best_key = key
                elif len(key) == max_key_len and max_key_len > 0:
                    best_match_projects.extend(projects)

        if not best_match_projects:
            return None

        # 2. TIE-BREAKER: Pokud je kandidátů víc, zkusíme najít název projektu v titulku
        # snaha o rozlišení mezi projekty, který mají stejný klíč (prace1.docx v projektA + prace1.docx v projektB)
        if len(best_match_projects) > 1:
            for p in best_match_projects:
                if p['project'].lower() in title_lower:
                    return {"client": p['client'], "project": p['project'], "matched_key": best_key}

        # 3. Vrátíme první nalezený (vždy to bude dict ze seznamu)
        p = best_match_projects[0]
        return {"client": p['client'], "project": p['project'], "matched_key": best_key}