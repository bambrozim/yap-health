from datetime import date

from app.rules.insights import trend_insight


def test_rhr_rise_flagged():
    baseline = [(date(2026, 5, d), 60.0) for d in range(1, 29)]
    recent = [(date(2026, 6, 1), 67.0)]
    msg = trend_insight("resting_heart_rate", baseline, recent)
    assert msg is not None
    assert "subiu" in msg.text.lower()


def test_stable_rhr_no_insight():
    baseline = [(date(2026, 5, d), 60.0) for d in range(1, 29)]
    recent = [(date(2026, 6, 1), 61.0)]
    assert trend_insight("resting_heart_rate", baseline, recent) is None


def test_hrv_drop_flagged():
    baseline = [(date(2026, 5, d), 50.0) for d in range(1, 29)]
    recent = [(date(2026, 6, 1), 35.0)]
    msg = trend_insight("hrv_rmssd", baseline, recent)
    assert msg is not None
    assert "caiu" in msg.text.lower()
