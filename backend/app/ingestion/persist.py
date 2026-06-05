from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Measurement, Workout
from app.ingestion.base import ParsedMeasurement, ParsedWorkout, make_dedup_key


def persist_measurements(session: Session, items: Iterable[ParsedMeasurement],
                         source: str, source_uuid: str | None = None) -> int:
    inserted = 0
    for it in items:
        key = make_dedup_key(it.metric, it.ts, it.value, source, source_uuid)
        if session.scalar(select(Measurement.id).where(Measurement.dedup_key == key)):
            continue
        session.add(Measurement(metric=it.metric, ts=it.ts, value=it.value,
                                unit=it.unit, source=source, dedup_key=key))
        inserted += 1
    session.commit()
    return inserted


def persist_workouts(session: Session, items: Iterable[ParsedWorkout],
                     source: str) -> int:
    inserted = 0
    for w in items:
        key = make_dedup_key("workout", w.start_ts, w.duration_s, source, w.source_uuid)
        if session.scalar(select(Workout.id).where(Workout.dedup_key == key)):
            continue
        session.add(Workout(type=w.type, start_ts=w.start_ts, end_ts=w.end_ts,
                            duration_s=w.duration_s, distance_km=w.distance_km,
                            calories=w.calories, source=source, dedup_key=key))
        inserted += 1
    session.commit()
    return inserted
