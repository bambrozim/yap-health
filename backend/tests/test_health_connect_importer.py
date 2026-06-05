from app.ingestion.health_connect import HealthConnectSqliteImporter
from tests.fixtures.make_hc_fixture import build


def test_parses_steps_and_spo2(tmp_path):
    db = build(tmp_path / "export.db")
    importer = HealthConnectSqliteImporter()
    parsed = list(importer.parse(db))
    metrics = {p.metric for p in parsed}
    assert "steps" in metrics and "spo2" in metrics
    steps = [p for p in parsed if p.metric == "steps"]
    assert len(steps) == 2
    assert steps[0].value == 43.0 and steps[0].unit == "count"
    spo2 = [p for p in parsed if p.metric == "spo2"][0]
    assert spo2.value == 96.0


def test_parses_heart_rate_from_series_table(tmp_path):
    db = build(tmp_path / "export.db")
    parsed = list(HealthConnectSqliteImporter().parse(db))
    hr = [p for p in parsed if p.metric == "heart_rate"]
    assert len(hr) == 2
    assert hr[0].value == 64.0 and hr[0].unit == "bpm"
