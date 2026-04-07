import os
from typing import Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from src.core.config import AppSettings
from .models import Base, Client, Project, ActivityLog
from sqlalchemy import event
from ..core.config import AppSettings

class DatabaseManager:
    def __init__(self,settings: AppSettings, db_url: str = "sqlite:///contextflow.db"):
        self.settings = settings
        self.engine = create_engine(db_url)
        
        # TENTO BLOK zapne hlídání cizích klíčů v SQLite
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def _get_or_create_project(self, session, client_name: str, project_name: str) -> Project:
        # 1. Hledáme klienta
        client = session.execute(
            select(Client).filter_by(name=client_name)
        ).scalar_one_or_none()
        
        if not client:
            client = Client(name=client_name)
            session.add(client)
        
        # 2. Hledáme projekt u tohoto klienta
        project = session.execute(
            select(Project).filter_by(name=project_name, client=client)
        ).scalar_one_or_none()
        
        if not project:
            # Tady je kouzlo: přiřadíme přímo objekt 'client'
            project = Project(name=project_name, client=client)
            session.add(project)
            
        return project

    def log_activity(self, client_name: str, project_name: str, window_title: str, executable: str):
        with self.Session() as session:
            project_obj = self._get_or_create_project(session, client_name, project_name)
            
            # Najdeme úplně poslední záznam v celé tabulce
            stmt = select(ActivityLog).order_by(ActivityLog.id.desc()).limit(1)
            last_entry = session.execute(stmt).scalar_one_or_none()
            now = datetime.now()

            if last_entry:
                is_same_project = last_entry.project_id == project_obj.id
                # Použijeme MAX_GAP_FOR_MERGE (např. 120s) pro spojování logů
                time_diff = (now - last_entry.end_time).total_seconds()
                
                if is_same_project and time_diff < self.settings.MAX_GAP_FOR_MERGE:
                    # PRODLOUŽENÍ: Jen posuneme konec
                    last_entry.end_time = now
                    # Titulek updatujeme jen pokud máme reálné info (nejsme v Grace Period)
                    if window_title != "Grace Period":
                        last_entry.window_title = window_title
                        last_entry.executable = executable
                    session.commit()
                    return

            # NOVÝ ZÁZNAM: Pokud je to jiný projekt nebo moc velká pauza
            new_entry = ActivityLog(
                project=project_obj,
                start_time=now, # Začínáme teď, žádné vracení do minulosti
                end_time=now,
                window_title=window_title,
                executable=executable
            )
            session.add(new_entry)
            session.commit()

    def get_last_log_time(self) -> Optional[datetime]:
        """Vrátí čas konce posledního záznamu v DB."""
        with self.Session() as session:
            stmt = select(ActivityLog.end_time).order_by(ActivityLog.id.desc()).limit(1)
            return session.execute(stmt).scalar_one_or_none()
        
# Pro editaci logů z GUI
    def update_activity_log(self, log_id, new_start, new_end):
        """Aktualizuje svůj záznam v DB."""
        with self.Session() as session:
            log = session.get(ActivityLog, log_id)
            if log:
                log.start_time = new_start
                log.end_time = new_end
                session.commit()
                return True
            return False

    def delete_activity_log(self, log_id):
        """Vymaže svůj záznam v DB."""
        with self.Session() as session:
            log = session.get(ActivityLog, log_id)
            if log:
                session.delete(log)
                session.commit()
                return True
            return False
    
    # Základ pro nový indexer NEWINDEX
'''
    def rename_project_path(self, old_path, new_path):
        with self.Session() as session:
            # 1. Najdeme projekt podle staré cesty
            project = session.execute(
                select(Project).where(Project.path == old_path)
            ).scalar_one_or_none()
            
            if project:
                # 2. Aktualizujeme cestu i jméno (pokud jméno odvozuješ ze složky)
                project.path = new_path
                project.name = os.path.basename(new_path)
                session.commit()
                return True
        return False
    
    def sync_project(self, client_name: str, project_name: str, project_path: str):
        """
        Zajistí, že klient a projekt existují. 
        Identifikace projektu probíhá primárně přes PATH.
        """
        with self.Session() as session:
            # 1. Zajistíme klienta
            client = session.execute(
                select(Client).where(Client.name == client_name)
            ).scalar_one_or_none()
            
            if not client:
                client = Client(name=client_name)
                session.add(client)
                session.flush()

            # 2. Zajistíme projekt podle PATH
            project = session.execute(
                select(Project).where(Project.path == project_path)
            ).scalar_one_or_none()

            if not project:
                # Nový projekt
                project = Project(name=project_name, path=project_path, client_id=client.id)
                session.add(project)
            else:
                # Existující projekt - aktualizujeme jméno (kdyby se složka přejmenovala)
                project.name = project_name
                # A ujistíme se, že má správného klienta (kdyby se složka přesunula k jinému)
                project.client_id = client.id

            session.commit()
            # Vrátíme ID a jména, aby si Indexer mohl postavit mapu v paměti
            return {
                "id": project.id,
                "name": project.name,
                "client": client.name
            }
'''
