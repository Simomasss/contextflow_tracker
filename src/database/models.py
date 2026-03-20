from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

class Base(DeclarativeBase):
    """Základní třída pro všechny naše budoucí tabulky."""
    pass

class ActivityLog(Base):
    """Tabulka, kam budeme sypat každý 'tick' z našeho Enginu."""
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now)
    client_name = Column(String, nullable=False)
    project_name = Column(String, nullable=False)
    window_title = Column(String)
    duration = Column(Integer)  # Délka ticku v sekundách (např. 5)

    def __repr__(self):
        return f"<Activity(client={self.client_name}, project={self.project_name})>"