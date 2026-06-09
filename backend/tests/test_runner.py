from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models import Base, Measurement
from app.ingestion.runner import process_file
from tests.fixtures.make_hc_fixture import build


def test_process_db_file_populates_measurements(tmp_path):
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    db = build(tmp_path / "export.db")
    with Session(eng) as s:
        run = process_file(s, db)
        assert run.status == "ok"
        assert run.rows_imported > 0
        assert s.query(Measurement).filter_by(metric="steps").count() == 2


def test_process_clue_measurements_populates_cycle(tmp_path):
    import json

    from app.db.models import CycleEntry
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    f = tmp_path / "measurements.json"
    f.write_text(json.dumps([
        {"type": "period", "id": "a", "date": "2026-05-23", "value": {"option": "heavy"}},
        {"type": "feelings", "id": "b", "date": "2026-05-23", "value": [{"option": "sad"}]},
    ]))
    with Session(eng) as s:
        run = process_file(s, f)
        assert run.status == "ok"
        assert run.rows_imported == 1
        assert s.query(CycleEntry).count() == 1


def test_process_unknown_file_is_skipped(tmp_path):
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    f = tmp_path / "notes.txt"
    f.write_text("hello")
    with Session(eng) as s:
        run = process_file(s, f)
        assert run.status == "skipped"
