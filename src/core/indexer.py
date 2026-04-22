import logging
from pathlib import Path
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
        """Projde rekurzivně vše pod MAIN a namapuje to na klienty/projekty. Ignoruje položky v IGNORED_DIR_NAMES a všechny skryté položky. (začínající '.')"""
        if not self.root_path.exists(): return
        new_map = {}
        
        for client_dir in self.root_path.iterdir():
            if not client_dir.is_dir(): continue
            
            for project_dir in client_dir.iterdir():
                if not project_dir.is_dir(): continue
                
                project_info = {"client": client_dir.name,
                                "project": project_dir.name
                                }
                
                new_map[project_dir.name.lower()] = project_info
                
                for item in project_dir.rglob("*"):
                    # FILTR
                    path_parts = item.parts
                    if any(part.startswith('.') or part in self.IGNORED_DIR_NAMES for part in path_parts):
                        continue
                    
                    # Indexujeme pouze soubory (složky už máme pokryté názvem projektu)
                    if item.is_file():
                        new_map[item.name.lower()] = project_info

        self.lookup_map = new_map
        logging.info(f"Index vyčištěn a aktualizován: {len(self.lookup_map)} relevantních položek.")

    def match_title(self, window_title: str) -> Optional[dict]:
        title_lower = window_title.lower()
        
        best_match = None
        max_key_length = 0

        # Projdeme všechny klíče v naší mapě
        for key, info in self.lookup_map.items():
            # Pokud klíč (název souboru/složky) najdeme v titulku okna
            if key in title_lower:
                # A pokud je tento klíč DELŠÍ než ten, co jsme našli předtím
                if len(key) > max_key_length:
                    max_key_length = len(key)
                    best_match = info
        
        # Vrátíme tu nejdelší (nejpřesnější) shodu
        return best_match