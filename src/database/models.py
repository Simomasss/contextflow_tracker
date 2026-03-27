from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from typing import List

class Base(DeclarativeBase):
    """Základní třída pro všechny naše budoucí tabulky."""
    pass

class Client(Base):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    projects: Mapped[List["Project"]] = relationship(back_populates="client")

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    
    client: Mapped["Client"] = relationship(back_populates="projects")
    activities: Mapped[List["ActivityLog"]] = relationship(back_populates="project")

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    end_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    window_title: Mapped[str] = mapped_column(String, nullable=True)
    executable: Mapped[str] = mapped_column(String, nullable=True)
    
    project: Mapped["Project"] = relationship(back_populates="activities")