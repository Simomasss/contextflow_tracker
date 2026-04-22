from src.core.indexer import IndexManager
from src.core.config import AppSettings


def main():
    settings = AppSettings()
    indexer = IndexManager(settings.MAIN_FOLDER)

    indexer.reindex()
    print("Index úspěšně vytvořen:")
    print(indexer.lookup_map)

if __name__ == "__main__":
    # Představ si, že uživatel vybral složku "C:/MojePrace"
    # Kde je struktura: C:/MojePrace/AdvokatniKancelar/Smlouvy_2024
    #manager = IndexManager("C:/Users/donth/VSE/BAKALARKA/MAIN")
    main()