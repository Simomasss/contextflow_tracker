from datetime import datetime, date, timedelta, time
from sqlalchemy import select, func
from ..database.models import ActivityLog, Project, Client, BillingProfile

class ActivityAggregator:
    def __init__(self, db_manager):
        self.db = db_manager

    def get_raw_logs(self, start_date: datetime, end_date: datetime):
        """Základní metoda pro získání logů v rozmezí."""
        with self.db.Session() as session:
            stmt = select(ActivityLog).where(
                ActivityLog.start_time >= start_date,
                ActivityLog.end_time <= end_date
            ).order_by(ActivityLog.start_time)
            return session.execute(stmt).scalars().all()

    def get_summary_for_billing(self, project_id: int, start_date: datetime, end_date: datetime):
        """Vrátí data připravená přímo pro fakturu."""
        with self.db.Session() as session:
            # 1. Získáme projekt a profil (kvůli sazbě a zaokrouhlování)
            project = session.get(Project, project_id)
            profile = session.execute(select(BillingProfile)).scalar_one_or_none()
            rounding = profile.rounding_minutes if profile else 15
            # TODO: Error handling, kdyby nebyl projekt

            # 2. Sečteme sekundy
            logs = self.get_raw_logs(start_date, end_date)
            project_logs = [l for l in logs if l.project_id == project_id]
            
            total_seconds = sum((l.end_time - l.start_time).total_seconds() for l in project_logs)
            
            # 3. Logika zaokrouhlování
            total_minutes = total_seconds / 60
            # Zaokrouhlení nahoru na nejbližší blok (např. 15 min)
            rounded_minutes = ((total_minutes + rounding - 1) // rounding) * rounding
            rounded_hours = rounded_minutes / 60

            return {
                "project_name": project.name,
                "client_name": project.client.name,
                "raw_seconds": total_seconds,
                "billable_hours": rounded_hours,
                "rate": project.hourly_rate or 0,
                "total_price": rounded_hours * (project.hourly_rate or 0),
                "currency": project.currency
            }

    def get_daily_stats(self, target_date: date): 
        """Data pro Dashboard - kolik času na každém projektu za den."""
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        
        logs = self.get_raw_logs(start, end)
        stats = {} # { "Projekt A": sekundy }
        
        for log in logs:
            name = log.project.name
            duration = (log.end_time - log.start_time).total_seconds()
            stats[name] = stats.get(name, 0) + duration
            
        return stats
    
    def get_invoice_data(self, project_id: int, start_date: date, end_date: date):
        """
        Posbírá kompletní data pro fakturu: Odesílatel, Příjemce, Čas a Peníze.
        """
        with self.db.Session() as session:
            # 1. Načtení základních entit
            project = session.get(Project, project_id)
            if not project:
                return None
            
            client = project.client
            profile = session.execute(select(BillingProfile)).scalar_one_or_none()
            
            # 2. Výpočet času (využijeme dříve napsanou logiku)
            # Musíme převést date na datetime (začátek prvního a konec posledního dne)
            start_dt = datetime.combine(start_date, time.min)
            end_dt = datetime.combine(end_date, time.max)
            
            billing_summary = self.get_summary_for_billing(project_id, start_dt, end_dt)
            
            # 3. Sestavení finálního balíčku
            invoice_package = {
                # Info o odesílateli (TY)
                "sender": {
                    "name": profile.name if profile else "NEVYPLNĚNO",
                    "address": profile.address if profile else "",
                    "ico": profile.ico if profile else "",
                    "dic": profile.dic if profile else "",
                    "bank_account": profile.bank_account if profile else "",
                },
                # Info o příjemci (KLIENT)
                "recipient": {
                    "name": client.name,
                    "address": client.address or "Adresa nevyplněna",
                    "ico": client.ico or "",
                    "dic": client.dic or "",
                    "email": client.email or "",
                },
                # Detaily projektu a práce
                "job": {
                    "project_name": project.name,
                    "period": f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}",
                    "total_hours": billing_summary["billable_hours"],
                    "hourly_rate": billing_summary["rate"],
                    "total_price": billing_summary["total_price"],
                    "currency": billing_summary["currency"]
                }
            }
            return invoice_package