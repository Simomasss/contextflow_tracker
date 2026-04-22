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

    def match_title(self, window_title: str, current_project = None) -> Optional[dict]:
        if not window_title: return None
        title_lower = window_title.lower()
        
        best_match = None
        max_key_len = 0
        potential_projects = []

        # Najdeme všechny shody (řešíme Ružu přes Regex)
        for key, projects in self.lookup_map.items():
            pattern = r"\b" + re.escape(key) + r"\b"
            if re.search(pattern, title_lower):
                if len(key) > max_key_len:
                    max_key_len = len(key)
                    potential_projects = projects

        if not potential_projects:
            return None

        # TIE-BREAKER (Rozhodování u stejnojmenných souborů)
        if len(potential_projects) > 1:
            # 1. Je jeden z nich ten, co zrovna děláme?
            if current_project:
                for p in potential_projects:
                    if p['project'] == current_project:
                        return p
            
            # 2. Je název projektu v titulu okna?
            for p in potential_projects:
                if p['project'].lower() in title_lower:
                    return p

        # 3. Pokud nevíme, nebo je jen jeden, vrátíme první možnost
        return potential_projects[0]
    

'''
def reindex(self):
        """Projde rekurzivně vše pod MAIN a namapuje to na klienty/projekty. Ignoruje položky v IGNORED_DIR_NAMES a všechny skryté položky. (začínající '.')"""
        if not self.root_path.exists(): return
        new_map = {}
        
        for client_dir in self.root_path.iterdir():
            if not client_dir.is_dir(): continue
            
            for project_dir in client_dir.iterdir():
                if not project_dir.is_dir(): continue
                
                p_info = {"client": client_dir.name, "project": project_dir.name}
                p_name_key = project_dir.name.lower()
                
                # 1. Přidáme název projektu (vždy unikátní v rámci klienta)
                if p_name_key not in new_map: new_map[p_name_key] = []
                new_map[p_name_key].append(p_info)
                
                # 2. Přidáme soubory
                for item in project_dir.rglob("*"):
                    # Ignorujeme balast (to už máš)
                    if any(part.startswith('.') or part in self.IGNORED_DIR_NAMES for part in item.parts):
                        continue
                    
                    if item.is_file():
                        f_key = item.name.lower()
                        if len(f_key) < 4: continue # Ochrana proti "1.pdf", "a.py"
                        
                        if f_key not in new_map: new_map[f_key] = []
                        # Zamezíme duplicitám v seznamu pro jeden soubor
                        if p_info not in new_map[f_key]:
                            new_map[f_key].append(p_info)

        self.lookup_map = new_map
        logging.info(f"Index aktualizován: {len(self.lookup_map)} unikátních klíčů.")
'''