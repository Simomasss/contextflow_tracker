from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, ActivityLog

class DatabaseManager:
    def __init__(self, db_path: str = "sqlite:///contextflow.db"):
        # Vytvoříme spojení s databází (pokud soubor neexistuje, vytvoří se)
        self.engine = create_engine(db_path)
        # Vytvoříme tabulky na základě našich modelů
        Base.metadata.create_all(self.engine)
        # Session je naše "brána" pro komunikaci s DB
        self.Session = sessionmaker(bind=self.engine)

    def log_activity(self, client: str, project: str, window_title: str, duration: int):
        """Uloží jeden záznam o aktivitě do databáze."""
        with self.Session() as session:
            new_entry = ActivityLog(
                client_name=client,
                project_name=project,
                window_title=window_title,
                duration=duration
            )
            session.add(new_entry)
            session.commit()
            # Po commitu se data fyzicky zapíšou na disk