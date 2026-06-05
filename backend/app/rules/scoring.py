from statistics import mean

from app.domain.metrics import metrics_for_domain
from app.rules.evaluation import evaluate_value

_POINTS = {"green": 100, "yellow": 60, "red": 20}
DOMAIN_WEIGHTS = {"cardio": 1.0, "activity": 1.0, "sleep": 1.0}


def status_to_points(status: str) -> int:
    return _POINTS[status]


def domain_score(domain: str, latest_values: dict[str, float]) -> float | None:
    points = []
    for metric in metrics_for_domain(domain):
        if metric not in latest_values:
            continue
        ev = evaluate_value(metric, latest_values[metric])
        if ev is None:
            continue
        points.append(_POINTS[ev.status])
    if not points:
        return None
    return round(mean(points), 1)


def overall_score(domain_scores: dict[str, float | None]) -> float | None:
    pairs = [(s, DOMAIN_WEIGHTS.get(d, 1.0))
             for d, s in domain_scores.items() if s is not None]
    if not pairs:
        return None
    num = sum(s * w for s, w in pairs)
    den = sum(w for _, w in pairs)
    return round(num / den, 1)
