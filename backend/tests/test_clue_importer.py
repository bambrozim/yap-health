import json

from app.ingestion.clue import ClueJsonImporter

MEASUREMENTS = [
    {"type": "period", "id": "a", "date": "2026-05-23", "value": {"option": "heavy"}},
    {"type": "period", "id": "b", "date": "2026-05-24", "value": {"option": "medium"}},
    {"type": "feelings", "id": "c", "date": "2026-05-24", "value": [{"option": "sad"}]},
    {"type": "sleep_duration", "id": "d", "date": "2026-05-24", "value": {"minutes": 400}},
]


def _write(tmp_path):
    f = tmp_path / "measurements.json"
    f.write_text(json.dumps(MEASUREMENTS))
    return f


def test_matches_only_measurements_json(tmp_path):
    imp = ClueJsonImporter()
    assert imp.matches(tmp_path / "measurements.json")
    assert not imp.matches(tmp_path / "user.json")
    assert not imp.matches(tmp_path / "export.db")


def test_parses_only_period_entries(tmp_path):
    f = _write(tmp_path)
    entries = sorted(ClueJsonImporter().parse(f), key=lambda e: e.day)
    assert len(entries) == 2  # feelings/sleep ignored
    assert entries[0].day.isoformat() == "2026-05-23"
    assert entries[0].flow == "heavy"
    assert entries[1].flow == "medium"
