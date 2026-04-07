import os

class IndexManager:
    def __init__(self, root_path=None):
        self.root_path = root_path
        self.index = {}  # Mapa: { 'NázevProjektu': {'client': 'Jméno', 'path': '...'} }

    def set_root(self, path):
        if os.path.exists(path):
            self.root_path = path
            return True
        return False

    def build_index(self):
        """Projde strukturu MAIN/Klient/Projekt a vytvoří mapu."""
        if not self.root_path or not os.path.exists(self.root_path):
            return False

        new_index = {}
        try:
            # 1. Úroveň: Klienti
            for client_name in os.listdir(self.root_path):
                client_path = os.path.join(self.root_path, client_name)
                
                if os.path.isdir(client_path):
                    # 2. Úroveň: Projekty
                    for project_name in os.listdir(client_path):
                        project_path = os.path.join(client_path, project_name)
                        
                        if os.path.isdir(project_path):
                            # Uložíme projekt do indexu
                            # Klíčem je název složky projektu, který hledáme v titulku okna
                            new_index[project_name] = {
                                "client": client_name,
                                "path": project_path
                            }
            
            self.index = new_index
            return True
        except Exception as e:
            logging.info(f"Chyba při indexaci: {e}")
            return False

    def get_project_keys(self):
        """Vrátí seznam všech názvů projektů pro matcher."""
        return list(self.index.keys())

# --- TEST ---
if __name__ == "__main__":
    # Představ si, že uživatel vybral složku "C:/MojePrace"
    # Kde je struktura: C:/MojePrace/AdvokatniKancelar/Smlouvy_2024
    manager = IndexManager("C:/Users/donth/VSE/BAKALARKA/MAIN")
    if manager.build_index():
        logging.info("Index úspěšně vytvořen:")
        for proj, info in manager.index.items():
            logging.info(f"Projekt: {proj} | Klient: {info['client']}")