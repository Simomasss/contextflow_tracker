from datetime import datetime, date, timedelta, time
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from ..database.models import ActivityLog, Project, Client, BillingProfile

class ActivityAggregator:
    def __init__(self, db_manager):
        self.db = db_manager

    def get_raw_logs(self, start_time: datetime, end_time: datetime):
        """Základní metoda pro získání logů v rozmezí s přednačtením projektů."""
        with self.db.Session() as session:
            stmt = (
                select(ActivityLog)
                .options(
                    joinedload(ActivityLog.project)   # 1. Načti projekt k logu
                    .joinedload(Project.client)       # 2. Načti klienta k tomu projektu (řetězení!)
                )
                .where(
                    ActivityLog.start_time >= start_time,
                    ActivityLog.end_time <= end_time
                )
            )
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
    
    def get_daily_stats_v2(self, target_date: date):
        """Vrátí strukturovaná data: {Klient: {Projekt: sekundy}}"""
        with self.db.Session() as session:
            start_dt = datetime.combine(target_date, datetime.min.time())
            end_dt = datetime.combine(target_date, datetime.max.time())
            
            # Tady také přidáme joinedload, abychom měli klienta k dispozici
            stmt = (
                select(ActivityLog)
                .options(joinedload(ActivityLog.project).joinedload(Project.client))
                .where(
                    ActivityLog.start_time >= start_dt,
                    ActivityLog.end_time <= end_dt
                )
            )
            logs = session.execute(stmt).scalars().all()
                        
            stats = {}
            for log in logs:
                c_name = log.project.client.name
                p_name = log.project.name
                
                if c_name not in stats: stats[c_name] = {}
                if p_name not in stats[c_name]: stats[c_name][p_name] = 0
                
                stats[c_name][p_name] += (log.end_time - log.start_time).total_seconds()
                
            return stats

    def get_invoice_data(self, project_ids: list[int], start_date: date, end_date: date):
        with self.db.Session() as session:
            # 1. Základní entity (bereme z prvního projektu, klient je stejný)
            first_project = session.get(Project, project_ids[0])
            client = first_project.client
            profile = session.execute(select(BillingProfile)).scalar_one_or_none()
            
            # 2. Sběr dat pro jednotlivé projekty
            jobs = []
            grand_total = 0
            
            for pid in project_ids:
                proj = session.get(Project, pid)
                start_dt = datetime.combine(start_date, time.min)
                end_dt = datetime.combine(end_date, time.max)
                
                summary = self.get_summary_for_billing(pid, start_dt, end_dt)
                
                if summary["billable_hours"] > 0:
                    jobs.append({
                        "name": proj.name,
                        "hours": summary["billable_hours"],
                        "rate": summary["rate"],
                        "total": summary["total_price"],
                        "currency": summary["currency"]
                    })
                    grand_total += summary["total_price"]

            return {
                "sender": { "name": profile.name if profile else "...", "address": profile.address or "...", "ico": profile.ico or "...", "dic": profile.dic or "...", "bank_account": profile.bank_account or "..." },
                "recipient": { "name": client.name, "address": client.address or "...", "ico": client.ico or "...", "dic": client.dic or "...", "email": client.email or "..." },
                "period": f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}",
                "jobs": jobs, # Seznam projektů
                "grand_total": grand_total,
                "currency": jobs[0]["currency"] if jobs else "CZK"
            }


    def get_all_clients_summary(self):
        """Vrátí seznam všech klientů a jejich celkový čas v sekundách."""
        with self.db.Session() as session:
            # Načteme klienty i s jejich projekty a logy
            stmt = select(Client).options(joinedload(Client.projects).joinedload(Project.logs))
            clients = session.execute(stmt).unique().scalars().all()
            
            summary = []
            for c in clients:
                total_sec = 0
                for p in c.projects:
                    total_sec += sum((l.end_time - l.start_time).total_seconds() for l in p.logs)
                
                summary.append({
                    "id": c.id,
                    "name": c.name,
                    "total_hours": total_sec / 3600,
                    "address": c.address or "",
                    "ico": c.ico or "",
                    "dic": c.dic or "",
                    "email": c.email or ""
                })
            return summary
        
    def get_project_hours(self, project_id: int, start_date: date, end_date: date) -> float:
        """Vrátí celkový počet hodin pro daný projekt v daném období."""
        with self.db.Session() as session:
            # Převedeme date na datetime pro porovnání v DB
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())
            
            # Sečteme délku všech logů
            stmt = (
                select(ActivityLog)
                .where(
                    ActivityLog.project_id == project_id,
                    ActivityLog.start_time >= start_dt,
                    ActivityLog.end_time <= end_dt
                )
            )
            logs = session.execute(stmt).scalars().all()
            
            total_seconds = sum((log.end_time - log.start_time).total_seconds() for log in logs)
            return total_seconds / 3600  # Převod na hodiny
        
'''
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
'''