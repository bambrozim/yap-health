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


def test_parses_sleep_duration_and_stages(tmp_path):
    db = build(tmp_path / "export.db")
    parsed = list(HealthConnectSqliteImporter().parse(db))
    dur = [p for p in parsed if p.metric == "sleep_duration"]
    assert len(dur) == 1
    assert dur[0].value == 8.0 and dur[0].unit == "h"
    deep = [p for p in parsed if p.metric == "sleep_deep"]
    rem = [p for p in parsed if p.metric == "sleep_rem"]
    assert deep[0].value == 2.0
    assert rem[0].value == 1.0
    # light stage (type 4) is not surfaced
    assert not [p for p in parsed if p.metric == "sleep_light"]


def test_parses_nutrition_and_skips_empty(tmp_path):
    db = build(tmp_path / "export.db")
    parsed = list(HealthConnectSqliteImporter().parse(db))
    energy = [p for p in parsed if p.metric == "energy_kcal"]
    assert len(energy) == 1  # the 0-energy record is skipped
    assert energy[0].value == 1410.0 and energy[0].unit == "kcal"
    sodium = [p for p in parsed if p.metric == "sodium_mg"][0]
    assert sodium.value == 2017.0 and sodium.unit == "mg"  # grams -> mg
    fiber = [p for p in parsed if p.metric == "fiber_g"][0]
    assert fiber.value == 19.2 and fiber.unit == "g"


def test_parses_body_weight_and_derives_bmi(tmp_path):
    db = build(tmp_path / "export.db")
    parsed = list(HealthConnectSqliteImporter().parse(db))
    weight = [p for p in parsed if p.metric == "weight_kg"][0]
    assert weight.value == 80.0 and weight.unit == "kg"  # grams -> kg
    bmi = [p for p in parsed if p.metric == "bmi"][0]
    assert bmi.value == 20.0  # 80 kg / (2.0 m)^2
    fat = [p for p in parsed if p.metric == "body_fat_pct"][0]
    assert fat.value == 25.0 and fat.unit == "%"
