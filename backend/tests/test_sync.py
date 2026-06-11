from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Base, Measurement
from app.ingestion.runner import sync_from_source

STEPS_CSV = "Date,Time,Steps,Source\n2026.05.20 06:01:00,06:01:00,19,x\n"


def test_sync_from_configured_source(tmp_path, monkeypatch):
    src = tmp_path / "Health Sync Steps"
    src.mkdir()
    (src / "Steps.csv").write_text(STEPS_CSV)
    # Point ingestion at tmp_path (which contains a "Health Sync *" marker folder).
    monkeypatch.setattr(settings, "source_dir", tmp_path)

    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        result = sync_from_source(s)
        assert result["ok"] is True
        assert result["rows"] == 1
        assert str(tmp_path) in result["source_dir"]
        assert s.query(Measurement).filter_by(metric="steps").count() == 1


def test_sync_reports_when_no_source(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "source_dir", None)
    # Search an empty dir so auto-detect finds nothing.
    import app.ingestion.runner as runner
    monkeypatch.setattr(runner, "resolve_source_dir", lambda explicit: None)

    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        result = sync_from_source(s)
        assert result["ok"] is False
        assert result["source_dir"] is None
        assert "Drive" in result["reason"]
