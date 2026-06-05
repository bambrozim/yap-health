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


def test_sleep_green_at_8h():
    assert evaluate_value("sleep_duration", 8.0).status == "green"


def test_sleep_red_when_too_short():
    assert evaluate_value("sleep_duration", 4.5).status == "red"


def test_sleep_yellow_when_slightly_short():
    assert evaluate_value("sleep_duration", 6.5).status == "yellow"


def test_sodium_green_under_2g():
    assert evaluate_value("sodium_mg", 1500.0).status == "green"


def test_sodium_red_when_high():
    assert evaluate_value("sodium_mg", 3000.0).status == "red"


def test_fiber_green_at_30g():
    assert evaluate_value("fiber_g", 30.0).status == "green"


def test_sugar_yellow_just_over_limit():
    assert evaluate_value("sugar_g", 55.0).status == "yellow"
