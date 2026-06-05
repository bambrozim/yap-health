from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.main import app, get_session
from app.db.models import Base, Measurement


def _override():
    # StaticPool shares one in-memory connection across sessions so the
    # seeded data is visible to the request-scoped dependency session.
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False},
                        poolclass=StaticPool)
    Base.metadata.create_all(eng)
    SL = sessionmaker(bind=eng)
    with SL() as s:
        s.add(Measurement(metric="spo2", ts=datetime(2026, 6, 4, 9, tzinfo=timezone.utc),
                          value=96.0, unit="%", source="x", dedup_key="a"))
        s.add(Measurement(metric="resting_heart_rate",
                          ts=datetime(2026, 6, 4, 9, tzinfo=timezone.utc),
                          value=130.0, unit="bpm", source="x", dedup_key="b"))
        s.commit()

    def _dep():
        with SL() as s:
            yield s
    return _dep


def test_score_endpoint():
    app.dependency_overrides[get_session] = _override()
    client = TestClient(app)
    r = client.get("/api/score?from=2026-06-01&to=2026-06-30")
    assert r.status_code == 200
    body = r.json()
    assert "overall" in body and "domains" in body
    app.dependency_overrides.clear()


def test_metric_series_endpoint():
    app.dependency_overrides[get_session] = _override()
    client = TestClient(app)
    r = client.get("/api/metrics/spo2?from=2026-06-01&to=2026-06-30")
    assert r.status_code == 200
    assert r.json()["points"][0]["value"] == 96.0
    app.dependency_overrides.clear()


def test_unknown_metric_404():
    app.dependency_overrides[get_session] = _override()
    client = TestClient(app)
    r = client.get("/api/metrics/bogus?from=2026-06-01&to=2026-06-30")
    assert r.status_code == 404
    app.dependency_overrides.clear()


def test_alerts_endpoint_flags_red_rhr():
    app.dependency_overrides[get_session] = _override()
    client = TestClient(app)
    r = client.get("/api/alerts?from=2026-06-01&to=2026-06-30")
    assert r.status_code == 200
    metrics = {a["metric"] for a in r.json()["alerts"]}
    assert "resting_heart_rate" in metrics  # 130 bpm -> red
    app.dependency_overrides.clear()
