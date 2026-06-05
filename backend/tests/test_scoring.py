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


def test_overall_is_weighted_mean():
    scores = {"cardio": 60.0, "activity": 100.0}
    assert overall_score(scores) == 80.0
