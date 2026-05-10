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
                    joinedload(ActivityLog.project)   # 1. Načíst projekt
                    .joinedload(Project.client)       # 2. Načíst klienta
                )
                .where(
                    ActivityLog.start_time <= end_time,
                    ActivityLog.end_time >= start_time
                )
            )
            return session.execute(stmt).scalars().all()

    def get_summary_for_billing(self, project_id: int, start_date: datetime, end_date: datetime):
        """Vrátí data připravená přímo pro fakturu."""
        with self.db.Session() as session:
            # 1. Získáme projekt a profil
            project = session.get(Project, project_id)
            profile = session.execute(select(BillingProfile)).scalar_one_or_none()
            rounding = profile.rounding_minutes if profile else 15

            # 2. Sečteme sekundy
            stmt = select(ActivityLog.start_time, ActivityLog.end_time).where(
                ActivityLog.project_id == project_id,
                ActivityLog.start_time <= end_date,
                ActivityLog.end_time >= start_date
            )
            project_logs = session.execute(stmt).all()
            
            total_seconds = 0
            for start, end in project_logs:
                actual_start = max(start, start_date)
                actual_end = min(end, end_date)
                total_seconds += (actual_end - actual_start).total_seconds()
            
            # 3. Logika zaokrouhlování
            total_minutes = total_seconds / 60
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
    
    def get_daily_stats_v2(self, target_date: date):
        """Vrátí strukturovaná data: {Klient: {Projekt: sekundy}}"""
        with self.db.Session() as session:
            start_dt = datetime.combine(target_date, datetime.min.time())
            end_dt = datetime.combine(target_date, datetime.max.time())
            
            stmt = (
                select(ActivityLog)
                .options(joinedload(ActivityLog.project).joinedload(Project.client))
                .where(
                    ActivityLog.start_time <= end_dt,
                    ActivityLog.end_time >= start_dt
                )
            )
            logs = session.execute(stmt).scalars().all()
                        
            stats = {}
            for log in logs:
                c_name = log.project.client.name
                p_name = log.project.name
                
                if c_name not in stats: stats[c_name] = {}
                if p_name not in stats[c_name]: stats[c_name][p_name] = 0
                
                actual_start = max(log.start_time, start_dt)
                actual_end = min(log.end_time, end_dt)
                stats[c_name][p_name] += (actual_end - actual_start).total_seconds()
                
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
                "sender": { 
                    "name": profile.name if profile and profile.name else "...", 
                    "address": profile.address if profile and profile.address else "...", 
                    "ico": profile.ico if profile and profile.ico else "...", 
                    "dic": profile.dic if profile and profile.dic else "...", 
                    "bank_account": profile.bank_account if profile and profile.bank_account else "...",
                    "logo_path": profile.logo_path if profile and profile.logo_path else None
                },
                "recipient": { "name": client.name, "address": client.address or "...", "ico": client.ico or "...", "dic": client.dic or "...", "email": client.email or "..." },
                "period": f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}",
                "jobs": jobs, # Seznam projektů
                "grand_total": grand_total,
                "currency": jobs[0]["currency"] if jobs else "CZK"
            }


    def get_all_clients_summary(self):
        """Vrátí seznam všech klientů a jejich celkový čas v sekundách."""
        with self.db.Session() as session:
            # Načteme klienty i s jejich projekty, BEZ LOGŮ 
            stmt = select(Client).options(joinedload(Client.projects))
            clients = session.execute(stmt).unique().scalars().all()
            
            logs_stmt = select(ActivityLog.project_id, ActivityLog.start_time, ActivityLog.end_time)
            all_logs = session.execute(logs_stmt).all()
            
            summary = []
            for c in clients:
                project_ids = {p.id for p in c.projects}
                total_sec = sum((end - start).total_seconds() for pid, start, end in all_logs if pid in project_ids)
                
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
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())
            
            stmt = (
                select(ActivityLog.start_time, ActivityLog.end_time)
                .where(
                    ActivityLog.project_id == project_id,
                    ActivityLog.start_time <= end_dt,
                    ActivityLog.end_time >= start_dt
                )
            )
            logs = session.execute(stmt).all()
            
            total_seconds = 0
            for start, end in logs:
                actual_start = max(start, start_dt)
                actual_end = min(end, end_dt)
                total_seconds += (actual_end - actual_start).total_seconds()
                
            return total_seconds / 3600 