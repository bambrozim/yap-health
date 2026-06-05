from datetime import date, datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models import Base, Measurement
from app.domain.service import build_scoreboard, latest_daily_values


def _seed(s):
    s.add(Measurement(metric="spo2", ts=datetime(2026, 6, 4, 9, tzinfo=timezone.utc),
                      value=96.0, unit="%", source="x", dedup_key="a"))
    s.add(Measurement(metric="resting_heart_rate", ts=datetime(2026, 6, 4, 9, tzinfo=timezone.utc),
                      value=130.0, unit="bpm", source="x", dedup_key="b"))
    s.commit()


def test_latest_daily_values():
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        _seed(s)
        vals = latest_daily_values(s, ["spo2", "resting_heart_rate"],
                                   date(2026, 6, 1), date(2026, 6, 30))
        assert vals["spo2"] == 96.0


def test_build_scoreboard_has_overall_and_domains():
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        _seed(s)
        board = build_scoreboard(s, date(2026, 6, 1), date(2026, 6, 30))
        assert "overall" in board and "domains" in board
        assert board["domains"]["cardio"] is not None
