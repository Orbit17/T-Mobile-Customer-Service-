from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .database import Base


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), index=True, unique=True)
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    events: Mapped[list["Event"]] = relationship("Event", back_populates="source")


class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime, index=True)
    region: Mapped[str] = mapped_column(String(64), index=True)
    source_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sources.id"), nullable=True)
    text: Mapped[str] = mapped_column(Text)
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # For app reviews
    keywords: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    sentiment: Mapped[Optional[float]] = mapped_column(Float, index=True, nullable=True)  # -1..1
    topic: Mapped[Optional[str]] = mapped_column(String(32), index=True, nullable=True)

    source: Mapped[Optional[Source]] = relationship("Source", back_populates="events")

    __table_args__ = (
        Index("idx_events_region_ts", "region", "ts"),
    )


class KPI(Base):
    __tablename__ = "kpis"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime, index=True)
    region: Mapped[str] = mapped_column(String(64), index=True)
    download_mbps: Mapped[float] = mapped_column(Float)
    latency_ms: Mapped[float] = mapped_column(Float)

    __table_args__ = (
        Index("idx_kpis_region_ts", "region", "ts"),
    )


class CHI(Base):
    __tablename__ = "chi"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime, index=True)
    region: Mapped[str] = mapped_column(String(64), index=True)
    score: Mapped[float] = mapped_column(Float)
    drivers_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index("idx_chi_region_ts", "region", "ts"),
    )


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime, index=True)
    region: Mapped[str] = mapped_column(String(64), index=True)
    chi_before: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    chi_after: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reason: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index("idx_alerts_region_ts", "region", "ts"),
    )


class Runbook(Base):
    __tablename__ = "runbook"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    issue: Mapped[str] = mapped_column(String(128), unique=True)
    steps: Mapped[list] = mapped_column(JSON)


