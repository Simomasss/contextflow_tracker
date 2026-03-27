from typing import Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from .models import Base, Client, Project, ActivityLog
from sqlalchemy import event

class DatabaseManager:
    def __init__(self, db_url: str = "sqlite:///contextflow.db"):
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

    def log_activity(self, client_name, project_name, window_title, executable, interval_sec, custom_start=None):
        with self.Session() as session:
            project_obj = self._get_or_create_project(session, client_name, project_name)
            
            stmt = select(ActivityLog).order_by(ActivityLog.id.desc()).limit(1)
            last_entry = session.execute(stmt).scalar_one_or_none()
            now = datetime.now()

            # --- 1. SCÉNÁŘ: POTVRZENÍ ZMĚNY (BACKDATING) ---
            if custom_start:
                if last_entry and last_entry.project_id != project_obj.id:
                    # POJISTKA: Chirugii děláme jen, pokud je mezera menší než např. 10 minut
                    # Pokud je mezera větší, starý log necháme být a nový prostě začne od custom_start
                    gap_to_old_log = (custom_start - last_entry.end_time).total_seconds()
                    
                    if 0 <= gap_to_old_log < 600: # 10 minut limit pro "sešití" logů
                        last_entry.end_time = custom_start
                        session.flush()
                
                # Vytvoříme nový záznam
                new_entry = ActivityLog(
                    project=project_obj,
                    start_time=custom_start,
                    end_time=now,
                    window_title=window_title,
                    executable=executable
                )
                session.add(new_entry)
                session.commit()
                return

            # --- 2. SCÉNÁŘ: POKRAČOVÁNÍ (SLUČOVÁNÍ) ---
            if last_entry:
                is_same_project = last_entry.project_id == project_obj.id
                time_diff = (now - last_entry.end_time).total_seconds()
                
                # POJISTKA PRO RESTART: Pokud je time_diff moc velký, neslučujeme!
                if is_same_project and time_diff < 120:
                    last_entry.end_time = now
                    
                    # OPRAVA ÚNIKU NÁZVU: Titulek a EXE updatujeme jen pokud 
                    # okno patří k našemu whitelistu (není Unknown)
                    if executable != "Unknown":
                        last_entry.window_title = window_title
                        last_entry.executable = executable
                        
                    session.commit()
                    return

            # --- 3. SCÉNÁŘ: NOVÝ START ---
            new_entry = ActivityLog(
                project=project_obj,
                start_time=now - timedelta(seconds=interval_sec),
                end_time=now,
                window_title=window_title,
                executable=executable
            )
            session.add(new_entry)
            session.commit()

'''
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
'''