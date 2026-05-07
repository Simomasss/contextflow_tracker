from sqlalchemy import Float, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, Optional

class Base(DeclarativeBase):
    """Základní třída pro všechny naše budoucí tabulky."""
    pass

# Všechno je mapped_column, kvuli pylance type sledovani
class Client(Base):
    __tablename__ = 'clients'
    id: Mapped[int] = mapped_column(primary_key=True) 
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String)
    ico: Mapped[Optional[str]] = mapped_column(String)
    dic: Mapped[Optional[str]] = mapped_column(String)
    email: Mapped[Optional[str]] = mapped_column(String)

    projects: Mapped[List["Project"]] = relationship("Project", back_populates="client", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = 'projects'
    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey('clients.id'))
    name: Mapped[str] = mapped_column(String, nullable=False)
    hourly_rate: Mapped[Optional[float]] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String, default="CZK")

    client: Mapped["Client"] = relationship("Client", back_populates="projects")
    logs: Mapped[List["ActivityLog"]] = relationship("ActivityLog", back_populates="project", cascade="all, delete-orphan")

class ActivityLog(Base):
    __tablename__ = 'activity_logs'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'))
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    window_title: Mapped[Optional[str]] = mapped_column(String)
    executable: Mapped[Optional[str]] = mapped_column(String)

    project: Mapped["Project"] = relationship("Project", back_populates="logs")

class BillingProfile(Base):
    __tablename__ = 'billing_profile'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String)
    ico: Mapped[Optional[str]] = mapped_column(String)
    dic: Mapped[Optional[str]] = mapped_column(String)
    bank_account: Mapped[Optional[str]] = mapped_column(String)
    logo_path: Mapped[Optional[str]] = mapped_column(String)
    rounding_minutes: Mapped[int] = mapped_column(Integer, default=15)