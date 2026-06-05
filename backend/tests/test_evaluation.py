from app.rules.evaluation import evaluate_value


def test_spo2_red_below_92():
    r = evaluate_value("spo2", 90.0)
    assert r.status == "red"
    assert r.source


def test_spo2_green_at_96():
    assert evaluate_value("spo2", 96.0).status == "green"


def test_rhr_yellow_just_above_range():
    assert evaluate_value("resting_heart_rate", 105.0).status == "yellow"


def test_steps_green_above_target():
    assert evaluate_value("steps", 9000.0).status == "green"


def test_metric_without_target_returns_none():
    assert evaluate_value("heart_rate", 70.0) is None
