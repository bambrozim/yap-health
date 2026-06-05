from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Measurement(Base):
    __tablename__ = "measurements"
    __table_args__ = (UniqueConstraint("dedup_key", name="uq_measurement_dedup"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    metric: Mapped[str] = mapped_column(String, index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    dedup_key: Mapped[str] = mapped_column(String)


class Workout(Base):
    __tablename__ = "workouts"
    __table_args__ = (UniqueConstraint("dedup_key", name="uq_workout_dedup"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String)
    start_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_s: Mapped[int] = mapped_column(Integer)
    distance_km: Mapped[float] = mapped_column(Float, default=0.0)
    calories: Mapped[float] = mapped_column(Float, default=0.0)
    source: Mapped[str] = mapped_column(String)
    dedup_key: Mapped[str] = mapped_column(String)


class ImportRun(Base):
    __tablename__ = "import_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    rows_imported: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    error: Mapped[str] = mapped_column(String, default="")
