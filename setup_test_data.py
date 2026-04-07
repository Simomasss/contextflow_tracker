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
    Base.metadata.drop_all(db.engine) # Smažeme staré tabulky pro čistý start
    Base.metadata.create_all(db.engine)

    with db.Session() as session:
        # 1. TVŮJ PROFIL (Odesílatel)
        profile = BillingProfile(
            name="Jan Programátor",
            address="Kódovací 128, Praha 10, 100 00",
            ico="12345678",
            dic="CZ12345678",
            bank_account="2100123456/2010",
            logo_path="C:/path/to/logo.png",
            rounding_minutes=15
        )
        session.add(profile)
        '''
        # 2. KLIENTI
        adam = Client(
            name="Adam", 
            address="U Lesa 5, Brno, 602 00", 
            ico="11223344", 
            dic="CZ11223344", 
            email="adam.klient@seznam.cz"
        )
        pepa = Client(
            name="Pepa", 
            address="Vysoká 10, Ostrava, 700 00", 
            ico="55667788", 
            dic="CZ55667788", 
            email="pepa.dedictvi@gmail.com"
        )
        '''
        adam = Client(
            name="Adam", 
            address="U Lesa 5, Brno, 602 00"
        )
        pepa = Client(
            name="Pepa"
        )
        session.add_all([adam, pepa])
        session.flush()

        # 3. PROJEKTY
        p1 = Project(name="projekt1", client=adam, hourly_rate=500.0, currency="CZK")
        p2 = Project(name="projekt2", client=adam, hourly_rate=750.0, currency="CZK")
        dedictvi = Project(name="dedictvi", client=pepa, hourly_rate=600.0, currency="CZK")
        session.add_all([p1, p2, dedictvi])
        session.flush()

        # 4. GENEROVÁNÍ LOGŮ
        now = datetime.now()
        
        # --- DEN 1: Historie (před 2 dny) ---
        d1 = now - timedelta(days=2)
        session.add(ActivityLog(project=p1, start_time=d1.replace(hour=9, minute=0), end_time=d1.replace(hour=11, minute=0), window_title="Dokumentace - Word", executable="winword.exe"))
        session.add(ActivityLog(project=p2, start_time=d1.replace(hour=13, minute=0), end_time=d1.replace(hour=15, minute=40), window_title="Tabulka nákladů - Excel", executable="excel.exe"))

        # --- DEN 2: Historie (včera) ---
        d2 = now - timedelta(days=1)
        session.add(ActivityLog(project=dedictvi, start_time=d2.replace(hour=10, minute=0), end_time=d2.replace(hour=11, minute=30), window_title="Prezentace pro Pepu", executable="powerpnt.exe"))
        session.add(ActivityLog(project=dedictvi, start_time=d2.replace(hour=14, minute=0), end_time=d2.replace(hour=15, minute=45), window_title="Smlouva - Word", executable="winword.exe"))

        # --- DEN 3: DNEŠEK (Minimálně 3 různé záznamy) ---
        # Záznam A: Ranní programování (Projekt 1)
        session.add(ActivityLog(
            project=p1, 
            start_time=now.replace(hour=8, minute=30, second=0), 
            end_time=now.replace(hour=10, minute=15, second=0), 
            window_title="Visual Studio Code", 
            executable="code.exe"
        ))

        # Záznam B: Odpolední research (Projekt 2)
        session.add(ActivityLog(
            project=p2, 
            start_time=now.replace(hour=11, minute=0, second=0), 
            end_time=now.replace(hour=11, minute=45, second=0), 
            window_title="Google Chrome - Dokumentace", 
            executable="chrome.exe"
        ))

        # Záznam C: Večerní administrativa (Dědictví)
        session.add(ActivityLog(
            project=dedictvi, 
            start_time=now.replace(hour=12, minute=20, second=0), 
            end_time=now.replace(hour=13, minute=10, second=0), 
            window_title="Outlook - E-maily", 
            executable="outlook.exe"
        ))

        session.commit()
        logging.info(f"✓ Databáze contextflow.db byla úspěšně aktualizována.")
        logging.info(f"✓ Vygenerovány 3 logy pro dnešek ({now.strftime('%d.%m.%Y')}).")
        logging.info(f"✓ Všechny spustitelné soubory jsou v lowercase.")

if __name__ == "__main__":
    setup_mock_data()