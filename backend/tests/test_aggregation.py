from datetime import date, datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models import Base, Measurement
from app.domain.aggregation import daily_series


def _seed(s):
    for v in (43.0, 17.0, 8.0):  # same day
        s.add(Measurement(metric="steps", ts=datetime(2026, 6, 4, 9, tzinfo=timezone.utc),
                          value=v, unit="count", source="x", dedup_key=str(v)))
    s.add(Measurement(metric="spo2", ts=datetime(2026, 6, 4, 9, tzinfo=timezone.utc),
                      value=96.0, unit="%", source="x", dedup_key="a"))
    s.add(Measurement(metric="spo2", ts=datetime(2026, 6, 4, 10, tzinfo=timezone.utc),
                      value=94.0, unit="%", source="x", dedup_key="b"))
    s.commit()


def test_steps_sum_spo2_mean():
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        _seed(s)
        steps = daily_series(s, "steps", date(2026, 6, 1), date(2026, 6, 30))
        assert steps == [(date(2026, 6, 4), 68.0)]
        spo2 = daily_series(s, "spo2", date(2026, 6, 1), date(2026, 6, 30))
        assert spo2 == [(date(2026, 6, 4), 95.0)]
