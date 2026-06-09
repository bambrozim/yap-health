from app.ingestion.health_sync_csv import HealthSyncCsvImporter


def _write(tmp_path, name, text):
    f = tmp_path / name
    f.write_text(text)
    return f


def test_steps_csv(tmp_path):
    f = _write(tmp_path, "Steps.csv",
               "Date,Time,Steps,Source\n2026.05.20 06:01:00,06:01:00,19,x\n")
    out = list(HealthSyncCsvImporter().parse(f))
    assert len(out) == 1
    assert out[0].metric == "steps" and out[0].value == 19.0
    assert out[0].ts.isoformat().startswith("2026-05-20T06:01:00")


def test_resting_vs_normal_heart_rate(tmp_path):
    hr = _write(tmp_path, "HR.csv",
                "Date,Time,Heart rate,Source\n2026.05.20 00:06:00,00:06:00,57,x\n")
    rhr = _write(tmp_path, "RHR.csv",
                 "Date,Time,Resting heart rate,Source\n2026.05.20 00:00:00,00:00:00,57,x\n")
    assert list(HealthSyncCsvImporter().parse(hr))[0].metric == "heart_rate"
    assert list(HealthSyncCsvImporter().parse(rhr))[0].metric == "resting_heart_rate"


def test_energy_burned_csv(tmp_path):
    f = _write(tmp_path, "Energy.csv",
               'Date,Time,Active calories,Resting calories,Total calories\n'
               '2026.05.20 00:00:00,00:00:00,"208.1","1886.3","2094.5"\n')
    metrics = {m.metric: m.value for m in HealthSyncCsvImporter().parse(f)}
    assert metrics["active_calories"] == 208.1  # already kcal, no /1000
    assert metrics["total_calories"] == 2094.5


def test_sleep_csv_duration_and_stages(tmp_path):
    f = _write(tmp_path, "Sleep.csv",
               "Date,Time,Duration in seconds,Sleep stage\n"
               "2026.06.04 01:00:00,01:00:00,3600,deep\n"
               "2026.06.04 02:00:00,02:00:00,1800,rem\n"
               "2026.06.04 03:00:00,03:00:00,600,awake\n")
    out = list(HealthSyncCsvImporter().parse(f))
    dur = sum(m.value for m in out if m.metric == "sleep_duration")
    assert dur == 1.5  # 3600s + 1800s = 5400s = 1.5h; awake excluded
    assert [m.value for m in out if m.metric == "sleep_deep"] == [1.0]
    assert [m.value for m in out if m.metric == "sleep_rem"] == [0.5]


def test_nutrition_csv(tmp_path):
    f = _write(tmp_path, "Nutrition.csv",
               "Date,Time,Meal,Name,Description,kCal,Carbohydrate (gram),"
               "Cholestorol (mg),Fat (gram),Fiber (gram),Sugar (gram)\n"
               "2026.05.11 00:00:00,00:00:00,5,null,null,366.0,38.95,0.0,16.15,2.3,2.27\n")
    metrics = {m.metric: m.value for m in HealthSyncCsvImporter().parse(f)}
    assert metrics["energy_kcal"] == 366.0
    assert metrics["fiber_g"] == 2.3
    assert "sodium_mg" not in metrics  # not present in Health Sync nutrition CSV


def test_weight_csv_with_height_derives_bmi(tmp_path):
    f = _write(tmp_path, "Weight.csv",
               "Date,Time,Weight,Body fat percentage\n"
               '2026.05.30 08:11:57,08:11:57,"80.0","25.0"\n')
    metrics = {m.metric: m.value for m in
               HealthSyncCsvImporter(height_m=2.0).parse(f)}
    assert metrics["weight_kg"] == 80.0
    assert metrics["body_fat_pct"] == 25.0
    assert metrics["bmi"] == 20.0


def test_unknown_csv_yields_nothing(tmp_path):
    f = _write(tmp_path, "Training.csv",
               "Source app,Activity type,Activity name,Date,Time\n"
               "hevy,TRAINING,null,2026.06.04 08:12:55,08:12:55\n")
    assert list(HealthSyncCsvImporter().parse(f)) == []
