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
        matched_candidates = []

        # 1. Najdeme VŠECHNY kandidáty, kteří se vyskytují v titulku okna
        for key, projects in self.lookup_map.items():
            pattern = r"\b" + re.escape(key) + r"\b"
            if re.search(pattern, title_lower):
                # Spočítáme váhu (raritu). Čím méně projektů soubor má, tím vyšší váha.
                rarity_score = 1.0 / len(projects)
                matched_candidates.append({
                    "key": key,
                    "projects": projects,
                    "rarity": rarity_score,
                    "length": len(key)
                })

        if not matched_candidates:
            return None

        # 2. Seřadíme kandidáty od nejlepšího:
        # Primárně podle nejvyšší rarity, sekundárně podle délky klíče
        matched_candidates.sort(key=lambda x: (x["rarity"], x["length"]), reverse=True)
        
        best_candidate = matched_candidates[0]
        best_key = best_candidate["key"]
        best_match_projects = best_candidate["projects"]

        # 3. TIE-BREAKER pro konflikty: Pokud má i vítězný klíč váhu menší než 1.0 (je ve více projektech),
        # zkusíme zjistit, jestli titulek okna náhodou neobsahuje i samotný název projektu.
        if len(best_match_projects) > 1:
            for p in best_match_projects:
                if p['project'].lower() in title_lower:
                    return {"client": p['client'], "project": p['project'], "matched_key": best_key}

        # 4. Pokud se konflikt nepodařilo rozseknout, prostě vrátíme první projekt
        p = best_match_projects[0]
        return {"client": p['client'], "project": p['project'], "matched_key": best_key}