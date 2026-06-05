from app.rules.scoring import domain_score, overall_score, status_to_points


def test_status_points():
    assert status_to_points("green") == 100
    assert status_to_points("yellow") == 60
    assert status_to_points("red") == 20


def test_domain_score_is_mean_of_scored_metrics():
    # spo2 green (100), resting_heart_rate red (20) -> 60; heart_rate has no target
    latest = {"spo2": 96.0, "resting_heart_rate": 130.0, "heart_rate": 70.0}
    assert domain_score("cardio", latest) == 60.0


def test_domain_score_none_when_no_scored_metric():
    assert domain_score("cardio", {"heart_rate": 70.0}) is None


def test_sleep_domain_scores_from_duration():
    # only sleep_duration is scored; deep/rem are chart-only (no target)
    latest = {"sleep_duration": 8.0, "sleep_deep": 2.0, "sleep_rem": 1.0}
    assert domain_score("sleep", latest) == 100.0


def test_nutrition_scores_from_sodium_sugar_fiber():
    # sodium green(100), sugar green(100), fiber red(20) -> mean 73.3;
    # energy/protein/carbs/fat have no target and are excluded
    latest = {"sodium_mg": 1500.0, "sugar_g": 30.0, "fiber_g": 10.0,
              "energy_kcal": 2000.0, "protein_g": 80.0}
    assert domain_score("nutrition", latest) == 73.3


def test_overall_is_weighted_mean():
    scores = {"cardio": 60.0, "activity": 100.0}
    assert overall_score(scores) == 80.0
