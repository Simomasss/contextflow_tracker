import logging
import random
from datetime import datetime, timedelta, time
from src.database.db_handler import DatabaseManager
from src.database.models import Base, BillingProfile, Client, Project, ActivityLog
from src.core.config import AppSettings
from sqlalchemy import select

# TED NEFUNUGJE KVULI PATH V PROJECT V MODELS
def setup_mock_data():
    settings = AppSettings(
        TICK_INTERVAL=5,
        PROTECTION_MINUTES=1.0,
        AFK_THRESHOLD=300,
        # Whitelist v configu taky raději lowercase pro konzistenci
        WHITELIST=["code.exe", "winword.exe", "chrome.exe", "excel.exe", "figma.exe", "explorer.exe"],
        MAIN_FOLDER="C:/Users/donth/VSE/BAKALARKA/MAIN"
    )
    
    # Inicializace TEST databáze
    db = DatabaseManager(settings=settings, db_url="sqlite:///contextflow.db")
    # Záměrně nemážeme tabulky pomocí drop_all, abychom zachovali dosavadní data
    Base.metadata.create_all(db.engine)

    with db.Session() as session:
        # 1. ZÍSKÁNÍ NEBO VYTVOŘENÍ KLIENTŮ A PROJEKTŮ
        client_cf = session.execute(select(Client).where(Client.name == "contextflow_tracker")).scalar_one_or_none()
        if not client_cf:
            client_cf = Client(name="contextflow_tracker")
            session.add(client_cf)
            
        client_lit = session.execute(select(Client).where(Client.name == "literatura")).scalar_one_or_none()
        if not client_lit:
            client_lit = Client(name="literatura")
            session.add(client_lit)
            
        session.flush()

        proj_src = session.execute(select(Project).where(Project.name == "src", Project.client_id == client_cf.id)).scalar_one_or_none()
        if not proj_src:
            proj_src = Project(name="src", client_id=client_cf.id, hourly_rate=500.0, currency="CZK")
            session.add(proj_src)

        proj_lit = session.execute(select(Project).where(Project.name == "projetkProMereniLiteratura", Project.client_id == client_lit.id)).scalar_one_or_none()
        if not proj_lit:
            proj_lit = Project(name="projetkProMereniLiteratura", client_id=client_lit.id, hourly_rate=600.0, currency="CZK")
            session.add(proj_lit)

        session.flush()

        # 2. GENEROVÁNÍ LOGŮ PODLE POŽADAVKŮ
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        
        logs = [
            # VČERA (10:00 - 12:00)
            ActivityLog(project=proj_src, start_time=yesterday.replace(hour=10, minute=14, second=30), 
                        end_time=yesterday.replace(hour=11, minute=22, second=15), 
                        window_title="core/engine.py - contextflow_tracker", executable="code.exe"),
            ActivityLog(project=proj_lit, start_time=yesterday.replace(hour=11, minute=27, second=10), 
                        end_time=yesterday.replace(hour=11, minute=58, second=45), 
                        window_title="prezentace_baka_seminar", executable="powerpnt.exe"),
            
            # VČERA (18:00 - 21:00)
            ActivityLog(project=proj_src, start_time=yesterday.replace(hour=18, minute=5, second=20), 
                        end_time=yesterday.replace(hour=19, minute=42, second=15), 
                        window_title="gui/app.py - contextflow_tracker", executable="code.exe"),
            ActivityLog(project=proj_src, start_time=yesterday.replace(hour=19, minute=47, second=30), 
                        end_time=yesterday.replace(hour=20, minute=54, second=10), 
                        window_title="watchers/window_watcher.py - contextflow_tracker", executable="code.exe"),

            # DNES (10:00 - 14:30)
            ActivityLog(project=proj_src, start_time=today.replace(hour=10, minute=5, second=12), 
                        end_time=today.replace(hour=11, minute=13, second=48), 
                        window_title="database/models.py - contextflow_tracker", executable="code.exe"),
            ActivityLog(project=proj_lit, start_time=today.replace(hour=11, minute=21, second=5), 
                        end_time=today.replace(hour=12, minute=44, second=33), 
                        window_title="prezentace_baka_seminar", executable="powerpnt.exe"),
            ActivityLog(project=proj_src, start_time=today.replace(hour=12, minute=56, second=10), 
                        end_time=today.replace(hour=13, minute=41, second=22), 
                        window_title="gui/frames/home.py - contextflow_tracker", executable="code.exe"),
            ActivityLog(project=proj_src, start_time=today.replace(hour=13, minute=48, second=40), 
                        end_time=today.replace(hour=14, minute=26, second=15), 
                        window_title="core/indexer.py - contextflow_tracker", executable="code.exe")
        ]

        session.add_all(logs)
        session.commit()
        
        logging.info(f"✓ Showcase data byla přidána do databáze bez mazání stávajících záznamů.")

if __name__ == "__main__":
    setup_mock_data()