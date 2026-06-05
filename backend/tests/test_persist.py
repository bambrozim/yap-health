from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models import Base, Measurement
from app.ingestion.base import ParsedMeasurement
from app.ingestion.persist import persist_measurements


def _session():
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    return Session(eng)


def test_persist_is_idempotent():
    s = _session()
    items = [ParsedMeasurement("steps", datetime(2026, 6, 4, tzinfo=timezone.utc), 43.0, "count")]
    n1 = persist_measurements(s, items, source="csv")
    n2 = persist_measurements(s, items, source="csv")  # same data again
    assert n1 == 1
    assert n2 == 0  # deduped
    assert s.query(Measurement).count() == 1
