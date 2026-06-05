from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models import Base, Measurement


def test_measurement_roundtrip():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        s.add(Measurement(
            metric="steps", ts=datetime(2026, 6, 4, tzinfo=timezone.utc),
            value=43.0, unit="count", source="health_connect",
            dedup_key="hc:abc"))
        s.commit()
        row = s.query(Measurement).one()
        assert row.metric == "steps"
        assert row.value == 43.0
