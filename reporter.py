from sqlalchemy import select
from src.database.db_handler import DatabaseManager
from src.database.models import ActivityLog
from src.core.config import AppSettings
from datetime import datetime

def show_report():
    settings = AppSettings()
    db = DatabaseManager(settings=settings)
    
    with db.Session() as session:
        # Chceme vidět logy za dnešek
        today = datetime.now().date()
        stmt = select(ActivityLog).order_by(ActivityLog.start_time)
        logs = session.execute(stmt).scalars().all()

        if not logs:
            print("Zatím žádná data k zobrazení.")
            return

        print(f"\n{'='*85}")
        print(f"{'ID':<4} | {'PROJEKT':<18} | {'START':<10} | {'KONEC':<10} | {'TRVÁNÍ':<10} | {'APP'}")
        print(f"{'-'*85}")

        total_work_time = {}

        for log in logs:
            duration = log.end_time - log.start_time
            # Agregujeme čas pro celkový souhrn
            total_work_time[log.project.name] = total_work_time.get(log.project.name, 0) + duration.total_seconds()
            
            # Formátování výstupu
            dur_min = int(duration.total_seconds() // 60)
            dur_sec = int(duration.total_seconds() % 60)
            
            print(f"{log.id:<4} | {log.project.name[:18]:<18} | "
                  f"{log.start_time.strftime('%H:%M:%S'):<10} | "
                  f"{log.end_time.strftime('%H:%M:%S'):<10} | "
                  f"{dur_min:2}m {dur_sec:02}s | {log.executable[:15]}")

        print(f"{'='*85}")
        print("\nSOUHRN PODLE PROJEKTŮ:")
        for proj, seconds in total_work_time.items():
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            print(f"- {proj:<20}: {h}h {m}m")
        print(f"{'='*85}\n")

if __name__ == "__main__":
    show_report()