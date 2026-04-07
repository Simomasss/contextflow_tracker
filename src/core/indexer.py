from pathlib import Path
from typing import Dict, Optional

class IndexManager:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        # Mapa: "jmeno_souboru_nebo_slozky" -> (klient, projekt)
        self.lookup_map: Dict[str, dict] = {}
        self.reindex()

    def reindex(self): # NEWINDEX
        """Projde rekurzivně vše pod MAIN a namapuje to na klienty/projekty."""
        if not self.root_path.exists():
            return

        new_map = {}
        
        # Projdeme složky klientů (úroveň 1)
        for client_dir in self.root_path.iterdir():
            if not client_dir.is_dir(): continue
            
            # Projdeme složky projektů (úroveň 2)
            for project_dir in client_dir.iterdir():
                if not project_dir.is_dir(): continue
                
                project_info = {
                    "client": client_dir.name,
                    "project": project_dir.name
                }
                
                # 1. Přidáme název projektu do mapy
                new_map[project_dir.name.lower()] = project_info
                
                # 2. Přidáme VŠECHNY soubory a podsložky v tomto projektu (úroveň 3+)
                # rglob("*") najde vše rekurzivně hluboko uvnitř
                for item in project_dir.rglob("*"):
                    # Klíčem je název souboru/složky (např. "rozpocet.xlsx")
                    # Hodnotou je pořád stejný klient a projekt
                    new_map[item.name.lower()] = project_info

        self.lookup_map = new_map
        print(f"Index aktualizován: {len(self.lookup_map)} sledovaných položek.")

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
    
    ''' - kratka shoda klice
    def match_title(self, window_title: str) -> Optional[dict]:
        """Tady se děje to kouzlo, o kterém jsi mluvil."""
        title_lower = window_title.lower()
        
        # Projdeme naši mapu a zkusíme, jestli je nějaký klíč v titulku okna
        for key, info in self.lookup_map.items():
            # Pokud se název souboru (klíč) nachází v titulku okna (např. "Word - analyza.docx")
            if key in title_lower and len(key) > 3: # len > 3 je ochrana proti krátkým nesmyslům
                return info
        
        return None
    '''